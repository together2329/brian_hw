#!/usr/bin/env python3
"""Validate the prompt-to-artifact checklist against current disk evidence.

This is a consistency audit, not an approval tool. A blocked checklist can be
valid when it accurately reflects an open human-owned gate such as req
approval. Use --strict-complete when blocked should be treated as a failing
process exit.
"""

from __future__ import annotations

import argparse
import json
import sys
import os
import threading
import uuid
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, f"missing {path}"
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {}, f"cannot parse {path}: {exc}"
    if not isinstance(doc, dict):
        return {}, f"{path} root must be a JSON object"
    return doc, ""


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _atomic_write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(
        path.suffix + f".tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}"
    )
    tmp.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _ratio(value: Any) -> str:
    if isinstance(value, dict):
        if "hit" in value and "total" in value:
            return f"{value.get('hit')}/{value.get('total')}"
        if "passed" in value and "total" in value:
            return f"{value.get('passed')}/{value.get('total')}"
    return ""


def _check_expected_summary(
    *,
    ip: str,
    root: Path,
    item: dict[str, Any],
) -> list[str]:
    item_id = str(item.get("id") or "")
    expected = item.get("expected_summary")
    if not isinstance(expected, dict):
        return []

    errors: list[str] = []
    if item_id == "equivalence":
        compare, err = _read_json(root / ip / "sim" / "fl_rtl_compare.json")
        if err:
            return [err]
        summary = compare.get("summary") if isinstance(compare.get("summary"), dict) else {}
        for key in ("goals_checked", "goals_passed", "goals_failed", "goals_blocked"):
            if key in expected and summary.get(key) != expected[key]:
                errors.append(
                    f"{item_id}: expected {key}={expected[key]!r}, got {summary.get(key)!r}"
                )
    elif item_id == "coverage":
        coverage, err = _read_json(root / ip / "cov" / "coverage.json")
        if err:
            return [err]
        actual = {
            "function_bins": _ratio(coverage.get("function_coverage")),
            "cycle_bins": _ratio(coverage.get("cycle_coverage")),
        }
        for key in ("function_bins", "cycle_bins"):
            if key in expected and actual.get(key) != expected[key]:
                errors.append(
                    f"{item_id}: expected {key}={expected[key]!r}, got {actual.get(key)!r}"
                )
    return errors


def _check_expected_current_summary(
    *,
    ip: str,
    root: Path,
    item: dict[str, Any],
) -> list[str]:
    expected = item.get("expected_current_summary")
    if not isinstance(expected, dict):
        return []

    audit, err = _read_json(root / ip / "sim" / "fl_rtl_goal_audit.json")
    if err:
        return [err]
    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    actual_passed = f"{summary.get('passed_checks')}/{summary.get('total_checks')}"
    actual = {
        "status": audit.get("status"),
        "passed": actual_passed,
        "blockers": summary.get("blockers") if isinstance(summary.get("blockers"), list) else [],
    }

    errors: list[str] = []
    for key in ("status", "passed", "blockers"):
        if key in expected and actual.get(key) != expected[key]:
            errors.append(
                f"{item.get('id')}: expected current {key}={expected[key]!r}, got {actual.get(key)!r}"
            )
    return errors


def audit(ip: str, root: Path) -> dict[str, Any]:
    root = root.resolve()
    checklist_path = root / ip / "review" / "prompt_to_artifact_checklist.json"
    checklist, err = _read_json(checklist_path)
    if err:
        return {
            "schema_version": 1,
            "type": "prompt_to_artifact_checklist_audit",
            "ip": ip,
            "status": "fail",
            "errors": [err],
            "blocked_items": [],
            "completion_ready": False,
        }

    errors: list[str] = []
    if checklist.get("type") != "prompt_to_artifact_completion_checklist":
        errors.append("checklist type must be prompt_to_artifact_completion_checklist")
    if checklist.get("ip") != ip:
        errors.append(f"checklist ip mismatch: expected {ip!r}, got {checklist.get('ip')!r}")

    items = checklist.get("checklist")
    if not isinstance(items, list) or not items:
        errors.append("checklist must contain a non-empty checklist[] array")
        items = []

    item_summaries: list[dict[str, Any]] = []
    blocked_items: list[str] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            errors.append("checklist item must be an object")
            continue
        item_id = str(raw_item.get("id") or "<missing>")
        status = str(raw_item.get("status") or "")
        evidence = raw_item.get("evidence") if isinstance(raw_item.get("evidence"), list) else []
        missing_expected = raw_item.get("missing") if isinstance(raw_item.get("missing"), list) else []
        item_errors: list[str] = []

        for rel_path in evidence:
            path = root / str(rel_path)
            if not path.exists():
                item_errors.append(f"missing evidence: {rel_path}")
        for rel_path in missing_expected:
            path = root / str(rel_path)
            if path.exists():
                item_errors.append(f"expected missing path exists: {rel_path}")

        item_errors.extend(_check_expected_summary(ip=ip, root=root, item=raw_item))
        item_errors.extend(_check_expected_current_summary(ip=ip, root=root, item=raw_item))

        if status == "blocked":
            blocked_items.append(item_id)
        elif status != "pass":
            item_errors.append(f"unsupported item status: {status!r}")

        errors.extend(f"{item_id}: {msg}" for msg in item_errors)
        item_summaries.append({
            "id": item_id,
            "declared_status": status,
            "evidence_count": len(evidence),
            "missing_count": len(missing_expected),
            "errors": item_errors,
        })

    audit_doc, audit_err = _read_json(root / ip / "sim" / "fl_rtl_goal_audit.json")
    audit_summary = audit_doc.get("summary") if isinstance(audit_doc.get("summary"), dict) else {}
    if audit_err:
        errors.append(audit_err)
    blockers = audit_summary.get("blockers") if isinstance(audit_summary.get("blockers"), list) else []
    completion_ready = (
        not errors
        and not blocked_items
        and audit_doc.get("status") == "pass"
        and blockers == []
    )
    status = "fail" if errors else ("pass" if completion_ready else "blocked")

    return {
        "schema_version": 1,
        "type": "prompt_to_artifact_checklist_audit",
        "ip": ip,
        "status": status,
        "completion_ready": completion_ready,
        "blocked_items": blocked_items,
        "final_audit": {
            "status": audit_doc.get("status"),
            "passed": f"{audit_summary.get('passed_checks')}/{audit_summary.get('total_checks')}",
            "blockers": blockers,
        },
        "items": item_summaries,
        "errors": errors,
        "source": _rel(checklist_path, root),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".", help="Project root")
    parser.add_argument("--json", action="store_true", help="Print full JSON")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write review/prompt_to_artifact_checklist_audit.json",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional explicit output path for --write",
    )
    parser.add_argument(
        "--strict-complete",
        action="store_true",
        help="Return non-zero when the checklist is valid but still blocked.",
    )
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    result = audit(args.ip, root)
    if args.write:
        output = Path(args.output).resolve() if args.output else root / args.ip / "review" / "prompt_to_artifact_checklist_audit.json"
        result["written_to"] = _rel(output, root)
        _atomic_write_json(output, result)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        blockers = ",".join(str(item) for item in result.get("blocked_items", [])) or "none"
        print(
            f"[prompt-checklist-audit] status={result['status']} "
            f"completion_ready={str(result['completion_ready']).lower()} "
            f"blocked_items={blockers}"
        )
        for err in result.get("errors", []):
            print(f"[prompt-checklist-audit] error: {err}", file=sys.stderr)

    if result["status"] == "fail":
        return 1
    if args.strict_complete and result["status"] != "pass":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
