#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Union

from pydantic import TypeAdapter, ValidationError
from typing_extensions import TypeAliasType

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_vcd import sampled_vcd_signals
from workflow.contract_reflection.semantic_freshness import semantic_freshness_issues


JsonValue = TypeAliasType("JsonValue", Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]])
JsonMap = dict[str, JsonValue]
JsonList = list[JsonValue]
JSON_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)


@dataclass(frozen=True)
class ContractResult:
    contract_ref: str
    status: str
    issues: tuple[str, ...]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_json(path: Path) -> JsonMap:
    if not path.is_file():
        raise SystemExit(f"[contract_reflection] FAIL: missing {path}")
    try:
        value = JSON_ADAPTER.validate_json(path.read_text(encoding="utf-8"))
    except ValidationError as exc:
        raise SystemExit(f"[contract_reflection] FAIL: invalid JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"[contract_reflection] FAIL: {path} root must be an object")
    return value


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[contract_reflection] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[contract_reflection] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _as_list(value: JsonValue) -> JsonList:
    return value if isinstance(value, list) else []


def _as_map(value: JsonValue) -> JsonMap:
    return value if isinstance(value, dict) else {}


def _strings(value: JsonValue) -> list[str]:
    return [item for item in _as_list(value) if isinstance(item, str) and item.strip()]


def _json_strings(values: tuple[str, ...]) -> JsonList:
    out: JsonList = []
    for value in values:
        out.append(value)
    return out


def _text(value: JsonValue) -> str:
    return value if isinstance(value, str) else ""


def _required(value: JsonMap) -> bool:
    status = _text(value.get("status")).lower()
    return value.get("required") is not False and status not in {"deferred", "optional", "waived"}


def _contract_refs_from_evidence(contract: JsonMap) -> set[str]:
    out: set[str] = set()
    for item in _as_list(contract.get("obligations")):
        data = _as_map(item)
        if not _required(data):
            continue
        out.update(_strings(data.get("contract_refs")))
    return out


def _reflection_map(reflection: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in _as_list(reflection.get("contract_refs")):
        data = _as_map(item)
        ref = _text(data.get("contract_ref"))
        if ref:
            out[ref] = data
    return out


def _ip_path(ip_dir: Path, rel: str) -> Path | None:
    if not rel:
        return None
    candidate = (ip_dir / rel).resolve()
    try:
        _ = candidate.relative_to(ip_dir)
    except ValueError:
        return None
    return candidate


def _path_exists(ip_dir: Path, rel: str) -> bool:
    path = _ip_path(ip_dir, rel)
    return path is not None and path.is_file()


def _check_path(ip_dir: Path, issues: list[str], label: str, path: str) -> None:
    if not path:
        issues.append(f"missing {label} path")
        return
    resolved = _ip_path(ip_dir, path)
    if resolved is None:
        issues.append(f"{label} path escapes IP root {path}")
    elif not resolved.is_file():
        issues.append(f"missing {label} artifact {path}")


def _wave_signals(ip_dir: Path, artifact: str, candidates: set[str]) -> tuple[set[str], list[str]]:
    if not candidates:
        return set(), ["missing wave observable candidates"]
    return sampled_vcd_signals(ip_dir, artifact, candidates)


def _check_ref(ip_dir: Path, contract_ref: str, reflection: JsonMap) -> ContractResult:
    issues: list[str] = []
    if not reflection:
        return ContractResult(contract_ref, "fail", (f"missing reflection for {contract_ref}",))
    _check_path(ip_dir, issues, "SSOT", _text(_as_map(reflection.get("ssot")).get("path")))
    _check_path(ip_dir, issues, "FL", _text(_as_map(reflection.get("fl")).get("path")))
    _check_path(ip_dir, issues, "CL", _text(_as_map(reflection.get("cl")).get("path")))
    _check_path(ip_dir, issues, "TB", _text(_as_map(reflection.get("tb")).get("path")))
    sim = _as_map(reflection.get("sim"))
    _check_path(ip_dir, issues, "scoreboard", _text(sim.get("scoreboard")))
    _check_path(ip_dir, issues, "wave", _text(sim.get("wave")))
    rtl = _as_map(reflection.get("rtl"))
    for owner in _strings(rtl.get("owner_files")):
        if not _path_exists(ip_dir, owner):
            issues.append(f"missing RTL owner {owner}")
    if not _strings(rtl.get("owner_files")):
        issues.append("missing RTL owner_files")
    if not _strings(rtl.get("observable_via")):
        issues.append("missing RTL observable_via")
    if not _text(_as_map(reflection.get("tb")).get("monitor")):
        issues.append("missing TB monitor")
    observable_via = set(_strings(rtl.get("observable_via")))
    wave_signals, wave_issues = _wave_signals(ip_dir, _text(sim.get("wave")), observable_via)
    issues.extend(wave_issues)
    if wave_signals and observable_via and not wave_signals.intersection(observable_via):
        issues.append("wave observations do not intersect RTL observable_via")
    return ContractResult(contract_ref, "pass" if not issues else "fail", tuple(issues))


def _analyze(ip_dir: Path) -> JsonMap:
    evidence = _load_json(ip_dir / "verify" / "evidence_contract.json")
    reflection = _load_json(ip_dir / "verify" / "contract_reflection.json")
    freshness_issues = [
        *semantic_freshness_issues(ip_dir, "verify/evidence_contract.json", evidence),
        *semantic_freshness_issues(ip_dir, "verify/contract_reflection.json", reflection),
    ]
    required_refs = sorted(_contract_refs_from_evidence(evidence))
    reflections = _reflection_map(reflection)
    results = [_check_ref(ip_dir, contract_ref, reflections.get(contract_ref, {})) for contract_ref in required_refs]
    passed = sum(1 for item in results if item.status == "pass")
    failed = sum(1 for item in results if item.status != "pass")
    contract_reports: JsonList = []
    for item in results:
        report: JsonMap = {
            "contract_ref": item.contract_ref,
            "issues": _json_strings(item.issues),
            "status": item.status,
        }
        contract_reports.append(report)
    return {
        "contract_refs": contract_reports,
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "issues": _json_strings(tuple(freshness_issues)),
        "schema_version": 1,
        "status": "pass" if failed == 0 and not freshness_issues else "fail",
        "summary": {"artifact_issues": len(freshness_issues), "failed": failed, "passed": passed, "total": len(results)},
        "type": "contract_reflection_coverage",
    }


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: check_contract_reflection.py <ip> [--root <root>]")
    ip = argv[0]
    root = Path(".")
    index = 1
    while index < len(argv):
        token = argv[index]
        if token != "--root":
            raise SystemExit(f"usage: unexpected argument {token!r}")
        if index + 1 >= len(argv):
            raise SystemExit("usage: --root requires a value")
        root = Path(argv[index + 1])
        index += 2
    return ip, root.resolve()


def main() -> int:
    ip, root = _parse_args(sys.argv[1:])
    ip_dir = _resolve_ip_dir(root, ip)
    report = _analyze(ip_dir)
    out = ip_dir / "signoff" / "contract_reflection_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[contract_reflection] {report['status']}: wrote {out}")
    for issue in _strings(report.get("issues")):
        print(f"[contract_reflection] artifact: {issue}")
    for item in _as_list(report.get("contract_refs")):
        data = _as_map(item)
        for issue in _strings(data.get("issues")):
            print(f"[contract_reflection] {data.get('contract_ref')}: {issue}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
