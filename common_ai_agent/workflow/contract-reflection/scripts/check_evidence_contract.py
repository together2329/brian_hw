#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from workflow.contract_reflection.evidence_contract_json import (
    JsonList,
    JsonMap,
    JsonValue,
    as_list as _as_list,
    as_map as _as_map,
    json_strings as _json_strings,
    load_json as _load_json,
    strings as _strings,
    text as _text,
)
from workflow.contract_reflection.evidence_contract_rows import RowsByArtifact, load_scoreboard_rows, matching_rows
from workflow.contract_reflection.evidence_contract_vcd import VCD_CONDITION_KINDS, check_vcd_condition, vcd_observable_names


CONDITION_KINDS: set[str] = {"observed_equals", "observed_masked_equals", "observed_nonzero", "observed_present", "row_passed", "strobe_contiguous"}


@dataclass(frozen=True)
class ObligationResult:
    obligation_id: str
    status: str
    issues: tuple[str, ...]
    condition_results: JsonMap
    matched_rows: tuple[JsonMap, ...]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _resolve_ip_dir(root: Path, ip: str) -> Path:
    raw_ip = Path(ip)
    if raw_ip.is_absolute():
        raise SystemExit(f"[evidence_contract] FAIL: ip path {ip} must stay under --root {root}")
    candidate = (root / raw_ip).resolve()
    try:
        _ = candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"[evidence_contract] FAIL: ip path {ip} must stay under --root {root}") from exc
    return candidate


def _required(value: JsonMap) -> bool:
    status = _text(value.get("status")).lower()
    return value.get("required") is not False and status not in {"deferred", "optional", "waived"}


def _known_requirements(index: JsonMap) -> set[str]:
    out: set[str] = set()
    for item in _as_list(index.get("requirements")):
        data = _as_map(item)
        if not _required(data):
            continue
        rid = _text(data.get("requirement_id"))
        if rid:
            out.add(rid)
    return out

def _requirement_obligation_issues(index: JsonMap, known_obligations: set[str]) -> list[str]:
    issues: list[str] = []
    for item in _as_list(index.get("requirements")):
        data = _as_map(item)
        if not _required(data):
            continue
        rid = _text(data.get("requirement_id")) or "<missing>"
        obligation_ids = _strings(data.get("obligation_ids"))
        if not obligation_ids:
            issues.append(f"{rid}: missing obligation_ids")
            continue
        for obligation_id in obligation_ids:
            if obligation_id not in known_obligations:
                issues.append(f"{rid}: missing obligation {obligation_id}")
    return issues

def _field(row: JsonMap, field: str) -> JsonValue:
    observed = _as_map(row.get("rtl_observed"))
    return observed.get(field)

def _contiguous_nonzero(value: JsonValue) -> bool:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return False
    normalized = value >> ((value & -value).bit_length() - 1)
    return (normalized & (normalized + 1)) == 0

def _condition_int(value: JsonValue) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _condition(ip_dir: Path, row: JsonMap, condition: JsonMap) -> tuple[str, bool, str]:
    cid = _text(condition.get("id"))
    kind = _text(condition.get("kind"))
    field = _text(condition.get("field"))
    if not cid:
        return "missing_condition_id", False, "condition missing id"
    if kind in VCD_CONDITION_KINDS:
        passed, message = check_vcd_condition(ip_dir, condition)
        return cid, passed, message
    if kind not in CONDITION_KINDS:
        return cid, False, f"unknown condition kind {kind}"
    if kind == "row_passed":
        return cid, row.get("passed") is True, "scoreboard row did not pass"
    if not field:
        return cid, False, "condition missing field"
    observed = _field(row, field)
    if kind == "observed_present":
        return cid, observed is not None, f"missing observable {field}"
    if kind == "observed_nonzero":
        return cid, isinstance(observed, int) and not isinstance(observed, bool) and observed != 0, f"{field} is zero/missing"
    if kind == "observed_equals":
        expected = condition.get("value")
        return cid, observed == expected, f"{field}={observed!r} expected {expected!r}"
    if kind == "observed_masked_equals":
        observed_int = _condition_int(observed)
        mask = _condition_int(condition.get("mask"))
        expected = _condition_int(condition.get("value"))
        if observed_int is None or mask is None or expected is None:
            return cid, False, f"{field}, mask, and value must be integers"
        return cid, (observed_int & mask) == expected, f"({field} & {mask!r})={observed_int & mask!r} expected {expected!r}"
    if kind == "strobe_contiguous":
        return cid, _contiguous_nonzero(observed), f"{field} is not a contiguous nonzero strobe"
    return cid, False, f"unhandled condition kind {kind}"


def _check_obligation(ip_dir: Path, obligation: JsonMap, known_reqs: set[str], rows: RowsByArtifact) -> ObligationResult:
    oid = _text(obligation.get("obligation_id")) or "<missing>"
    issues: list[str] = []
    for rid in _strings(obligation.get("requirement_ids")):
        if rid not in known_reqs:
            issues.append(f"unknown requirement_id {rid}")
    for key in ("contract_refs", "scenario_ids", "required_observables", "pass_conditions"):
        if not _as_list(obligation.get(key)):
            issues.append(f"missing {key}")
    matched_rows = matching_rows(obligation, rows)
    if not matched_rows:
        issues.append("no matching scoreboard row")
        return ObligationResult(oid, "fail", tuple(issues), {}, ())
    observed_names = set[str]()
    for row in matched_rows:
        observed_names.update(_as_map(row.get("rtl_observed")).keys())
        if row.get("passed") is not True:
            issues.append(f"{row.get('scenario_id')}: scoreboard row did not pass")
    for item in _as_list(obligation.get("pass_conditions")):
        observed_names.update(vcd_observable_names(_as_map(item)))
    for name in _strings(obligation.get("required_observables")):
        if name not in observed_names:
            issues.append(f"missing observable {name}")
    condition_results: JsonMap = {}
    for item in _as_list(obligation.get("pass_conditions")):
        cid, passed, message = _condition(ip_dir, matched_rows[0], _as_map(item))
        condition_results[cid] = passed
        if not passed:
            issues.append(f"{cid}: {message}")
    status = "pass" if not issues else "fail"
    return ObligationResult(oid, status, tuple(issues), condition_results, tuple(matched_rows))


def _matched_row_refs(rows: tuple[JsonMap, ...]) -> JsonList:
    return [{"goal_id": row.get("goal_id"), "scenario_id": row.get("scenario_id")} for row in rows]


def _obligation_reports(results: list[ObligationResult]) -> JsonList:
    out: JsonList = []
    for item in results:
        report: JsonMap = {
            "condition_results": item.condition_results,
            "issues": _json_strings(item.issues),
            "matched_rows": _matched_row_refs(item.matched_rows),
            "obligation_id": item.obligation_id,
            "status": item.status,
        }
        out.append(report)
    return out


def _analyze(ip_dir: Path) -> JsonMap:
    index = _load_json(ip_dir / "verify" / "requirements_index.json", "evidence_contract")
    contract = _load_json(ip_dir / "verify" / "evidence_contract.json", "evidence_contract")
    rows = load_scoreboard_rows(ip_dir, contract)
    known_reqs = _known_requirements(index)
    obligations = [_as_map(item) for item in _as_list(contract.get("obligations")) if _required(_as_map(item))]
    known_obligations = {_text(item.get("obligation_id")) for item in obligations if _text(item.get("obligation_id"))}
    index_issues = _requirement_obligation_issues(index, known_obligations)
    results = [_check_obligation(ip_dir, _as_map(item), known_reqs, rows) for item in obligations]
    passed = sum(1 for item in results if item.status == "pass")
    failed = sum(1 for item in results if item.status != "pass")
    return {
        "generated_at": _utc(),
        "ip": ip_dir.name,
        "issues": _json_strings(index_issues),
        "obligations": _obligation_reports(results),
        "schema_version": 1,
        "status": "pass" if failed == 0 and not index_issues else "fail",
        "summary": {"failed": failed, "index_issues": len(index_issues), "passed": passed, "total": len(results)},
        "type": "evidence_contract_coverage",
    }


def _parse_args(argv: list[str]) -> tuple[str, Path]:
    if not argv or argv[0] in {"-h", "--help"}:
        raise SystemExit("usage: check_evidence_contract.py <ip> [--root <root>]")
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
    out = ip_dir / "signoff" / "evidence_contract_coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    _ = out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"[evidence_contract] {report['status']}: wrote {out}")
    for issue in _strings(report.get("issues")):
        print(f"[evidence_contract] index: {issue}")
    for item in _as_list(report.get("obligations")):
        data = _as_map(item)
        for issue in _strings(data.get("issues")):
            print(f"[evidence_contract] {data.get('obligation_id')}: {issue}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
