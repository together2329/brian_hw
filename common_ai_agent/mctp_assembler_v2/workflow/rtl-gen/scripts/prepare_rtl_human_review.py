#!/usr/bin/env python3
"""Prepare human-review packets for RTL gates that must not be auto-approved.

The packet is a bridge artifact only: it collects reference target-scale
candidates and pending connection-contract rows so a reviewer can lock them
into SSOT through resolve_rtl_blockers.py after review. It deliberately writes
draft_rtl_blocker_answers, not rtl_blocker_answers, to avoid accidental
approval by downstream tools.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any


TARGET_SCALE_ID = "RTL_TARGET_SCALE_POLICY"
CONNECTION_CONTRACT_ID = "RTL_RESOLVE_CONNECTION_CONTRACTS"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit(f"[prepare_rtl_human_review] invalid JSON {path}: {exc}") from exc
    return data if isinstance(data, dict) else {}


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _question(blocked: dict[str, Any], qid: str) -> dict[str, Any]:
    for item in blocked.get("questions") or []:
        if isinstance(item, dict) and str(item.get("id") or "") == qid:
            return item
    return {}


def _reference_target_scale_candidate(plan: dict[str, Any], authoring: dict[str, Any]) -> dict[str, Any]:
    for source in (_dict(plan.get("reference_profile")), _dict(authoring.get("reference_profile"))):
        suggested = _dict(source.get("suggested_ssot_target_scale"))
        if suggested:
            return suggested
    for source in (plan, authoring):
        suggested = _dict(source.get("suggested_ssot_target_scale"))
        if suggested:
            return suggested
    return {}


def _target_scale_question_from_plan(plan: dict[str, Any], authoring: dict[str, Any]) -> dict[str, Any]:
    suggested = _reference_target_scale_candidate(plan, authoring)
    target_scale = _dict(plan.get("target_scale"))
    target_scale_waiver = _dict(plan.get("target_scale_waiver"))
    if not suggested and not target_scale and not target_scale_waiver:
        return {}
    return {
        "id": TARGET_SCALE_ID,
        "decision_needed": (
            "Review the reference-derived structural scale candidate and lock approved positive minima "
            "into quality_gates.rtl_gen.target_scale, or approve target_scale_waiver with owner and reason."
        ),
        "recommended_default": "Treat suggested_ssot_target_scale as review input only; do not auto-approve it.",
        "current_target_scale": target_scale,
        "current_target_scale_waiver": target_scale_waiver,
        "suggested_ssot_target_scale": suggested,
        "reference_scale_gap": _dict(plan.get("reference_scale_gap")) or _dict(authoring.get("reference_scale_gap")),
    }


def _connection_contract_gap_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    gap = _dict(plan.get("connection_contract_gap"))
    if gap:
        return gap
    hierarchy = _dict(plan.get("manifest_hierarchy_evidence"))
    issues = hierarchy.get("connection_contract_issues")
    if hierarchy.get("connection_contract_status") == "fail" or isinstance(issues, list):
        return {
            "status": "missing",
            "issues": issues if isinstance(issues, list) else [],
            "required_sources": ["integration.connections", "sub_modules[].connections"],
        }
    return {}


def _connection_contract_question_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    gap = _connection_contract_gap_from_plan(plan)
    if not gap:
        return {}
    return {
        "id": CONNECTION_CONTRACT_ID,
        "decision_needed": (
            "Review pending RTL-observed connection rows and approve machine-readable SSOT "
            "connection contracts before production signoff."
        ),
        "recommended_default": "Use the candidate rows as review input only; do not auto-approve wiring.",
        "connection_contract_gap": gap,
    }


def _merge_question(current: dict[str, Any], fresh: dict[str, Any], *, fresh_keys: tuple[str, ...]) -> dict[str, Any]:
    if not current:
        return dict(fresh)
    if not fresh:
        return dict(current)
    merged = dict(current)
    for key, value in fresh.items():
        if key in fresh_keys and value not in (None, "", [], {}):
            merged[key] = value
        elif key not in merged or merged[key] in (None, "", [], {}):
            merged[key] = value
    return merged


def _clean_connection_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key in (
        "module",
        "instance",
        "port",
        "signal",
        "direction",
        "range",
        "width",
        "clock_domain",
        "reset_domain",
        "source_ref",
        "confidence",
        "review_status",
    ):
        value = row.get(key)
        if value not in (None, "", [], {}):
            out[key] = value
    out.setdefault("review_status", "pending")
    out["approval_target"] = "integration.connections"
    out["approval_required"] = True
    return out


def _connection_rows(suggestions: dict[str, Any]) -> list[dict[str, Any]]:
    rows = suggestions.get("rows")
    if not isinstance(rows, list):
        rows = suggestions.get("suggestions")
    if not isinstance(rows, list):
        return []
    cleaned: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        module = str(item.get("module") or "").strip()
        port = str(item.get("port") or "").strip()
        signal = str(item.get("signal") or "").strip()
        instance = str(item.get("instance") or "").strip()
        if not module or not port or not signal:
            continue
        key = (module, instance, port, signal)
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(_clean_connection_row(item))
    return cleaned


def _approved_connection_payload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for row in rows:
        item = {
            "module": row["module"],
            "port": row["port"],
            "signal": row["signal"],
        }
        for key in ("instance", "direction", "source_ref", "range", "width"):
            if row.get(key) not in (None, "", [], {}):
                item[key] = row[key]
        payload.append(item)
    return payload


def _target_scale_review(question: dict[str, Any], authoring: dict[str, Any]) -> dict[str, Any]:
    suggested = question.get("suggested_ssot_target_scale")
    if not isinstance(suggested, dict):
        suggested = {}
    reference_gap = question.get("reference_scale_gap")
    if not isinstance(reference_gap, dict):
        reference_gap = authoring.get("reference_scale_gap") if isinstance(authoring.get("reference_scale_gap"), dict) else {}
    return {
        "blocker_id": TARGET_SCALE_ID,
        "decision_needed": question.get("decision_needed") or "",
        "recommended_default": question.get("recommended_default") or "",
        "current_target_scale": question.get("current_target_scale") if isinstance(question.get("current_target_scale"), dict) else {},
        "current_target_scale_waiver": question.get("current_target_scale_waiver") if isinstance(question.get("current_target_scale_waiver"), dict) else {},
        "suggested_target_scale": suggested,
        "reference_scale_gap": reference_gap,
        "approval_rule": (
            "Copy edited positive minima into quality_gates.rtl_gen.target_scale only after human architecture review, "
            "or approve target_scale_waiver with owner and reason."
        ),
    }


def _connection_contract_review(question: dict[str, Any], suggestions: dict[str, Any]) -> dict[str, Any]:
    rows = _connection_rows(suggestions)
    return {
        "blocker_id": CONNECTION_CONTRACT_ID,
        "decision_needed": question.get("decision_needed") or "",
        "recommended_default": question.get("recommended_default") or "",
        "connection_contract_gap": question.get("connection_contract_gap") if isinstance(question.get("connection_contract_gap"), dict) else {},
        "summary": suggestions.get("summary") if isinstance(suggestions.get("summary"), dict) else {},
        "candidate_count": len(rows),
        "candidate_rows": rows,
        "approval_rule": (
            "Rows become SSOT authority only after the SSOT-gen workflow records them inline "
            "into <ip>/yaml/<ip>.ssot.yaml."
        ),
    }


def _draft_answers(target_review: dict[str, Any], connection_review: dict[str, Any]) -> list[dict[str, Any]]:
    answers: list[dict[str, Any]] = []
    target = target_review.get("suggested_target_scale")
    if isinstance(target, dict) and target:
        answers.append({
            "id": TARGET_SCALE_ID,
            "review_status": "pending_human_approval",
            "target_scale": target,
        })
    rows = connection_review.get("candidate_rows")
    if isinstance(rows, list) and rows:
        answers.append({
            "id": CONNECTION_CONTRACT_ID,
            "review_status": "pending_human_approval",
            "connection_contracts": _approved_connection_payload([row for row in rows if isinstance(row, dict)]),
        })
    return answers


def _markdown(packet: dict[str, Any], *, max_rows: int) -> str:
    target = packet.get("target_scale_review") if isinstance(packet.get("target_scale_review"), dict) else {}
    conn = packet.get("connection_contract_review") if isinstance(packet.get("connection_contract_review"), dict) else {}
    rows = conn.get("candidate_rows") if isinstance(conn.get("candidate_rows"), list) else []
    lines = [
        f"# RTL Human Review Packet: {packet.get('ip')}",
        "",
        "Status: pending_human_review",
        "",
        "This packet is not approval. It is a review aid for human-locked RTL gates.",
        "",
        "## Target Scale",
        "",
        f"- Blocker: {TARGET_SCALE_ID}",
        f"- Decision: {target.get('decision_needed') or 'review target scale'}",
        f"- Suggested minima: `{json.dumps(target.get('suggested_target_scale') or {}, sort_keys=True)}`",
        "",
        "## Connection Contracts",
        "",
        f"- Blocker: {CONNECTION_CONTRACT_ID}",
        f"- Candidate rows: {conn.get('candidate_count') or 0}",
        "- Approval target: `integration.connections` or matching `sub_modules[].connections`",
        "",
        "| module | instance | port | signal | direction |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows[:max_rows]:
        if not isinstance(row, dict):
            continue
        lines.append(
            "| {module} | {instance} | {port} | {signal} | {direction} |".format(
                module=row.get("module", ""),
                instance=row.get("instance", ""),
                port=row.get("port", ""),
                signal=row.get("signal", ""),
                direction=row.get("direction", ""),
            )
        )
    if len(rows) > max_rows:
        lines.append(f"| ... | ... | ... | {len(rows) - max_rows} more row(s) in JSON | ... |")
    lines.extend([
        "",
        "## Apply Rule",
        "",
        "After human review, copy the edited `draft_rtl_blocker_answers` into an answers JSON as `rtl_blocker_answers`, then run:",
        "",
        "```sh",
        "python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/resolve_rtl_blockers.py\" <ip> --root \"$ATLAS_PROJECT_ROOT\" --answers-json <approved-answers.json>",
        "```",
        "",
        "Then rerun RTL TODO derivation. If the RTL files were already common_ai_agent-authored and only SSOT metadata changed, refresh provenance:",
        "",
        "```sh",
        "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py <ip> --root . --audit-rtl",
        "python3 workflow/rtl-gen/scripts/refresh_rtl_provenance.py <ip> --root .",
        "```",
        "",
        "Do not treat this packet as SSOT authority by itself.",
        "",
    ])
    return "\n".join(lines)


def build_packet(root: Path, ip: str) -> dict[str, Any]:
    ip_dir = root / ip
    rtl_dir = ip_dir / "rtl"
    blocked_path = rtl_dir / "rtl_blocked.json"
    todo_plan_path = rtl_dir / "rtl_todo_plan.json"
    authoring_path = rtl_dir / "rtl_authoring_plan.json"
    suggestions_path = rtl_dir / "connection_contract_suggestions.json"
    blocked = _read_json(blocked_path)
    plan = _read_json(todo_plan_path)
    if not blocked and not plan:
        raise SystemExit(
            f"[prepare_rtl_human_review] missing blocker evidence: {blocked_path} "
            f"or fresh TODO audit: {todo_plan_path}"
        )
    authoring = _read_json(authoring_path)
    suggestions = _read_json(suggestions_path)
    target_question = _merge_question(
        _question(blocked, TARGET_SCALE_ID),
        _target_scale_question_from_plan(plan, authoring),
        fresh_keys=(
            "current_target_scale",
            "current_target_scale_waiver",
            "suggested_ssot_target_scale",
            "reference_scale_gap",
        ),
    )
    connection_question = _merge_question(
        _question(blocked, CONNECTION_CONTRACT_ID),
        _connection_contract_question_from_plan(plan),
        fresh_keys=("connection_contract_gap",),
    )
    target_review = _target_scale_review(target_question, authoring)
    connection_review = _connection_contract_review(connection_question, suggestions)
    draft_answers = _draft_answers(target_review, connection_review)
    return {
        "schema_version": 1,
        "type": "rtl_human_review_packet",
        "status": "pending_human_review",
        "ip": ip,
        "top": blocked.get("top") or authoring.get("top") or plan.get("top") or ip,
        "evidence_source": "rtl_blocked+rtl_todo_plan" if blocked and plan else ("rtl_blocked" if blocked else "rtl_todo_plan"),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inputs": {
            "rtl_blocked": str(blocked_path.relative_to(root)) if blocked_path.is_file() else "",
            "rtl_todo_plan": str(todo_plan_path.relative_to(root)) if todo_plan_path.is_file() else "",
            "rtl_authoring_plan": str(authoring_path.relative_to(root)) if authoring_path.is_file() else "",
            "connection_contract_suggestions": str(suggestions_path.relative_to(root)) if suggestions_path.is_file() else "",
        },
        "guardrails": [
            "This packet does not approve target scale or connection contracts.",
            "Downstream resolver consumes rtl_blocker_answers, while this packet only provides draft_rtl_blocker_answers.",
            "A packet built from rtl_todo_plan is review material only; it is not a substitute for approved SSOT answers.",
            "Production PASS remains blocked until reviewed answers are explicitly applied into the SSOT.",
        ],
        "target_scale_review": target_review,
        "connection_contract_review": connection_review,
        "draft_rtl_blocker_answers": draft_answers,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--max-markdown-rows", type=int, default=24)
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    packet = build_packet(root, ns.ip)
    rtl_dir = root / ns.ip / "rtl"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    packet_path = rtl_dir / "rtl_human_review_packet.json"
    markdown_path = rtl_dir / "rtl_human_review_packet.md"
    _write_json(packet_path, packet)
    markdown_path.write_text(_markdown(packet, max_rows=max(1, ns.max_markdown_rows)), encoding="utf-8")
    print(f"[prepare_rtl_human_review] wrote {packet_path.relative_to(root)}")
    print(f"[prepare_rtl_human_review] wrote {markdown_path.relative_to(root)}")
    print("[prepare_rtl_human_review] status=pending_human_review; no SSOT approval was applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
