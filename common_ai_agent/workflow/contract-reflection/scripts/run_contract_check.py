#!/usr/bin/env python3

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_json import (
    JSON_ADAPTER,
    JsonList,
    JsonMap,
    JsonValue,
    as_map as _as_map,
    strings as _strings,
)
from workflow.contract_reflection.owner_routing import route_from_reports


@dataclass(frozen=True)
class StepRun:
    label: str
    returncode: int
    stdout: str


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _parse_args(argv: list[str]) -> tuple[str, Path, bool, bool]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: run_contract_check.py <ip> [--root <root>] [--require-contract-closure] [--require-sim-freshness]")
    ip = argv[0]
    root = Path(".")
    require_contract_closure = False
    require_sim_freshness = False
    index = 1
    while index < len(argv):
        token = argv[index]
        if token == "--require-contract-closure":
            require_contract_closure = True
            index += 1
            continue
        if token == "--require-sim-freshness":
            require_sim_freshness = True
            index += 1
            continue
        if token != "--root":
            raise SystemExit(f"usage: unexpected argument {token!r}")
        if index + 1 >= len(argv):
            raise SystemExit("usage: --root requires a value")
        root = Path(argv[index + 1])
        index += 2
    return ip, root.resolve(), require_contract_closure, require_sim_freshness


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw = Path(ip)
    if raw.is_absolute():
        raise SystemExit(f"[contract_check] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[contract_check] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _load_json(path: Path) -> JsonMap:
    if not path.is_file():
        return {}
    try:
        value = JSON_ADAPTER.validate_json(path.read_text(encoding="utf-8"))
    except ValidationError:
        return {}
    return value if isinstance(value, dict) else {}


def _script(name: str) -> Path:
    return Path(__file__).resolve().parent / name


def _run(label: str, script: Path, ip: str, root: Path) -> StepRun:
    proc = subprocess.run(
        [sys.executable, str(script), ip, "--root", str(root)],
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return StepRun(label, int(proc.returncode), (proc.stdout or "").strip())


def _step_reports(runs: list[StepRun]) -> JsonList:
    reports: JsonList = []
    for run in runs:
        reports.append({"label": run.label, "returncode": run.returncode, "stdout": run.stdout})
    return reports


def _summary(reflection: JsonMap, evidence: JsonMap) -> JsonMap:
    reflection_summary = _as_map(reflection.get("summary"))
    evidence_summary = _as_map(evidence.get("summary"))
    return {
        "evidence_failed": _int_value(evidence_summary.get("failed")),
        "evidence_passed": _int_value(evidence_summary.get("passed")),
        "evidence_total": _int_value(evidence_summary.get("total")),
        "reflection_failed": _int_value(reflection_summary.get("failed")),
        "reflection_passed": _int_value(reflection_summary.get("passed")),
        "reflection_total": _int_value(reflection_summary.get("total")),
    }


def _int_value(value: JsonValue) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else 0


def _status(reflection: JsonMap, evidence: JsonMap, overlays: list[StepRun], reflection_run: StepRun, evidence_run: StepRun) -> str:
    if any(run.returncode != 0 for run in overlays):
        return "fail"
    child_failed = reflection_run.returncode != 0 or evidence_run.returncode != 0
    if reflection.get("status") == "pass" and evidence.get("status") == "pass":
        if child_failed:
            return "fail"
        return "pass"
    return "blocked"


def _failed_step_route(ip_dir: Path, run: StepRun) -> JsonMap:
    owner = "sim-debug" if run.label == "sim_evidence_freshness" else "contract-reflection"
    commands: JsonList = ["/wf sim-debug", "/contract-check <ip> --require-sim-freshness"] if owner == "sim-debug" else ["/wf contract-reflection", "/contract-check <ip>"]
    return {
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "owner_workflow": owner,
        "reason": f"{run.label}: {run.stdout}",
        "rerun_after_repair": ["contract-check"],
        "schema_version": 1,
        "status": "blocked",
        "suggested_commands": commands,
        "type": "contract_owner_routing",
    }


def _stale_child_failure(reflection: JsonMap, evidence: JsonMap, reflection_run: StepRun, evidence_run: StepRun) -> StepRun | None:
    if reflection_run.returncode != 0 and reflection.get("status") == "pass":
        return reflection_run
    if evidence_run.returncode != 0 and evidence.get("status") == "pass":
        return evidence_run
    return None


def _write_owner_route(ip_dir: Path, route: JsonMap) -> None:
    out = ip_dir / "signoff" / "contract_owner_routing.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(route, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_report(ip_dir: Path, status: str, runs: list[StepRun], reflection: JsonMap, evidence: JsonMap, route: JsonMap) -> JsonMap:
    report: JsonMap = {
        "artifacts": [
            "verify/semantic_contracts.json",
            "verify/requirements_index.json",
            "verify/evidence_contract.json",
            "verify/contract_reflection.json",
            "signoff/contract_reflection_coverage.json",
            "signoff/evidence_contract_coverage.json",
            "sim/evidence_freshness.json",
            "signoff/sim_evidence_freshness.json",
            "signoff/contract_owner_routing.json",
        ],
        "evidence": evidence,
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "owner_route": route,
        "reflection": reflection,
        "runs": _step_reports(runs),
        "schema_version": 1,
        "status": status,
        "summary": _summary(reflection, evidence),
        "type": "contract_check",
    }
    out = ip_dir / "signoff" / "contract_check.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def _print_report(report: JsonMap) -> None:
    status = str(report.get("status") or "").upper()
    print(f"Contract Check: {status}")
    summary = _as_map(report.get("summary"))
    reflection = _as_map(report.get("reflection"))
    evidence = _as_map(report.get("evidence"))
    print(f"Reflection: {reflection.get('status', 'missing')} {summary.get('reflection_passed')}/{summary.get('reflection_total')}")
    print(f"Evidence: {evidence.get('status', 'missing')} {summary.get('evidence_passed')}/{summary.get('evidence_total')}")
    route = _as_map(report.get("owner_route"))
    owner = str(route.get("owner_workflow") or "")
    if owner:
        print(f"Owner: {owner}")
        print(f"Reason: {route.get('reason') or ''}")
        print(f"Rerun after repair: {' -> '.join(_strings(route.get('rerun_after_repair')))}")


def main() -> int:
    ip, root, require_contract_closure, require_sim_freshness = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    runs: list[StepRun] = []
    semantic_overlay = StepRun("semantic_contract_overlay", 0, "skipped: verify/semantic_contracts.json not present")
    if (ip_dir / "verify" / "semantic_contracts.json").is_file():
        semantic_overlay = _run("semantic_contract_overlay", _script("emit_semantic_contract_overlay.py"), ip, root)
    elif require_contract_closure:
        semantic_overlay = StepRun("semantic_contract_overlay", 1, "required: missing verify/semantic_contracts.json")
    runs.append(semantic_overlay)
    overlay = StepRun("goal_contract_overlay", 0, "skipped: verify/equivalence_goals.json not present")
    if (ip_dir / "verify" / "equivalence_goals.json").is_file():
        overlay = _run("goal_contract_overlay", _script("emit_goal_contract_overlay.py"), ip, root)
    runs.append(overlay)
    sim_freshness = StepRun("sim_evidence_freshness", 0, "skipped: --require-sim-freshness not set")
    if require_sim_freshness:
        sim_freshness = _run("sim_evidence_freshness", _script("check_sim_evidence_freshness.py"), ip, root)
    runs.append(sim_freshness)
    reflection_run = _run("contract_reflection", _script("check_contract_reflection.py"), ip, root)
    evidence_run = _run("evidence_contract", _script("check_evidence_contract.py"), ip, root)
    runs.extend([reflection_run, evidence_run])
    reflection = _load_json(ip_dir / "signoff" / "contract_reflection_coverage.json")
    evidence = _load_json(ip_dir / "signoff" / "evidence_contract_coverage.json")
    route: JsonMap = {}
    status = _status(reflection, evidence, [semantic_overlay, overlay, sim_freshness], reflection_run, evidence_run)
    stale_child = _stale_child_failure(reflection, evidence, reflection_run, evidence_run)
    if status == "pass":
        route = route_from_reports(ip_dir)
        _write_owner_route(ip_dir, route)
    elif stale_child is not None:
        route = _failed_step_route(ip_dir, stale_child)
        _write_owner_route(ip_dir, route)
    else:
        owner_run = _run("contract_owner", _script("classify_contract_owner.py"), ip, root)
        runs.append(owner_run)
        route = _load_json(ip_dir / "signoff" / "contract_owner_routing.json")
        for run in (sim_freshness, semantic_overlay, overlay):
            if run.returncode != 0:
                route = _failed_step_route(ip_dir, run)
                _write_owner_route(ip_dir, route)
                break
    report = _write_report(ip_dir, status, runs, reflection, evidence, route)
    _print_report(report)
    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
