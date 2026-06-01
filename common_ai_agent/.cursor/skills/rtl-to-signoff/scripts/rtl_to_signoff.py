#!/usr/bin/env python3
"""Cursor runner for the ATLAS RTL-to-signoff workflow.

DV stages are delegated to WorkflowStageEngine, the same common engine used by
ATLAS UI/Textual/headless flows. EDA stages are delegated to workflow command
scripts. This file routes stages and aggregates evidence; it does not define
pass/fail policy itself.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
SKILL_ROOT = SCRIPT.parents[1]
SOURCE_ROOT = SCRIPT.parents[4]
MANIFEST_PATH = SKILL_ROOT / "STAGE_MANIFEST.json"

if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from src.workflow_stage_engine import WorkflowStageEngine  # noqa: E402
from src.workflow_stage_surface import compute_kpi_dots_labeled  # noqa: E402


def utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def expand_evidence(items: list[str], ip: str) -> list[str]:
    return [item.replace("<ip>", ip) for item in items]


def stage_sequence(manifest: dict[str, Any], profile: str, include_dft: bool) -> list[str]:
    profiles = manifest["profiles"]
    if profile not in profiles:
        raise SystemExit(f"unknown --profile {profile!r}; choose one of: {', '.join(sorted(profiles))}")
    stages = list(profiles[profile])
    if include_dft and "dft" not in stages:
        stages.append("dft")
    return stages


def slice_stages(stages: list[str], from_stage: str | None, until: str | None) -> list[str]:
    if from_stage and from_stage not in stages:
        raise SystemExit(f"unknown --from-stage {from_stage!r}; choose one of: {', '.join(stages)}")
    if until and until not in stages:
        raise SystemExit(f"unknown --until {until!r}; choose one of: {', '.join(stages)}")
    start = stages.index(from_stage) if from_stage else 0
    end = stages.index(until) + 1 if until else len(stages)
    return stages[start:end]


def stage_log_path(root: Path, ip: str, engine_stage: str) -> str:
    return str(root / ip / "logs" / "stage_engine" / f"{engine_stage}.json")


def plan_stage(stage_id: str, spec: dict[str, Any], root: Path, ip: str) -> None:
    evidence = expand_evidence(spec.get("evidence", []), ip)
    print(f"[{stage_id}]")
    print(f"  invoke : {spec['invoke']}")
    print(f"  owner  : {spec.get('owner', '')}")
    print(f"  slash  : {spec.get('slash', '')}")
    if spec.get("command_json"):
        print(f"  command: {spec['command_json']}")
    if spec["invoke"] == "engine":
        print(f"  engine : WorkflowStageEngine.run_stage({spec['engine_stage']!r}, {ip!r})")
    elif spec["invoke"] == "bash":
        print(f"  script : {spec['script']}")
    elif spec["invoke"] == "headless":
        print(f"  script : src/headless_workflow.py --stages {spec.get('stages_arg', 'pipeline')}")
    if evidence:
        print(f"  evidence: {', '.join(evidence)}")
    try:
        dots = compute_kpi_dots_labeled(ip, spec.get("pipeline_id", stage_id), root=root)
    except Exception as exc:  # planning must not fail just because KPI read failed
        print(f"  kpi    : unavailable ({exc})")
    else:
        if dots:
            rendered = ", ".join(f"{dot.get('label')}={dot.get('state')}" for dot in dots)
            print(f"  kpi    : {rendered}")
    print("")


def run_engine_stage(stage_id: str, spec: dict[str, Any], root: Path, ip: str, run_mode: str) -> dict[str, Any]:
    engine_stage = spec["engine_stage"]
    print(f"\n=== [{stage_id}] common-engine:{engine_stage}", flush=True)
    result = WorkflowStageEngine(root, source_root=SOURCE_ROOT, run_mode=run_mode).run_stage(engine_stage, ip)
    print(result.message)
    record = result.to_dict()
    record.update(
        {
            "stage_id": stage_id,
            "invoke": "engine",
            "owner": spec.get("owner", ""),
            "slash": spec.get("slash", ""),
            "pipeline_id": spec.get("pipeline_id", stage_id),
            "evidence": expand_evidence(spec.get("evidence", []), ip),
            "stage_log": stage_log_path(root, ip, result.stage),
        }
    )
    if result.status in {"blocked", "human_gate", "fail"}:
        record["repair_route"] = {
            "owner": spec.get("owner", ""),
            "workflow": record.get("workflow", ""),
            "blocker": result.blocker,
            "next": f"route repair through {spec.get('owner', record.get('workflow', 'owner workflow'))} and rerun from {stage_id}",
        }
    print(f"=== [{stage_id}] {result.status.upper()} rc={result.returncode}", flush=True)
    return record


def run_bash_stage(stage_id: str, spec: dict[str, Any], root: Path, ip: str, env: dict[str, str]) -> dict[str, Any]:
    script = SOURCE_ROOT / spec["script"]
    timeout = int(spec.get("timeout_sec") or 300)
    command = ["bash", str(script), ip]
    print(f"\n=== [{stage_id}] {' '.join(shlex.quote(part) for part in command)}", flush=True)
    proc = subprocess.run(
        command,
        cwd=root,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    status = "pass" if proc.returncode == 0 else ("optional-fail" if spec.get("optional") else "fail")
    print(f"=== [{stage_id}] {status.upper()} rc={proc.returncode}", flush=True)
    return {
        "stage_id": stage_id,
        "stage": stage_id,
        "invoke": "bash",
        "owner": spec.get("owner", ""),
        "slash": spec.get("slash", ""),
        "pipeline_id": spec.get("pipeline_id", stage_id),
        "command": command,
        "cwd": str(root),
        "status": status,
        "returncode": proc.returncode,
        "evidence": expand_evidence(spec.get("evidence", []), ip),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
        "repair_route": {
            "owner": spec.get("owner", ""),
            "next": f"fix {spec.get('owner', stage_id)} inputs/environment and rerun from {stage_id}",
        } if status == "fail" else {},
    }


def run_headless_stage(stage_id: str, spec: dict[str, Any], root: Path, ip: str, args: argparse.Namespace, env: dict[str, str]) -> dict[str, Any]:
    command = [
        sys.executable,
        str(SOURCE_ROOT / "src" / "headless_workflow.py"),
        "--root",
        str(root),
        "--ip",
        ip,
        "--stages",
        str(spec.get("stages_arg") or "pipeline"),
        "--provider",
        args.provider,
        "--run-mode",
        args.run_mode,
    ]
    if args.req:
        command.extend(["--req", args.req])
    print(f"\n=== [{stage_id}] {' '.join(shlex.quote(part) for part in command)}", flush=True)
    proc = subprocess.run(
        command,
        cwd=SOURCE_ROOT,
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=args.timeout,
        check=False,
    )
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    status = "pass" if proc.returncode == 0 else "fail"
    print(f"=== [{stage_id}] {status.upper()} rc={proc.returncode}", flush=True)
    return {
        "stage_id": stage_id,
        "stage": stage_id,
        "invoke": "headless",
        "owner": spec.get("owner", ""),
        "slash": spec.get("slash", ""),
        "pipeline_id": spec.get("pipeline_id", stage_id),
        "command": command,
        "cwd": str(SOURCE_ROOT),
        "status": status,
        "returncode": proc.returncode,
        "evidence": expand_evidence(spec.get("evidence", []), ip),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def write_summary(root: Path, ip: str, args: argparse.Namespace, selected: list[str], results: list[dict[str, Any]]) -> Path:
    verify_dir = root / ip / "verify"
    verify_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema_version": 2,
        "type": "cursor_rtl_to_signoff_summary",
        "ip": ip,
        "root": str(root),
        "source_root": str(SOURCE_ROOT),
        "manifest": str(MANIFEST_PATH),
        "generated_at": utc(),
        "command": sys.argv,
        "profile": args.profile,
        "selected_stages": selected,
        "run_mode": args.run_mode,
        "provider": args.provider,
        "passed": all(item.get("status") in {"pass", "optional-fail"} for item in results),
        "results": results,
    }
    out = verify_dir / "cursor_rtl_to_signoff_summary.json"
    out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the common_ai_agent RTL-to-signoff workflow through Cursor.")
    parser.add_argument("ip", help="IP directory name relative to --root")
    parser.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT", "."), help="IP parent root")
    profile_choices = sorted(load_manifest()["profiles"])
    parser.add_argument("--profile", choices=profile_choices, default="full")
    parser.add_argument("--run-mode", choices=["starter", "engineering", "signoff"], default=os.environ.get("ATLAS_RUN_MODE", "signoff"))
    parser.add_argument("--provider", choices=["fake", "cached", "real"], default="fake", help="Provider for headless stages only")
    parser.add_argument("--req", default="", help="Requirement file for headless stages")
    parser.add_argument("--plan", action="store_true", help="Show stages, owners, KPIs, and evidence without running")
    parser.add_argument("--execute", action="store_true", help="Run selected stages")
    parser.add_argument("--from-stage", default=None, help="Start at a manifest stage id")
    parser.add_argument("--until", default=None, help="Stop after a manifest stage id")
    parser.add_argument("--include-dft", action="store_true", help="Append optional dft stage")
    parser.add_argument("--timeout", type=int, default=1800, help="Timeout for headless stages, seconds")
    args = parser.parse_args()

    if args.plan == args.execute:
        parser.error("choose exactly one of --plan or --execute")

    manifest = load_manifest()
    root = Path(args.root).expanduser().resolve()
    ip_dir = root / args.ip
    if not ip_dir.is_dir():
        raise SystemExit(f"IP directory not found: {ip_dir}")
    if not (SOURCE_ROOT / "workflow").is_dir():
        raise SystemExit(f"workflow directory not found under source root: {SOURCE_ROOT}")

    selected = slice_stages(
        stage_sequence(manifest, args.profile, include_dft=args.include_dft),
        from_stage=args.from_stage,
        until=args.until,
    )
    specs = manifest["stages"]

    print(f"source_root: {SOURCE_ROOT}")
    print(f"ip_root    : {root}")
    print(f"ip         : {args.ip}")
    print(f"profile    : {args.profile}")
    print(f"run_mode   : {args.run_mode}")
    print("")

    if args.plan:
        for stage_id in selected:
            plan_stage(stage_id, specs[stage_id], root, args.ip)
        return 0

    env = os.environ.copy()
    env.setdefault("ATLAS_SOURCE_ROOT", str(SOURCE_ROOT))
    env.setdefault("ATLAS_WORKFLOW_ROOT", str(SOURCE_ROOT / "workflow"))
    env.setdefault("ATLAS_PROJECT_ROOT", str(root))
    env.setdefault("ATLAS_RUN_MODE", args.run_mode)
    env.setdefault("IP_NAME", args.ip)

    results: list[dict[str, Any]] = []
    for stage_id in selected:
        spec = specs[stage_id]
        try:
            if spec["invoke"] == "engine":
                record = run_engine_stage(stage_id, spec, root, args.ip, args.run_mode)
            elif spec["invoke"] == "bash":
                record = run_bash_stage(stage_id, spec, root, args.ip, env)
            elif spec["invoke"] == "headless":
                record = run_headless_stage(stage_id, spec, root, args.ip, args, env)
            else:
                raise RuntimeError(f"unknown invoke mode: {spec['invoke']}")
        except subprocess.TimeoutExpired as exc:
            record = {
                "stage_id": stage_id,
                "stage": stage_id,
                "invoke": spec.get("invoke", ""),
                "owner": spec.get("owner", ""),
                "status": "timeout",
                "returncode": 124,
                "evidence": expand_evidence(spec.get("evidence", []), args.ip),
                "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
                "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            }
            print(f"=== [{stage_id}] TIMEOUT", file=sys.stderr)
        results.append(record)
        if record.get("status") not in {"pass", "optional-fail"}:
            break

    summary_path = write_summary(root, args.ip, args, selected, results)
    print(f"\nsummary: {summary_path}")
    return 0 if all(item.get("status") in {"pass", "optional-fail"} for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
