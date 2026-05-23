#!/usr/bin/env python3
"""Derive RTL implementation TODOs directly from the SSOT.

The legacy ssot-rtl checklist is only a bootstrap seed.  This script builds
the real, IP-sized implementation plan from the YAML SSOT so a complex IP naturally
produces dozens or hundreds of concrete RTL tasks.  It also emits a lightweight
static gate that rejects orphan function/cycle behavior and, after RTL exists,
checks that required implementation terms appear in the generated DUT sources.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import time
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


IMPLEMENTATION_SECTIONS = (
    "parameters",
    "io_list",
    "sub_modules",
    "registers",
    "memory",
    "interrupts",
    "fsm",
    "features",
    "dataflow",
    "function_model",
    "cycle_model",
    "timing",
    "power",
    "security",
    "error_handling",
    "debug_observability",
    "integration",
    "dft",
    "synthesis",
    "coding_rules",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "next_step_todos",
)


def _resolve_project_root(root_arg: str, ip_root_arg: str, ip: str) -> Path:
    project_root = Path(os.path.expandvars(root_arg or os.environ.get("ATLAS_PROJECT_ROOT") or ".")).expanduser().resolve()
    ip_root_raw = (ip_root_arg or os.environ.get("ATLAS_IP_ROOT") or "").strip()
    if ip_root_raw:
        ip_root = Path(os.path.expandvars(ip_root_raw)).expanduser()
        if not ip_root.is_absolute():
            ip_root = project_root / ip_root
        ip_root = ip_root.resolve()
        if not ip or ip_root.name == ip or (ip_root / "yaml").is_dir():
            return ip_root.parent
    return project_root

STATIC_EVIDENCE_CATEGORIES = (
    "function_model.",
    "cycle_model.",
    "registers.",
    "memory.",
    "interrupts.",
    "fsm.",
    "features.",
    "dataflow.",
    "error_handling.",
    "security.",
    "debug_observability.",
)

AUTHORING_PACKET_TASK_LIMIT = 48
AUTHORING_RECOMMENDED_PACKET_BATCH_LIMIT = 4
UI_TODO_TARGET_MIN = 20
UI_TODO_TARGET_MAX = 30
AUTHORING_PACKET_SECTION_ORDER = {
    "rtl_flow": 0,
    "io_list": 1,
    "parameters": 2,
    "integration": 3,
    "function_model": 4,
    "cycle_model": 5,
    "fsm": 6,
    "registers": 7,
    "memory": 8,
    "features": 9,
    "error_handling": 10,
    "interrupts": 11,
    "security": 12,
    "synthesis": 13,
    "test_requirements": 14,
    "coverage": 15,
    "equivalence": 16,
    "workflow_todo": 17,
}

EVIDENCE_STOPWORDS = {
    "access",
    "according",
    "all",
    "an",
    "and",
    "any",
    "approved",
    "architectural",
    "as",
    "auto",
    "be",
    "before",
    "behavior",
    "boundary",
    "clear",
    "clears",
    "control",
    "counter",
    "counters",
    "cycle",
    "declared",
    "downstream",
    "effect",
    "effects",
    "error",
    "event",
    "events",
    "every",
    "exactly",
    "expr",
    "expression",
    "externally",
    "feature",
    "field",
    "fields",
    "fl",
    "for",
    "from",
    "function",
    "function_model",
    "generate",
    "generated",
    "generates",
    "gen",
    "has",
    "have",
    "implement",
    "input",
    "interface",
    "interfaces",
    "io",
    "io_list",
    "is",
    "listed",
    "list",
    "map",
    "mapping",
    "mapped",
    "maps",
    "model",
    "module",
    "non",
    "no",
    "observable",
    "okay",
    "output",
    "pending",
    "preserve",
    "protocol",
    "repair",
    "repair_ssot_schema",
    "retained",
    "rtl",
    "rule",
    "rule_expr_completeness",
    "schema",
    "scoreboard",
    "set",
    "side",
    "ssot",
    "stage",
    "state",
    "tb",
    "the",
    "to",
    "transaction",
    "transactions",
    "with",
}

REFERENCE_STOPWORDS = {
    "backpressure",
    "cycle_model",
    "dataflow",
    "error_cases",
    "fsm",
    "function_model",
    "handshake_rules",
    "inputs",
    "invariants",
    "observability",
    "ordering",
    "output_rules",
    "outputs",
    "pipeline",
    "preconditions",
    "register_list",
    "registers",
    "side_effects",
    "state_updates",
    "state_variables",
    "test_requirements",
    "transactions",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(value: object, fallback: str = "item") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text:
        text = fallback
    if not re.match(r"^[A-Za-z_]", text):
        text = f"{fallback}_{text}"
    return text[:96]


def _present(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"none", "n/a", "na", "tbd", "todo"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": val} for key, val in value.items()]
    return [value]


def _load_reference_profile(ip_dir: Path) -> dict[str, Any] | None:
    for rel in ("reports/rtl_reference_profile.json", "rtl/rtl_reference_profile.json"):
        path = ip_dir / rel
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict) or data.get("type") != "rtl_reference_profile":
            continue
        guidance = data.get("guidance") if isinstance(data.get("guidance"), dict) else {}
        summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
        target_summary = (
            data.get("target_candidate_summary")
            if isinstance(data.get("target_candidate_summary"), dict)
            else {}
        )
        bucket_summaries = (
            data.get("bucket_summaries")
            if isinstance(data.get("bucket_summaries"), dict)
            else {}
        )
        summary_keys = (
            "file_count",
            "lines",
            "modules",
            "always_blocks",
            "assigns",
            "nonconstant_assigns",
            "case_blocks",
            "instance_candidates",
            "state_updates",
        )
        return {
            "path": rel,
            "label": data.get("label") or "",
            "generated_at": data.get("generated_at") or "",
            "summary": {
                key: summary.get(key)
                for key in summary_keys
                if key in summary
            },
            "target_candidate_summary": {
                key: target_summary.get(key)
                for key in summary_keys
                if key in target_summary
            },
            "target_candidate_basis": data.get("target_candidate_basis") or "",
            "bucket_summaries": bucket_summaries,
            "top_by_lines": data.get("top_by_lines") if isinstance(data.get("top_by_lines"), list) else [],
            "suggested_ssot_target_scale": data.get("suggested_ssot_target_scale")
            if isinstance(data.get("suggested_ssot_target_scale"), dict)
            else {},
            "guidance": {
                "calibration_only": guidance.get("calibration_only", True),
                "do_not_copy_reference_rtl": guidance.get("do_not_copy_reference_rtl", True),
                "target_candidate_rule": guidance.get("target_candidate_rule") or "",
            },
        }
    return None


RTL_WORKFLOW_NAMES = {"rtl", "rtl-gen", "ssot-rtl", "ssot-rtl-gen", "rtl-generation"}

TOP_FALLBACK_SECTIONS = {
    "top_module",
    "io_list",
    "parameters",
    "interrupts",
    "features",
    "error_handling",
    "security",
    "debug_observability",
    "integration",
    "timing",
    "power",
    "synthesis",
    "dft",
    "test_requirements",
    "quality_gates",
    "workflow_todos",
    "next_step_todos",
}


def _norm_workflow(value: Any) -> str:
    return re.sub(r"[\s_]+", "-", str(value or "").strip().lower())


def _is_rtl_workflow(value: Any) -> bool:
    return _norm_workflow(value) in RTL_WORKFLOW_NAMES


def _ci_get(item: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in item:
            return item[key]
    lower_to_key = {str(key).lower(): key for key in item}
    for key in keys:
        actual = lower_to_key.get(key.lower())
        if actual is not None:
            return item[actual]
    return None


def _rtl_gen_gate_config(doc: dict[str, Any]) -> dict[str, Any]:
    qg = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
    rtl_gen = (
        _ci_get(qg, "rtl_gen", "rtl-gen", "rtl_gate", "rtl_gate.rtl_gen")
        if isinstance(qg, dict) else {}
    )
    if not isinstance(rtl_gen, dict):
        rtl_gen = {}
    return rtl_gen


def _rtl_quality_profile(doc: dict[str, Any], ip: str) -> str:
    """Return the RTL gate profile requested by SSOT.

    The default remains generic/lightweight.  Complex signoff profiles are
    opt-in from SSOT quality_gates, with a narrow DMA330/PL330 name heuristic
    for the common high-complexity DMA flow.
    """
    qg = doc.get("quality_gates") if isinstance(doc.get("quality_gates"), dict) else {}
    rtl_gen = _rtl_gen_gate_config(doc)
    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    raw = (
        _ci_get(rtl_gen, "profile", "quality_profile", "level", "signoff_profile")
        or _ci_get(qg, "rtl_quality_profile", "quality_profile")
        or _ci_get(top, "quality_profile", "rtl_quality_profile")
        or ""
    )
    norm = re.sub(r"[^a-z0-9]+", "_", str(raw).strip().lower()).strip("_")
    if norm in {"prod", "production", "signoff", "pl330", "pl330_level", "dma330", "dma330_level"}:
        return "production"
    name_text = f"{ip} {_ci_get(top, 'name') or ''}".lower()
    if any(token in name_text for token in ("pl330", "dma330", "dma_330")):
        return "production"
    return "standard"


def _int_target(value: Any) -> int | None:
    if value is None or value is False:
        return None
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _rtl_target_scale(doc: dict[str, Any]) -> dict[str, Any]:
    """Return optional SSOT-locked implementation-scale targets.

    These targets are human-owned SSOT policy, not values inferred from a
    reference RTL tree.  Reference profiles may help humans choose the numbers,
    but this parser only trusts explicit SSOT quality_gates fields.
    """
    rtl_gen = _rtl_gen_gate_config(doc)
    raw = _ci_get(
        rtl_gen,
        "target_scale",
        "scale_targets",
        "implementation_scale",
        "rtl_scale",
        "depth_targets",
    )
    if not isinstance(raw, dict):
        return {}

    aliases = {
        "min_source_files": ("min_source_files", "source_files_min", "file_count_min", "files_min", "min_files"),
        "min_modules": ("min_modules", "modules_min", "module_count_min"),
        "min_lines": ("min_lines", "lines_min", "line_count_min"),
        "min_nonconstant_assigns": (
            "min_nonconstant_assigns",
            "nonconstant_assigns_min",
            "assigns_min",
            "min_assigns",
        ),
        "min_procedural_blocks": (
            "min_procedural_blocks",
            "procedural_blocks_min",
            "always_blocks_min",
            "min_always_blocks",
        ),
        "min_state_updates": ("min_state_updates", "state_updates_min"),
        "min_control_flow": ("min_control_flow", "control_flow_min", "case_blocks_min", "min_case_blocks"),
        "min_instances": ("min_instances", "instances_min", "instance_candidates_min"),
        "min_depth_score": ("min_depth_score", "depth_score_min", "implementation_depth_score_min"),
        "min_logic_modules": ("min_logic_modules", "logic_modules_min"),
        "min_behavior_owner_logic_modules": (
            "min_behavior_owner_logic_modules",
            "behavior_owner_logic_modules_min",
            "behavior_owner_modules_min",
        ),
    }
    targets: dict[str, Any] = {}
    for canonical, names in aliases.items():
        value = None
        for name in names:
            value = _ci_get(raw, name)
            if value is not None:
                break
        parsed = _int_target(value)
        if parsed is not None:
            targets[canonical] = parsed

    if not any(key.startswith("min_") for key in targets):
        return {}

    basis = _ci_get(raw, "basis", "source", "rationale", "reference")
    if _present(basis):
        targets["basis"] = _short_text(basis, limit=240)
    reference_profile = _ci_get(raw, "reference_profile", "reference_profile_path", "calibrated_from")
    if _present(reference_profile):
        targets["reference_profile"] = str(reference_profile).strip()
    targets["policy"] = (
        "SSOT-locked scale target. It may be calibrated from a reference profile, "
        "but rtl-gen must satisfy it through IP-specific SSOT behavior, not by copying reference RTL."
    )
    return targets


def _rtl_target_scale_waiver(doc: dict[str, Any]) -> dict[str, Any]:
    rtl_gen = _rtl_gen_gate_config(doc)
    raw = _ci_get(
        rtl_gen,
        "target_scale_waiver",
        "scale_waiver",
        "implementation_scale_waiver",
        "rtl_scale_waiver",
    )
    if not isinstance(raw, dict):
        return {}
    approved = bool(_ci_get(raw, "approved", "accepted", "waived"))
    reason = _ci_get(raw, "reason", "rationale", "why", "basis")
    owner = _ci_get(raw, "owner", "approver", "approved_by")
    waiver: dict[str, Any] = {
        "approved": approved,
        "reason": _short_text(reason, limit=240) if _present(reason) else "",
        "owner": str(owner).strip() if _present(owner) else "",
    }
    return {key: value for key, value in waiver.items() if value not in {"", False}}


def _criteria_items(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [line.strip(" -") for line in value.splitlines() if line.strip(" -")]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                text = _ci_get(item, "criteria", "criterion", "content", "description", "text", "name")
                out.append(_short_text(text if _present(text) else item))
            elif _present(item):
                out.append(str(item))
        return [item for item in out if item]
    if isinstance(value, dict):
        return [f"{key}: {_short_text(val)}" for key, val in value.items() if _present(val)]
    return [str(value)] if _present(value) else []


def _workflow_todo_refs(item: Any) -> list[str]:
    if not isinstance(item, dict):
        return []
    refs: list[str] = []
    for key in ("source_refs", "ssot_refs", "refs", "trace_refs", "source_ref", "ssot_ref", "ref"):
        raw = _ci_get(item, key)
        if isinstance(raw, str):
            refs.extend(part.strip() for part in re.split(r"[,;\n]+", raw) if part.strip())
        elif isinstance(raw, list):
            refs.extend(str(part).strip() for part in raw if str(part).strip())
    return sorted({ref for ref in refs if ref})


def _workflow_todo_entries(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []

    def add_from_sequence(source_base: str, value: Any, *, require_stage: bool) -> None:
        if isinstance(value, dict) and _present(_ci_get(value, "content", "title", "task", "name")):
            stage = _ci_get(value, "workflow", "stage", "step", "target", "agent")
            if not require_stage or not _present(stage) or _is_rtl_workflow(stage):
                entries.append((source_base, value))
            return
        for idx, item in enumerate(_as_list(value)):
            if not isinstance(item, dict):
                item = {"content": item}
            stage = _ci_get(item, "workflow", "stage", "step", "target", "agent")
            if require_stage and _present(stage) and not _is_rtl_workflow(stage):
                continue
            if require_stage and not _present(stage):
                continue
            entries.append((f"{source_base}[{idx}]", item))

    for section in ("workflow_todos", "next_step_todos"):
        root = doc.get(section)
        if isinstance(root, dict):
            for key, value in root.items():
                if _is_rtl_workflow(key):
                    add_from_sequence(f"{section}.{key}", value, require_stage=False)
            for key in ("todos", "items", "tasks"):
                if key in root:
                    add_from_sequence(f"{section}.{key}", root.get(key), require_stage=True)
        elif isinstance(root, list):
            add_from_sequence(section, root, require_stage=True)

    flow = doc.get("generation_flow")
    if isinstance(flow, dict):
        for key in ("workflow_todos", "next_step_todos", "todos", "tasks"):
            if key in flow:
                add_from_sequence(f"generation_flow.{key}", flow.get(key), require_stage=True)
        for step_idx, step in enumerate(_as_list(flow.get("steps"))):
            if not isinstance(step, dict):
                continue
            name = _ci_get(step, "name", "workflow", "stage")
            if not _is_rtl_workflow(name) and "rtl" not in _norm_workflow(name):
                continue
            for key in ("todos", "tasks", "next_step_todos"):
                if key in step:
                    add_from_sequence(f"generation_flow.steps[{step_idx}].{key}", step.get(key), require_stage=False)
    return entries


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _json_report_passed(report: dict[str, Any]) -> bool:
    status = str(report.get("status") or "").strip().lower()
    return report.get("passed") is True or status in {"pass", "passed", "ok"}


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "pass", "passed", "ok"}


def _falsey(value: Any) -> bool:
    if isinstance(value, bool):
        return not value
    return str(value or "").strip().lower() in {"0", "false", "no", "n", "optional", "waived"}


def _required_unblocked_equivalence_goal_ids(goals_doc: dict[str, Any]) -> list[str]:
    goals = goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []
    ids: list[str] = []
    seen: set[str] = set()
    for goal in goals:
        if not isinstance(goal, dict):
            continue
        blocked = _truthy(goal.get("blocked"))
        required = not _falsey(goal.get("required"))
        optional = _truthy(goal.get("optional"))
        gid = str(goal.get("goal_id") or goal.get("id") or "").strip()
        if not gid or blocked or optional or not required:
            continue
        if gid not in seen:
            ids.append(gid)
            seen.add(gid)
    return ids


def _int_field(data: dict[str, Any], *keys: str) -> int | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return int(value)
        try:
            text = str(value).strip()
            if text:
                return int(float(text))
        except (TypeError, ValueError):
            continue
    return None


def _fl_rtl_compare_goal_coverage_issue(goals_doc: dict[str, Any], compare: dict[str, Any]) -> str:
    required_ids = _required_unblocked_equivalence_goal_ids(goals_doc)
    if not required_ids:
        return "equivalence_goals.json has no required unblocked equivalence goals."
    if not compare:
        return "Missing FL-vs-RTL compare artifact: sim/fl_rtl_compare.json."
    if not _json_report_passed(compare):
        return "FL-vs-RTL compare report is not pass."

    summary = compare.get("summary") if isinstance(compare.get("summary"), dict) else {}
    missing_evidence = summary.get("missing_evidence") if isinstance(summary.get("missing_evidence"), list) else []
    stale_evidence = summary.get("stale_evidence") if isinstance(summary.get("stale_evidence"), list) else []
    if missing_evidence:
        return "FL-vs-RTL compare report has missing evidence: " + ", ".join(str(item) for item in missing_evidence[:6])
    if stale_evidence:
        return "FL-vs-RTL compare report has stale evidence: " + ", ".join(str(item) for item in stale_evidence[:6])
    blocked = _int_field(summary, "goals_blocked", "blocked")
    failed = _int_field(summary, "goals_failed", "failed")
    untested = _int_field(summary, "goals_untested", "untested")
    if blocked and blocked > 0:
        return f"FL-vs-RTL compare report still has {blocked} blocked goal(s)."
    if failed and failed > 0:
        return f"FL-vs-RTL compare report still has {failed} failed goal(s)."
    if untested and untested > 0:
        return f"FL-vs-RTL compare report still has {untested} untested goal(s)."

    required_set = set(required_ids)
    goal_rows = compare.get("goals") if isinstance(compare.get("goals"), list) else []
    if goal_rows:
        seen_ids: set[str] = set()
        passed_ids: set[str] = set()
        for row in goal_rows:
            if not isinstance(row, dict):
                continue
            gid = str(row.get("goal_id") or row.get("id") or "").strip()
            if gid not in required_set:
                continue
            status = str(row.get("status") or "").strip().lower()
            events = _int_field(row, "events", "scoreboard_events", "rows")
            if status not in {"untested", "missing", "blocked"} and (events is None or events > 0):
                seen_ids.add(gid)
            if status in {"pass", "passed", "ok"} and (events is None or events > 0):
                passed_ids.add(gid)
        missing = sorted(required_set - seen_ids)
        if missing:
            return "FL-vs-RTL compare did not check required goal(s): " + ", ".join(missing[:8])
        not_passed = sorted(required_set - passed_ids)
        if not_passed:
            return "FL-vs-RTL compare did not pass required goal(s): " + ", ".join(not_passed[:8])
        return ""

    required_count = len(required_ids)
    total = _int_field(summary, "total", "goals_total")
    checked = _int_field(summary, "goals_checked", "checked")
    passed = _int_field(summary, "goals_passed", "passed")
    if total is not None and total < required_count:
        return f"FL-vs-RTL compare total={total} is smaller than required unblocked goals={required_count}."
    if checked is None or checked < required_count:
        return f"FL-vs-RTL compare checked={checked or 0} is smaller than required unblocked goals={required_count}."
    if passed is None or passed < required_count:
        return f"FL-vs-RTL compare passed={passed or 0} is smaller than required unblocked goals={required_count}."
    return ""


def _coverage_closure_issue(report: dict[str, Any]) -> str:
    if not _json_report_passed(report):
        return "Coverage closure report is not pass."
    if report.get("source") != "ssot_coverage_summary":
        return "Coverage closure must be produced by ssot_coverage_summary, not a raw or ad-hoc report."
    limitations = report.get("limitations") if isinstance(report.get("limitations"), dict) else {}
    if limitations:
        return "Coverage closure report still has unwaived limitations."

    functional = report.get("functional") if isinstance(report.get("functional"), dict) else {}
    hit = _int_field(functional, "hit")
    total = _int_field(functional, "total")
    pct_value = functional.get("pct")
    try:
        pct = float(pct_value)
    except (TypeError, ValueError):
        pct = -1.0
    if total is None or total <= 0:
        return "Coverage closure has no planned functional bins."
    if hit is None or hit < total or pct < 100.0:
        return f"Functional coverage is not closed by RTL-observed evidence: hit={hit or 0} total={total} pct={pct_value}."

    rtl_observed = report.get("rtl_observed") if isinstance(report.get("rtl_observed"), dict) else {}
    rtl_status = str(rtl_observed.get("status") or "").strip().lower()
    if rtl_status not in {"pass", "passed", "ok"}:
        return "RTL-observed coverage status is not pass."
    missing_bins = rtl_observed.get("missing_bins") if isinstance(rtl_observed.get("missing_bins"), list) else []
    invalid_rows = rtl_observed.get("invalid_rows") if isinstance(rtl_observed.get("invalid_rows"), list) else []
    if missing_bins:
        return "RTL-observed coverage is missing bin(s): " + ", ".join(str(item) for item in missing_bins[:8])
    if invalid_rows:
        return "RTL-observed coverage has invalid scoreboard row(s): " + ", ".join(str(item) for item in invalid_rows[:4])
    if (_int_field(rtl_observed, "scoreboard_events") or 0) <= 0:
        return "Coverage closure has no scoreboard_events evidence."
    if (_int_field(rtl_observed, "scoreboard_passed_events_with_refs") or 0) <= 0:
        return "Coverage closure has no passing scoreboard event with coverage refs."
    goal_refs = rtl_observed.get("goal_refs") if isinstance(rtl_observed.get("goal_refs"), list) else []
    if not goal_refs:
        return "Coverage closure has no RTL-observed equivalence goal coverage refs."
    return ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _rows_by_id(rows: Any) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(rows, list):
        return out
    for row in rows:
        if not isinstance(row, dict):
            continue
        rid = str(row.get("id") or "").strip()
        if rid:
            out[rid] = row
    return out


def _authority_manifest_issue(authority: dict[str, Any], ip: str) -> str:
    if not authority:
        return "Missing or invalid governance/authority.json."
    if authority.get("type") != "human_llm_authority_manifest":
        return "authority.json is not a human_llm_authority_manifest."
    if str(authority.get("ip") or "") != ip:
        return f"authority.json ip does not match {ip}."

    rules = _rows_by_id(authority.get("operating_rules"))
    missing_rules = [rid for rid in (f"R{idx}" for idx in range(1, 7)) if rid not in rules]
    if missing_rules:
        return "authority.json is missing operating rule(s): " + ", ".join(missing_rules)

    loops = _rows_by_id(authority.get("llm_loops"))
    missing_loops = [lid for lid in (f"L{idx}" for idx in range(1, 10)) if lid not in loops]
    if missing_loops:
        return "authority.json is missing LLM loop(s): " + ", ".join(missing_loops)

    gates = _rows_by_id(authority.get("human_gates"))
    missing_gates = [gid for gid in (f"G{idx}" for idx in range(1, 10)) if gid not in gates]
    if missing_gates:
        return "authority.json is missing human gate(s): " + ", ".join(missing_gates)

    rtl_gen_required_gates = [f"G{idx}" for idx in range(1, 8)]
    not_approved = [
        f"{gid}={str(gates[gid].get('status') or 'missing')}"
        for gid in rtl_gen_required_gates
        if str(gates[gid].get("status") or "").strip().lower() != "approved"
    ]
    if not_approved:
        return "Human authority gate(s) required before production RTL-GEN are not approved: " + ", ".join(not_approved)

    for gid in rtl_gen_required_gates:
        gate = gates[gid]
        if not _string_list(gate.get("locked_artifacts")):
            return f"authority.json {gid} has no locked_artifacts."
        if not _string_list(gate.get("evidence_required")):
            return f"authority.json {gid} has no evidence_required."

    layout = authority.get("repo_layout") if isinstance(authority.get("repo_layout"), dict) else {}
    locked = set(_string_list(layout.get("locked")))
    llm_editable = set(_string_list(layout.get("llm_editable")))
    validators = set(_string_list(layout.get("agent_runnable_validators")))
    for required in ("yaml/", "model/", "verify/equivalence_goals.json"):
        if required not in locked:
            return f"authority.json repo_layout.locked is missing {required}."
    for required in ("rtl/", "tb/", "sim/", "reports/"):
        if required not in llm_editable:
            return f"authority.json repo_layout.llm_editable is missing {required}."
    for required in ("lint/", "sim/", "cov/coverage.json"):
        if required not in validators:
            return f"authority.json repo_layout.agent_runnable_validators is missing {required}."
    return ""


def _signature_canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _signature_hash(obj: Any) -> str:
    return hashlib.sha256(_signature_canon(obj).encode("utf-8")).hexdigest()


def _signature_rule_items(section: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    if isinstance(section, dict):
        for key, value in section.items():
            items.append({"name": key, "value": value})
    elif isinstance(section, list):
        for entry in section:
            if isinstance(entry, dict):
                items.append(entry)
            else:
                items.append({"value": entry})
    return items


def _expected_model_signature(ip: str, ssot: dict[str, Any]) -> dict[str, Any]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = _as_list(fm.get("transactions"))

    def hash_lines(parts: list[str]) -> str:
        return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()

    transaction_parts = [_signature_canon(tx) for tx in txs] if txs else []
    invariants = fm.get("invariants")
    exprs: list[str] = []
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        sample_condition = tx.get("sample_condition")
        if sample_condition is not None:
            exprs.append(str(sample_condition))
        for item in _signature_rule_items(tx.get("output_rules")):
            for field in ("expr", "expression", "value"):
                value = item.get(field)
                if value is not None:
                    exprs.append(str(value))
        for item in _signature_rule_items(tx.get("state_updates")):
            for field in ("expr", "expression", "value"):
                value = item.get(field)
                if value is not None:
                    exprs.append(str(value))
    exprs.sort()
    return {
        "schema_version": 1,
        "type": "model_signature",
        "ip": ip,
        "ssot_hash": _signature_hash(ssot),
        "transactions_hash": hash_lines(transaction_parts),
        "invariants_hash": hashlib.sha256((_signature_canon(invariants) if invariants is not None else "").encode("utf-8")).hexdigest(),
        "expressions_hash": hash_lines(exprs),
    }


def _model_signature_issue(ip_dir: Path, ip: str, signature: dict[str, Any]) -> str:
    if not signature:
        return "Missing or invalid model/model_signature.json."
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot_path.is_file():
        return "Missing SSOT YAML needed to verify model_signature.json."
    try:
        ssot = yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception as exc:
        return f"Cannot read SSOT YAML needed to verify model_signature.json: {exc}."
    if not isinstance(ssot, dict):
        return "SSOT YAML is not a mapping; model_signature.json cannot be verified."
    expected = _expected_model_signature(ip, ssot)
    for key, expected_value in expected.items():
        actual = signature.get(key)
        if actual != expected_value:
            return f"model_signature.json drift at {key}: expected current SSOT-derived value."
    return ""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


RTL_TODO_HASH_VOLATILE_KEYS = {
    "connection_contract_suggestions",
    "generated_at",
    "gate",
    "manifest_hierarchy_evidence",
    "manifest_signal_flow_evidence",
    "owner_logic_evidence",
    "reference_profile",
    "reference_scale_gap",
    "rtl_implementation_depth_evidence",
    "rtl_placeholder_free_evidence",
    "static_evidence",
    "static_rtl_evidence",
    "todo_completion",
    "top_input_consumption_evidence",
    "top_io_contract_evidence",
    "top_output_drive_evidence",
}


def _stable_json_sha256(path: Path, *, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or RTL_TODO_HASH_VOLATILE_KEYS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in volatile_keys
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_ssot(root: Path, ip: str) -> tuple[Path, dict[str, Any]]:
    path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"[derive_rtl_todos] missing SSOT: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(data, dict):
        raise SystemExit("[derive_rtl_todos] SSOT top-level must be a mapping")
    return path, data


def _top_name(doc: dict[str, Any], fallback: str) -> str:
    top = doc.get("top_module") or fallback
    if isinstance(top, dict):
        top = top.get("name") or fallback
    return str(top or fallback)


def _module_file(ip: str, top: str, module: dict[str, Any]) -> str:
    rel = str(module.get("file") or "").strip()
    if rel:
        return rel
    name = str(module.get("name") or top or ip)
    return f"rtl/{_slug(name)}.sv"


def _module_contract_refs(module: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "implements",
        "source_sections",
        "ssot_refs",
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
    ):
        value = module.get(key)
        if isinstance(value, str):
            refs.extend(item.strip() for item in re.split(r"[,;\n]+", value) if item.strip())
        elif isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            refs.extend(str(key2).strip() for key2 in value if str(key2).strip())
    return _expand_relative_refs(refs)


def _expand_relative_refs(refs: list[str]) -> list[str]:
    """Expand shorthand SSOT refs like `.decode` using the prior ref prefix."""

    out: list[str] = []
    base_prefix = ""
    for raw in refs:
        ref = str(raw or "").strip()
        if not ref:
            continue
        if ref.startswith(".") and base_prefix:
            ref = base_prefix + ref
        if not ref.startswith(".") and "." in ref:
            base_prefix = ref.rsplit(".", 1)[0]
        out.append(ref)
    return sorted({ref for ref in out if ref})


def _active_modules(doc: dict[str, Any], ip: str, top: str) -> list[dict[str, Any]]:
    modules: list[dict[str, Any]] = []
    raw = doc.get("sub_modules")
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            ownership = str(item.get("ownership") or "manifest").lower()
            if ownership in {"child_ssot", "conceptual", "coverage", "verification"} or item.get("ssot"):
                continue
            if item.get("rtl_emit") is False:
                continue
            name = str(item.get("name") or Path(_module_file(ip, top, item)).stem or top)
            modules.append({
                "name": name,
                "file": _module_file(ip, top, item),
                "refs": _module_contract_refs(item),
                "raw": item,
            })
    if modules and not any(str(module.get("name") or "") == top or Path(str(module.get("file") or "")).stem == top for module in modules):
        modules.append({
            "name": top,
            "file": f"rtl/{top}.sv",
            "refs": [
                "top_module",
                "io_list",
                "parameters",
                "interrupts",
                "features",
                "error_handling",
                "security",
                "debug_observability",
                "integration",
                "timing",
                "power",
                "synthesis",
                "dft",
                "test_requirements",
                "quality_gates",
                "workflow_todos",
                "next_step_todos",
            ],
            "raw": {"synthetic_top_owner": True},
        })
    if not modules:
        modules.append({"name": top, "file": f"rtl/{top}.sv", "refs": ["top_module", "function_model", "cycle_model"], "raw": {}})
    return modules


def _ref_is_covered(ref: str, owner_ref: str) -> bool:
    return (
        ref == owner_ref
        or ref.startswith(owner_ref + ".")
        or owner_ref.startswith(ref + ".")
        or _ref_leaf_strong_match(ref, owner_ref)
    )


def _ref_leaf_strong_match(ref: str, owner_ref: str) -> bool:
    ref_parent, _, ref_leaf = ref.rpartition(".")
    owner_parent, _, owner_leaf = owner_ref.rpartition(".")
    if not ref_parent or ref_parent != owner_parent:
        return False
    ref_parts = {part for part in re.split(r"[_\\W]+", ref_leaf.lower()) if len(part) > 1}
    owner_parts = {part for part in re.split(r"[_\\W]+", owner_leaf.lower()) if len(part) > 1}
    if not ref_parts or not owner_parts:
        return False
    return owner_parts.issubset(ref_parts) or ref_parts.issubset(owner_parts)


def _owner_token_set(value: Any) -> set[str]:
    tokens: set[str] = set()

    def add_text(text: Any) -> None:
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(text or "")):
            for part in re.split(r"[_\W]+", token):
                lower = part.lower().strip("_")
                if len(lower) <= 1 or lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
                    continue
                tokens.add(lower)
            lower_token = token.lower().strip("_")
            if len(lower_token) > 1 and lower_token not in EVIDENCE_STOPWORDS and lower_token not in REFERENCE_STOPWORDS:
                tokens.add(lower_token)

    def visit(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, dict):
            for key, val in item.items():
                if str(key).lower() not in {"metadata", "notes"}:
                    visit(val)
            return
        if isinstance(item, list):
            for val in item:
                visit(val)
            return
        add_text(item)

    visit(value)
    return tokens


def _module_owner_terms(module: dict[str, Any], top: str) -> tuple[set[str], set[str]]:
    top_terms = _owner_token_set(top)
    name_text = " ".join(str(module.get(key) or "") for key in ("name", "file"))
    name_terms = _owner_token_set(name_text) - top_terms - {"rtl", "sv", "v", "module"}
    ref_terms: set[str] = set()
    for owner_ref in module.get("refs") or []:
        ref_terms.update(_owner_token_set(owner_ref))
    return name_terms, ref_terms - top_terms


def _module_owner_ref_terms_for_task(module: dict[str, Any], task_ref: str, top: str) -> set[str]:
    top_terms = _owner_token_set(top)
    section = str(task_ref or "").split(".", 1)[0]
    terms: set[str] = set()
    for owner_ref in module.get("refs") or []:
        owner_ref = str(owner_ref or "")
        if owner_ref == section or owner_ref.startswith(section + "."):
            terms.update(_owner_token_set(owner_ref))
    return terms - top_terms


def _semantic_task_terms(ref: str, value: Any) -> set[str]:
    terms = _owner_token_set(ref)
    if re.fullmatch(r"function_model\.transactions\.[^.]+", ref) and isinstance(value, dict):
        primary = {
            key: value.get(key)
            for key in ("id", "name", "opcode", "op", "category", "class", "type", "kind")
            if _present(value.get(key))
        }
        terms.update(_owner_token_set(primary))
        return terms
    terms.update(_owner_token_set(value))
    return terms


def _semantic_owner_match(ref: str, value: Any, modules: list[dict[str, Any]], top: str) -> dict[str, str] | None:
    task_terms = _semantic_task_terms(ref, value)
    task_terms -= {"function", "model", "cycle", "transactions", "transaction", "state", "variables"}
    if not task_terms:
        return None
    scored: list[tuple[int, int, dict[str, Any], str]] = []
    for index, module in enumerate(modules):
        name_terms, _all_ref_terms = _module_owner_terms(module, top)
        ref_terms = _module_owner_ref_terms_for_task(module, ref, top)
        name_hits = task_terms & name_terms
        ref_hits = task_terms & ref_terms
        score = len(ref_hits) * 2 + len(name_hits) * 3
        if score <= 0:
            continue
        hit_terms = sorted(ref_hits | name_hits)
        scored.append((score, -index, module, "semantic_terms:" + ",".join(hit_terms[:6])))
    if not scored:
        return None
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    score, _neg_index, module, matched_ref = scored[0]
    if score < 2:
        return None
    return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}


def _memory_owner_fallback(ref: str, value: Any, modules: list[dict[str, Any]], top: str) -> dict[str, str] | None:
    if not ref.startswith("memory."):
        return None
    task_terms = _semantic_task_terms(ref, value)
    task_terms -= {
        "memory",
        "memories",
        "instance",
        "instances",
        "register",
        "registers",
        "storage",
        "width",
        "depth",
        "latency",
        "ff",
    }
    if not task_terms:
        return None
    scored: list[tuple[int, int, dict[str, Any], str]] = []
    for index, module in enumerate(modules):
        name_terms, ref_terms = _module_owner_terms(module, top)
        hits = task_terms & (name_terms | ref_terms)
        if not hits:
            continue
        score = len(hits) * 2
        if hits & name_terms:
            score += 1
        scored.append((score, -index, module, "memory_semantic_terms:" + ",".join(sorted(hits)[:6])))
    if not scored:
        return None
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    _score, _neg_index, module, matched_ref = scored[0]
    return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}


def _control_owner_fallback(ref: str, modules: list[dict[str, Any]], top: str) -> dict[str, str] | None:
    if not ref.startswith(("function_model.", "cycle_model.")):
        return None
    candidates: list[tuple[int, int, dict[str, Any], str]] = []
    for index, module in enumerate(modules):
        name_terms, ref_terms = _module_owner_terms(module, top)
        combined = name_terms | ref_terms
        score = 0
        if combined & {"engine", "core", "controller", "control", "fsm"}:
            score += 4
        if combined & {"pipeline", "execute", "decode", "fetch"}:
            score += 2
        if "top" in combined:
            score += 1
        if score:
            candidates.append((score, -index, module, "control_owner_fallback"))
    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    score, _neg_index, module, matched_ref = candidates[0]
    if score < 2:
        return None
    return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}


def _direct_name_owner_match(ref: str, modules: list[dict[str, Any]]) -> dict[str, str] | None:
    """Map a task ref to a module whose name uniquely contains the ref's
    second-level token.

    This catches the common case where the SSOT omits ``sub_modules[].refs``
    but uses consistent naming (e.g. ``fsm.rx_fsm.transitions.transition_0``
    should land on a module named ``*rx_fsm*``). Token length must exceed two
    characters to avoid noise from generic prefixes like ``tx`` or ``rx`` when
    they happen to appear as substrings of unrelated module names.
    """
    parts = [part for part in str(ref or "").split(".") if part]
    if len(parts) < 2:
        return None
    candidate = parts[1].lower()
    if len(candidate) < 3:
        return None
    hits = [m for m in modules if candidate in str(m.get("name", "")).lower()]
    if len(hits) != 1:
        return None
    module = hits[0]
    return {
        "module": str(module.get("name") or ""),
        "file": str(module.get("file") or ""),
        "matched_ref": f"name_token:{candidate}",
    }


def _owner_for(ref: str, modules: list[dict[str, Any]], top: str, value: Any = None) -> dict[str, str]:
    if ref.startswith("cycle_model.handshake_rules."):
        top_module = next((m for m in modules if str(m.get("name")) == top or Path(str(m.get("file"))).stem == top), None)
        if top_module is not None:
            return {
                "module": str(top_module["name"]),
                "file": str(top_module["file"]),
                "matched_ref": "top_level_handshake_rule",
            }
    matches: list[tuple[dict[str, Any], str]] = []
    for module in modules:
        refs = module.get("refs") if isinstance(module.get("refs"), list) else []
        for owner_ref in refs:
            owner_ref = str(owner_ref)
            if _ref_is_covered(ref, owner_ref):
                matches.append((module, owner_ref))
    if matches:
        def _specificity(item):
            return (len(str(item[1]).split(".")), len(str(item[1])))
        best = _specificity(max(matches, key=_specificity))
        top_tier = [item for item in matches if _specificity(item) == best]
        if len(top_tier) > 1:
            # Multiple modules share the same most-specific owner_ref (e.g. both
            # ``uart_lite_tx`` and ``uart_lite_rx`` carry ``cycle_model.pipeline``
            # in their refs). Break the tie by counting name-vs-task token
            # overlap — the leaf parts of the ref typically encode which side
            # owns it (``RX_IDLE`` vs ``TX_DATA``), and the module whose name
            # shares tokens with the ref is the right owner.
            ref_tokens = _owner_token_set(ref)
            scored = []
            for module, matched_ref in top_tier:
                name_tokens = _owner_token_set(module.get("name", ""))
                # Strip top-module tokens so generic shared prefixes like
                # ``uart`` / ``lite`` do not count toward the hit total.
                top_tokens = _owner_token_set(top)
                disc_name_tokens = name_tokens - top_tokens
                hits = len(ref_tokens & disc_name_tokens)
                scored.append((hits, module, matched_ref))
            scored.sort(key=lambda row: row[0], reverse=True)
            if scored[0][0] > scored[1][0]:
                _, module, matched_ref = scored[0]
                return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}
        module, matched_ref = top_tier[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}
    direct_owner = _direct_name_owner_match(ref, modules)
    if direct_owner is not None:
        return direct_owner
    semantic_owner = _semantic_owner_match(ref, value, modules, top)
    if semantic_owner is not None:
        return semantic_owner
    memory_owner = _memory_owner_fallback(ref, value, modules, top)
    if memory_owner is not None:
        return memory_owner
    section = ref.split(".", 1)[0]
    section_matches = [
        module
        for module in modules
        if any(str(owner_ref) == section or str(owner_ref).startswith(section + ".") for owner_ref in (module.get("refs") or []))
    ]
    if len(section_matches) == 1:
        module = section_matches[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": f"unique_{section}_owner"}
    if len(modules) == 1:
        module = modules[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": "single_owner"}
    control_owner = _control_owner_fallback(ref, modules, top)
    if control_owner is not None:
        return control_owner
    top_module = next((m for m in modules if str(m.get("name")) == top or Path(str(m.get("file"))).stem == top), None)
    if top_module is not None and section in TOP_FALLBACK_SECTIONS:
        return {"module": str(top_module["name"]), "file": str(top_module["file"]), "matched_ref": "top_fallback"}
    return {"module": "", "file": "", "matched_ref": ""}


def _normalize_owner_file_for_ip(owner_file: Any, ip: str) -> str:
    rel = str(owner_file or "").strip()
    if not rel:
        return ""
    rel = rel.replace("\\", "/")
    prefix = f"{ip}/"
    if rel.startswith(prefix):
        rel = rel[len(prefix):]
    return rel.lstrip("/")


def _rtl_contract_owner_overrides(ip_dir: Path, ip: str, modules: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    """Read rtl-gen-owned owner resolutions from rtl_contract.json.

    Some production packets are intentionally emitted as RTL contract metadata
    first, then the TODO derivation step decides which owner module packet
    should receive the concrete RTL edit.  Without this bridge those tasks stay
    permanently "unowned" and the LLM keeps reopening a human gate.
    """
    path = ip_dir / "rtl" / "rtl_contract.json"
    report = _safe_read_json(path)
    if not report:
        return {}

    module_by_name = {str(module.get("name") or ""): module for module in modules}
    module_by_file = {
        str(module.get("file") or "").replace("\\", "/"): module
        for module in modules
        if str(module.get("file") or "").strip()
    }

    overrides: dict[str, dict[str, str]] = {}
    rows: list[Any] = []
    for key in ("ownership_updates", "owner_resolution", "owner_resolutions", "source_ref_ownership"):
        value = report.get(key)
        if isinstance(value, list):
            rows.extend(value)

    for row in rows:
        if not isinstance(row, dict):
            continue
        source_ref = str(row.get("source_ref") or row.get("ssot_ref") or "").strip()
        if not source_ref:
            continue
        owner_module = str(row.get("owner_module") or row.get("module") or "").strip()
        owner_file = _normalize_owner_file_for_ip(row.get("owner_file") or row.get("file"), ip)
        manifest = module_by_name.get(owner_module) if owner_module else None
        if manifest is None and owner_file:
            manifest = module_by_file.get(owner_file)
        if manifest is None:
            continue
        manifest_name = str(manifest.get("name") or owner_module).strip()
        manifest_file = str(manifest.get("file") or owner_file).strip()
        if not manifest_name or not manifest_file:
            continue
        overrides[source_ref] = {
            "module": manifest_name,
            "file": manifest_file,
            "matched_ref": "rtl_contract.owner_resolution",
        }
    return overrides


def _apply_rtl_contract_owner_overrides(
    tasks: list[dict[str, Any]],
    owner_overrides: dict[str, dict[str, str]],
) -> None:
    if not owner_overrides:
        return
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("owner_module") or task.get("owner_file"):
            continue
        source_ref = str(task.get("source_ref") or "").strip()
        owner = owner_overrides.get(source_ref)
        if not owner:
            continue
        task["owner_module"] = owner.get("module") or ""
        task["owner_file"] = owner.get("file") or ""
        task["owner_match"] = owner.get("matched_ref") or "rtl_contract.owner_resolution"


def _task_mentions_name(task: dict[str, Any], name: str) -> bool:
    needle = str(name or "").strip().lower()
    if not needle:
        return False
    fields = [
        task.get("source_ref"),
        task.get("content"),
        task.get("detail"),
        task.get("evidence_terms"),
        task.get("ssot_context"),
        task.get("ssot_refs"),
    ]
    return needle in json.dumps(fields, sort_keys=True, default=str).lower()


def _apply_memory_owner_from_function_tasks(tasks: list[dict[str, Any]]) -> None:
    """Assign unowned SSOT memory flops to the FunctionModel task that updates them."""

    owner_tasks = [
        task
        for task in tasks
        if isinstance(task, dict)
        and str(task.get("category") or "").startswith("function_model.")
        and (task.get("owner_module") or task.get("owner_file"))
    ]
    category_weight = {
        "function_model.state_update": 50,
        "function_model.output_rule": 35,
        "function_model.input": 30,
        "function_model.state_variable": 20,
        "function_model.transaction": 10,
    }
    for task in tasks:
        if not isinstance(task, dict) or str(task.get("category") or "") != "memory.instances":
            continue
        if task.get("owner_module") or task.get("owner_file"):
            continue
        ctx = task.get("ssot_context") if isinstance(task.get("ssot_context"), dict) else {}
        name = str(ctx.get("name") or str(task.get("source_ref") or "").rsplit(".", 1)[-1]).strip()
        if not name:
            continue
        candidates: list[tuple[int, str, str, dict[str, Any]]] = []
        for other in owner_tasks:
            if not _task_mentions_name(other, name):
                continue
            category = str(other.get("category") or "")
            score = category_weight.get(category, 1)
            source_ref = str(other.get("source_ref") or "")
            if name in source_ref:
                score += 20
            if f"{name}_next" in source_ref:
                score += 20
            owner_module = str(other.get("owner_module") or "")
            owner_file = str(other.get("owner_file") or "")
            candidates.append((score, owner_module, owner_file, other))
        if not candidates:
            continue
        candidates.sort(key=lambda row: row[0], reverse=True)
        top_score = candidates[0][0]
        top = [row for row in candidates if row[0] == top_score]
        top_owners = {(row[1], row[2]) for row in top}
        if len(top_owners) != 1:
            continue
        _score, owner_module, owner_file, owner_task = top[0]
        task["owner_module"] = owner_module
        task["owner_file"] = owner_file
        task["owner_match"] = f"function_model_memory_owner:{owner_task.get('source_ref')}"


def _looks_like_design_token(token: str) -> bool:
    text = str(token or "").strip()
    if len(text) <= 1:
        return False
    lower = text.lower()
    if lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
        return False
    if _looks_like_requirement_label_token(text):
        return False
    if re.fullmatch(r".*_\d+", text):
        return False
    return bool("_" in text or re.search(r"[A-Z]", text) or re.search(r"\d", text))


def _looks_like_requirement_label_token(token: str) -> bool:
    """Detect snake-case requirement labels that are not RTL identifiers.

    SSOT cycle-model prose is sometimes compressed into labels such as
    ``no_apb_backpressure_generated`` or
    ``every_function_model_transaction_has_cycle_model_stage_mapping``.  Those
    labels describe behavior; treating the whole string as a required live RTL
    identifier encourages unused marker signals.
    """

    text = str(token or "").strip()
    if "_" not in text:
        return False
    lower = text.lower()
    parts = [part for part in lower.split("_") if part]
    if not parts:
        return False
    if parts[0] in {"every", "no"} and (
        "generated" in parts
        or "mapping" in parts
        or "transaction" in parts
        or "transactions" in parts
        or "backpressure" in parts
    ):
        return True
    if "function_model" in lower or "cycle_model" in lower:
        if any(part in {"every", "has", "mapping", "transaction", "transactions"} for part in parts):
            return True
    return False


def _split_design_token(token: str) -> set[str]:
    out: set[str] = set() if _looks_like_requirement_label_token(token) else {token}
    if "_" in token:
        for part in token.split("_"):
            if _looks_like_design_token(part) or part.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS:
                out.add(part)
    return {
        item
        for item in out
        if _looks_like_design_token(item)
        or ("_" not in item and len(item) > 1 and item.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS)
    }


def _field_name_aliases_parent_register(field: str, parent_register: str) -> bool:
    """Return true when a short field name is a clear alias of its register.

    Register field names often use compact forms such as ``dout`` for
    ``DATA_OUT`` or ``din`` for ``DATA_IN``. Requiring the literal compact
    field token in RTL pushes the LLM toward marker-only identifiers even
    though the real implementation naturally uses the parent register name.
    """

    field_norm = re.sub(r"[^a-z0-9]", "", str(field or "").lower())
    parent_parts = [
        part
        for part in re.split(r"[^a-z0-9]+", str(parent_register or "").lower())
        if part
    ]
    if not field_norm or not parent_parts:
        return False
    parent_norm = "".join(parent_parts)
    if field_norm == parent_norm or field_norm in parent_norm:
        return True
    if len(parent_parts) >= 2:
        first_initial_rest = parent_parts[0][0] + "".join(parent_parts[1:])
        acronym = "".join(part[0] for part in parent_parts)
        if field_norm in {first_initial_rest, acronym}:
            return True
    return False


def _direct_string_token_is_evidence(category: str, token: str) -> bool:
    lower = str(token or "").lower()
    if lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
        return False
    if category == "cycle_model.observability":
        # Observability entries are often prose such as "Every transaction maps..."
        # Plain English words must not become RTL evidence requirements.
        return _looks_like_design_token(token)
    return True


DIRECT_STRING_EVIDENCE_CATEGORIES = {
    "cycle_model.observability",
    "registers.field",
    "fsm.state",
    "fsm.transition",
}

NAME_EVIDENCE_CATEGORIES = {
    "function_model.output_rule",
    "function_model.state_update",
    "function_model.state_variable",
    "registers.register",
    "registers.field",
    "registers.architectural_state",
    "memory.instances",
    "interrupts.sources",
    "cycle_model.handshake_rules",
    "cycle_model.pipeline",
    "cycle_model.observability",
    "fsm.state",
    "fsm.transition",
}


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except TypeError:
        return str(value)


def _is_repair_generated_fm_marker(value: Any) -> bool:
    """Detect repair-only FunctionModel marker rows.

    repair_ssot_schema.py may make prose-only transactions machine-readable by
    adding ``*_observed`` state markers. Those markers keep the SSOT structurally
    valid, but they are not real architectural RTL identifiers. Requiring them as
    live DUT tokens causes rtl-gen to add marker signals instead of implementing
    the actual IP behavior.
    """

    text = _json_text(value).lower()
    marker_phrases = (
        "auto-injected transaction coverage/state marker",
        "repair marker making this transaction machine-checkable",
        "ssot-gen should replace with ip-specific",
        "architectural output matches feature definition",
        "architectural state updates according to fsm/control policy",
        "feature trigger is asserted under legal configuration",
    )
    if any(phrase in text for phrase in marker_phrases) and re.search(r"\bfm\d+_observed\b", text):
        return True
    if isinstance(value, dict):
        tx_id = str(value.get("id") or "").strip().lower()
        name = str(value.get("name") or "").strip().lower()
        if re.fullmatch(r"fm\d+", tx_id) and re.fullmatch(r"feature_\d+", name):
            state_text = _json_text(value.get("state") or value.get("states") or value.get("signal")).lower()
            if re.search(r"\bfm\d+_observed\b", state_text):
                return True
    return False


def _is_repair_generated_fm_task(category: str, value: Any) -> bool:
    return category.startswith("function_model.") and _is_repair_generated_fm_marker(value)


def _evidence_terms(category: str, source_ref: str, value: Any) -> list[str]:
    if _is_repair_generated_fm_task(category, value):
        return []

    terms: set[str] = set()
    protocol_alias_seen = False
    reserved_register_field = (
        category == "registers.field"
        and (
            str(_ci_get(value, "name", "field", "id") or "").strip().lower() == "reserved"
            or str(source_ref or "").rsplit(".", 1)[-1].lower() == "reserved"
        )
    )

    def add_identifier_terms(value: Any) -> None:
        """Add explicit SSOT identifiers such as ports/states/registers.

        These are not prose, so lowercase SystemVerilog-style names like
        ``prdata`` and ``paddr`` are valid evidence terms even though they do
        not contain underscores or uppercase characters.
        """
        if value is None:
            return
        if isinstance(value, dict):
            for item in value.values():
                add_identifier_terms(item)
            return
        if isinstance(value, list):
            for item in value:
                add_identifier_terms(item)
            return
        text = str(value)
        raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
        if not raw_tokens:
            return
        for token in raw_tokens:
            lower = token.lower()
            if lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
                continue
            if len(raw_tokens) == 1 or _looks_like_design_token(token):
                terms.update(_split_design_token(token))
                terms.add(token)

    def add_protocol_aliases(text: str) -> None:
        nonlocal protocol_alias_seen
        lower = text.lower()
        if "okay" not in lower and "ok" not in lower:
            return
        if "rresp" in lower or "read response" in lower:
            terms.update({"rsp", "ld_rsp_error_i", "ld_rsp_error"})
            protocol_alias_seen = True
        if "bresp" in lower or "write response" in lower:
            terms.update({"rsp", "st_rsp_error_i", "st_rsp_error"})
            protocol_alias_seen = True

    def visit(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, dict):
            identity_keys = ("field", "signal", "port", "state", "output", "event", "stage", "register", "from", "to")
            if category in NAME_EVIDENCE_CATEGORIES:
                identity_keys = ("id", "name", *identity_keys)
            if category == "cycle_model.pipeline":
                identity_keys = ("clock", "action", "signal", "port", "event", "condition", "expr", "expression")
            if category == "workflow_todo.rtl_gen":
                # Workflow TODO IDs/source_refs are often generated bookkeeping
                # names such as RTL_FM_TX_FM2. The SSOT-derived semantic tasks
                # below carry the actual behavior checks, so workflow_todo static
                # evidence should anchor to real owner artifacts/signals only.
                identity_keys = ("owner_module", "owner_file", "signal", "port", "state", "output", "event", "register")
            for key in identity_keys:
                if _present(value.get(key)):
                    if key in {"id", "name", "field", "signal", "port", "state", "output", "event", "register", "from", "to"}:
                        add_identifier_terms(value.get(key))
                    visit(value.get(key))
            for key in ("expr", "expression", "condition"):
                if isinstance(value.get(key), str):
                    add_protocol_aliases(value[key])
                    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", value[key]):
                        if _looks_like_design_token(token):
                            terms.update(_split_design_token(token))
            return
        if isinstance(value, list):
            for item in value:
                visit(item)
            return
        text = str(value)
        for quoted in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", text):
            if _looks_like_design_token(quoted):
                terms.update(_split_design_token(quoted))
        if category in {"cycle_model.observability", "cycle_model.ordering"}:
            # Free-form cycle-model prose is guidance for model/coverage
            # alignment, not a request to mint RTL identifiers from words in
            # the sentence. A single structured/standalone signal name still
            # becomes evidence; prose should be covered by more specific tasks.
            raw_tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
            if len(raw_tokens) == 1 and _looks_like_design_token(raw_tokens[0]):
                terms.update(_split_design_token(raw_tokens[0]))
            return
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
            if category in DIRECT_STRING_EVIDENCE_CATEGORIES and _direct_string_token_is_evidence(category, token):
                terms.add(token)
            elif _looks_like_requirement_label_token(token):
                terms.update(_split_design_token(token))
            elif "_" in token and _looks_like_design_token(token):
                terms.update(_split_design_token(token))

    visit(value)
    if category == "registers.field" and not reserved_register_field:
        match = re.search(r"registers\.register_list\.([^.]+)\.fields\.([^.]+)$", str(source_ref or ""))
        if match:
            parent, field = match.group(1), match.group(2)
            field_name = str(_ci_get(value, "name", "field", "id") or field)
            if _field_name_aliases_parent_register(field_name, parent):
                terms.add(parent)
                terms.update(_split_design_token(parent))
    if reserved_register_field:
        # "reserved" is a semantic field policy, not a live RTL identifier.
        # Use the parent register/mask evidence instead so LLMs do not add
        # marker-only reserved signals solely to satisfy static text matching.
        terms.discard("reserved")
        parent = ""
        match = re.search(r"registers\.register_list\.([^.]+)\.fields\.reserved$", str(source_ref or ""))
        if match:
            parent = match.group(1)
        if parent:
            terms.add(parent)
            terms.update(_split_design_token(parent))
        terms.update({"mask", "GPIO_MASK"})
    if protocol_alias_seen and category.startswith("function_model."):
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", source_ref):
            if token.startswith("FM_"):
                terms.update(_split_design_token(token))
    terms = {term for term in terms if term.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS}
    return sorted(terms)[:16]


def _function_leaf_evidence_value(tx: dict[str, Any], key: str, sub: Any) -> Any:
    if key not in {"inputs", "outputs", "side_effects", "error_cases"}:
        return sub
    output_ports: list[Any] = []
    for rule in _as_list(tx.get("output_rules")):
        if isinstance(rule, dict):
            output_ports.append(rule.get("port") or rule.get("name"))
    state_names: list[Any] = []
    for update in _as_list(tx.get("state_updates")):
        if isinstance(update, dict):
            state_names.append(update.get("name") or update.get("state"))
    return {
        "id": tx.get("id"),
        "name": tx.get("name"),
        "signal": [sub, *(_as_list(tx.get("required_fields")))],
        "port": output_ports,
        "state": state_names,
        "condition": tx.get("sample_condition"),
    }


def _function_invariant_evidence_value(fm: dict[str, Any], item: Any) -> Any:
    raw_terms = _owner_token_set(item)
    states: list[Any] = []
    for state in _as_list(fm.get("state_variables")):
        if not isinstance(state, dict):
            continue
        state_terms = _owner_token_set({
            "name": state.get("name"),
            "source": state.get("source"),
            "description": state.get("description"),
        })
        if raw_terms & state_terms:
            states.append(state.get("name"))

    ports: list[Any] = []
    for tx in _as_list(fm.get("transactions")):
        if not isinstance(tx, dict):
            continue
        tx_terms = _owner_token_set(tx)
        if not (raw_terms & tx_terms):
            continue
        ports.extend(_as_list(tx.get("required_fields")))
        for rule in _as_list(tx.get("output_rules")):
            if isinstance(rule, dict):
                ports.append(rule.get("port") or rule.get("name"))

    return {
        "signal": item,
        "state": states,
        "port": ports,
    }


def _short_text(value: Any, limit: int = 120) -> str:
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _ssot_context(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {"value": _short_text(value)} if _present(value) else {}
    context: dict[str, str] = {}
    for key in (
        "id",
        "name",
        "field",
        "register",
        "port",
        "signal",
        "state",
        "output",
        "event",
        "stage",
        "from",
        "to",
        "condition",
        "action",
        "expr",
        "expression",
        "value",
        "width",
        "depth",
        "reset",
        "access",
        "offset",
        "address",
        "cycle",
        "latency",
        "direction",
        "clear",
        "mask",
        "expected",
    ):
        if _present(value.get(key)):
            context[key] = _short_text(value.get(key))
    return context


def _append_detail_context(detail: str, *, source_ref: str, owner: dict[str, str], value: Any) -> str:
    lines = [detail.rstrip()]
    lines.append(f"SSOT ref: {source_ref}.")
    if owner.get("module") or owner.get("file"):
        lines.append(
            "Owner: "
            f"{owner.get('module') or '(unassigned)'}"
            f" in {owner.get('file') or '(unassigned file)'}"
            f" via {owner.get('matched_ref') or 'no match'}."
        )
    context = _ssot_context(value)
    if context:
        rendered = "; ".join(f"{key}={val}" for key, val in context.items())
        lines.append(f"SSOT item context: {rendered}.")
    return "\n".join(lines)


def _specific_criteria(category: str, source_ref: str, value: Any, owner: dict[str, str]) -> list[str]:
    criteria: list[str] = [
        f"Traceability keeps source_ref {source_ref}",
    ]
    if owner.get("file"):
        criteria.append(f"Primary implementation evidence is in {owner['file']}")
    context = _ssot_context(value)
    name = context.get("name") or context.get("id") or context.get("field") or context.get("port") or source_ref
    if context.get("width"):
        criteria.append(f"{name} width matches SSOT value {context['width']}")
    if "reset" in context:
        criteria.append(f"{name} reset behavior matches SSOT value {context['reset']}")
    if context.get("access"):
        criteria.append(f"{name} access policy {context['access']} is implemented without read/write shortcuts")
    if context.get("offset") or context.get("address"):
        criteria.append(f"{name} decode uses SSOT address/offset {context.get('offset') or context.get('address')}")
    if context.get("expr") or context.get("expression"):
        criteria.append(f"{name} RTL expression implements SSOT expression {context.get('expr') or context.get('expression')}")
    if context.get("port"):
        criteria.append(f"DUT port {context['port']} is the implementation/observation point for {name}")
    if context.get("direction"):
        criteria.append(f"{name} port direction remains {context['direction']}")
    if context.get("condition"):
        criteria.append(f"{name} condition is implemented as RTL control logic: {context['condition']}")
    if context.get("from") or context.get("to"):
        criteria.append(f"{name} transition path {context.get('from', '?')} -> {context.get('to', '?')} is encoded or explicitly proven equivalent")
    if context.get("cycle") or context.get("latency"):
        criteria.append(f"{name} timing uses SSOT cycle/latency {context.get('cycle') or context.get('latency')}")
    if context.get("depth"):
        criteria.append(f"{name} storage depth matches SSOT value {context['depth']}")
    if context.get("clear"):
        criteria.append(f"{name} clear behavior matches SSOT clear policy {context['clear']}")
    if context.get("mask"):
        criteria.append(f"{name} mask behavior matches SSOT mask policy {context['mask']}")
    if context.get("expected"):
        criteria.append(f"Downstream checker compares RTL-observed behavior against expected result: {context['expected']}")

    if category == "registers.field":
        criteria.extend([
            f"{name} readback returns implemented RTL state when readable",
            f"{name} write/clear side effects are connected to owning control/status logic",
        ])
    elif category == "function_model.output_rule":
        criteria.append(f"{name} is not implemented only in FunctionalModel or scoreboard code")
    elif category == "function_model.state_update":
        criteria.append(f"{name} updates exactly once at the SSOT-defined transaction acceptance point")
    elif category.startswith("cycle_model."):
        criteria.append(f"{name} appears in RTL sample/hold/FSM/ready-valid timing, not only in TB")
    elif category == "coverage.functional_bin":
        criteria.append(f"{name} can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals")

    seen: set[str] = set()
    out: list[str] = []
    for item in criteria:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _task(
    tasks: list[dict[str, Any]],
    *,
    category: str,
    source_ref: str,
    title: str,
    detail: str,
    criteria: list[str],
    owner: dict[str, str],
    priority: str = "high",
    value: Any = None,
    required: bool = True,
) -> None:
    index = len(tasks) + 1
    repair_generated_fm_marker = _is_repair_generated_fm_task(category, value)
    if repair_generated_fm_marker:
        required = False
        priority = "low"
    requires_static = category.startswith(STATIC_EVIDENCE_CATEGORIES) or category == "workflow_todo.rtl_gen"
    terms = _evidence_terms(category, source_ref, value)
    enriched_detail = _append_detail_context(detail, source_ref=source_ref, owner=owner, value=value)
    if repair_generated_fm_marker:
        enriched_detail = (
            enriched_detail
            + "\n\nRepair-generated FunctionModel marker: this SSOT row is advisory traceability from schema repair. "
            "Do not add dedicated RTL ports, wires, or state solely for fm*_observed markers."
        )
    enriched_criteria: list[str] = []
    seen_criteria: set[str] = set()
    for item in [*criteria, *_specific_criteria(category, source_ref, value, owner)]:
        if item not in seen_criteria:
            enriched_criteria.append(item)
            seen_criteria.add(item)
    task = {
        "id": f"RTL-{index:04d}",
        "category": category,
        "source_ref": source_ref,
        "content": title,
        "detail": enriched_detail,
        "criteria": enriched_criteria,
        "owner_module": owner.get("module") or "",
        "owner_file": owner.get("file") or "",
        "owner_match": owner.get("matched_ref") or "",
        "ssot_refs": [source_ref],
        "ssot_context": _ssot_context(value),
        "evidence_terms": terms,
        "requires_static_rtl_evidence": requires_static and bool(terms),
        "required": required,
        "priority": priority,
    }
    if repair_generated_fm_marker:
        task["policy_tags"] = ["repair_generated_fm_marker", "verification_advisory"]
    tasks.append(task)


def _item_name(item: Any, idx: int, fallback: str = "item") -> str:
    if isinstance(item, dict):
        for key in ("id", "name", "field", "signal", "port", "state", "stage", "event", "register"):
            if _present(item.get(key)):
                return str(item[key])
    return f"{fallback}_{idx}"


def _add_base_tasks(tasks: list[dict[str, Any]], ip: str, top: str, owner: dict[str, str]) -> None:
    _task(
        tasks,
        category="rtl_flow.seed",
        source_ref="top_module",
        title="Read SSOT and build dynamic RTL implementation ledger",
        detail="Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.",
        criteria=[
            "rtl_todo_plan.json was regenerated from the current SSOT",
            "Every required task in the plan is either implemented, evidenced, or escalated",
            "No IP-specific fixed template is used as the source of truth",
        ],
        owner=owner,
        value={"ip": ip, "top": top},
    )
    _task(
        tasks,
        category="rtl_flow.top",
        source_ref="io_list",
        title="Implement top-level ports, reset, and filelist integration",
        detail="The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.",
        criteria=[
            "Top module name matches SSOT top_module",
            "Every SSOT top-level port appears with matching direction and width",
            "Filelist contains all LLM-authored RTL sources and no stale sources",
        ],
        owner=owner,
        value=top,
    )


def _add_rtl_gate_todo_tasks(tasks: list[dict[str, Any]], owner: dict[str, str], *, profile: str) -> None:
    gate_specs = [
        {
            "kind": "ssot_required_sections",
            "source_ref": "quality_gates.rtl_gen.ssot_required_sections",
            "content": "Gate: SSOT function_model and cycle_model are present before RTL generation",
            "detail": "rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.",
            "criteria": [
                "function_model is present and non-empty in the SSOT",
                "cycle_model is present and non-empty in the SSOT",
                "Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL",
            ],
            "artifact": "yaml/<ip>.ssot.yaml",
        },
        {
            "kind": "ssot_workflow_todo_format",
            "source_ref": "quality_gates.rtl_gen.workflow_todo_contract",
            "content": "Gate: SSOT-authored rtl-gen workflow TODOs are well formed",
            "detail": "Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.",
            "criteria": [
                "Every workflow_todos.rtl-gen item has content",
                "Every workflow_todos.rtl-gen item has detail",
                "Every workflow_todos.rtl-gen item has at least one criteria entry",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "owner_traceability",
            "source_ref": "quality_gates.rtl_gen.owner_traceability",
            "content": "Gate: every SSOT-derived RTL behavior has an owner module",
            "detail": "Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.",
            "criteria": [
                "No required function_model task is orphaned",
                "No required cycle_model task is orphaned",
                "No required register/dataflow/FSM task is orphaned",
                "Owner module and owner file are recorded in rtl_todo_plan.json",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "common_ai_agent_authoring",
            "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
            "content": "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
            "detail": "RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.",
            "criteria": [
                "rtl/rtl_authoring_provenance.json exists",
                "provenance agent is common_ai_agent",
                "provenance workflow is rtl-gen",
                "provenance surface is atlas_ui, textual_ui, or headless_common_engine",
                "provenance todo_plan_sha256 matches the current rtl_todo_plan.json",
                "provenance rtl_files lists every SSOT manifest RTL file",
                "provenance rtl_files covers the current DUT filelist sources",
            ],
            "artifact": "rtl/rtl_authoring_provenance.json",
        },
        {
            "kind": "static_rtl_evidence",
            "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
            "content": "Gate: required SSOT behavior has static DUT RTL evidence after audit",
            "detail": "After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.",
            "criteria": [
                "derive_rtl_todos.py --audit-rtl ran after the final RTL edit",
                "rtl_todo_plan.json static_rtl_evidence.missing is zero",
                "Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token",
                "No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "owner_logic_structure_evidence",
            "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
            "content": "Gate: behavior-owner RTL modules contain real implementation structure",
            "detail": (
                "Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain "
                "real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract."
            ),
            "criteria": [
                "Every active behavior-owner module is declared in its owner file",
                "Behavior-owner modules contain non-placeholder assign/procedural implementation logic",
                "State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "rtl_placeholder_free_evidence",
            "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
            "content": "Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs",
            "detail": (
                "Production RTL cannot carry audit-banned incomplete/fake implementation markers in source code or comments. "
                "Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, "
                "with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. "
                "If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract."
            ),
            "criteria": [
                "Listed RTL source files contain no TODO/TBD/FIXME/HACK markers",
                "Listed RTL source files contain no audit-banned incomplete/fake implementation text",
                "Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs",
                "Default generated RTL uses input/output logic ports and portable always @ syntax",
                "FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style",
                "Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "top_io_contract_evidence",
            "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
            "content": "Gate: SSOT top IO contracts match the RTL top module",
            "detail": (
                "The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. "
                "A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation."
            ),
            "criteria": [
                "SSOT clock/reset names are declared on the RTL top module",
                "Explicit io_list ports/signals are declared on the RTL top module",
                "Known SSOT directions and simple widths match RTL declarations",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "top_output_drive_evidence",
            "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
            "content": "Gate: SSOT top outputs are driven by real RTL logic",
            "detail": (
                "Declaring output ports is not enough. Each SSOT-declared top output must be driven by "
                "nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. "
                "Constant tieoffs require an explicit SSOT constant/tieoff allowance."
            ),
            "criteria": [
                "Every SSOT output/inout top contract has drive evidence in the RTL top",
                "Non-waived output constants are rejected as placeholder tieoffs",
                "Child-instance drive evidence uses a declared child output/inout port, not an unknown direction",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "top_input_consumption_evidence",
            "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
            "content": "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
            "detail": (
                "Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed "
                "real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. "
                "Unused inputs require an explicit SSOT unused/reserved allowance."
            ),
            "criteria": [
                "Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top",
                "Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction",
                "Unused or reserved inputs are accepted only when explicitly waived by SSOT",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "manifest_hierarchy_integration",
            "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
            "content": "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
            "detail": (
                "File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top "
                "RTL module must be declared and reachable from the SSOT top through real module instantiation."
            ),
            "criteria": [
                "Every manifest-owned non-top submodule is declared in listed DUT RTL sources",
                "Each child module is reachable from the SSOT top module through SystemVerilog instantiation",
                "A disconnected child file or flattened top cannot close the manifest hierarchy gate",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "manifest_port_connection_evidence",
            "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
            "content": "Gate: manifest-owned child instances have machine-checkable port connections",
            "detail": (
                "Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports "
                "must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs."
            ),
            "criteria": [
                "Each reachable manifest child instance uses named port mapping",
                "Every declared child port is connected by name on at least one reachable instance",
                "No child port connection is empty unless represented by an explicit SSOT waiver",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "manifest_signal_flow_evidence",
            "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
            "content": "Gate: manifest child port connections carry live RTL signal flow",
            "detail": (
                "Named port maps prove that ports are connected, but not that the connected signals are useful. "
                "Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and "
                "child outputs must feed a top output, parent logic, or another declared child input/inout."
            ),
            "criteria": [
                "Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance",
                "Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts",
                "Named port-map entries reference ports declared by the child module",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "manifest_connection_contract_evidence",
            "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
            "content": "Gate: SSOT connection contracts match RTL child port maps",
            "detail": (
                "Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. "
                "When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those "
                "machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts."
            ),
            "criteria": [
                "Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections",
                "Each SSOT connection contract resolves to a reachable manifest child module and port",
                "RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
        {
            "kind": "dut_compile",
            "source_ref": "quality_gates.rtl_gen.dut_compile",
            "content": "Gate: DUT-only RTL compile report passes after the final RTL edit",
            "detail": "Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.",
            "criteria": [
                "rtl/rtl_compile.json exists",
                "rtl_compile.json reports dut_only=true",
                "rtl_compile.json passed=true with zero errors, diagnostics, and style violations",
                "rtl_compile.json is newer than or equal to every listed DUT RTL source",
                "rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources",
            ],
            "artifact": "rtl/rtl_compile.json",
        },
        {
            "kind": "dut_lint",
            "source_ref": "quality_gates.rtl_gen.dut_lint",
            "content": "Gate: DUT-only lint report passes after the final RTL edit",
            "detail": "Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.",
            "criteria": [
                "lint/dut_lint.json exists",
                "dut_lint.json reports dut_only=true",
                "dut_lint.json passed=true with zero errors and zero warnings",
                "dut_lint.json is newer than or equal to every listed DUT RTL source",
                "dut_lint.json rtl_files covers the current DUT filelist RTL/header sources",
                "No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver",
            ],
            "artifact": "lint/dut_lint.json",
        },
        {
            "kind": "dynamic_todo_closure",
            "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
            "content": "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS",
            "detail": "rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.",
            "criteria": [
                "Every required non-closure task has todo_completion.status=pass",
                "open_required_todos is zero",
                "all_required_todos_pass is true",
            ],
            "artifact": "rtl/rtl_todo_plan.json",
        },
    ]
    if profile == "production":
        gate_specs.extend([
            {
                "kind": "golden_authority_artifacts",
                "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
                "content": "Gate: production RTL uses locked SSOT/FL/coverage authority artifacts",
                "detail": (
                    "PL330-level RTL cannot proceed from prose alone. It must carry machine-readable "
                    "authority artifacts that separate human-owned truth from LLM-editable implementation."
                ),
                "criteria": [
                    "governance/authority.json exists",
                    "authority.json is the current IP human_llm_authority_manifest",
                    "authority operating rules R1..R6 and LLM loops L1..L9 are present",
                    "human authority gates G1..G7 are approved before production RTL-GEN",
                    "repo_layout separates locked SSOT/model/coverage truth from LLM-editable rtl/tb/sim/report work",
                    "model/functional_model.py exists",
                    "model/fl_model_check.json passed=true",
                    "model/model_signature.json matches the current SSOT-derived golden model signature",
                    "model/decomposition.json complete=true with unblocked implementation units",
                    "cov/fcov_plan.json has planned bins before RTL signoff",
                    "verify/equivalence_goals.json has required, unblocked goals",
                ],
                "artifact": "governance/authority.json",
            },
            {
                "kind": "target_scale_policy",
                "source_ref": "quality_gates.rtl_gen.target_scale",
                "content": "Gate: production RTL scale target is locked or explicitly waived",
                "detail": (
                    "When a calibration reference profile provides target-scale candidates, a human must "
                    "lock the chosen minimum structural scale in SSOT quality_gates.rtl_gen.target_scale "
                    "or record an explicit SSOT target_scale_waiver before rtl-gen can claim production signoff."
                ),
                "criteria": [
                    "Reference-derived suggested_ssot_target_scale candidates are review inputs only",
                    "SSOT quality_gates.rtl_gen.target_scale contains human-locked structural depth minima before PL330-level PASS claims",
                    "If target scale is intentionally not enforced, SSOT contains target_scale_waiver.approved=true with a rationale",
                ],
                "artifact": "yaml/<ip>.ssot.yaml",
            },
            {
                "kind": "rtl_implementation_depth_evidence",
                "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
                "content": "Gate: production RTL has SSOT-scaled implementation depth",
                "detail": (
                    "Production-profile RTL cannot be a shallow shell that merely satisfies names, ports, "
                    "or compile checks. The RTL must contain aggregate implementation structure scaled from "
                    "the current SSOT task count, behavior-owner modules, and manifest hierarchy."
                ),
                "criteria": [
                    "Implementation depth thresholds are derived from SSOT owner/task complexity, not a fixed IP template",
                    "Listed DUT RTL sources contain enough nonconstant logic, procedural/state/control structure, and child instances for the SSOT profile",
                    "Production multi-module IPs distribute implementation depth across behavior-owner modules instead of hiding behavior in a wrapper shell",
                ],
                "artifact": "rtl/rtl_todo_plan.json",
            },
            {
                "kind": "cycle_model_artifacts",
                "source_ref": "quality_gates.rtl_gen.cycle_model_artifacts",
                "content": "Gate: production RTL has executable cycle/handshake model evidence",
                "detail": (
                    "Complex DMA-class RTL needs a cycle-level oracle for latency, handshake, "
                    "ordering, backpressure, and performance-sensitive behavior."
                ),
                "criteria": [
                    "model/cycle_model.py exists",
                    "model/cl_model_check.json passed=true",
                    "cycle_model evidence traces to SSOT cycle_model",
                ],
                "artifact": "model/cycle_model.py",
            },
            {
                "kind": "protocol_assertion_evidence",
                "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
                "content": "Gate: production RTL has protocol assertion generation and clean simulation evidence",
                "detail": (
                    "PL330-level RTL needs protocol-checker style evidence for interface, ordering, "
                    "valid/ready, reset, and backpressure rules. The assertion source comes from SSOT "
                    "cycle_model; the pass condition comes from real simulation evidence."
                ),
                "criteria": [
                    "verify/protocol_assertions.sva exists",
                    "verify/protocol_assertions.summary.json has assertions_total > 0",
                    "sim/assertion_failures.jsonl exists after simulation",
                    "assertion_failures.jsonl is newer than or equal to every listed DUT RTL source",
                    "assertion_failures.jsonl has zero non-empty failure records",
                    "Assertion rules trace to SSOT cycle_model/interface contracts",
                ],
                "artifact": "verify/protocol_assertions.sva",
            },
            {
                "kind": "fl_rtl_goal_audit",
                "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
                "content": "Gate: production RTL passes FL-vs-RTL goal audit",
                "detail": (
                    "Passing compile/lint is not enough. The final RTL must be proven against "
                    "FunctionalModel-derived equivalence goals using real RTL-observed evidence."
                ),
                "criteria": [
                    "sim/fl_rtl_goal_audit.json exists",
                    "fl_rtl_goal_audit.json is newer than or equal to every listed DUT RTL source",
                    "fl_rtl_goal_audit status is pass",
                    "failed_checks is zero",
                    "blockers list is empty",
                    "sim/fl_rtl_compare.json exists and is newer than or equal to every listed DUT RTL source",
                    "Every required unblocked verify/equivalence_goals.json goal is checked and passed by fl_rtl_compare",
                ],
                "artifact": "sim/fl_rtl_goal_audit.json",
            },
            {
                "kind": "coverage_closure",
                "source_ref": "quality_gates.rtl_gen.coverage_closure",
                "content": "Gate: production RTL closes SSOT functional coverage goals",
                "detail": (
                    "Coverage must be measured from passing RTL-observed scoreboard evidence. "
                    "Raw FL-only coverage or weakened coverage goals cannot close this gate."
                ),
                "criteria": [
                    "cov/coverage.json exists",
                    "coverage.json is newer than or equal to every listed DUT RTL source",
                    "coverage status is pass",
                    "functional coverage pct meets target",
                    "coverage.json source is ssot_coverage_summary",
                    "functional hit equals total with pct >= 100 for planned bins",
                    "rtl_observed.status is pass with passing scoreboard events and coverage refs",
                    "rtl_observed missing_bins and invalid_rows are empty",
                    "coverage limitations are empty or explicitly waived in SSOT",
                ],
                "artifact": "cov/coverage.json",
            },
        ])
    for spec in gate_specs:
        _task(
            tasks,
            category="rtl_gate.rtl_gen",
            source_ref=spec["source_ref"],
            title=spec["content"],
            detail=spec["detail"],
            criteria=spec["criteria"],
            owner=owner,
            value={"gate_check": spec["kind"], "artifact": spec["artifact"]},
            priority="critical",
        )
        task = tasks[-1]
        task["gate_todo"] = {
            "stage": "rtl-gen",
            "kind": spec["kind"],
            "artifact": spec["artifact"],
            "profile": profile,
        }
        task["ssot_refs"] = sorted({spec["source_ref"], "quality_gates"})


def _add_parameter_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for idx, item in enumerate(_as_list(doc.get("parameters"))):
        name = _item_name(item, idx, "param")
        ref = f"parameters.{_slug(name)}"
        _task(
            tasks,
            category="parameters.item",
            source_ref=ref,
            title=f"Implement parameter {name}",
            detail="Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.",
            criteria=[
                "Parameter default/value matches SSOT",
                "Parameter-derived widths are implemented outside procedural part-selects",
                "Compile/lint evidence covers the parameterized form",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
            priority="normal",
        )


def _iter_io_ports(io: Any) -> list[tuple[str, dict[str, Any]]]:
    ports: list[tuple[str, dict[str, Any]]] = []
    if not isinstance(io, dict):
        return ports
    for group_key in ("clock_domains", "resets", "interfaces"):
        for group_idx, group in enumerate(_as_list(io.get(group_key))):
            if not isinstance(group, dict):
                continue
            for idx, port in enumerate(_as_list(group.get("ports"))):
                if isinstance(port, dict) and _present(port.get("name")):
                    base = str(group.get("name") or group.get("type") or group_key)
                    ports.append((f"io_list.{group_key}.{_slug(base)}.ports.{_slug(port.get('name'))}", port))
                elif _present(port):
                    ports.append((f"io_list.{group_key}.{group_idx}.ports.{idx}", {"name": str(port)}))
    return ports


def _add_io_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for ref, port in _iter_io_ports(doc.get("io_list")):
        name = str(port.get("name") or ref.rsplit(".", 1)[-1])
        _task(
            tasks,
            category="io_list.port",
            source_ref=ref,
            title=f"Implement and connect port {name}",
            detail="The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.",
            criteria=[
                "RTL declaration matches SSOT direction and width",
                "Active input controls are consumed by behavior or explicitly justified",
                "Active outputs are driven by implemented logic, not placeholder constants",
            ],
            owner=_owner_for(ref, modules, top),
            value=port,
            priority="normal",
        )


def _add_function_model_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    fm = doc.get("function_model")
    if not isinstance(fm, dict):
        return
    for idx, item in enumerate(_as_list(fm.get("state_variables"))):
        name = _item_name(item, idx, "state")
        ref = f"function_model.state_variables.{_slug(name)}"
        _task(
            tasks,
            category="function_model.state_variable",
            source_ref=ref,
            title=f"Implement RTL state owner for FL state {name}",
            detail="Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.",
            criteria=[
                "State has a flop/register/memory owner in RTL",
                "Reset value matches SSOT",
                "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
            ],
            owner=_owner_for(ref, modules, top, value=item),
            value=item,
        )
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            tx = {"name": str(tx)}
        tx_name = _item_name(tx, idx, "transaction")
        base = f"function_model.transactions.{_slug(tx.get('id') or tx_name)}"
        _task(
            tasks,
            category="function_model.transaction",
            source_ref=base,
            title=f"Implement transaction {tx_name}",
            detail="Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.",
            criteria=[
                "Acceptance/precondition logic is explicit in RTL",
                "All outputs and side effects occur exactly once per accepted transaction",
                "The transaction is covered by equivalence goals and scoreboard observations downstream",
            ],
            owner=_owner_for(base, modules, top, value=tx),
            value=tx,
        )
        for key, category, label in (
            ("preconditions", "function_model.precondition", "precondition"),
            ("inputs", "function_model.input", "input"),
            ("outputs", "function_model.output", "output"),
            ("output_rules", "function_model.output_rule", "output rule"),
            ("state_updates", "function_model.state_update", "state update"),
            ("side_effects", "function_model.side_effect", "side effect"),
            ("counter_rules", "function_model.counter_rule", "counter rule"),
            ("event_rules", "function_model.event_rule", "event rule"),
            ("error_cases", "function_model.error_case", "error case"),
        ):
            for sub_idx, sub in enumerate(_as_list(tx.get(key))):
                sub_name = _item_name(sub, sub_idx, label.replace(" ", "_"))
                ref = f"{base}.{key}.{_slug(sub_name, 'entry')}"
                evidence_value = _function_leaf_evidence_value(tx, key, sub)
                _task(
                    tasks,
                    category=category,
                    source_ref=ref,
                    title=f"Implement {label} for {tx_name}: {sub_name}",
                    detail="This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.",
                    criteria=[
                        "RTL owner logic is identifiable for this SSOT leaf",
                        "Reset/enable/error behavior is consistent with the parent transaction",
                        "Downstream equivalence/coverage can observe this behavior",
                    ],
                    owner=_owner_for(ref, modules, top, value=evidence_value),
                    value=evidence_value,
                )
    for idx, item in enumerate(_as_list(fm.get("invariants"))):
        name = _item_name(item, idx, "invariant")
        ref = f"function_model.invariants.{_slug(name)}"
        evidence_value = _function_invariant_evidence_value(fm, item)
        _task(
            tasks,
            category="function_model.invariant",
            source_ref=ref,
            title=f"Preserve FL invariant {name}",
            detail="Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.",
            criteria=[
                "RTL behavior cannot violate the invariant in normal operation",
                "If the invariant is verification-only, the SSOT names that evidence owner",
                "Coverage/equivalence references this invariant when observable",
            ],
            owner=_owner_for(ref, modules, top, value=evidence_value),
            value=evidence_value,
        )


def _add_cycle_model_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    cm = doc.get("cycle_model")
    if not isinstance(cm, dict):
        return
    for key in ("clock", "reset", "latency"):
        if _present(cm.get(key)):
            ref = f"cycle_model.{key}"
            _task(
                tasks,
                category=f"cycle_model.{key}",
                source_ref=ref,
                title=f"Implement cycle-model {key}",
                detail="Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.",
                criteria=[
                    "RTL sequential logic uses the SSOT clock/reset phase",
                    "Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence",
                    "Downstream scoreboard samples the same acceptance/result phase",
                ],
                owner=_owner_for(ref, modules, top, value=cm.get(key)),
                value=cm.get(key),
            )
    for key, label in (
        ("handshake_rules", "handshake rule"),
        ("pipeline", "pipeline stage"),
        ("ordering", "ordering rule"),
        ("backpressure", "backpressure rule"),
        ("observability", "observability signal"),
        ("arbitration", "arbitration rule"),
        ("stall_rules", "stall rule"),
        ("completion", "completion rule"),
        ("timeouts", "timeout rule"),
    ):
        for idx, item in enumerate(_as_list(cm.get(key))):
            name = _item_name(item, idx, label.replace(" ", "_"))
            ref = f"cycle_model.{key}.{_slug(name)}"
            _task(
                tasks,
                category=f"cycle_model.{key}",
                source_ref=ref,
                title=f"Implement {label}: {name}",
                detail="Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.",
                criteria=[
                    "RTL contains the control/state/handshake logic for this cycle rule",
                    "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
                    "TB scoreboard/coverage can observe the rule at the declared phase",
                ],
                owner=_owner_for(ref, modules, top, value=item),
                value=item,
            )


def _register_fields(reg: Any) -> list[tuple[str, Any]]:
    if not isinstance(reg, dict):
        return []
    raw = reg.get("fields")
    out: list[tuple[str, Any]] = []
    if isinstance(raw, dict):
        for name, value in raw.items():
            item = value if isinstance(value, dict) else {"value": value}
            item.setdefault("name", name)
            out.append((str(name), item))
    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            name = _item_name(item, idx, "field")
            out.append((name, item))
    return out


def _add_register_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    regs = doc.get("registers")
    if not isinstance(regs, dict):
        return
    for idx, reg in enumerate(_as_list(regs.get("register_list"))):
        if not isinstance(reg, dict):
            reg = {"name": str(reg)}
        name = _item_name(reg, idx, "register")
        ref = f"registers.register_list.{_slug(name)}"
        _task(
            tasks,
            category="registers.register",
            source_ref=ref,
            title=f"Implement CSR/register {name}",
            detail="Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.",
            criteria=[
                "Address/decode behavior matches SSOT",
                "Readable fields return RTL state, not a constant placeholder",
                "Write semantics and illegal access response match SSOT",
            ],
            owner=_owner_for(ref, modules, top),
            value=reg,
        )
        for field_name, field in _register_fields(reg):
            field_ref = f"{ref}.fields.{_slug(field_name)}"
            # Pure reserved fields (access=reserved with explicit read_value +
            # write_effect=ignore) are fully specified by SSOT — RTL only ties
            # them off. Emitting an "implement this" task creates an open
            # required todo that the audit cannot close without scanning for
            # bit-pattern matches, which is fragile. Skip these so the audit
            # focuses on real implementation gaps.
            if isinstance(field, dict):
                access = str(field.get("access") or "").strip().lower()
                write_effect = str(field.get("write_effect") or "").strip().lower()
                has_read_value = "read_value" in field
                if access == "reserved" and write_effect == "ignore" and has_read_value:
                    continue
            _task(
                tasks,
                category="registers.field",
                source_ref=field_ref,
                title=f"Implement field {name}.{field_name}",
                detail="Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.",
                criteria=[
                    "Field bit range, mask, and write strobe decode match SSOT",
                    "Field reset/access policy matches SSOT",
                    "Read/write/W1C/W0C/RO behavior is implemented or precisely blocked",
                    "Reserved fields read as the SSOT value and ignore writes",
                    "Field side effects are connected to owning control/status logic",
                ],
                owner=_owner_for(field_ref, modules, top),
                value=field,
            )
    for idx, item in enumerate(_as_list(regs.get("architectural_state"))):
        name = _item_name(item, idx, "architectural_state")
        ref = f"registers.architectural_state.{_slug(name)}"
        _task(
            tasks,
            category="registers.architectural_state",
            source_ref=ref,
            title=f"Implement architectural state {name}",
            detail="Architectural state listed outside the register map still needs RTL storage and reset/update ownership.",
            criteria=[
                "State storage is present in RTL",
                "Reset/update behavior matches SSOT",
                "State is observable if required by registers/debug/coverage",
            ],
            owner=_owner_for(ref, modules, top),
            value=item,
        )


def _add_section_list_tasks(
    tasks: list[dict[str, Any]],
    doc: dict[str, Any],
    modules: list[dict[str, Any]],
    top: str,
    *,
    section: str,
    keys: tuple[str, ...],
    label: str,
    category_prefix: str | None = None,
) -> None:
    value = doc.get(section)
    if not isinstance(value, dict):
        return
    category_prefix = category_prefix or section
    for key in keys:
        for idx, item in enumerate(_as_list(value.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or label)
            ref = f"{section}.{key}.{_slug(name)}"
            _task(
                tasks,
                category=f"{category_prefix}.{key}",
                source_ref=ref,
                title=f"Implement {label} {name}",
                detail=f"This SSOT {section}.{key} item must map to RTL behavior, integration evidence, or a precise blocker.",
                criteria=[
                    "RTL owner/evidence is named for this SSOT item",
                    "Behavior is not represented only by comments or TB code",
                    "Downstream verification can observe or justify the item",
                ],
                owner=_owner_for(ref, modules, top, value=item),
                value=item,
            )


def _add_feature_dataflow_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    for idx, feature in enumerate(_as_list(doc.get("features"))):
        name = _item_name(feature, idx, "feature")
        ref = f"features.{_slug(name)}"
        _task(
            tasks,
            category="features.item",
            source_ref=ref,
            title=f"Implement feature {name}",
            detail="Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.",
            criteria=[
                "Feature trigger/control/data behavior has RTL owner logic",
                "Feature observability and error behavior match SSOT",
                "Feature is covered by function/cycle/coverage tasks or explicitly blocked",
            ],
            owner=_owner_for(ref, modules, top),
            value=feature,
        )
    dataflow = doc.get("dataflow")
    if isinstance(dataflow, dict):
        for key in ("source", "sequence", "sinks", "ordering", "transforms", "notes"):
            for idx, item in enumerate(_as_list(dataflow.get(key))):
                name = _item_name(item, idx, key)
                ref = f"dataflow.{key}.{_slug(name)}"
                _task(
                    tasks,
                    category=f"dataflow.{key}",
                    source_ref=ref,
                    title=f"Implement dataflow {key}: {name}",
                    detail="Dataflow steps must be reflected in real datapath/control/storage logic.",
                    criteria=[
                        "RTL data/control path implements the described step",
                        "Ordering/backpressure is consistent with cycle_model",
                        "Downstream checks can observe the result or side effect",
                    ],
                    owner=_owner_for(ref, modules, top),
                    value=item,
                )


def _add_fsm_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    fsm = doc.get("fsm")
    if not isinstance(fsm, dict):
        return
    controls = []
    if isinstance(fsm.get("control"), dict):
        controls.append(("control", fsm["control"]))
    for key, value in fsm.items():
        if isinstance(value, dict) and key != "control":
            controls.append((key, value))
    if not controls and fsm:
        controls.append(("fsm", fsm))
    for ctrl_name, ctrl in controls:
        for idx, state in enumerate(_as_list(ctrl.get("states"))):
            name = _item_name(state, idx, "state")
            ref = f"fsm.{_slug(ctrl_name)}.states.{_slug(name)}"
            _task(
                tasks,
                category="fsm.state",
                source_ref=ref,
                title=f"Implement FSM state {ctrl_name}.{name}",
                detail=(
                    "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. "
                    "Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style."
                ),
                criteria=[
                    "State is encoded/reachable or explicitly replaced by equivalent logic",
                    "Reset/entry/exit behavior matches SSOT",
                    "FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure",
                    "Coverage can observe the state or equivalent condition",
                ],
                owner=_owner_for(ref, modules, top),
                value=state,
            )
        for idx, transition in enumerate(_as_list(ctrl.get("transitions"))):
            name = _item_name(transition, idx, "transition")
            ref = f"fsm.{_slug(ctrl_name)}.transitions.{_slug(name)}"
            _task(
                tasks,
                category="fsm.transition",
                source_ref=ref,
                title=f"Implement FSM transition {ctrl_name}.{name}",
                detail=(
                    "Transition condition, action, and timing must be implemented in RTL and covered downstream. "
                    "Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style."
                ),
                criteria=[
                    "Transition condition is present in RTL control logic",
                    "Transition action/state update is implemented",
                    "Illegal/missing transition behavior is handled per SSOT",
                ],
                owner=_owner_for(ref, modules, top),
                value=transition,
            )


def _add_test_coverage_tasks(tasks: list[dict[str, Any]], doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> None:
    tests = doc.get("test_requirements")
    if not isinstance(tests, dict):
        return
    for idx, scenario in enumerate(_as_list(tests.get("scenarios"))):
        name = _item_name(scenario, idx, "scenario")
        ref = f"test_requirements.scenarios.{_slug(name)}"
        _task(
            tasks,
            category="test_requirements.scenario",
            source_ref=ref,
            title=f"Keep RTL observable for scenario {name}",
            detail="Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.",
            criteria=[
                "RTL exposes enough signals/status/outputs for the scenario checker",
                "FunctionalModel expected result and RTL observed result can be compared",
                "Scenario has coverage refs or a precise SSOT reason for exclusion",
            ],
            owner=_owner_for(ref, modules, top),
            value=scenario,
            priority="normal",
        )
    goals = tests.get("coverage_goals")
    planned_bins = goals.get("planned_bins") if isinstance(goals, dict) else None
    for idx, bin_item in enumerate(_as_list(planned_bins)):
        name = _item_name(bin_item, idx, "coverage_bin")
        ref = f"test_requirements.coverage_goals.planned_bins.{_slug(name)}"
        _task(
            tasks,
            category="coverage.functional_bin",
            source_ref=ref,
            title=f"Provide RTL evidence for coverage bin {name}",
            detail="Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.",
            criteria=[
                "Bin has a scoreboard coverage_refs entry",
                "Scoreboard row includes concrete rtl_observed DUT signals",
                "Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage",
            ],
            owner=_owner_for(ref, modules, top),
            value=bin_item,
            priority="normal",
        )


def _add_module_equivalence_tasks(tasks: list[dict[str, Any]], modules: list[dict[str, Any]], top: str) -> None:
    for module in modules:
        refs = [str(ref) for ref in module.get("refs") or [] if str(ref).strip()]
        behavior_refs = [
            ref for ref in refs
            if ref.startswith((
                "function_model",
                "cycle_model",
                "features",
                "dataflow",
                "registers",
                "memory",
                "interrupts",
                "fsm",
                "error_handling",
            ))
        ]
        if len(modules) == 1 and not behavior_refs:
            behavior_refs = ["function_model", "cycle_model"]
        if not behavior_refs:
            continue
        name = str(module.get("name") or top)
        file_name = str(module.get("file") or f"rtl/{name}.sv")
        ref = f"sub_modules.{_slug(name)}.module_equivalence"
        _task(
            tasks,
            category="equivalence.module",
            source_ref=ref,
            title=f"Prove module {name} is functionally equivalent to FL",
            detail=(
                "This is a functionality-equality gate, not a style or file-existence check. "
                "The module must be driven from the same SSOT transaction intent used by "
                "FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result."
            ),
            criteria=[
                "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
                "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
                "scoreboard row fl_expected.model_api is FunctionalModel.apply",
                "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
                "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
            ],
            owner={"module": name, "file": file_name, "matched_ref": "module_equivalence"},
            value={"module": name, "file": file_name, "behavior_refs": behavior_refs},
        )


def _workflow_todo_owner(item: dict[str, Any], source_refs: list[str], modules: list[dict[str, Any]], top: str) -> dict[str, str]:
    owner_module = _ci_get(item, "owner_module", "module", "rtl_module")
    owner_file = _ci_get(item, "owner_file", "file", "rtl_file")
    if _present(owner_module) or _present(owner_file):
        module_name = str(owner_module or Path(str(owner_file)).stem)
        file_name = str(owner_file or "")
        if not file_name:
            matched = next((module for module in modules if str(module.get("name")) == module_name), None)
            file_name = str((matched or {}).get("file") or f"rtl/{_slug(module_name)}.sv")
        return {"module": module_name, "file": file_name, "matched_ref": "workflow_todos.owner"}
    for ref in source_refs:
        owner = _owner_for(ref, modules, top)
        if owner.get("module") or owner.get("file"):
            return owner
    return _owner_for("top_module", modules, top)


def _add_workflow_todo_tasks(
    tasks: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    doc: dict[str, Any],
    modules: list[dict[str, Any]],
    top: str,
) -> None:
    for idx, (source_ref, item) in enumerate(_workflow_todo_entries(doc), start=1):
        content = _ci_get(item, "content", "title", "task", "name", "summary")
        detail = _ci_get(item, "detail", "details", "description", "instructions", "rationale")
        criteria = _criteria_items(_ci_get(item, "criteria", "acceptance_criteria", "done_when", "pass_criteria"))
        missing = [
            field
            for field, value in (("content", content), ("detail", detail), ("criteria", criteria))
            if not _present(value)
        ]
        todo_id = str(_ci_get(item, "id", "todo_id", "name") or f"RTL_WORKFLOW_TODO_{idx:03d}")
        if missing:
            blockers.append({
                "id": f"MALFORMED_RTL_WORKFLOW_TODO_{idx:03d}",
                "source_ref": source_ref,
                "reason": "SSOT workflow_todos entries for rtl-gen must include content, detail, and criteria.",
                "missing_fields": missing,
                "owner": "ssot-gen",
            })
            continue

        source_refs = _workflow_todo_refs(item)
        owner = _workflow_todo_owner(item, source_refs, modules, top)
        priority = str(_ci_get(item, "priority") or "high").lower()
        required_raw = _ci_get(item, "required", "mandatory")
        required = False if str(required_raw).strip().lower() in {"false", "0", "no", "optional"} else True
        category_raw = _ci_get(item, "category", "class")
        _task(
            tasks,
            category="workflow_todo.rtl_gen",
            source_ref=source_ref,
            title=str(content),
            detail=str(detail),
            criteria=[
                *criteria,
                "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
                "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
            ],
            owner=owner,
            value=item,
            priority=priority if priority in {"critical", "high", "normal", "low"} else "high",
            required=required,
        )
        task = tasks[-1]
        task["workflow_todo"] = {
            "stage": "rtl-gen",
            "id": todo_id,
            "user_category": str(category_raw or ""),
            "source_refs": source_refs,
        }
        task["ssot_refs"] = sorted({source_ref, *source_refs})
        if source_refs:
            task["criteria"].append("Semantic source_refs covered: " + ", ".join(source_refs))


def _todo_active_form(content: str) -> str:
    active_form = content
    verb_map = {
        "read": "Reading",
        "write": "Writing",
        "implement": "Implementing",
        "create": "Creating",
        "run": "Running",
        "check": "Checking",
        "verify": "Verifying",
        "build": "Building",
        "design": "Designing",
        "extract": "Extracting",
        "define": "Defining",
        "add": "Adding",
        "instantiate": "Instantiating",
        "connect": "Connecting",
        "close": "Closing",
    }
    content_lower = content.lower()
    for verb, verb_ing in verb_map.items():
        if content_lower.startswith(verb):
            active_form = verb_ing + content[len(verb):]
            break
    return active_form


def _rtl_gate_ui_group(task: dict[str, Any]) -> tuple[int, str, str]:
    gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
    kind = str(gate.get("kind") or "")
    if kind in {
        "ssot_required_sections",
        "ssot_workflow_todo_format",
        "common_ai_agent_authoring",
        "golden_authority_artifacts",
        "target_scale_policy",
    }:
        return (80, "gate.authority", "Close RTL authority and provenance gates")
    if kind in {
        "owner_traceability",
        "static_rtl_evidence",
        "owner_logic_structure_evidence",
        "rtl_placeholder_free_evidence",
        "dynamic_todo_closure",
        "rtl_implementation_depth_evidence",
    }:
        return (81, "gate.traceability", "Close RTL traceability and implementation-depth gates")
    if kind in {
        "top_io_contract_evidence",
        "top_output_drive_evidence",
        "top_input_consumption_evidence",
        "manifest_hierarchy_integration",
        "manifest_port_connection_evidence",
        "manifest_signal_flow_evidence",
        "manifest_connection_contract_evidence",
    }:
        return (82, "gate.hierarchy_io", "Close top IO, hierarchy, and connection gates")
    if kind in {"dut_compile", "dut_lint"}:
        return (90, "gate.compile_lint", "Run DUT-only compile and lint closure gates")
    if kind in {
        "cycle_model_artifacts",
        "protocol_assertion_evidence",
        "fl_rtl_goal_audit",
        "coverage_closure",
    }:
        return (91, "gate.sim_coverage", "Close cycle, assertion, FL-vs-RTL, and coverage gates")
    return (89, "gate.remaining", "Close remaining RTL quality gates")


def _ui_group_for_task(task: dict[str, Any]) -> tuple[int, str, str]:
    category = str(task.get("category") or "uncategorized")
    section, _, subsection = category.partition(".")
    content = str(task.get("content") or "").strip()

    if category == "rtl_flow.seed":
        return (0, "flow.prepare", "Prepare SSOT-derived RTL generation authority")
    if category == "rtl_flow.top" or section == "io_list":
        return (1, "interface.top_io", "Implement top module, ports, reset, and filelist")
    if section == "parameters":
        return (2, "interface.parameters", "Implement Verilog include parameters and constants")
    if section == "registers":
        return (3, "interface.registers", "Implement register decode, storage, and field behavior")
    if section == "memory":
        return (4, "datapath.memory", "Implement SSOT memory instances and access behavior")
    if section == "interrupts":
        return (5, "control.interrupts", "Implement interrupt sources, enables, and clears")
    if category == "workflow_todo.rtl_gen":
        return (10, "workflow.rtl_gen", "Execute SSOT-authored rtl-gen workflow TODOs")
    if section == "function_model":
        if subsection in {"input", "output", "output_rule", "transaction"}:
            return (20, "function.io_transactions", "Implement function_model inputs, outputs, and transactions")
        if subsection in {"precondition", "invariant"}:
            return (21, "function.conditions", "Implement function_model preconditions and invariants")
        if subsection in {"state_variable", "side_effect", "state_update"}:
            return (22, "function.state_effects", "Implement function_model state and side effects")
        if subsection in {"error_case"}:
            return (23, "function.error_cases", "Implement function_model error cases")
        return (24, "function.remaining", "Implement remaining function_model behavior")
    if section == "cycle_model":
        if subsection in {"handshake_rules", "backpressure", "arbitration"}:
            return (30, "cycle.handshake", "Implement cycle_model handshake, backpressure, and arbitration")
        return (31, "cycle.timing_order", "Implement cycle_model timing, ordering, pipeline, and reset")
    if section == "fsm":
        return (40, "control.fsm", "Implement FSM states and transitions")
    if section == "dataflow":
        return (41, "datapath.dataflow", "Implement SSOT dataflow and ordering behavior")
    if section == "features":
        return (42, "feature.contracts", "Implement feature-level RTL contracts")
    if section == "error_handling":
        return (43, "control.error_recovery", "Implement error handling and recovery behavior")
    if section in {"security", "integration", "synthesis"}:
        return (44, "integration.signoff_constraints", "Close security, integration, and synthesis constraints")
    if section == "test_requirements":
        return (60, "verification.test_scenarios", "Preserve RTL evidence for SSOT test scenarios")
    if section == "coverage":
        return (61, "verification.coverage_goals", "Preserve RTL evidence for SSOT coverage goals")
    if section == "equivalence":
        return (62, "verification.equivalence", "Preserve FL-vs-RTL module equivalence mapping")
    if category == "rtl_gate.rtl_gen":
        return _rtl_gate_ui_group(task)
    title = f"Implement {section} RTL contracts" if section != "uncategorized" else "Close remaining SSOT RTL contracts"
    return (70, f"section.{section}", title)


def _priority_label(tasks: list[dict[str, Any]]) -> str:
    labels = {"critical": 0, "high": 1, "normal": 2, "medium": 2, "low": 3}
    best = "normal"
    best_rank = labels[best]
    for task in tasks:
        priority = str(task.get("priority") or "normal").strip().lower()
        rank = labels.get(priority, 2)
        if rank < best_rank:
            best = priority
            best_rank = rank
    return best


def _ui_criteria_line(task: dict[str, Any]) -> str:
    task_id = str(task.get("id") or "").strip()
    source_ref = str(task.get("source_ref") or "").strip()
    content = str(task.get("content") or "").strip()
    prefix = task_id or source_ref or "ledger-item"
    if source_ref and source_ref != prefix:
        prefix = f"{prefix} {source_ref}"
    return f"{prefix}: {content}" if content else prefix


def _ui_todo_from_group(group: dict[str, Any]) -> dict[str, Any]:
    group_tasks = [task for task in group["tasks"] if isinstance(task, dict)]
    content = str(group["title"])
    task_ids = [str(task.get("id") or "") for task in group_tasks if task.get("id")]
    sections = sorted({
        str(task.get("category") or "").split(".", 1)[0]
        for task in group_tasks
        if task.get("category")
    })
    critical = sum(1 for task in group_tasks if str(task.get("priority") or "").lower() == "critical")
    high = sum(1 for task in group_tasks if str(task.get("priority") or "").lower() == "high")
    id_span = f"{task_ids[0]}..{task_ids[-1]}" if len(task_ids) > 1 else (task_ids[0] if task_ids else "n/a")
    detail_lines = [
        f"Grouped from {len(group_tasks)} SSOT-derived RTL ledger item(s).",
        f"Ledger ids: {id_span}.",
        "Use rtl/rtl_todo_plan.json for the original per-item detail, criteria, traceability, and evidence audit.",
    ]
    if sections:
        detail_lines.append("SSOT sections: " + ", ".join(sections))
    if critical or high:
        detail_lines.append(f"Priority mix: critical={critical}, high={high}.")

    criteria_lines = [
        f"Close every ledger item represented by this UI TODO ({len(group_tasks)} item(s))",
        "Preserve the original source_ref and owner evidence in rtl_todo_plan.json",
        *(_ui_criteria_line(task) for task in group_tasks),
    ]
    return {
        "content": content,
        "activeForm": _todo_active_form(content),
        "status": "pending",
        "detail": "\n".join(detail_lines),
        "criteria": "\n".join(line for line in criteria_lines if line),
        "priority": _priority_label(group_tasks),
    }


def _tracker_status_for_ledger_task(task: dict[str, Any]) -> str:
    # TodoTracker status is execution state, not audit state.  Even if a
    # ledger row currently passes audit, a fresh workflow run must force the
    # agent to review/close that row explicitly instead of inheriting PASS.
    return "pending"


def _tracker_content_for_ledger_task(task: dict[str, Any]) -> str:
    task_id = str(task.get("id") or "").strip()
    content = str(task.get("content") or "").strip()
    category = str(task.get("category") or "").strip()
    prefix = task_id or category or "RTL"
    return f"{prefix}: {content}" if content else prefix


def _tracker_detail_for_ledger_task(task: dict[str, Any]) -> str:
    lines: list[str] = []
    for label, key in (
        ("Ledger id", "id"),
        ("Category", "category"),
        ("Source ref", "source_ref"),
        ("Owner module", "owner_module"),
        ("Owner file", "owner_file"),
    ):
        value = task.get(key)
        if value not in (None, "", []):
            lines.append(f"{label}: {value}")

    detail = str(task.get("detail") or "").strip()
    if detail:
        lines.append("")
        lines.append(detail)

    completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
    reason = str(completion.get("reason") or "").strip()
    if reason:
        lines.append("")
        lines.append(f"Current audit reason: {reason}")
    basis = completion.get("evidence_basis")
    if isinstance(basis, list) and basis:
        lines.append("")
        lines.append("Evidence basis:")
        lines.extend(f"- {item}" for item in basis if str(item).strip())
    return "\n".join(lines)


def _tracker_criteria_for_ledger_task(task: dict[str, Any]) -> str:
    criteria = task.get("criteria")
    lines: list[str] = []
    if isinstance(criteria, list):
        lines.extend(str(item).strip() for item in criteria if str(item).strip())
    elif str(criteria or "").strip():
        lines.extend(line.strip() for line in str(criteria).splitlines() if line.strip())

    source_ref = str(task.get("source_ref") or "").strip()
    owner_file = str(task.get("owner_file") or "").strip()
    task_id = str(task.get("id") or "").strip()
    if task_id:
        lines.append(f"Ledger task {task_id} is closed in rtl/rtl_todo_plan.json")
    if source_ref:
        lines.append(f"Traceability preserves source_ref {source_ref}")
    if owner_file:
        lines.append(f"Primary implementation evidence is in {owner_file}")
    lines.append("todo_completion.status is pass after derive_rtl_todos.py --audit-rtl")
    return "\n".join(dict.fromkeys(lines))


def _tracker_todo_from_ledger_task(task: dict[str, Any]) -> dict[str, Any]:
    content = _tracker_content_for_ledger_task(task)
    todo = {
        "content": content,
        "activeForm": _todo_active_form(content),
        "status": _tracker_status_for_ledger_task(task),
        "detail": _tracker_detail_for_ledger_task(task),
        "criteria": _tracker_criteria_for_ledger_task(task),
        "priority": str(task.get("priority") or "normal"),
    }
    completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
    if todo["status"] == "approved":
        reason = str(completion.get("reason") or "").strip()
        todo["approved_reason"] = reason or "Ledger task already passes current RTL audit."
    return todo


def _convert_to_template_format(plan: dict[str, Any]) -> dict[str, Any]:
    ledger_tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    tasks = [_tracker_todo_from_ledger_task(task) for task in ledger_tasks]
    status_counts = dict(sorted(Counter(str(task.get("status") or "unknown") for task in tasks).items()))

    return {
        "name": f"{plan.get('ip', 'unknown')}-rtl",
        "description": (
            f"Auto-generated flat TodoTracker list from SSOT RTL plan for {plan.get('ip', '')}. "
            "Each TodoTracker item maps one-to-one to a task in rtl_todo_plan.json so the existing "
            "flat TodoTracker can execute ledger items one at a time."
        ),
        "source_plan": "rtl/rtl_todo_plan.json",
        "source_task_count": len(ledger_tasks),
        "status_counts": status_counts,
        "ui_grouping": {
            "strategy": "flat_ledger_one_todo_per_rtl_task",
            "target_min": len(tasks),
            "target_max": len(tasks),
            "actual_count": len(tasks),
            "status_counts": status_counts,
            "detail_policy": "Each TodoTracker item preserves one rtl_todo_plan.json ledger task with source_ref, owner, criteria, and current audit status.",
        },
        "lock_additions": False,
        "tasks": tasks,
    }


def _priority_rank(task: dict[str, Any]) -> tuple[int, str]:
    priority = str(task.get("priority") or "normal").strip().lower()
    ranks = {"critical": 0, "high": 1, "normal": 2, "medium": 2, "low": 3}
    return (ranks.get(priority, 2), str(task.get("id") or task.get("source_ref") or ""))


def _packet_slug(value: object, fallback: str = "packet") -> str:
    return _slug(value, fallback=fallback).lower()


def _packet_task_item(task: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "category",
        "source_ref",
        "ssot_refs",
        "content",
        "detail",
        "criteria",
        "ssot_context",
        "owner_module",
        "owner_file",
        "evidence_terms",
        "static_evidence",
        "todo_completion",
        "priority",
        "required",
        "policy_tags",
        "gate_todo",
        "workflow_todo",
    )
    return {key: task.get(key) for key in keys if key in task}


def _is_repair_generated_fm_task_record(task: dict[str, Any]) -> bool:
    tags = task.get("policy_tags") if isinstance(task.get("policy_tags"), list) else []
    return "repair_generated_fm_marker" in {str(tag) for tag in tags}


def _packet_section_key(task: dict[str, Any]) -> str:
    category = str(task.get("category") or "unknown").split(".", 1)[0]
    return _packet_slug(category or "unknown", fallback="section")


def _chunked(items: list[dict[str, Any]], limit: int) -> list[list[dict[str, Any]]]:
    if limit <= 0:
        return [items]
    return [items[index:index + limit] for index in range(0, len(items), limit)]


def _module_authoring_slices(
    owner_module: str,
    tasks: list[dict[str, Any]],
    *,
    task_limit: int = AUTHORING_PACKET_TASK_LIMIT,
) -> list[dict[str, Any]]:
    ordered = sorted(tasks, key=_priority_rank)
    if len(ordered) <= task_limit:
        return [
            {
                "enabled": False,
                "key": "all",
                "index": 1,
                "count": 1,
                "module_task_count": len(ordered),
                "task_limit": task_limit,
                "tasks": ordered,
            }
        ]

    section_groups: dict[str, list[dict[str, Any]]] = {}
    for task in ordered:
        section_groups.setdefault(_packet_section_key(task), []).append(task)

    def section_sort_key(item: tuple[str, list[dict[str, Any]]]) -> tuple[int, str]:
        section, _items = item
        return (AUTHORING_PACKET_SECTION_ORDER.get(section, 100), section)

    raw_slices: list[dict[str, Any]] = []
    for section, section_tasks in sorted(section_groups.items(), key=section_sort_key):
        chunks = _chunked(section_tasks, task_limit)
        for chunk_index, chunk in enumerate(chunks, start=1):
            key = section if len(chunks) == 1 else f"{section}_{chunk_index:02d}"
            raw_slices.append({
                "enabled": True,
                "key": key,
                "section": section,
                "section_chunk_index": chunk_index,
                "section_chunk_count": len(chunks),
                "module_task_count": len(ordered),
                "task_limit": task_limit,
                "tasks": chunk,
            })

    total = len(raw_slices)
    for index, item in enumerate(raw_slices, start=1):
        item["index"] = index
        item["count"] = total
        item["rule"] = (
            f"Owner module {owner_module} is split into {total} authoring slices. "
            "Update the same owner_file incrementally and preserve logic from earlier slices."
        )
    return raw_slices


_DRAFT_BLOCKING_GATE_KINDS = {
    "ssot_required_sections",
    "ssot_workflow_todo_format",
    "owner_traceability",
}

_LOCKED_TRUTH_GATE_KINDS = {
    "ssot_required_sections",
    "ssot_workflow_todo_format",
    "owner_traceability",
    "manifest_connection_contract_evidence",
    "golden_authority_artifacts",
    "target_scale_policy",
    "cycle_model_artifacts",
}


_TOOL_EVIDENCE_GATE_KINDS = {
    "common_ai_agent_authoring",
    "dut_compile",
    "dut_lint",
    "dynamic_todo_closure",
    "protocol_assertion_evidence",
    "fl_rtl_goal_audit",
    "coverage_closure",
}


_CONNECTION_CONTRACT_DEPENDENT_GATE_KINDS = {
    "manifest_connection_contract_evidence",
}


def _task_status(task: dict[str, Any]) -> str:
    completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
    return str(completion.get("status") or "unknown")


def _task_reason(task: dict[str, Any]) -> str:
    completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
    return str(completion.get("reason") or "")


def _is_open_required_task(task: dict[str, Any]) -> bool:
    return bool(task.get("required", True)) and _task_status(task) != "pass"


def _gate_kind(task: dict[str, Any]) -> str:
    gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
    return str(gate.get("kind") or "")


def _compact_policy_blocker(item: dict[str, Any], *, source: str) -> dict[str, Any]:
    if source == "plan_blocker":
        return {
            "source": source,
            "id": str(item.get("id") or ""),
            "source_ref": str(item.get("source_ref") or ""),
            "reason": str(item.get("reason") or ""),
            "owner": str(item.get("owner") or ""),
        }
    if source == "orphan_task":
        return {
            "source": source,
            "task_id": str(item.get("task_id") or ""),
            "source_ref": str(item.get("source_ref") or ""),
            "category": str(item.get("category") or ""),
            "reason": str(item.get("reason") or ""),
        }
    return {
        "source": source,
        "task_id": str(item.get("id") or ""),
        "gate_kind": _gate_kind(item),
        "source_ref": str(item.get("source_ref") or ""),
        "status": _task_status(item),
        "reason": _task_reason(item),
        "owner_module": str(item.get("owner_module") or ""),
    }


def _tool_evidence_instruction(plan: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    ip = str(plan.get("ip") or "<ip>")
    top = str(plan.get("top") or ip or "<top>")
    kind = _gate_kind(task)
    status = _task_status(task)
    reason = _task_reason(task)
    common = {
        "gate_kind": kind,
        "task_id": str(task.get("id") or ""),
        "source_ref": str(task.get("source_ref") or ""),
        "status": status,
        "reason": reason,
        "artifact": str((task.get("gate_todo") or {}).get("artifact") or task.get("artifact") or ""),
    }
    by_kind: dict[str, dict[str, Any]] = {
        "common_ai_agent_authoring": {
            "stage_sequence": ["ssot-rtl"],
            "commands": [
                f"python3 src/headless_workflow.py --root . --ip {ip} --stages rtl-gen",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [
                f"{ip}/rtl/rtl_authoring_provenance.json",
                f"{ip}/rtl/rtl_todo_plan.json",
            ],
            "prerequisites": ["An LLM authoring pass emitted or repaired DUT RTL files."],
            "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        },
        "dut_compile": {
            "stage_sequence": ["ssot-rtl", "dut_compile"],
            "commands": [
                f"python3 workflow/rtl-gen/scripts/rtl_compile_report.py {ip} --top {top} --project-root .",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [f"{ip}/rtl/rtl_compile.json", f"{ip}/rtl/rtl_compile.log"],
            "prerequisites": [f"{ip}/list/{ip}.f covers the current DUT RTL sources."],
            "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        },
        "dut_lint": {
            "stage_sequence": ["lint", "dut_lint"],
            "commands": [
                f"python3 workflow/lint/scripts/dut_lint_report.py {ip} --top {top}",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [f"{ip}/lint/dut_lint.json"],
            "prerequisites": [f"{ip}/list/{ip}.f covers the current DUT RTL/header sources."],
            "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        },
        "protocol_assertion_evidence": {
            "stage_sequence": ["ssot-protocol-assertions", "sim"],
            "commands": [
                f"python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py {ip} --root .",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [
                f"{ip}/verify/protocol_assertions.sva",
                f"{ip}/verify/protocol_assertions.summary.json",
                f"{ip}/sim/assertion_failures.jsonl",
            ],
            "prerequisites": ["SSOT cycle_model/protocol rules are machine-checkable.", "Simulation has run after RTL edits."],
            "closure_rule": "Generated assertions exist and latest simulation has zero assertion failure records.",
        },
        "fl_rtl_goal_audit": {
            "stage_sequence": ["ssot-fl-model", "ssot-equiv-goals", "ssot-tb-cocotb", "sim", "goal-audit"],
            "commands": [
                f"python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py {ip} --root .",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [f"{ip}/sim/fl_rtl_goal_audit.json"],
            "prerequisites": ["FL model, equivalence goals, TB, and simulation evidence are current."],
            "closure_rule": "fl_rtl_goal_audit.json must be fresh and status=pass.",
        },
        "coverage_closure": {
            "stage_sequence": ["sim", "coverage"],
            "commands": [
                f"python3 workflow/coverage/scripts/ssot_coverage_summary.py {ip}",
                f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl",
            ],
            "artifacts": [f"{ip}/cov/coverage.json"],
            "prerequisites": ["Simulation evidence exists and planned coverage bins are observable."],
            "closure_rule": "coverage.json must be fresh, come from ssot_coverage_summary, and close every planned required bin.",
        },
        "dynamic_todo_closure": {
            "stage_sequence": ["audit-rtl"],
            "commands": [f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl"],
            "artifacts": [f"{ip}/rtl/rtl_todo_plan.json", f"{ip}/rtl/rtl_authoring_status.md"],
            "prerequisites": ["All non-closure required TODOs have pass status."],
            "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        },
    }
    detail = by_kind.get(kind, {
        "stage_sequence": [],
        "commands": [f"python3 workflow/rtl-gen/scripts/derive_rtl_todos.py {ip} --root . --audit-rtl"],
        "artifacts": [str((task.get("gate_todo") or {}).get("artifact") or "")],
        "prerequisites": [],
        "closure_rule": "Run the canonical evidence producer for this gate, then rerun rtl_todo_plan audit.",
    })
    return {**common, **detail}


def _tool_evidence_plan(plan: dict[str, Any], tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    instructions: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for task in tasks:
        if not isinstance(task, dict) or not _is_tool_evidence_gate_task(task):
            continue
        key = (_gate_kind(task), str(task.get("id") or ""))
        if key in seen:
            continue
        seen.add(key)
        instructions.append(_tool_evidence_instruction(plan, task))
    return instructions


def _machine_connection_contracts(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        item for item in plan.get("ssot_connection_contracts", [])
        if isinstance(item, dict) and item.get("machine_readable")
    ]


def _production_connection_contract_gap(plan: dict[str, Any]) -> dict[str, Any]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    quality_profile = str(
        policy.get("rtl_quality_profile")
        or summary.get("rtl_quality_profile")
        or "standard"
    )
    top = str(plan.get("top") or "")
    owner_modules = [
        item for item in summary.get("owner_modules", [])
        if isinstance(item, dict)
    ]
    child_count = sum(
        1
        for item in owner_modules
        if str(item.get("name") or "") != top and not bool(item.get("wiring_only"))
    )
    required = quality_profile == "production" and child_count > 0
    machine_contracts = _machine_connection_contracts(plan)
    missing = required and not machine_contracts
    return {
        "status": "missing" if missing else "ok",
        "required_for_profile": required,
        "machine_readable_contract_count": len(machine_contracts),
        "reason": (
            "Production-profile multi-module RTL requires machine-readable integration.connections "
            "or sub_modules[].connections before top integration or signoff can close."
        ),
    }


def _sv_declared_signal_names_from_module_body(body: str) -> set[str]:
    clean = _strip_sv_comments(body)
    signals: set[str] = set()
    for decl in re.findall(r"\b(?:wire|reg|logic)\b(?P<decl>[^;]+);", clean):
        text = re.sub(r"\[[^\]]+\]", " ", decl)
        text = re.sub(r"\b(?:wire|reg|logic|signed|unsigned)\b", " ", text)
        for segment in text.split(","):
            names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", segment)
            if names:
                signals.add(names[-1])
    return signals


def _connection_contract_suggestion_context(plan: dict[str, Any]) -> dict[str, Any]:
    suggestions = (
        plan.get("connection_contract_suggestions")
        if isinstance(plan.get("connection_contract_suggestions"), dict)
        else {}
    )
    if not suggestions:
        return {}
    rows = suggestions.get("rows") if isinstance(suggestions.get("rows"), list) else []
    summary = suggestions.get("summary") if isinstance(suggestions.get("summary"), dict) else {}
    return {
        "path": "rtl/connection_contract_suggestions.json",
        "summary": summary,
        "sample_rows": [
            {
                key: row.get(key)
                for key in ("module", "instance", "port", "signal", "direction", "confidence", "review_status")
                if key in row
            }
            for row in rows[:16]
            if isinstance(row, dict)
        ],
        "rule": suggestions.get("rule"),
    }


def _packet_connection_contract_suggestions(plan: dict[str, Any], owner_module: str, kind: str) -> dict[str, Any]:
    suggestions = (
        plan.get("connection_contract_suggestions")
        if isinstance(plan.get("connection_contract_suggestions"), dict)
        else {}
    )
    if not suggestions:
        return {}
    rows = suggestions.get("rows") if isinstance(suggestions.get("rows"), list) else []
    top = str(plan.get("top") or "")
    if kind == "gate" or owner_module == top:
        selected = [row for row in rows if isinstance(row, dict)]
    else:
        owner_l = owner_module.lower()
        selected = [
            row for row in rows
            if isinstance(row, dict)
            and (
                str(row.get("module") or "").lower() == owner_l
                or str(row.get("instance") or "").lower() == owner_l
            )
        ]
    if not selected:
        return {}
    summary = suggestions.get("summary") if isinstance(suggestions.get("summary"), dict) else {}
    return {
        "path": "rtl/connection_contract_suggestions.json",
        "summary": {
            key: summary.get(key)
            for key in ("status", "suggested_rows", "pending_review", "applied_to_ssot", "draft_top_integration_fragment")
            if key in summary
        },
        "rows": [
            {
                key: row.get(key)
                for key in ("module", "instance", "port", "signal", "direction", "confidence", "review_status")
                if key in row
            }
            for row in selected[:32]
        ],
        "rule": suggestions.get("rule"),
    }


def _rtl_module_short_name(module: str, top: str) -> str:
    name = str(module or "").strip()
    for prefix in (f"{top}_target_", f"{top}_"):
        if top and name.startswith(prefix) and len(name) > len(prefix):
            name = name[len(prefix):]
            break
    return re.sub(r"[^A-Za-z0-9_]+", "_", name).strip("_") or "child"


def _conventional_top_signal(port: str, top_symbols: set[str]) -> tuple[str, str]:
    lower = port.lower()
    clock_candidates = ("clk", "clock", "aclk", "pclk", "hclk")
    reset_candidates = ("rst_n", "resetn", "aresetn", "presetn", "reset_n", "rst", "reset")
    if lower in clock_candidates:
        for candidate in clock_candidates:
            if candidate in top_symbols:
                return candidate, "conventional_clock"
    if lower in reset_candidates:
        for candidate in reset_candidates:
            if candidate in top_symbols:
                return candidate, "conventional_reset"
    return "", ""


def _suggest_connection_signal(
    *,
    module: str,
    port: str,
    direction: str,
    top: str,
    top_symbols: set[str],
) -> tuple[str, str]:
    if port in top_symbols:
        return port, "exact_top_signal"
    conventional, confidence = _conventional_top_signal(port, top_symbols)
    if conventional:
        return conventional, confidence
    short = _rtl_module_short_name(module, top)
    if port.startswith(short + "_"):
        signal = port
    else:
        signal = f"{short}_{port}"
    if signal in top_symbols:
        return signal, "exact_internal_signal"
    suffix = "output_signal" if direction == "output" else "input_signal"
    return signal, f"proposed_{suffix}"


def _draft_connection_contract_suggestions(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    gap = _production_connection_contract_gap(plan)
    if gap.get("status") != "missing":
        return {
            "schema_version": 1,
            "type": "rtl_connection_contract_suggestions",
            "summary": {
                "status": "not_required",
                "suggested_rows": 0,
                "pending_review": 0,
                "applied_to_ssot": False,
            },
            "rows": [],
            "rule": "Suggestions are emitted only when production connection contracts are missing.",
        }

    sources = _read_rtl_sources(ip_dir)
    module_bodies: dict[str, str] = {}
    module_files: dict[str, str] = {}
    for rel, text in sources.items():
        for module_name, body in _sv_module_bodies(text).items():
            module_bodies[module_name] = body
            module_files[module_name] = rel

    top = str(plan.get("top") or ip_dir.name)
    top_candidates = [name for name in _top_aliases(top) if name in module_bodies]
    top_module = top if top in module_bodies else (sorted(top_candidates)[0] if top_candidates else "")
    top_body = module_bodies.get(top_module, "")
    top_ports = _sv_declared_port_details_from_module_body(top_body) if top_body else {}
    top_symbols = set(top_ports) | _sv_declared_signal_names_from_module_body(top_body)
    top_instances = _sv_instance_named_port_maps(top_body) if top_body else []
    instances_by_module: dict[str, list[dict[str, Any]]] = {}
    for instance in top_instances:
        module_name = str(instance.get("module") or "")
        if module_name:
            instances_by_module.setdefault(module_name, []).append(instance)

    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    owners = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    top_aliases = _top_aliases(top)
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    child_count = 0

    for owner in owners:
        if not isinstance(owner, dict) or owner.get("wiring_only") or _skip_hierarchy_module(owner):
            continue
        aliases = _hierarchy_module_aliases(owner)
        if aliases & top_aliases:
            continue
        child_count += 1
        declared = sorted(alias for alias in aliases if alias in module_bodies)
        module_name = str(owner.get("name") or Path(str(owner.get("file") or "")).stem)
        rtl_module = module_name if module_name in module_bodies else (declared[0] if declared else module_name)
        body = module_bodies.get(rtl_module, "")
        port_details = _sv_declared_port_details_from_module_body(body) if body else {}
        if not port_details:
            issues.append({
                "module": module_name,
                "file": owner.get("file") or module_files.get(rtl_module, ""),
                "issue": "No RTL-declared ports were available for connection-contract suggestions.",
            })
            continue
        module_instances = [
            instance
            for alias in sorted(aliases)
            for instance in instances_by_module.get(alias, [])
        ]
        for port, details in sorted(port_details.items()):
            direction = str(details.get("direction") or "")
            port_range = str(details.get("range") or "")
            observed = next(
                (
                    instance for instance in module_instances
                    if isinstance(instance.get("ports"), dict)
                    and str((instance.get("ports") or {}).get(port) or "").strip()
                ),
                None,
            )
            if observed:
                signal = str((observed.get("ports") or {}).get(port) or "").strip()
                instance_name = str(observed.get("instance") or "")
                confidence = "observed_named_port_map"
            else:
                signal, confidence = _suggest_connection_signal(
                    module=rtl_module,
                    port=port,
                    direction=direction,
                    top=top,
                    top_symbols=top_symbols,
                )
                instance_name = f"u_{_rtl_module_short_name(rtl_module, top)}"
            row = {
                "module": rtl_module,
                "instance": instance_name,
                "port": port,
                "signal": signal,
                "signal_terms": sorted(_signal_terms(signal)),
                "direction": direction,
                "range": port_range,
                "source_ref": f"rtl.connection_contract_suggestions.{rtl_module}.{port}",
                "confidence": confidence,
                "review_status": "pending",
                "applied_to_ssot": False,
                "machine_readable": False,
                "approval_target": "integration.connections",
                "approval_rule": (
                    "Human approval through RTL_RESOLVE_CONNECTION_CONTRACTS is required before "
                    "this row becomes SSOT authority."
                ),
            }
            if _is_constant_expr(signal):
                row["tieoff_candidate"] = True
            rows.append(row)

    return {
        "schema_version": 1,
        "type": "rtl_connection_contract_suggestions",
        "summary": {
            "status": "pending_review" if rows else "unavailable",
            "reason": gap.get("reason"),
            "top": top,
            "top_module": top_module,
            "child_modules": child_count,
            "suggested_rows": len(rows),
            "pending_review": len(rows),
            "applied_to_ssot": False,
            "draft_top_integration_fragment": "rtl/connection_contract_draft_top.svfrag" if rows else "",
            "observed_named_port_map_rows": sum(1 for row in rows if row.get("confidence") == "observed_named_port_map"),
            "proposed_rows": sum(1 for row in rows if str(row.get("confidence") or "").startswith("proposed_")),
        },
        "rows": rows,
        "issues": issues[:64],
        "rule": (
            "This artifact is a pending QA aid only. It is not SSOT authority, does not close "
            "manifest_connection_contract_evidence, and must be approved into integration.connections "
            "or sub_modules[].connections by a human."
        ),
    }


def _connection_contract_draft_fragment_text(suggestions: dict[str, Any]) -> str:
    rows = suggestions.get("rows") if isinstance(suggestions.get("rows"), list) else []
    valid_rows = [
        row for row in rows
        if isinstance(row, dict)
        and str(row.get("module") or "").strip()
        and str(row.get("instance") or "").strip()
        and str(row.get("port") or "").strip()
        and str(row.get("signal") or "").strip()
    ]
    if not valid_rows:
        return ""

    declarations: dict[str, str] = {}
    for row in valid_rows:
        signal = str(row.get("signal") or "").strip()
        confidence = str(row.get("confidence") or "")
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", signal):
            continue
        if not (confidence.startswith("proposed_") or confidence == "exact_internal_signal"):
            continue
        declarations.setdefault(signal, str(row.get("range") or "").strip())

    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in valid_rows:
        key = (str(row.get("module") or "").strip(), str(row.get("instance") or "").strip())
        groups.setdefault(key, []).append(row)

    lines = [
        "// DRAFT ONLY: generated from pending connection_contract_suggestions.",
        "// This fragment is not SSOT authority and must be reviewed before signoff.",
        "// Paste/adapt inside the top module only after checking directions, widths, and reset/clock domains.",
        "",
    ]
    if declarations:
        lines.extend(["// Suggested internal signals."])
        for signal, port_range in sorted(declarations.items()):
            range_text = f" {port_range}" if port_range else ""
            lines.append(f"wire{range_text} {signal};")
        lines.append("")

    lines.extend(["// Suggested child instances."])
    for (module, instance), group_rows in sorted(groups.items()):
        lines.append(f"{module} {instance} (")
        port_lines = []
        sorted_rows = sorted(group_rows, key=lambda item: str(item.get("port") or ""))
        for row in sorted_rows:
            port = str(row.get("port") or "").strip()
            signal = str(row.get("signal") or "").strip()
            port_lines.append(f"  .{port}({signal})")
        for index, port_line in enumerate(port_lines):
            suffix = "," if index < len(port_lines) - 1 else ""
            row = sorted_rows[index]
            confidence = str(row.get("confidence") or "pending")
            lines.append(f"{port_line}{suffix} // {confidence}; review_status=pending")
        lines.append(");")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _is_tool_evidence_gate_task(task: dict[str, Any]) -> bool:
    return task.get("category") == "rtl_gate.rtl_gen" and _gate_kind(task) in _TOOL_EVIDENCE_GATE_KINDS


def _is_locked_truth_gate_task(task: dict[str, Any]) -> bool:
    return task.get("category") == "rtl_gate.rtl_gen" and _gate_kind(task) in _LOCKED_TRUTH_GATE_KINDS


def _is_connection_contract_blocked_gate_task(plan: dict[str, Any], task: dict[str, Any]) -> bool:
    if task.get("category") != "rtl_gate.rtl_gen":
        return False
    if _gate_kind(task) not in _CONNECTION_CONTRACT_DEPENDENT_GATE_KINDS:
        return False
    return _production_connection_contract_gap(plan).get("status") == "missing"


def _is_llm_actionable_gate_task(plan: dict[str, Any], task: dict[str, Any]) -> bool:
    if task.get("category") != "rtl_gate.rtl_gen":
        return False
    return not (
        _is_locked_truth_gate_task(task)
        or _is_tool_evidence_gate_task(task)
        or _is_connection_contract_blocked_gate_task(plan, task)
    )


def _authoring_execution_policy(plan: dict[str, Any]) -> dict[str, Any]:
    tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    open_required = [task for task in tasks if _is_open_required_task(task)]
    open_gate_tasks = [task for task in open_required if task.get("category") == "rtl_gate.rtl_gen"]
    hard_blockers = [
        _compact_policy_blocker(item, source="plan_blocker")
        for item in (plan.get("blockers") if isinstance(plan.get("blockers"), list) else [])
        if isinstance(item, dict)
    ]
    hard_blockers.extend(
        _compact_policy_blocker(item, source="orphan_task")
        for item in (plan.get("orphans") if isinstance(plan.get("orphans"), list) else [])
        if isinstance(item, dict)
    )
    hard_blockers.extend(
        _compact_policy_blocker(task, source="gate_todo")
        for task in open_gate_tasks
        if _gate_kind(task) in _DRAFT_BLOCKING_GATE_KINDS and _task_status(task) == "open"
    )

    locked_truth_blockers = [
        _compact_policy_blocker(task, source="gate_todo")
        for task in open_gate_tasks
        if _is_locked_truth_gate_task(task)
        and not _is_connection_contract_blocked_gate_task(plan, task)
    ]
    connection_gap = _production_connection_contract_gap(plan)
    if connection_gap.get("status") == "missing":
        suggestion_context = _connection_contract_suggestion_context(plan)
        locked_truth_blockers.insert(0, {
            "source": "ssot_connection_contracts",
            "gate_kind": "manifest_connection_contract_evidence",
            "status": "missing",
            "reason": connection_gap["reason"],
            "pending_suggestions": suggestion_context,
        })
        locked_truth_blockers.extend(
            _compact_policy_blocker(task, source="gate_todo")
            for task in open_gate_tasks
            if _is_connection_contract_blocked_gate_task(plan, task)
        )

    llm_work_blockers = [
        _compact_policy_blocker(task, source="gate_todo")
        for task in open_gate_tasks
        if _is_llm_actionable_gate_task(plan, task)
    ]
    tool_evidence_blockers = [
        _compact_policy_blocker(task, source="gate_todo")
        for task in open_gate_tasks
        if _is_tool_evidence_gate_task(task)
    ]
    tool_evidence_plan = _tool_evidence_plan(plan, open_gate_tasks)
    gate = plan.get("gate") if isinstance(plan.get("gate"), dict) else {}
    pass_allowed = (
        gate.get("status") == "pass"
        and bool((plan.get("todo_completion") or {}).get("all_required_todos_pass"))
    )
    draft_allowed = not hard_blockers
    return {
        "draft_allowed": draft_allowed,
        "deferred_human_qa_allowed": draft_allowed and not pass_allowed,
        "pass_allowed": pass_allowed,
        "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
        "gate_status": str(gate.get("status") or "unknown"),
        "open_required_todos": int((plan.get("todo_completion") or {}).get("open_required_tasks") or 0),
        "hard_blockers": hard_blockers[:32],
        "blocked_by_locked_truth": locked_truth_blockers[:32],
        "blocked_by_llm_work": llm_work_blockers[:32],
        "blocked_by_tool_evidence": tool_evidence_blockers[:32],
        "tool_evidence_plan": tool_evidence_plan[:32],
        "connection_contract_gap": connection_gap,
        "connection_contract_suggestions": _connection_contract_suggestion_context(plan),
        "allowed_draft_work": [
            "Author module RTL from SSOT-derived TODO packets.",
            "Add tests, vectors, assertions, reports, and repair RTL under LLM-editable surfaces.",
            "Leave unresolved locked-truth decisions as human_gate/change-request records instead of changing SSOT authority.",
        ],
        "stop_conditions": [
            "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
            "Do not claim rtl-gen PASS while pass_allowed is false.",
            "Do not sign off top integration while required connection contracts are missing.",
        ],
    }


def _packet_execution_policy(
    plan: dict[str, Any],
    kind: str,
    owner_module: str,
    ordered_tasks: list[dict[str, Any]],
    context: dict[str, Any],
) -> dict[str, Any]:
    plan_policy = _authoring_execution_policy(plan)
    packet_open_required = [
        task for task in ordered_tasks
        if _is_open_required_task(task)
    ]
    packet_locked = [
        _compact_policy_blocker(task, source="packet_task")
        for task in packet_open_required
        if _is_locked_truth_gate_task(task)
        or _is_connection_contract_blocked_gate_task(plan, task)
    ]
    packet_tool_evidence = [
        _compact_policy_blocker(task, source="packet_task")
        for task in packet_open_required
        if _is_tool_evidence_gate_task(task)
    ]
    packet_tool_evidence_plan = _tool_evidence_plan(plan, packet_open_required)
    human_locked_open_count = len(packet_locked)
    llm_actionable_open_count = sum(
        1
        for task in packet_open_required
        if not (
            _is_locked_truth_gate_task(task)
            or _is_tool_evidence_gate_task(task)
            or _is_connection_contract_blocked_gate_task(plan, task)
        )
    )
    gap = context.get("connection_contract_gap") if isinstance(context.get("connection_contract_gap"), dict) else {}
    top = str(plan.get("top") or "")
    top_or_gate = kind == "gate" or (owner_module and owner_module == top)
    integration_signoff_allowed = not (top_or_gate and gap.get("status") == "missing")
    if not integration_signoff_allowed and kind == "gate" and packet_locked:
        human_locked_open_count += 1
        packet_locked.insert(0, {
            "source": "ssot_connection_contracts",
            "gate_kind": "manifest_connection_contract_evidence",
            "status": "missing",
            "reason": gap.get("reason") or "Missing machine-readable SSOT connection contracts.",
        })
    work_allowed = bool(plan_policy.get("draft_allowed"))
    pass_allowed = (
        bool(plan_policy.get("pass_allowed"))
        and not packet_open_required
        and integration_signoff_allowed
    )
    return {
        "work_allowed": work_allowed,
        "draft_allowed": work_allowed and kind != "gate",
        "evidence_closure_allowed": work_allowed and kind == "gate",
        "deferred_human_qa_allowed": bool(plan_policy.get("deferred_human_qa_allowed")),
        "pass_allowed": pass_allowed,
        "integration_signoff_allowed": integration_signoff_allowed,
        "open_required_count": len(packet_open_required),
        "llm_actionable": llm_actionable_open_count > 0,
        "llm_actionable_open_count": llm_actionable_open_count,
        "human_locked_open_count": human_locked_open_count,
        "tool_evidence_open_count": len(packet_tool_evidence),
        "contract_blocked_open_count": sum(
            1 for task in packet_open_required if _is_connection_contract_blocked_gate_task(plan, task)
        ),
        "blocked_by_locked_truth": packet_locked[:32],
        "blocked_by_tool_evidence": packet_tool_evidence[:32],
        "tool_evidence_plan": packet_tool_evidence_plan[:32],
        "stop_conditions": [
            "Close this packet only after every required task in the packet has pass status.",
            "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
            "Never use a fixed RTL template as the implementation.",
        ],
    }


REFERENCE_PROFILE_PACKET_CONTEXT_KEYS = (
    "path",
    "label",
    "summary",
    "target_candidate_basis",
    "target_candidate_summary",
    "suggested_ssot_target_scale",
    "guidance",
)


def _packet_reference_profile_context(plan: dict[str, Any]) -> dict[str, Any] | None:
    profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
    if not profile:
        return None
    return {
        key: profile.get(key)
        for key in REFERENCE_PROFILE_PACKET_CONTEXT_KEYS
        if key in profile
    }


def _packet_target_scale_context(plan: dict[str, Any]) -> dict[str, Any] | None:
    target_scale = plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {}
    return dict(target_scale) if target_scale else None


def _packet_owner_context(plan: dict[str, Any], kind: str, owner_module: str, owner_file: str) -> dict[str, Any]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    owner_modules = [
        item for item in summary.get("owner_modules", [])
        if isinstance(item, dict)
    ]
    top = str(plan.get("top") or "")
    quality_profile = str(
        (plan.get("policy") or {}).get("rtl_quality_profile")
        or summary.get("rtl_quality_profile")
        or "standard"
    )
    contracts = [
        item for item in plan.get("ssot_connection_contracts", [])
        if isinstance(item, dict)
    ]
    owner = next(
        (
            {
                "name": str(item.get("name") or ""),
                "file": str(item.get("file") or ""),
                "refs": [str(ref) for ref in item.get("refs", [])[:32]] if isinstance(item.get("refs"), list) else [],
                "wiring_only": bool(item.get("wiring_only")),
            }
            for item in owner_modules
            if str(item.get("name") or "") == owner_module
        ),
        {"name": owner_module, "file": owner_file, "refs": [], "wiring_only": False},
    )

    def compact_contract(item: dict[str, Any]) -> dict[str, Any]:
        return {
            key: item.get(key)
            for key in ("source_ref", "module", "instance", "port", "signal", "signal_terms", "machine_readable")
            if key in item
        }

    if kind == "gate" or owner_module == top:
        relevant_contracts = contracts
    else:
        owner_l = owner_module.lower()
        relevant_contracts = [
            item for item in contracts
            if str(item.get("module") or "").lower() == owner_l
            or str(item.get("instance") or "").lower() == owner_l
        ]

    contract_gap = _production_connection_contract_gap(plan)
    top_io = [
        {
            key: item.get(key)
            for key in ("source_ref", "name", "direction", "width", "aliases", "allow_constant", "allow_unused")
            if key in item
        }
        for item in (plan.get("ssot_top_io_contracts") or [])
        if isinstance(item, dict)
    ]
    peer_modules = [
        {
            "name": str(item.get("name") or ""),
            "file": str(item.get("file") or ""),
            "wiring_only": bool(item.get("wiring_only")),
        }
        for item in owner_modules[:64]
    ]
    return {
        "quality_profile": quality_profile,
        "owner": owner,
        "peer_modules": peer_modules,
        "reference_profile": _packet_reference_profile_context(plan),
        "target_scale": _packet_target_scale_context(plan),
        "connection_contract_gap": contract_gap,
        "connection_contract_suggestions": _packet_connection_contract_suggestions(plan, owner_module, kind),
        "ssot_connection_contracts": [compact_contract(item) for item in relevant_contracts[:128]],
        "ssot_top_io_contracts": top_io[:128] if kind == "gate" or owner_module == top else [],
    }


def _packet_markdown(packet: dict[str, Any]) -> str:
    lines = [
        f"# RTL Authoring Packet: {packet['packet_id']}",
        "",
        f"- Kind: {packet['kind']}",
        f"- Owner module: {packet.get('owner_module') or '<none>'}",
        f"- Owner file: {packet.get('owner_file') or '<none>'}",
        f"- Task count: {packet['summary']['task_count']}",
        f"- Required tasks: {packet['summary']['required_count']}",
        "",
        "## Rules",
        "",
        *[f"- {rule}" for rule in packet.get("rules", [])],
        "",
        "## Context",
        "",
        f"- Quality profile: {(packet.get('context') or {}).get('quality_profile') or '<unknown>'}",
    ]
    context = packet.get("context") if isinstance(packet.get("context"), dict) else {}
    policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
    lines.extend([
        f"- Work allowed: {bool(policy.get('work_allowed'))}",
        f"- Draft allowed: {bool(policy.get('draft_allowed'))}",
        f"- Evidence closure allowed: {bool(policy.get('evidence_closure_allowed'))}",
        f"- PASS allowed: {bool(policy.get('pass_allowed'))}",
        f"- Integration signoff allowed: {bool(policy.get('integration_signoff_allowed', True))}",
        f"- LLM-actionable open tasks: {int(policy.get('llm_actionable_open_count') or 0)}",
        f"- Human-locked open tasks: {int(policy.get('human_locked_open_count') or 0)}",
    ])
    owner = context.get("owner") if isinstance(context.get("owner"), dict) else {}
    refs = owner.get("refs") if isinstance(owner.get("refs"), list) else []
    if refs:
        lines.append("- Owner refs: " + ", ".join(str(ref) for ref in refs[:16]))
    module_slice = context.get("module_slice") if isinstance(context.get("module_slice"), dict) else {}
    if module_slice.get("enabled"):
        lines.append(
            "- Module slice: "
            f"{module_slice.get('index')}/{module_slice.get('count')} "
            f"section={module_slice.get('section') or module_slice.get('key')} "
            f"task_limit={module_slice.get('task_limit')}"
        )
        if module_slice.get("rule"):
            lines.append(f"- Slice rule: {module_slice.get('rule')}")
    reference_profile = context.get("reference_profile") if isinstance(context.get("reference_profile"), dict) else {}
    reference_summary = reference_profile.get("summary") if isinstance(reference_profile.get("summary"), dict) else {}
    target_candidate_summary = (
        reference_profile.get("target_candidate_summary")
        if isinstance(reference_profile.get("target_candidate_summary"), dict)
        else {}
    )
    if reference_summary:
        lines.append(
            "- Reference scale profile: "
            f"{reference_profile.get('path') or '<profile>'} "
            f"(calibration-only, files={reference_summary.get('file_count', 0)}, "
                f"modules={reference_summary.get('modules', 0)}, lines={reference_summary.get('lines', 0)})"
        )
    if target_candidate_summary and target_candidate_summary != reference_summary:
        lines.append(
            "- Reference target-candidate subset: "
            f"basis={reference_profile.get('target_candidate_basis') or '<unknown>'}, "
            f"files={target_candidate_summary.get('file_count', 0)}, "
            f"modules={target_candidate_summary.get('modules', 0)}, "
            f"lines={target_candidate_summary.get('lines', 0)}"
        )
    target_scale = context.get("target_scale") if isinstance(context.get("target_scale"), dict) else {}
    target_keys = [key for key in sorted(target_scale) if key.startswith("min_")]
    if target_keys:
        lines.append(
            "- SSOT target scale: "
            + ", ".join(f"{key}={target_scale[key]}" for key in target_keys[:12])
        )
    candidate = (reference_profile.get("suggested_ssot_target_scale") if isinstance(reference_profile, dict) else None)
    if isinstance(candidate, dict) and candidate and not target_keys:
        lines.append("- Reference target-scale candidate present; SSOT target_scale is not locked yet")
    gap = context.get("connection_contract_gap") if isinstance(context.get("connection_contract_gap"), dict) else {}
    if gap.get("status") == "missing":
        lines.append(f"- Connection contract gap: {gap.get('reason')}")
    suggestion_context = context.get("connection_contract_suggestions") if isinstance(context.get("connection_contract_suggestions"), dict) else {}
    suggestion_rows = suggestion_context.get("rows") if isinstance(suggestion_context.get("rows"), list) else []
    suggestion_summary = suggestion_context.get("summary") if isinstance(suggestion_context.get("summary"), dict) else {}
    if suggestion_rows:
        lines.append(
            "- Pending connection-contract suggestions: "
            f"{suggestion_summary.get('pending_review', len(suggestion_rows))} rows in "
            f"{suggestion_context.get('path') or 'rtl/connection_contract_suggestions.json'}"
        )
        if suggestion_summary.get("draft_top_integration_fragment"):
            lines.append(f"- Draft top integration fragment: {suggestion_summary.get('draft_top_integration_fragment')}")
        lines.append(
            "- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, "
            "but they are not SSOT authority and cannot close connection-contract signoff."
        )
        for row in suggestion_rows[:8]:
            if not isinstance(row, dict):
                continue
            lines.append(
                "  - "
                f"{row.get('module') or '<module>'}.{row.get('port') or '<port>'} <= "
                f"{row.get('signal') or '<signal>'} "
                f"({row.get('confidence') or 'pending'})"
            )
    locked = policy.get("blocked_by_locked_truth") if isinstance(policy.get("blocked_by_locked_truth"), list) else []
    if locked:
        lines.append("- Locked-truth blockers:")
        for item in locked[:8]:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('gate_kind') or item.get('source') or 'gate'}: "
                f"{item.get('reason') or item.get('status') or '<open>'}"
            )
    tool_blockers = policy.get("blocked_by_tool_evidence") if isinstance(policy.get("blocked_by_tool_evidence"), list) else []
    if tool_blockers:
        lines.append("- Tool-evidence blockers:")
        for item in tool_blockers[:8]:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('gate_kind') or item.get('source') or 'gate'}: "
                f"{item.get('reason') or item.get('status') or '<open>'}"
            )
    tool_plan = policy.get("tool_evidence_plan") if isinstance(policy.get("tool_evidence_plan"), list) else []
    if tool_plan:
        lines.append("- Tool-evidence runbook:")
        for item in tool_plan[:8]:
            if not isinstance(item, dict):
                continue
            stages = item.get("stage_sequence") if isinstance(item.get("stage_sequence"), list) else []
            artifacts = item.get("artifacts") if isinstance(item.get("artifacts"), list) else []
            lines.append(
                "  - "
                f"{item.get('gate_kind') or '<gate>'}: "
                f"stages={', '.join(str(stage) for stage in stages[:6]) or '<manual>'}; "
                f"artifact={artifacts[0] if artifacts else item.get('artifact') or '<artifact>'}"
            )
    contracts = context.get("ssot_connection_contracts") if isinstance(context.get("ssot_connection_contracts"), list) else []
    if contracts:
        lines.append("- SSOT connection contracts:")
        for item in contracts[:12]:
            if not isinstance(item, dict):
                continue
            lines.append(
                "  - "
                f"{item.get('module') or '<module>'}.{item.get('port') or '<port>'} <= "
                f"{item.get('signal') or '<signal>'} ({item.get('source_ref') or '<source>'})"
            )
    top_io = context.get("ssot_top_io_contracts") if isinstance(context.get("ssot_top_io_contracts"), list) else []
    if top_io:
        lines.append(f"- SSOT top IO contracts: {len(top_io)}")
    lines.extend([
        "",
        "## Tasks",
        "",
    ])
    for task in packet.get("tasks", []):
        criteria = task.get("criteria") if isinstance(task.get("criteria"), list) else []
        lines.extend([
            f"### {task.get('id') or '<unknown>'}: {task.get('content') or '<no content>'}",
            "",
            f"- Priority: {task.get('priority') or 'normal'}",
            f"- Required: {bool(task.get('required', True))}",
            f"- Status: {(task.get('todo_completion') or {}).get('status') or '<unknown>'}",
            f"- Category: {task.get('category') or '<none>'}",
            f"- Source ref: {task.get('source_ref') or '<none>'}",
            f"- Detail: {task.get('detail') or '<none>'}",
        ])
        reason = (task.get("todo_completion") or {}).get("reason")
        if reason:
            lines.append(f"- Current reason: {reason}")
        if criteria:
            lines.append("- Criteria:")
            lines.extend(f"  - {item}" for item in criteria)
        refs = task.get("ssot_refs")
        if isinstance(refs, list) and refs:
            lines.append("- SSOT refs: " + ", ".join(str(item) for item in refs[:16]))
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _authoring_status_markdown(authoring_plan: dict[str, Any]) -> str:
    summary = authoring_plan.get("summary") if isinstance(authoring_plan.get("summary"), dict) else {}
    reference_profile = authoring_plan.get("reference_profile") if isinstance(authoring_plan.get("reference_profile"), dict) else {}
    reference_summary = reference_profile.get("summary") if isinstance(reference_profile.get("summary"), dict) else {}
    target_candidate = (
        reference_profile.get("suggested_ssot_target_scale")
        if isinstance(reference_profile.get("suggested_ssot_target_scale"), dict)
        else {}
    )
    packets = authoring_plan.get("packets") if isinstance(authoring_plan.get("packets"), list) else []
    packet_by_id = {
        str(packet.get("packet_id") or ""): packet
        for packet in packets
        if isinstance(packet, dict) and packet.get("packet_id")
    }
    lines = [
        f"# RTL Authoring Status: {authoring_plan.get('ip') or '<ip>'}",
        "",
        "## Status",
        "",
        f"- Top: {authoring_plan.get('top') or '<unknown>'}",
        f"- Packets: {summary.get('packets', 0)}",
        f"- LLM-actionable tasks: {summary.get('llm_actionable_tasks', 0)}",
        f"- Human-locked tasks: {summary.get('human_locked_tasks', 0)}",
        f"- Tool-evidence tasks: {summary.get('tool_evidence_tasks', 0)}",
        f"- Deferred human QA allowed: {bool(summary.get('deferred_human_qa_allowed'))}",
        f"- PASS allowed: {bool(summary.get('pass_allowed'))}",
        f"- Target scale locked: {bool(summary.get('target_scale_present'))}",
        f"- Pending connection-contract suggestions: {int(summary.get('pending_connection_contract_suggestions') or 0)}",
        f"- Recommended packet batch limit: {summary.get('recommended_packet_batch_limit', AUTHORING_RECOMMENDED_PACKET_BATCH_LIMIT)}",
    ]
    if reference_summary:
        lines.extend([
            f"- Reference profile: {reference_profile.get('path') or reference_profile.get('label') or 'rtl_reference_profile'}",
            (
                "- Reference scale: "
                f"files={reference_summary.get('file_count', 0)}, "
                f"modules={reference_summary.get('modules', 0)}, "
                f"lines={reference_summary.get('lines', 0)}, "
                f"procedural_blocks={reference_summary.get('always_blocks', 0)}"
            ),
        ])
    target_candidate_summary = (
        reference_profile.get("target_candidate_summary")
        if isinstance(reference_profile.get("target_candidate_summary"), dict)
        else {}
    )
    if target_candidate_summary and target_candidate_summary != reference_summary:
        lines.append(
            "- Reference target-candidate subset: "
            f"basis={reference_profile.get('target_candidate_basis') or '<unknown>'}, "
            f"files={target_candidate_summary.get('file_count', 0)}, "
            f"modules={target_candidate_summary.get('modules', 0)}, "
            f"lines={target_candidate_summary.get('lines', 0)}"
        )
    reference_scale_gap = authoring_plan.get("reference_scale_gap") if isinstance(authoring_plan.get("reference_scale_gap"), dict) else {}
    gap_metrics = reference_scale_gap.get("metrics") if isinstance(reference_scale_gap.get("metrics"), dict) else {}
    if gap_metrics:
        parts = []
        for key in ("source_files", "modules", "lines", "instances", "procedural_blocks"):
            item = gap_metrics.get(key)
            if not isinstance(item, dict):
                continue
            parts.append(
                f"{key}={item.get('current', 0)}/{item.get('reference', 0)} ({item.get('percent', 0)}%)"
            )
        if parts:
            lines.append("- Reference scale gap: " + ", ".join(parts))
    if target_candidate and not summary.get("target_scale_present"):
        lines.append("- Target scale candidate: present but not SSOT-locked")
    next_packets = summary.get("next_llm_packets") if isinstance(summary.get("next_llm_packets"), list) else []
    if next_packets:
        lines.extend(["", "## Next LLM Packets", ""])
        for packet_id in next_packets[:8]:
            packet = packet_by_id.get(str(packet_id), {})
            policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
            lines.append(
                f"- {packet_id}: {packet.get('json') or '<packet>'} "
                f"(llm_open={int(policy.get('llm_actionable_open_count') or 0)}, "
                f"human_locked={int(policy.get('human_locked_open_count') or 0)})"
            )
    tool_packets = [
        packet for packet in packets
        if isinstance(packet, dict)
        and int((packet.get("execution_policy") or {}).get("tool_evidence_open_count") or 0) > 0
    ]
    if tool_packets:
        lines.extend(["", "## Tool Evidence Queue", ""])
        for packet in tool_packets[:12]:
            policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
            plan_items = policy.get("tool_evidence_plan") if isinstance(policy.get("tool_evidence_plan"), list) else []
            first_plan = plan_items[0] if plan_items and isinstance(plan_items[0], dict) else {}
            stages = first_plan.get("stage_sequence") if isinstance(first_plan.get("stage_sequence"), list) else []
            lines.append(
                f"- {packet.get('packet_id') or '<packet>'}: "
                f"tool_evidence={int(policy.get('tool_evidence_open_count') or 0)}, "
                f"next_tool={stages[0] if stages else first_plan.get('gate_kind') or '<tool>'}, "
                f"json={packet.get('json') or '<packet>'}"
            )
    locked_packets = [
        packet for packet in packets
        if isinstance(packet, dict)
        and int((packet.get("execution_policy") or {}).get("human_locked_open_count") or 0) > 0
    ]
    if locked_packets:
        lines.extend(["", "## Human-Locked Queue", ""])
        for packet in locked_packets[:12]:
            policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
            lines.append(
                f"- {packet.get('packet_id') or '<packet>'}: "
                f"human_locked={int(policy.get('human_locked_open_count') or 0)}, "
                f"json={packet.get('json') or '<packet>'}"
            )
    lines.extend([
        "",
        "## Rules",
        "",
    ])
    lines.extend(f"- {rule}" for rule in authoring_plan.get("rules", []) if isinstance(rule, str))
    return "\n".join(lines).rstrip() + "\n"


def _write_authoring_packets(ip_dir: Path, plan: dict[str, Any], *, todo_plan_sha256: str) -> dict[str, Any]:
    rtl_dir = ip_dir / "rtl"
    packet_dir = rtl_dir / "authoring_packets"
    packet_dir.mkdir(parents=True, exist_ok=True)
    for stale in list(packet_dir.glob("*.json")) + list(packet_dir.glob("*.md")):
        stale.unlink()

    module_groups: dict[str, list[dict[str, Any]]] = {}
    gate_tasks: list[dict[str, Any]] = []
    unowned_tasks: list[dict[str, Any]] = []
    owner_files: dict[str, str] = {}

    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        if task.get("category") == "rtl_gate.rtl_gen":
            gate_tasks.append(task)
            continue
        owner_module = str(task.get("owner_module") or "").strip()
        owner_file = str(task.get("owner_file") or "").strip()
        if owner_module:
            module_groups.setdefault(owner_module, []).append(task)
            owner_files.setdefault(owner_module, owner_file)
        else:
            unowned_tasks.append(task)

    packets: list[dict[str, Any]] = []

    def add_packet(
        kind: str,
        packet_id: str,
        tasks: list[dict[str, Any]],
        *,
        owner_module: str = "",
        owner_file: str = "",
        module_slice: dict[str, Any] | None = None,
    ) -> None:
        ordered = sorted(tasks, key=_priority_rank)
        context = _packet_owner_context(plan, kind, owner_module, owner_file)
        slice_context = {
            key: value
            for key, value in (module_slice or {}).items()
            if key != "tasks"
        }
        if slice_context:
            context["module_slice"] = slice_context
        packet = {
            "schema_version": plan.get("schema_version", 1),
            "type": "rtl_authoring_packet",
            "packet_id": packet_id,
            "kind": kind,
            "ip": plan.get("ip"),
            "top": plan.get("top"),
            "source_plan": "rtl/rtl_todo_plan.json",
            "todo_plan_sha256": todo_plan_sha256,
            "owner_module": owner_module,
            "owner_file": owner_file,
            "rules": [
                "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
                "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
                "Every task must satisfy content, detail, and criteria before the packet is closed.",
                "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
                "Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.",
                "Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.",
                "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.",
            ],
            "summary": {
                "task_count": len(ordered),
                "required_count": sum(1 for item in ordered if item.get("required", True)),
                "status_counts": dict(sorted(Counter(str((item.get("todo_completion") or {}).get("status") or "unknown") for item in ordered).items())),
                "open_required_count": sum(
                    1
                    for item in ordered
                    if item.get("required", True) and (item.get("todo_completion") or {}).get("status") != "pass"
                ),
                "categories": dict(sorted(Counter(str(item.get("category") or "unknown") for item in ordered).items())),
                "source_refs": [str(item.get("source_ref")) for item in ordered if item.get("source_ref")][:24],
                "module_slice": slice_context,
            },
            "context": context,
            "execution_policy": _packet_execution_policy(plan, kind, owner_module, ordered, context),
            "tasks": [_packet_task_item(task) for task in ordered],
        }
        json_rel = f"rtl/authoring_packets/{packet_id}.json"
        md_rel = f"rtl/authoring_packets/{packet_id}.md"
        (ip_dir / json_rel).write_text(
            json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (ip_dir / md_rel).write_text(_packet_markdown(packet), encoding="utf-8")
        packets.append({
            "packet_id": packet_id,
            "kind": kind,
            "owner_module": owner_module,
            "owner_file": owner_file,
            "json": json_rel,
            "markdown": md_rel,
            "summary": packet["summary"],
            "execution_policy": packet["execution_policy"],
        })

    for owner_module in sorted(module_groups):
        owner_slug = _packet_slug(owner_module, fallback="module")
        module_slices = _module_authoring_slices(owner_module, module_groups[owner_module])
        used_ids: set[str] = set()
        for module_slice in module_slices:
            if module_slice.get("enabled"):
                base_id = f"module__{owner_slug}__{_packet_slug(module_slice.get('key'), fallback='slice')}"
                packet_id = base_id
                suffix = 2
                while packet_id in used_ids:
                    packet_id = f"{base_id}_{suffix}"
                    suffix += 1
            else:
                packet_id = f"module__{owner_slug}"
            used_ids.add(packet_id)
            add_packet(
                "module",
                packet_id,
                module_slice["tasks"],
                owner_module=owner_module,
                owner_file=owner_files.get(owner_module, ""),
                module_slice=module_slice,
            )
    if unowned_tasks:
        add_packet("unowned", "unowned_tasks", unowned_tasks)
    if gate_tasks:
        top_owner = str(plan.get("top") or "")
        top_owner_file = f"rtl/{plan.get('top') or plan.get('ip')}.sv"
        llm_gate_tasks = [
            task
            for task in gate_tasks
            if _is_llm_actionable_gate_task(plan, task)
        ]
        tool_gate_tasks = [
            task
            for task in gate_tasks
            if _is_tool_evidence_gate_task(task)
        ]
        contract_blocked_gate_tasks = [
            task
            for task in gate_tasks
            if _is_connection_contract_blocked_gate_task(plan, task)
        ]
        locked_gate_tasks = [
            task
            for task in gate_tasks
            if _is_locked_truth_gate_task(task)
            and not _is_connection_contract_blocked_gate_task(plan, task)
        ]
        if llm_gate_tasks:
            add_packet(
                "gate",
                "rtl_gate_evidence_closure",
                llm_gate_tasks,
                owner_module=top_owner,
                owner_file=top_owner_file,
            )
        if tool_gate_tasks:
            add_packet(
                "gate",
                "rtl_gate_tool_evidence",
                tool_gate_tasks,
                owner_module=top_owner,
                owner_file=top_owner_file,
            )
        if contract_blocked_gate_tasks:
            add_packet(
                "gate",
                "rtl_gate_contract_blocked",
                contract_blocked_gate_tasks,
                owner_module=top_owner,
                owner_file=top_owner_file,
            )
        if locked_gate_tasks:
            add_packet(
                "gate",
                "rtl_gate_human_closure",
                locked_gate_tasks,
                owner_module=top_owner,
                owner_file=top_owner_file,
            )

    top = str(plan.get("top") or plan.get("ip") or "").strip()
    top_file = f"rtl/{top}.sv" if top else ""
    top_file_exists = bool(top_file and (ip_dir / top_file).is_file())
    owner_order = {
        str(item.get("name") or ""): index
        for index, item in enumerate((plan.get("summary") or {}).get("owner_modules") or [])
        if isinstance(item, dict)
    }

    def packet_work_rank(packet: dict[str, Any]) -> tuple[int, int, int, int, int, str]:
        summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
        policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
        kind = str(packet.get("kind") or "")
        owner_module = str(packet.get("owner_module") or "")
        owner_file = str(packet.get("owner_file") or "")
        llm_open = int(policy.get("llm_actionable_open_count") or 0)
        open_required = int(summary.get("open_required_count") or 0)
        owner_missing = bool(owner_file and not (ip_dir / owner_file).is_file())
        kind_rank = {"module": 0, "unowned": 1, "gate": 2}.get(kind, 3)
        if llm_open <= 0:
            actionable_rank = 2 if open_required <= 0 else 1
        else:
            actionable_rank = 0
        # Once the top RTL exists, missing manifest children should be authored before
        # residual top-level TODO slices; otherwise PL330-class runs keep expanding top.
        missing_child_rank = 0 if top_file_exists and kind == "module" and owner_module != top and owner_missing else 1
        return (
            actionable_rank,
            kind_rank,
            missing_child_rank,
            owner_order.get(owner_module, 10_000),
            -llm_open,
            str(packet.get("packet_id") or ""),
        )

    packets.sort(key=packet_work_rank)

    llm_actionable_packets = [
        packet
        for packet in packets
        if int((packet.get("execution_policy") or {}).get("llm_actionable_open_count") or 0) > 0
    ]
    human_locked_packets = [
        packet
        for packet in packets
        if int((packet.get("execution_policy") or {}).get("human_locked_open_count") or 0) > 0
    ]
    tool_evidence_packets = [
        packet
        for packet in packets
        if int((packet.get("execution_policy") or {}).get("tool_evidence_open_count") or 0) > 0
    ]
    plan_execution_policy = _authoring_execution_policy(plan)
    connection_suggestions = (
        plan.get("connection_contract_suggestions")
        if isinstance(plan.get("connection_contract_suggestions"), dict)
        else {}
    )
    connection_suggestion_summary = (
        connection_suggestions.get("summary")
        if isinstance(connection_suggestions.get("summary"), dict)
        else {}
    )
    reference_scale_gap = _reference_scale_gap_summary(plan)
    authoring_plan = {
        "schema_version": plan.get("schema_version", 1),
        "type": "rtl_authoring_plan",
        "ip": plan.get("ip"),
        "top": plan.get("top"),
        "source_plan": "rtl/rtl_todo_plan.json",
        "todo_plan_sha256": todo_plan_sha256,
        "packet_dir": "rtl/authoring_packets",
        "status_markdown": "rtl/rtl_authoring_status.md",
        "execution_policy": plan_execution_policy,
        "policy": plan.get("policy"),
        "target_scale": plan.get("target_scale"),
        "reference_scale_gap": reference_scale_gap,
        "rules": [
            "Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.",
            "Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.",
            "Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.",
            "Do not close static RTL evidence with comments: derive_rtl_todos.py strips comments before matching, so evidence_terms must be preserved in live lint-clean RTL identifiers/logic.",
            "Do not close static RTL evidence with evidence-only alias wires or marker-only helper wires; the matched identifiers must participate in real RTL behavior.",
            "If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.",
            "After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.",
            "Keep locked authority artifacts unchanged unless a human approves a change request.",
            "Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.",
        ],
        "summary": {
            "packets": len(packets),
            "module_packets": sum(1 for packet in packets if packet["kind"] == "module"),
            "gate_packets": sum(1 for packet in packets if packet["kind"] == "gate"),
            "unowned_packets": sum(1 for packet in packets if packet["kind"] == "unowned"),
            "total_tasks": len(plan.get("tasks", [])),
            "required_tasks": sum(1 for task in plan.get("tasks", []) if isinstance(task, dict) and task.get("required", True)),
            "reference_profile_present": bool(plan.get("reference_profile")),
            "target_scale_present": bool(plan.get("target_scale")),
            "connection_contract_suggestions_present": bool(
                int(connection_suggestion_summary.get("suggested_rows") or 0)
            ),
            "reference_scale_gap_present": bool(reference_scale_gap),
            "pending_connection_contract_suggestions": int(connection_suggestion_summary.get("pending_review") or 0),
            "deferred_human_qa_allowed": bool(plan_execution_policy.get("deferred_human_qa_allowed")),
            "pass_allowed": bool(plan_execution_policy.get("pass_allowed")),
            "recommended_packet_batch_limit": AUTHORING_RECOMMENDED_PACKET_BATCH_LIMIT,
            "llm_actionable_packets": len(llm_actionable_packets),
            "llm_actionable_tasks": sum(
                int((packet.get("execution_policy") or {}).get("llm_actionable_open_count") or 0)
                for packet in llm_actionable_packets
            ),
            "human_locked_packets": len(human_locked_packets),
            "human_locked_tasks": sum(
                int((packet.get("execution_policy") or {}).get("human_locked_open_count") or 0)
                for packet in human_locked_packets
            ),
            "tool_evidence_packets": len(tool_evidence_packets),
            "tool_evidence_tasks": sum(
                int((packet.get("execution_policy") or {}).get("tool_evidence_open_count") or 0)
                for packet in tool_evidence_packets
            ),
            "next_llm_packets": [str(packet.get("packet_id") or "") for packet in llm_actionable_packets[:8] if packet.get("packet_id")],
            "packet_task_limit": AUTHORING_PACKET_TASK_LIMIT,
            "sliced_module_packets": sum(
                1
                for packet in packets
                if (packet.get("summary") or {}).get("module_slice", {}).get("enabled")
            ),
            "max_packet_required_tasks": max(
                [int((packet.get("summary") or {}).get("required_count") or 0) for packet in packets] or [0]
            ),
        },
        "reference_profile": plan.get("reference_profile"),
        "packets": packets,
    }
    (rtl_dir / "rtl_authoring_plan.json").write_text(
        json.dumps(authoring_plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (rtl_dir / "rtl_authoring_status.md").write_text(_authoring_status_markdown(authoring_plan), encoding="utf-8")
    return authoring_plan


def _write_outputs(ip_dir: Path, plan: dict[str, Any]) -> None:
    rtl_dir = ip_dir / "rtl"
    logs_dir = ip_dir / "logs" / "rtl-gen"
    rtl_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)

    full_plan_text = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (logs_dir / "rtl_todo_plan.json").write_text(full_plan_text, encoding="utf-8")
    todo_plan_path = rtl_dir / "rtl_todo_plan.json"
    todo_plan_path.write_text(full_plan_text, encoding="utf-8")
    todo_dir = ip_dir / "todo"
    todo_dir.mkdir(parents=True, exist_ok=True)
    # New canonical TODO artifact location under <ip>/todo/.
    # Keep legacy rtl/ copies for backward compatibility.
    (todo_dir / "rtl_todo_plan.json").write_text(full_plan_text, encoding="utf-8")
    todo_plan_sha256 = _stable_json_sha256(todo_plan_path) or hashlib.sha256(full_plan_text.encode("utf-8")).hexdigest()
    authoring_plan = _write_authoring_packets(ip_dir, plan, todo_plan_sha256=todo_plan_sha256)

    connection_suggestions = (
        plan.get("connection_contract_suggestions")
        if isinstance(plan.get("connection_contract_suggestions"), dict)
        else {}
    )
    connection_suggestion_rows = (
        connection_suggestions.get("rows")
        if isinstance(connection_suggestions.get("rows"), list)
        else []
    )
    connection_suggestion_path = rtl_dir / "connection_contract_suggestions.json"
    connection_fragment_path = rtl_dir / "connection_contract_draft_top.svfrag"
    if connection_suggestion_rows:
        connection_suggestion_path.write_text(
            json.dumps(connection_suggestions, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        fragment_text = _connection_contract_draft_fragment_text(connection_suggestions)
        if fragment_text:
            connection_fragment_path.write_text(fragment_text, encoding="utf-8")
        elif connection_fragment_path.exists():
            connection_fragment_path.unlink()
    else:
        if connection_suggestion_path.exists():
            connection_suggestion_path.unlink()
        if connection_fragment_path.exists():
            connection_fragment_path.unlink()

    reference_scale_gap = plan.get("reference_scale_gap") if isinstance(plan.get("reference_scale_gap"), dict) else {}
    reference_scale_gap_path = rtl_dir / "reference_scale_gap.json"
    if reference_scale_gap:
        reference_scale_gap_path.write_text(
            json.dumps(reference_scale_gap, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif reference_scale_gap_path.exists():
        reference_scale_gap_path.unlink()

    template_plan = _convert_to_template_format(plan)
    template_text = json.dumps(template_plan, ensure_ascii=False, indent=2) + "\n"
    (rtl_dir / "rtl_todo_tracker.json").write_text(template_text, encoding="utf-8")
    (todo_dir / "rtl_todo_tracker.json").write_text(template_text, encoding="utf-8")
    _direct_load_session_todo(ip_dir, plan, template_text)
    trace = {
        "schema_version": plan["schema_version"],
        "type": "rtl_traceability_matrix",
        "ip": plan["ip"],
        "top": plan["top"],
        "generated_at": plan["generated_at"],
        "rows": [
            {
                "task_id": task["id"],
                "source_ref": task["source_ref"],
                "category": task["category"],
                "owner_module": task["owner_module"],
                "owner_file": task["owner_file"],
                "evidence_terms": task["evidence_terms"],
                "static_evidence": task.get("static_evidence"),
            }
            for task in plan["tasks"]
        ],
        "authoring_plan": "rtl/rtl_authoring_plan.json",
        "authoring_packets": [
            {"packet_id": packet["packet_id"], "json": packet["json"], "markdown": packet["markdown"]}
            for packet in authoring_plan["packets"]
        ],
        "gate": plan["gate"],
    }
    (rtl_dir / "rtl_traceability.json").write_text(
        json.dumps(trace, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _direct_load_session_todo(ip_dir: Path, plan: dict[str, Any], template_text: str) -> None:
    """Direct-load dynamic TODOs into a session-scoped todo.json.

    Target path contract:
      .session/<session_id>/<ip_id>/<workflow>/todo.json
    """
    root = ip_dir.parent
    ip = str(plan.get("ip") or ip_dir.name)
    workflow = (
        os.environ.get("ACTIVE_WORKSPACE")
        or os.environ.get("ATLAS_DEFAULT_WORKFLOW")
        or "rtl-gen"
    ).strip() or "rtl-gen"

    active_session = (os.environ.get("ATLAS_ACTIVE_SESSION") or "").strip().strip("/")
    session_hint = (
        os.environ.get("SESSION_ID")
        or os.environ.get("ACTIVE_PROJECT")
        or "default"
    ).strip().strip("/")

    parts: list[str]
    if active_session:
        raw = [p for p in active_session.split("/") if p]
        if len(raw) >= 3:
            parts = [raw[0], raw[1], raw[2]]
        elif len(raw) == 2:
            parts = [raw[0], raw[1], workflow]
        else:
            parts = [raw[0], ip, workflow]
    else:
        raw = [p for p in session_hint.split("/") if p]
        if len(raw) >= 3:
            parts = [raw[0], raw[1], raw[2]]
        elif len(raw) == 2:
            parts = [raw[0], raw[1], workflow]
        else:
            parts = [raw[0] if raw else "default", ip, workflow]

    session_todo = root / ".session" / parts[0] / parts[1] / parts[2] / "todo.json"
    session_todo.parent.mkdir(parents=True, exist_ok=True)
    session_todo.write_text(template_text, encoding="utf-8")
    plan.setdefault("artifacts", {})
    plan["artifacts"]["session_todo"] = str(session_todo.relative_to(root))


def _write_dynamic_blocker(ip_dir: Path, plan: dict[str, Any]) -> None:
    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
    if not blockers and not orphans:
        return
    questions: list[dict[str, Any]] = []
    if blockers:
        required_fields = sorted({
            str(item.get("source_ref") or item.get("id") or "")
            for item in blockers
            if isinstance(item, dict) and (item.get("source_ref") or item.get("id"))
        })
        questions.append({
            "id": "RTL_DYNAMIC_TODO_SSOT_REQUIRED_SECTIONS",
            "decision_needed": "Repair the SSOT so rtl-gen has mandatory source sections and well-formed SSOT-defined workflow todos.",
            "evidence": "rtl/rtl_todo_plan.json blockers",
            "options": [
                "Update SSOT with structured function_model and cycle_model sections.",
                "Update workflow_todos.rtl-gen[] entries so every item has content, detail, and criteria.",
                "Move non-RTL intent out of RTL implementation sections and rerun /ssot-rtl.",
            ],
            "recommended_default": "Use ssot-gen to fill function_model, cycle_model, workflow_todos.rtl-gen content/detail/criteria, decomposition, DV plan, and coverage from the requirement.",
            "required_fields": required_fields or ["function_model", "cycle_model", "workflow_todos.rtl-gen[].content/detail/criteria"],
            "blocking_items": blockers[:32],
        })
    if orphans:
        candidate_modules = [
            {"name": item.get("name"), "file": item.get("file"), "refs": item.get("refs")}
            for item in ((plan.get("summary") or {}).get("owner_modules") or [])
            if isinstance(item, dict)
        ]
        questions.append({
            "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
            "decision_needed": "Assign every SSOT-derived function/cycle/register/dataflow/FSM task to an RTL module owner.",
            "evidence": "rtl/rtl_todo_plan.json orphans",
            "options": [
                "Add exact sub_modules[].*_refs ownership for each orphan source_ref.",
                "Split or refine SSOT decomposition until each behavior has one RTL owner.",
                "Promote independently verified blocks to child_ssot with an explicit SSOT path.",
            ],
            "recommended_default": "Patch sub_modules[] with function_model_refs, cycle_model_refs, register_refs, dataflow_refs, and fsm_refs.",
            "orphan_refs": [item.get("source_ref") for item in orphans[:128] if isinstance(item, dict)],
            "orphan_groups": _orphan_groups(orphans),
            "candidate_modules": candidate_modules[:32],
            "required_fields": [
                "sub_modules[].function_model_refs",
                "sub_modules[].cycle_model_refs",
                "sub_modules[].register_refs",
                "sub_modules[].dataflow_refs",
                "sub_modules[].fsm_refs",
            ],
            "answer_schema": {
                "format": "YAML or JSON",
                "root_key": "module_contracts",
                "rule": "Every orphan source_ref must be covered by an exact ref or a dotted parent ref in the owning sub_modules[] row.",
            },
        })
    out = {
        "schema_version": 1,
        "type": "rtl_blocker",
        "status": "blocked",
        "owner": "ssot-gen",
        "ip": plan.get("ip"),
        "top": plan.get("top"),
        "reason": "SSOT-derived dynamic RTL TODO gate is blocked.",
        "questions": questions,
        "next_action": "Answer these questions inline so SSOT-gen records them, update SSOT, regenerate FL/equivalence goals, then rerun /ssot-rtl.",
        "timestamp": _utc(),
    }
    path = ip_dir / "rtl" / "rtl_blocked.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _orphan_groups(orphans: list[dict[str, Any]], limit: int = 24) -> list[dict[str, Any]]:
    field_by_section = {
        "function_model": "function_model_refs",
        "cycle_model": "cycle_model_refs",
        "registers": "register_refs",
        "dataflow": "dataflow_refs",
        "features": "feature_refs",
        "fsm": "fsm_refs",
    }
    groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in orphans:
        if not isinstance(item, dict):
            continue
        source_ref = str(item.get("source_ref") or "").strip()
        category = str(item.get("category") or "").strip()
        section = source_ref.split(".", 1)[0] if "." in source_ref else source_ref
        field = field_by_section.get(section, "ssot_refs")
        key = (section, category, field)
        group = groups.setdefault(
            key,
            {
                "section_id": section,
                "category": category,
                "required_field": f"sub_modules[].{field}",
                "count": 0,
                "sample_refs": [],
            },
        )
        group["count"] += 1
        if source_ref and len(group["sample_refs"]) < 12:
            group["sample_refs"].append(source_ref)
    return sorted(groups.values(), key=lambda item: (-int(item["count"]), item["section_id"], item["category"]))[:limit]


def _rtl_source_paths(ip_dir: Path) -> list[tuple[str, Path]]:
    entries: list[str] = []
    filelist = ip_dir / "list" / f"{ip_dir.name}.f"
    if filelist.is_file():
        for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.split("//", 1)[0].split("#", 1)[0].strip()
            if line.endswith((".sv", ".v", ".svh", ".vh")):
                entries.append(line)
    if not entries and (ip_dir / "rtl").is_dir():
        entries = [str(path.relative_to(ip_dir)) for path in sorted((ip_dir / "rtl").glob("*.sv")) + sorted((ip_dir / "rtl").glob("*.v"))]
    rtl_dir = ip_dir / "rtl"
    if rtl_dir.is_dir():
        for path in sorted(rtl_dir.glob("*_param.vh")):
            rel = str(path.relative_to(ip_dir))
            if rel not in entries:
                entries.append(rel)
    paths: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for rel in entries:
        path = ip_dir / rel
        if not path.is_file():
            path = ip_dir.parent / rel
        if path.is_file():
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            paths.append((rel, path))
    return paths


def _read_rtl_sources(ip_dir: Path) -> dict[str, str]:
    sources: dict[str, str] = {}
    for rel, path in _rtl_source_paths(ip_dir):
        try:
            sources[rel] = path.read_text(encoding="utf-8", errors="replace")[:400000]
        except OSError:
            pass
    return sources


def _artifact_freshness_issue(ip_dir: Path, artifact_path: Path, label: str) -> str:
    sources = _rtl_source_paths(ip_dir)
    if not sources:
        return f"{label} freshness cannot be proven because no DUT RTL source files are listed."
    try:
        artifact_mtime = artifact_path.stat().st_mtime
    except OSError as exc:
        return f"Cannot stat {artifact_path.relative_to(ip_dir)} for freshness: {exc}."
    latest: tuple[float, str] | None = None
    for rel, path in sources:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if latest is None or mtime > latest[0]:
            latest = (mtime, rel)
    if latest is None:
        return f"{label} freshness cannot be proven because listed DUT RTL source files could not be statted."
    latest_mtime, latest_rel = latest
    if artifact_mtime + 1e-6 < latest_mtime:
        rel_artifact = artifact_path.relative_to(ip_dir)
        return f"{rel_artifact} is older than current RTL source {latest_rel}; rerun {label} after the final RTL edit."
    return ""


def _normalize_rtl_rel(ip_dir: Path, value: Any) -> str:
    rel = str(value or "").strip().replace("\\", "/")
    if rel.startswith("./"):
        rel = rel[2:]
    prefix = f"{ip_dir.name}/"
    if rel.startswith(prefix):
        rel = rel[len(prefix) :]
    return rel


def _report_source_set_issue(
    ip_dir: Path,
    report: dict[str, Any],
    label: str,
    *,
    extensions: tuple[str, ...],
) -> str:
    current = {
        _normalize_rtl_rel(ip_dir, rel)
        for rel, _path in _rtl_source_paths(ip_dir)
        if _normalize_rtl_rel(ip_dir, rel).endswith(extensions)
    }
    if not current:
        return f"{label} source coverage cannot be proven because no matching DUT RTL source files are listed."
    raw_reported = report.get("rtl_files")
    if not isinstance(raw_reported, list):
        return f"{label} report does not list rtl_files for current filelist coverage."
    reported = {
        _normalize_rtl_rel(ip_dir, item)
        for item in raw_reported
        if str(item or "").strip().endswith(extensions)
    }
    missing = sorted(current - reported)
    if missing:
        sample = ", ".join(missing[:6])
        return f"{label} report rtl_files does not cover current DUT filelist source(s): {sample}."
    return ""


def _manifest_rtl_files_from_plan(plan: dict[str, Any]) -> set[str]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    owners = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    files: set[str] = set()
    for owner in owners:
        if not isinstance(owner, dict):
            continue
        rel = str(owner.get("file") or "").strip().replace("\\", "/")
        if rel.endswith((".v", ".sv")):
            files.add(rel)
    return files


def _reported_rtl_file_set(ip_dir: Path, report: dict[str, Any], key: str = "rtl_files") -> set[str]:
    raw = report.get(key)
    if not isinstance(raw, list):
        return set()
    return {
        _normalize_rtl_rel(ip_dir, item)
        for item in raw
        if str(item or "").strip().endswith((".v", ".sv", ".vh", ".svh"))
    }


def _strip_sv_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text or "", flags=re.S)
    return re.sub(r"//.*", "", text)


def _strip_sv_subprogram_blocks(text: str) -> str:
    clean = text or ""
    clean = re.sub(r"\bfunction\b.*?\bendfunction\b", " ", clean, flags=re.S)
    return re.sub(r"\btask\b.*?\bendtask\b", " ", clean, flags=re.S)


def _sv_module_bodies(text: str) -> dict[str, str]:
    clean = _strip_sv_comments(text)
    modules: dict[str, str] = {}
    pattern = re.compile(
        r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b(?P<body>.*?)(?=\bendmodule\b)",
        re.S,
    )
    for match in pattern.finditer(clean):
        modules[match.group(1)] = match.group("body")
    return modules


def _sv_declared_ports_from_module_body(body: str) -> set[str]:
    return set(_sv_declared_port_details_from_module_body(body))


def _sv_declared_port_details_from_module_body(body: str) -> dict[str, dict[str, str]]:
    clean = _strip_sv_comments(body)
    ports: dict[str, dict[str, str]] = {}
    header_match = re.search(r"\((?P<header>.*?)\)\s*;", clean, flags=re.S)
    current_direction = ""
    current_range = ""
    if header_match:
        for segment in header_match.group("header").split(","):
            range_match = re.search(r"\[[^\]]+\]", segment)
            if range_match:
                current_range = range_match.group(0)
            text = re.sub(r"\[[^\]]+\]", " ", segment)
            direction = re.search(r"\b(input|output|inout)\b", text)
            if direction:
                current_direction = direction.group(1)
                if not range_match:
                    current_range = ""
            if not current_direction:
                continue
            text = re.sub(r"\b(?:input|output|inout|wire|reg|logic|signed|unsigned)\b", " ", text)
            names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", text)
            if names:
                ports[names[-1]] = {"direction": current_direction, "range": current_range}
    decl_scan = clean[header_match.end():] if header_match else clean
    decl_scan = _strip_sv_subprogram_blocks(decl_scan)
    for direction, decl in re.findall(r"\b(input|output|inout)\b(?P<decl>[^;]+);", decl_scan):
        range_match = re.search(r"\[[^\]]+\]", decl)
        port_range = range_match.group(0) if range_match else ""
        text = re.sub(r"\[[^\]]+\]", " ", decl)
        text = re.sub(r"\b(?:wire|reg|logic|signed|unsigned)\b", " ", text)
        for segment in text.split(","):
            names = re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\b", segment)
            if names:
                ports[names[-1]] = {"direction": direction, "range": port_range}
    return {
        port: info
        for port, info in ports.items()
        if port not in {"input", "output", "inout"}
    }


def _eval_int_expr(expr: Any, params: dict[str, int]) -> int | None:
    text = str(expr or "").strip()
    if not text:
        return None

    def visit(node: ast.AST) -> int:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int):
            return int(node.value)
        if isinstance(node, ast.Name) and node.id in params:
            return int(params[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.FloorDiv, ast.Div)):
            left = visit(node.left)
            right = visit(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if right == 0:
                raise ValueError("division by zero")
            return left // right
        raise ValueError(f"unsupported width expression: {text}")

    try:
        return int(visit(ast.parse(text, mode="eval")))
    except Exception:
        return None


def _sv_int_literal_to_int(text: str) -> int | None:
    value = str(text or "").strip().replace("_", "")
    if not value:
        return None
    sized = re.fullmatch(r"\d+'s?([bBdDhHoO])([0-9a-fA-FxzXZ?]+)", value)
    if sized:
        base_ch = sized.group(1).lower()
        digits = sized.group(2).lower()
        if re.search(r"[xz?]", digits):
            return None
        base = {"b": 2, "d": 10, "h": 16, "o": 8}[base_ch]
        try:
            return int(digits, base)
        except ValueError:
            return None
    if re.fullmatch(r"\d+", value):
        return int(value)
    return None


def _sv_macro_int_defines(text: str) -> dict[str, int]:
    defines: dict[str, int] = {}
    clean = _strip_sv_comments(text)
    for match in re.finditer(r"^\s*`define\s+([A-Za-z_][A-Za-z0-9_]*)\s+([^\n]+)", clean, flags=re.M):
        name = match.group(1)
        raw_value = match.group(2).split(None, 1)[0]
        value = _sv_int_literal_to_int(raw_value)
        if value is not None:
            defines[name] = value
    return defines


def _replace_sv_macro_refs(expr: Any, defines: dict[str, int]) -> str:
    text = str(expr or "").strip()
    if not text or not defines:
        return text
    return re.sub(
        r"`([A-Za-z_][A-Za-z0-9_]*)",
        lambda match: str(defines.get(match.group(1), match.group(0))),
        text,
    )


def _sv_declared_parameter_defaults_from_module_body(body: str, defines: dict[str, int] | None = None) -> dict[str, int]:
    clean = _strip_sv_comments(body)
    header_match = re.search(r"\((?P<header>.*?)\)\s*;", clean, flags=re.S)
    header = clean[:header_match.end()] if header_match else clean
    raw: dict[str, str] = {}
    for match in re.finditer(
        r"\bparameter\b(?:\s+(?:integer|logic|wire|reg|signed|unsigned))*\s+"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^,\)\n;]+)",
        header,
    ):
        raw[match.group(1)] = match.group(2).strip()
    resolved: dict[str, int] = {}
    for _ in range(max(1, len(raw))):
        progressed = False
        for name, expr in raw.items():
            if name in resolved:
                continue
            value = _eval_int_expr(_replace_sv_macro_refs(expr, defines or {}), resolved)
            if value is not None:
                resolved[name] = value
                progressed = True
        if not progressed:
            break
    return resolved


def _sv_instance_named_port_maps(text: str) -> list[dict[str, Any]]:
    clean = _strip_sv_comments(text)
    keywords = {
        "assign",
        "always",
        "always_comb",
        "always_ff",
        "always_latch",
        "begin",
        "case",
        "casex",
        "casez",
        "class",
        "end",
        "endcase",
        "endclass",
        "endfunction",
        "endgenerate",
        "endmodule",
        "endpackage",
        "endtask",
        "enum",
        "for",
        "function",
        "generate",
        "if",
        "initial",
        "input",
        "inout",
        "interface",
        "localparam",
        "logic",
        "modport",
        "module",
        "output",
        "package",
        "parameter",
        "reg",
        "return",
        "struct",
        "task",
        "typedef",
        "union",
        "while",
        "wire",
    }
    instances: list[dict[str, Any]] = []
    pattern = re.compile(
        r"(?<![$A-Za-z0-9_])([A-Za-z_][A-Za-z0-9_]*)\s*(?:#\s*\((?:[^()]|\([^()]*\))*\)\s*)?"
        r"([A-Za-z_][A-Za-z0-9_]*)\s*\((?P<ports>[^;]*)\)\s*;",
        re.S,
    )
    for match in pattern.finditer(clean):
        module_name = match.group(1)
        if module_name.lower() in keywords:
            continue
        raw_ports = match.group("ports")
        named_ports: dict[str, str] = {}
        for port, expr in re.findall(r"\.([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)", raw_ports, re.S):
            named_ports[port] = " ".join(expr.split())
        instances.append({
            "module": module_name,
            "instance": match.group(2),
            "has_named_ports": bool(re.search(r"\.[A-Za-z_][A-Za-z0-9_]*\s*\(", raw_ports)),
            "ports": named_ports,
        })
    return instances


def _sv_instantiated_modules(text: str) -> set[str]:
    return {item["module"] for item in _sv_instance_named_port_maps(text)}


def _top_aliases(top: str) -> set[str]:
    return {name for name in {top, f"{top}_top", "top", "wrapper"} if name}


def _hierarchy_module_aliases(item: dict[str, Any]) -> set[str]:
    aliases: set[str] = set()
    for raw in (item.get("name"), Path(str(item.get("file") or "")).stem):
        name = str(raw or "").strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            aliases.add(name)
    return aliases


def _skip_hierarchy_module(item: dict[str, Any]) -> bool:
    rel = str(item.get("file") or "")
    name = str(item.get("name") or Path(rel).stem)
    if rel.endswith((".svh", ".vh")):
        return True
    return name.endswith("_pkg") or name.endswith("_types")


def _contract_aliases_for_module(name: str, file_name: str, top: str) -> set[str]:
    aliases: set[str] = set()
    for raw in (name, Path(str(file_name or "")).stem):
        text = str(raw or "").strip()
        if not text:
            continue
        aliases.add(text)
        for prefix in (f"{top}_", f"{top}_target_"):
            if top and text.startswith(prefix) and len(text) > len(prefix):
                aliases.add(text[len(prefix):])
        parts = [part for part in text.split("_") if part]
        if parts:
            aliases.add(parts[-1])
    return {alias for alias in aliases if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias)}


def _contract_alias_map(modules: list[dict[str, Any]], top: str) -> dict[str, str]:
    raw: dict[str, set[str]] = {}
    for item in modules:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or "").strip()
        file_name = str(item.get("file") or "").strip()
        if not name and not file_name:
            continue
        canonical = name or Path(file_name).stem
        for alias in _contract_aliases_for_module(canonical, file_name, top):
            raw.setdefault(alias.lower(), set()).add(canonical)
    return {
        alias: next(iter(names))
        for alias, names in raw.items()
        if len(names) == 1
    }


def _parse_endpoint(value: Any, alias_map: dict[str, str]) -> tuple[str, str]:
    text = str(value or "").strip()
    if not text:
        return "", ""
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)
    if not tokens:
        return "", ""
    if len(tokens) == 1:
        return "", tokens[0]
    module = alias_map.get(tokens[-2].lower(), tokens[-2])
    return module, tokens[-1]


def _signal_terms(value: Any) -> set[str]:
    text = str(value or "").strip()
    terms: set[str] = set()
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text):
        terms.add(token)
    if terms:
        terms.add(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text)[-1])
    return {term for term in terms if term.lower() not in EVIDENCE_STOPWORDS | REFERENCE_STOPWORDS}


def _normalize_expr(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or ""))


def _connection_contract_from_entry(
    raw: Any,
    *,
    source_ref: str,
    default_module: str,
    alias_map: dict[str, str],
) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []

    def contract(module: str, port: str, signal: Any, instance: Any = "") -> dict[str, Any]:
        resolved = alias_map.get(str(module or "").lower(), str(module or ""))
        return {
            "source_ref": source_ref,
            "module": resolved,
            "instance": str(instance or "").strip(),
            "port": str(port or "").strip(),
            "signal": str(signal or "").strip(),
            "signal_terms": sorted(_signal_terms(signal)),
            "machine_readable": bool(resolved and str(port or "").strip()),
            "raw": _short_text(raw, limit=240),
        }

    if isinstance(raw, dict):
        for map_key in ("ports", "port_map", "connections"):
            nested = _ci_get(raw, map_key)
            if isinstance(nested, dict):
                module = _ci_get(raw, "module", "child", "target_module", "sink_module") or default_module
                instance = _ci_get(raw, "instance", "inst")
                for port, signal in nested.items():
                    contracts.append(contract(str(module), str(port), signal, instance))
                return contracts
            if isinstance(nested, list):
                module = _ci_get(raw, "module", "child", "target_module", "sink_module") or default_module
                for idx, item in enumerate(nested):
                    contracts.extend(
                        _connection_contract_from_entry(
                            item,
                            source_ref=f"{source_ref}.{map_key}[{idx}]",
                            default_module=str(module),
                            alias_map=alias_map,
                        )
                    )
                return contracts

        explicit_module = _ci_get(
            raw,
            "module",
            "child",
            "target_module",
            "sink_module",
            "to_module",
            "dst_module",
            "destination_module",
        )
        module = explicit_module or default_module
        port = _ci_get(raw, "port", "child_port", "target_port", "sink_port", "to_port", "dst_port")
        signal = _ci_get(raw, "signal", "expr", "expression", "source_signal", "from_signal", "top_signal")
        instance = _ci_get(raw, "instance", "inst")
        endpoint = _ci_get(raw, "to", "sink", "target", "dst", "destination")
        if _present(endpoint):
            endpoint_module, endpoint_port = _parse_endpoint(endpoint, alias_map)
            module = module or endpoint_module
            port = port or endpoint_port
        source = _ci_get(raw, "from", "source", "src")
        if not _present(signal) and _present(source):
            _, signal_port = _parse_endpoint(source, alias_map)
            signal = signal_port or source
        if _present(port):
            contracts.append(contract(str(module or ""), str(port or ""), signal or "", instance))
            return contracts

        mapping_like = [
            (key, value)
            for key, value in raw.items()
            if str(key).lower()
            not in {
                "id",
                "name",
                "description",
                "note",
                "notes",
                "type",
                "rule",
                "module",
                "child",
                "target_module",
                "sink_module",
                "instance",
                "inst",
                "machine_readable",
                "source_ref",
                "ssot_ref",
            }
            and not isinstance(value, (dict, list))
        ]
        if mapping_like:
            for port_key, signal_value in mapping_like:
                contracts.append(contract(str(module or default_module), str(port_key), signal_value, instance))
            return contracts
        if _present(explicit_module):
            contracts.append(contract(str(module or ""), "", signal or "", instance))
            return contracts

    elif isinstance(raw, list):
        for idx, item in enumerate(raw):
            contracts.extend(
                _connection_contract_from_entry(
                    item,
                    source_ref=f"{source_ref}[{idx}]",
                    default_module=default_module,
                    alias_map=alias_map,
                )
            )
        return contracts

    if _present(raw):
        contracts.append({
            "source_ref": source_ref,
            "module": default_module,
            "instance": "",
            "port": "",
            "signal": "",
            "signal_terms": [],
            "machine_readable": False,
            "raw": _short_text(raw, limit=240),
        })
    return contracts


def _collect_connection_contracts(doc: dict[str, Any], modules: list[dict[str, Any]], top: str) -> list[dict[str, Any]]:
    alias_map = _contract_alias_map(modules, top)
    contracts: list[dict[str, Any]] = []
    for idx, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        raw_item = module.get("raw") if isinstance(module.get("raw"), dict) else {}
        if not _present(raw_item.get("connections")):
            continue
        name = str(module.get("name") or Path(str(module.get("file") or "")).stem)
        contracts.extend(
            _connection_contract_from_entry(
                raw_item.get("connections"),
                source_ref=f"sub_modules[{idx}].connections",
                default_module=name,
                alias_map=alias_map,
            )
        )

    integration = doc.get("integration") if isinstance(doc.get("integration"), dict) else {}
    for key in ("connections", "internal_connections", "port_connections", "wiring"):
        if key not in integration:
            continue
        contracts.extend(
            _connection_contract_from_entry(
                integration.get(key),
                source_ref=f"integration.{key}",
                default_module="",
                alias_map=alias_map,
            )
        )
    return contracts


def _infer_bundle_direction(item: dict[str, Any]) -> str:
    explicit = _ci_get(item, "direction", "dir")
    if _present(explicit):
        direction = str(explicit).strip().lower()
        return direction if direction in {"input", "output", "inout"} else ""
    text = f"{_ci_get(item, 'type', 'kind') or ''} {_ci_get(item, 'role') or ''}".lower()
    if "inout" in text:
        return "inout"
    if "input" in text:
        return "input"
    if "output" in text or "irq" in text:
        return "output"
    return ""


def _simple_width(value: Any) -> str:
    if not _present(value):
        return ""
    text = str(value).strip()
    if text in {"1", "1'b1", "1'b0"}:
        return "1"
    return text


def _top_io_contract(
    *,
    source_ref: str,
    name: str,
    direction: str = "",
    width: Any = "",
    aliases: list[str] | None = None,
    allow_constant: bool = False,
    constant_value: Any = None,
    allow_unused: bool = False,
) -> dict[str, Any]:
    alias_set = {str(name or "").strip()}
    alias_set.update(str(alias or "").strip() for alias in (aliases or []))
    alias_set = {alias for alias in alias_set if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", alias)}
    return {
        "source_ref": source_ref,
        "name": str(name or "").strip(),
        "aliases": sorted(alias_set),
        "direction": direction if direction in {"input", "output", "inout"} else "",
        "width": _simple_width(width),
        "allow_constant": bool(allow_constant),
        "constant_value": _short_text(constant_value) if _present(constant_value) else "",
        "allow_unused": bool(allow_unused),
    }


def _constant_allowed_from_io_item(item: dict[str, Any]) -> tuple[bool, Any]:
    constant_value = _ci_get(item, "constant", "tieoff", "fixed_value", "constant_value")
    allow_constant = _ci_get(item, "allow_constant", "constant_ok", "tieoff_ok")
    if _present(constant_value):
        return True, constant_value
    return bool(allow_constant), constant_value


def _unused_allowed_from_io_item(item: dict[str, Any]) -> bool:
    return bool(_ci_get(item, "allow_unused", "unused_ok", "reserved", "no_connect", "nc"))


def _collect_top_io_contracts(doc: dict[str, Any]) -> list[dict[str, Any]]:
    contracts: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()

    def add(contract: dict[str, Any]) -> None:
        name = str(contract.get("name") or "").strip()
        if not name:
            return
        key = (name, str(contract.get("direction") or ""), str(contract.get("width") or ""))
        if key in seen:
            return
        seen.add(key)
        contracts.append(contract)

    for idx, item in enumerate(_as_list(doc.get("clocks"))):
        if isinstance(item, dict):
            name = _ci_get(item, "name", "signal", "clock")
        else:
            name = item
        if _present(name):
            add(_top_io_contract(source_ref=f"clocks[{idx}]", name=str(name), direction="input", width=1))

    for idx, item in enumerate(_as_list(doc.get("resets"))):
        if isinstance(item, dict):
            name = _ci_get(item, "name", "signal", "reset")
        else:
            name = item
        if _present(name):
            add(_top_io_contract(source_ref=f"resets[{idx}]", name=str(name), direction="input", width=1))

    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for group_key, direction in (("clock_domains", "input"), ("resets", "input")):
        for group_idx, group in enumerate(_as_list(io.get(group_key))):
            if isinstance(group, dict):
                group_name = _ci_get(group, "name", "signal", "clock", "reset")
                ports = group.get("ports")
                if _present(group_name) and not ports:
                    add(_top_io_contract(source_ref=f"io_list.{group_key}[{group_idx}]", name=str(group_name), direction=direction, width=1))
                for port_idx, port in enumerate(_as_list(ports)):
                    if isinstance(port, dict):
                        name = _ci_get(port, "name", "signal", "port")
                        width = _ci_get(port, "width", "bits")
                        port_dir = _ci_get(port, "direction", "dir") or direction
                        allow_unused = _unused_allowed_from_io_item(port)
                    else:
                        name, width, port_dir = port, 1, direction
                        allow_unused = False
                    if _present(name):
                        add(_top_io_contract(source_ref=f"io_list.{group_key}[{group_idx}].ports[{port_idx}]", name=str(name), direction=str(port_dir).lower(), width=width or 1, allow_unused=allow_unused))
            elif _present(group):
                add(_top_io_contract(source_ref=f"io_list.{group_key}[{group_idx}]", name=str(group), direction=direction, width=1))

    for if_idx, iface in enumerate(_as_list(io.get("interfaces"))):
        if not isinstance(iface, dict):
            continue
        iface_name = str(_ci_get(iface, "name") or f"if_{if_idx}")
        iface_dir = _infer_bundle_direction(iface)
        iface_width = _ci_get(iface, "width", "data_width")
        if _present(iface.get("count")) and ("array" in str(_ci_get(iface, "type", "kind") or "").lower() or not _present(iface_width)):
            iface_width = iface.get("count")
        ports = _as_list(iface.get("ports")) if _present(iface.get("ports")) else []
        signals = _as_list(iface.get("signals")) if _present(iface.get("signals")) else []
        for port_idx, port in enumerate(ports):
            allow_constant = False
            constant_value = None
            allow_unused = False
            if isinstance(port, dict):
                name = _ci_get(port, "name", "signal", "port")
                width = _ci_get(port, "width", "bits") or iface_width
                port_dir = _ci_get(port, "direction", "dir") or iface_dir
                allow_constant, constant_value = _constant_allowed_from_io_item(port)
                allow_unused = _unused_allowed_from_io_item(port)
            else:
                name, width, port_dir = port, iface_width, iface_dir
            if _present(name):
                aliases = [f"{iface_name}_{name}"] if iface_name and str(name) != iface_name else []
                add(_top_io_contract(source_ref=f"io_list.interfaces[{if_idx}].ports[{port_idx}]", name=str(name), direction=str(port_dir).lower(), width=width, aliases=aliases, allow_constant=allow_constant, constant_value=constant_value, allow_unused=allow_unused))
        for sig_idx, signal in enumerate(signals):
            allow_constant = False
            constant_value = None
            allow_unused = False
            if isinstance(signal, dict):
                name = _ci_get(signal, "name", "signal", "port")
                width = _ci_get(signal, "width", "bits") or iface_width
                sig_dir = _ci_get(signal, "direction", "dir") or iface_dir
                allow_constant, constant_value = _constant_allowed_from_io_item(signal)
                allow_unused = _unused_allowed_from_io_item(signal)
            else:
                name, width, sig_dir = signal, iface_width, iface_dir
            if _present(name):
                aliases = [f"{iface_name}_{name}"] if iface_name and str(name) != iface_name else []
                add(_top_io_contract(source_ref=f"io_list.interfaces[{if_idx}].signals[{sig_idx}]", name=str(name), direction=str(sig_dir).lower(), width=width, aliases=aliases, allow_constant=allow_constant, constant_value=constant_value, allow_unused=allow_unused))
        if not ports and not signals and iface_dir and _present(iface_name):
            allow_constant, constant_value = _constant_allowed_from_io_item(iface)
            add(_top_io_contract(source_ref=f"io_list.interfaces[{if_idx}]", name=iface_name, direction=iface_dir, width=iface_width, allow_constant=allow_constant, constant_value=constant_value, allow_unused=_unused_allowed_from_io_item(iface)))
    return contracts


def _sv_identifier_terms(expr: str) -> list[str]:
    return re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", str(expr or ""))


def _symbolic_width_alias_matches(actual_range: str, expected_width: str) -> bool:
    expected = _normalize_expr(expected_width)
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", expected):
        return False
    expected_norm = expected.lower().replace("_", "")
    for symbol in _sv_identifier_terms(actual_range):
        symbol_norm = symbol.lower().replace("_", "")
        if symbol_norm and (expected_norm.endswith(symbol_norm) or symbol_norm.endswith(expected_norm)):
            return True
    return False


def _width_matches_contract(actual_range: str, expected_width: str, params: dict[str, int] | None = None) -> bool:
    width = str(expected_width or "").strip()
    if not width:
        return True
    actual = _normalize_expr(actual_range)
    expected = _normalize_expr(width)
    if expected in {"", "1"}:
        return actual in {"", "[0:0]"}
    if not actual:
        return False
    simple_range = re.fullmatch(r"\[(\d+):(\d+)\]", actual)
    simple_width = re.fullmatch(r"\d+", expected)
    if simple_range and simple_width:
        msb = int(simple_range.group(1))
        lsb = int(simple_range.group(2))
        return abs(msb - lsb) + 1 == int(expected)
    param_values = params or {}
    range_match = re.fullmatch(r"\[(.+):(.+)\]", actual)
    if range_match and simple_width:
        msb = _eval_int_expr(range_match.group(1), param_values)
        lsb = _eval_int_expr(range_match.group(2), param_values)
        if msb is not None and lsb is not None:
            return abs(msb - lsb) + 1 == int(expected)
    if range_match and not simple_width:
        if _symbolic_width_alias_matches(actual, expected):
            return True
    return expected in actual


def _is_constant_expr(expr: str) -> bool:
    norm = re.sub(r"\s+", "", str(expr or "")).lower().replace("_", "")
    norm = norm.strip("()")
    if norm in {"", "0", "1", "'0", "'1"}:
        return True
    if re.fullmatch(r"\d+'[s]?[bdho][0-9a-fxz?]+", norm):
        return True
    if re.fullmatch(r"\d+", norm):
        return True
    return False


def _owner_refs_claim_behavior(refs: list[Any]) -> bool:
    behavior_prefixes = (
        "function_model",
        "cycle_model",
        "registers",
        "memory",
        "interrupts",
        "fsm",
        "features",
        "dataflow",
        "error_handling",
        "security",
        "debug_observability",
    )
    return any(str(ref).startswith(behavior_prefixes) for ref in refs)


def _owner_refs_require_state(refs: list[Any]) -> bool:
    state_prefixes = (
        "function_model.state_variables",
        "function_model.transactions",
        "registers",
        "memory",
        "interrupts",
        "fsm",
        "error_handling",
        "debug_observability",
    )
    return any(str(ref).startswith(state_prefixes) for ref in refs)


def _module_logic_metrics(body: str) -> dict[str, Any]:
    clean = _strip_sv_comments(body)
    assignments = re.findall(r"\bassign\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*([^;]+);", clean)
    nonconstant_assigns = [
        lhs
        for lhs, expr in assignments
        if not lhs.startswith("ssot_") and not _is_constant_expr(expr)
    ]
    procedural_blocks = len(re.findall(r"\balways(?:_[a-zA-Z0-9_]+)?\b", clean))
    state_updates = len(re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\s*<=", clean))
    storage_decls = len(re.findall(r"\b(?:reg|logic)\b[^;]*\b[A-Za-z_][A-Za-z0-9_]*\b[^;]*;", clean))
    control_flow = len(re.findall(r"\b(?:if|case|for)\b", clean))
    instances = len(_sv_instance_named_port_maps(clean))
    return {
        "nonconstant_assigns": len(nonconstant_assigns),
        "procedural_blocks": procedural_blocks,
        "state_updates": state_updates,
        "storage_decls": storage_decls,
        "control_flow": control_flow,
        "instances": instances,
        "placeholder_tokens": bool(re.search(r"\b(?:TBD|TODO|FIXME|HACK)\b", clean, flags=re.I)),
    }


def _audit_owner_logic_structure(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    modules_by_source: dict[str, dict[str, str]] = {}
    ip_prefix = ip_dir.name + "/"
    for rel, text in sources.items():
        bodies = _sv_module_bodies(text)
        norm_rel = rel.replace("\\", "/")
        modules_by_source[norm_rel] = bodies
        if norm_rel.startswith(ip_prefix):
            modules_by_source[norm_rel[len(ip_prefix):]] = bodies
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    owners = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    top = str(plan.get("top") or ip_dir.name)
    issues: list[dict[str, Any]] = []
    checked = 0

    for owner in owners:
        if not isinstance(owner, dict):
            continue
        refs = owner.get("refs") if isinstance(owner.get("refs"), list) else []
        if not _owner_refs_claim_behavior(refs):
            continue
        name = str(owner.get("name") or "").strip()
        rel = str(owner.get("file") or "").strip()
        if str(owner.get("wiring_only") or "").lower() == "true":
            continue
        if rel.endswith((".svh", ".vh")) or name.endswith(("_pkg", "_types")):
            continue
        module_bodies = modules_by_source.get(rel, {})
        aliases = {name, Path(rel).stem} - {""}
        body = ""
        matched_module = ""
        for alias in aliases:
            if alias in module_bodies:
                body = module_bodies[alias]
                matched_module = alias
                break
        if not body:
            checked += 1
            issues.append({
                "module": name or Path(rel).stem,
                "file": rel,
                "issue": "Behavior-owner module is not declared in its owner file",
            })
            continue

        checked += 1
        metrics = _module_logic_metrics(body)
        has_logic = bool(
            metrics["nonconstant_assigns"]
            or metrics["procedural_blocks"]
            or metrics["state_updates"]
            or metrics["instances"]
        )
        if metrics["placeholder_tokens"]:
            issues.append({
                "module": matched_module,
                "file": rel,
                "issue": "Behavior-owner module still contains placeholder TODO/TBD markers",
                "metrics": metrics,
            })
        if not has_logic:
            issues.append({
                "module": matched_module,
                "file": rel,
                "issue": "Behavior-owner module has no nonconstant assign, procedural block, state update, or child instance",
                "metrics": metrics,
            })
        state_required = _owner_refs_require_state(refs)
        top_wrapper_with_children = matched_module in _top_aliases(top) and bool(metrics["instances"])
        if state_required and not top_wrapper_with_children and not (metrics["state_updates"] or metrics["procedural_blocks"]):
            issues.append({
                "module": matched_module,
                "file": rel,
                "issue": "State/register/memory/FSM owner lacks sequential/procedural update evidence",
                "metrics": metrics,
            })

    return {
        "status": "pass" if not issues else "fail",
        "checked": checked,
        "issues": issues[:128],
    }


def _audit_rtl_placeholder_free(ip_dir: Path) -> dict[str, Any]:
    # Strict markers: work-in-progress tokens that must never appear, even in
    # comments. These signal incomplete authoring regardless of context.
    strict_placeholder_re = re.compile(
        r"\b(?:TODO|TBD|FIXME|HACK|PLACEHOLDER|STUB|DUMMY)\b",
        flags=re.I,
    )
    # Soft markers: phrases that are legitimate when documenting an intentional
    # SSOT-driven omission (e.g. `// break detect: not implemented per SSOT`).
    # These must only fail when they appear in executable code, not in comments.
    code_only_placeholder_re = re.compile(
        r"not\s+implemented|implement\s+later",
        flags=re.I,
    )
    banned_reasons = [
        (re.compile(r"\b(?:package|endpackage)\b"), "RTL source uses package/endpackage instead of rtl/<ip>_param.vh include parameters"),
        (re.compile(r"\bimport\b|\b[A-Za-z_][A-Za-z0-9_]*::\*"), "RTL source uses import or package scope syntax"),
        (re.compile(r"\b(?:interface|endinterface|modport)\b"), "RTL source uses interface/modport syntax"),
        (re.compile(r"\b(?:function|endfunction|task|endtask)\b"), "RTL source uses function/task blocks"),
        (re.compile(r"\bfor\s*\("), "RTL source uses a for loop"),
        (re.compile(r"\bwhile\s*\("), "RTL source uses a while loop"),
        (re.compile(r"\b(?:typedef|enum)\b"), "RTL source uses SystemVerilog typedef/enum instead of localparam state encoding"),
        (re.compile(r"\balways_(?:ff|comb|latch)\b"), "RTL source uses SystemVerilog always_ff/always_comb/always_latch"),
        (re.compile(r"\b(?:bit|byte|int|longint|shortint)\b"), "RTL source uses SystemVerilog scalar integer types"),
    ]
    issues: list[dict[str, Any]] = []
    checked = 0
    for rel, path in _rtl_source_paths(ip_dir):
        if not rel.endswith((".v", ".sv", ".vh", ".svh")):
            continue
        checked += 1
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError as exc:
            issues.append({"file": rel, "issue": f"Cannot read RTL source: {exc}"})
            continue
        for line_no, line in enumerate(lines, start=1):
            policy_line = line.split("//", 1)[0]
            match = strict_placeholder_re.search(line)
            if match:
                issues.append({
                    "file": rel,
                    "line": line_no,
                    "token": match.group(0),
                    "issue": "RTL source contains a placeholder implementation marker",
                })
                if len(issues) >= 128:
                    break
            soft_match = code_only_placeholder_re.search(policy_line)
            if soft_match:
                issues.append({
                    "file": rel,
                    "line": line_no,
                    "token": soft_match.group(0),
                    "issue": "RTL source contains a placeholder implementation marker",
                })
                if len(issues) >= 128:
                    break
            for pattern, reason in banned_reasons:
                policy_match = pattern.search(policy_line)
                if policy_match:
                    issues.append({
                        "file": rel,
                        "line": line_no,
                        "token": policy_match.group(0),
                        "issue": reason,
                    })
                    if len(issues) >= 128:
                        break
            if len(issues) >= 128:
                break
        if len(issues) >= 128:
            break
    if checked == 0:
        issues.append({
            "issue": "No listed RTL source files were readable, so placeholder-free evidence cannot be checked",
        })
    return {
        "status": "pass" if not issues else "fail",
        "checked": checked,
        "issues": issues,
    }


def _rtl_behavior_tasks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        task
        for task in (plan.get("tasks") if isinstance(plan.get("tasks"), list) else [])
        if isinstance(task, dict)
        and bool(task.get("required", True))
        and str(task.get("category") or "").startswith(STATIC_EVIDENCE_CATEGORIES)
    ]


def _rtl_behavior_owners(plan: dict[str, Any]) -> list[dict[str, Any]]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    owners = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    result: list[dict[str, Any]] = []
    for owner in owners:
        if not isinstance(owner, dict):
            continue
        refs = owner.get("refs") if isinstance(owner.get("refs"), list) else []
        if not _owner_refs_claim_behavior(refs):
            continue
        if str(owner.get("wiring_only") or "").lower() == "true":
            continue
        if _skip_hierarchy_module(owner):
            continue
        result.append(owner)
    return result


def _rtl_depth_thresholds(plan: dict[str, Any]) -> dict[str, int]:
    behavior_tasks = _rtl_behavior_tasks(plan)
    behavior_owners = _rtl_behavior_owners(plan)
    manifest_files = _manifest_rtl_files_from_plan(plan)
    machine_connections = _machine_connection_contracts(plan)
    behavior_task_count = len(behavior_tasks)
    behavior_owner_count = len(behavior_owners)
    connection_count = len(machine_connections)
    thresholds = {
        "behavior_tasks": behavior_task_count,
        "behavior_owners": behavior_owner_count,
        "manifest_rtl_files": len(manifest_files),
        "machine_connection_contracts": connection_count,
        "min_depth_score": max(
            6,
            min(
                240,
                (behavior_task_count + 2) // 3
                + behavior_owner_count * 4
                + min(connection_count, 32) * 2,
            ),
        ),
        "min_logic_modules": max(1, min(behavior_owner_count or 1, max(1, (behavior_task_count + 15) // 16))),
    }
    target_scale = plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {}
    target_mapping = {
        "min_source_files": "min_source_files",
        "min_modules": "min_modules",
        "min_lines": "min_lines",
        "min_nonconstant_assigns": "min_nonconstant_assigns",
        "min_procedural_blocks": "min_procedural_blocks",
        "min_state_updates": "min_state_updates",
        "min_control_flow": "min_control_flow",
        "min_instances": "min_instances",
        "min_depth_score": "min_depth_score",
        "min_logic_modules": "min_logic_modules",
        "min_behavior_owner_logic_modules": "min_behavior_owner_logic_modules",
    }
    for source_key, threshold_key in target_mapping.items():
        parsed = _int_target(target_scale.get(source_key))
        if parsed is not None:
            thresholds[threshold_key] = max(int(thresholds.get(threshold_key) or 0), parsed)
    return thresholds


def _module_depth_score(metrics: dict[str, Any]) -> int:
    return (
        int(metrics.get("nonconstant_assigns") or 0)
        + int(metrics.get("procedural_blocks") or 0) * 3
        + int(metrics.get("state_updates") or 0) * 2
        + int(metrics.get("storage_decls") or 0)
        + int(metrics.get("control_flow") or 0)
        + int(metrics.get("instances") or 0) * 2
    )


def _rtl_reference_comparison(aggregate: dict[str, Any], reference_profile: Any) -> dict[str, Any] | None:
    if not isinstance(reference_profile, dict):
        return None
    target_candidate_summary = (
        reference_profile.get("target_candidate_summary")
        if isinstance(reference_profile.get("target_candidate_summary"), dict)
        else {}
    )
    reference_summary = target_candidate_summary or reference_profile.get("summary")
    if not isinstance(reference_summary, dict) or not reference_summary:
        return None
    reference_basis = (
        str(reference_profile.get("target_candidate_basis") or "target_candidate")
        if target_candidate_summary
        else "summary"
    )
    pairs = {
        "source_files": "file_count",
        "lines": "lines",
        "modules": "modules",
        "procedural_blocks": "always_blocks",
        "nonconstant_assigns": "nonconstant_assigns",
        "control_flow": "case_blocks",
        "instances": "instance_candidates",
        "state_updates": "state_updates",
    }
    ratios: dict[str, dict[str, Any]] = {}
    for current_key, reference_key in pairs.items():
        reference_value = int(reference_summary.get(reference_key) or 0)
        current_value = int(aggregate.get(current_key) or 0)
        if reference_value <= 0:
            continue
        ratios[current_key] = {
            "current": current_value,
            "reference": reference_value,
            "ratio": round(current_value / reference_value, 4),
        }
    if not ratios:
        return None
    return {
        "status": "diagnostic_only",
        "reference_profile": reference_profile.get("path") or reference_profile.get("label") or "rtl_reference_profile",
        "reference_basis": reference_basis,
        "calibration_only": True,
        "do_not_copy_reference_rtl": True,
        "ratios": ratios,
        "rule": "Reference comparison is a scale diagnostic only; it must not become a template or PASS gate.",
    }


def _reference_scale_gap_summary(plan: dict[str, Any]) -> dict[str, Any]:
    depth = plan.get("rtl_implementation_depth_evidence") if isinstance(plan.get("rtl_implementation_depth_evidence"), dict) else {}
    comparison = depth.get("reference_comparison") if isinstance(depth.get("reference_comparison"), dict) else {}
    ratios = comparison.get("ratios") if isinstance(comparison.get("ratios"), dict) else {}
    if not ratios:
        return {}
    metric_order = (
        "source_files",
        "modules",
        "lines",
        "instances",
        "procedural_blocks",
        "nonconstant_assigns",
        "control_flow",
        "state_updates",
    )
    metrics: dict[str, dict[str, Any]] = {}
    below: list[dict[str, Any]] = []
    for key in metric_order:
        item = ratios.get(key)
        if not isinstance(item, dict):
            continue
        current = int(item.get("current") or 0)
        reference = int(item.get("reference") or 0)
        ratio = float(item.get("ratio") or 0.0)
        row = {
            "current": current,
            "reference": reference,
            "ratio": ratio,
            "percent": round(ratio * 100.0, 1),
        }
        metrics[key] = row
        if reference > 0 and ratio < 1.0:
            below.append({"metric": key, **row})
    return {
        "schema_version": 1,
        "type": "rtl_reference_scale_gap",
        "status": "diagnostic_only",
        "calibration_only": True,
        "do_not_copy_reference_rtl": True,
        "reference_profile": comparison.get("reference_profile"),
        "reference_basis": comparison.get("reference_basis"),
        "metrics": metrics,
        "below_reference": sorted(below, key=lambda item: (float(item.get("ratio") or 0.0), str(item.get("metric") or ""))),
        "rule": (
            "This is a scale diagnostic and target-scale review aid. It does not close or fail PASS by itself; "
            "production PASS still requires human-approved quality_gates.rtl_gen.target_scale or an approved waiver."
        ),
    }


def _reference_target_scale_candidate(plan: dict[str, Any]) -> dict[str, Any]:
    reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
    suggested = reference_profile.get("suggested_ssot_target_scale")
    return suggested if isinstance(suggested, dict) and suggested else {}


def _audit_rtl_implementation_depth(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    profile = str(policy.get("rtl_quality_profile") or summary.get("rtl_quality_profile") or "standard")
    thresholds = _rtl_depth_thresholds(plan)
    sources = {
        rel: text
        for rel, text in _read_rtl_sources(ip_dir).items()
        if rel.endswith((".v", ".sv"))
    }
    aggregate = {
        "source_files": len(sources),
        "modules": 0,
        "lines": 0,
        "nonconstant_assigns": 0,
        "procedural_blocks": 0,
        "state_updates": 0,
        "storage_decls": 0,
        "control_flow": 0,
        "instances": 0,
        "depth_score": 0,
        "logic_modules": 0,
        "behavior_owner_logic_modules": 0,
    }
    module_rows: list[dict[str, Any]] = []
    metrics_by_module: dict[str, dict[str, Any]] = {}
    for rel, text in sources.items():
        for module_name, body in _sv_module_bodies(text).items():
            metrics = _module_logic_metrics(body)
            score = _module_depth_score(metrics)
            metrics_by_module[module_name] = metrics
            aggregate["modules"] += 1
            aggregate["lines"] += body.count("\n") + 1
            aggregate["depth_score"] += score
            for key in (
                "nonconstant_assigns",
                "procedural_blocks",
                "state_updates",
                "storage_decls",
                "control_flow",
                "instances",
            ):
                aggregate[key] += int(metrics.get(key) or 0)
            if score > 0:
                aggregate["logic_modules"] += 1
            module_rows.append({
                "module": module_name,
                "file": rel,
                "depth_score": score,
                "metrics": metrics,
            })

    behavior_owner_hits: set[str] = set()
    for owner in _rtl_behavior_owners(plan):
        name = str(owner.get("name") or "").strip()
        rel = str(owner.get("file") or "").strip()
        aliases = {name, Path(rel).stem} - {""}
        for alias in aliases:
            metrics = metrics_by_module.get(alias)
            if metrics and _module_depth_score(metrics) > 0:
                behavior_owner_hits.add(name or alias)
                break
    aggregate["behavior_owner_logic_modules"] = len(behavior_owner_hits)

    target_scale = plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {}
    issues: list[dict[str, Any]] = []
    if profile == "production" or target_scale:
        if not sources:
            issues.append({
                "issue": "No listed DUT RTL sources are available for production implementation-depth audit",
            })

        def require_metric(metric: str, threshold_key: str, issue: str) -> None:
            required = int(thresholds.get(threshold_key) or 0)
            if required <= 0:
                return
            actual = int(aggregate.get(metric) or 0)
            if actual < required:
                issues.append({
                    "issue": issue,
                    "actual": actual,
                    "required": required,
                    "source": "quality_gates.rtl_gen.target_scale" if threshold_key in target_scale else "ssot_derived_threshold",
                })

        require_metric(
            "source_files",
            "min_source_files",
            "Production RTL source-file count is below the SSOT-locked target scale",
        )
        require_metric(
            "modules",
            "min_modules",
            "Production RTL module count is below the SSOT-locked target scale",
        )
        require_metric(
            "lines",
            "min_lines",
            "Production RTL line count is below the SSOT-locked target scale",
        )
        require_metric(
            "nonconstant_assigns",
            "min_nonconstant_assigns",
            "Production RTL nonconstant assignment count is below the SSOT-locked target scale",
        )
        require_metric(
            "procedural_blocks",
            "min_procedural_blocks",
            "Production RTL procedural block count is below the SSOT-locked target scale",
        )
        require_metric(
            "state_updates",
            "min_state_updates",
            "Production RTL state-update count is below the SSOT-locked target scale",
        )
        require_metric(
            "control_flow",
            "min_control_flow",
            "Production RTL control-flow count is below the SSOT-locked target scale",
        )
        require_metric(
            "instances",
            "min_instances",
            "Production RTL instance count is below the SSOT-locked target scale",
        )
        if int(aggregate["depth_score"]) < thresholds["min_depth_score"]:
            issues.append({
                "issue": "Production RTL implementation depth score is below the SSOT-derived or target-scale threshold",
                "actual": aggregate["depth_score"],
                "required": thresholds["min_depth_score"],
                "source": "quality_gates.rtl_gen.target_scale"
                if _int_target(target_scale.get("min_depth_score")) is not None
                else "ssot_derived_threshold",
            })
        if int(aggregate["logic_modules"]) < thresholds["min_logic_modules"]:
            issues.append({
                "issue": "Too few RTL modules contain implementation structure for the SSOT behavior complexity",
                "actual": aggregate["logic_modules"],
                "required": thresholds["min_logic_modules"],
                "source": "quality_gates.rtl_gen.target_scale"
                if _int_target(target_scale.get("min_logic_modules")) is not None
                else "ssot_derived_threshold",
            })
        min_behavior_owner_logic_modules = int(
            thresholds.get("min_behavior_owner_logic_modules")
            or thresholds.get("min_logic_modules")
            or 0
        )
        if int(aggregate["behavior_owner_logic_modules"]) < min_behavior_owner_logic_modules:
            issues.append({
                "issue": "Too few SSOT behavior-owner modules contain implementation-depth evidence",
                "actual": aggregate["behavior_owner_logic_modules"],
                "required": min_behavior_owner_logic_modules,
                "source": "quality_gates.rtl_gen.target_scale"
                if _int_target(target_scale.get("min_behavior_owner_logic_modules")) is not None
                else "ssot_derived_threshold",
            })

    return {
        "status": "pass" if not issues else "fail",
        "profile": profile,
        "target_scale": target_scale,
        "thresholds": thresholds,
        "aggregate": aggregate,
        "reference_comparison": _rtl_reference_comparison(aggregate, plan.get("reference_profile")),
        "modules": sorted(module_rows, key=lambda item: (-int(item["depth_score"]), item["module"]))[:128],
        "issues": issues,
    }


def _audit_top_io_contracts(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    defines: dict[str, int] = {}
    for text in sources.values():
        defines.update(_sv_macro_int_defines(text))
    declarations: dict[str, str] = {}
    port_details_by_module: dict[str, dict[str, dict[str, str]]] = {}
    params_by_module: dict[str, dict[str, int]] = {}
    for rel, text in sources.items():
        for module_name, body in _sv_module_bodies(text).items():
            declarations[module_name] = rel
            port_details_by_module[module_name] = _sv_declared_port_details_from_module_body(body)
            params_by_module[module_name] = _sv_declared_parameter_defaults_from_module_body(body, defines)

    top = str(plan.get("top") or ip_dir.name)
    roots = sorted(_top_aliases(top) & set(declarations))
    contracts = plan.get("ssot_top_io_contracts") if isinstance(plan.get("ssot_top_io_contracts"), list) else []
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    profile = str(policy.get("rtl_quality_profile") or summary.get("rtl_quality_profile") or "standard")
    issues: list[dict[str, Any]] = []

    if profile == "production" and not contracts:
        issues.append({
            "issue": "Production-profile RTL has no machine-readable SSOT top IO contracts",
            "required_sources": ["clocks", "resets", "io_list"],
        })
    if contracts and not roots:
        issues.append({
            "module": top,
            "file": f"rtl/{top}.sv",
            "issue": "SSOT top module is not declared in listed RTL sources",
        })
        return {
            "status": "fail",
            "contracts": len(contracts),
            "roots": roots,
            "issues": issues,
        }

    top_ports: dict[str, dict[str, str]] = {}
    top_params: dict[str, int] = {}
    for root in roots:
        top_ports.update(port_details_by_module.get(root, {}))
        top_params.update(params_by_module.get(root, {}))
    lower_to_port = {name.lower(): name for name in top_ports}
    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        aliases = [str(item) for item in contract.get("aliases") or [] if str(item).strip()]
        if not aliases and contract.get("name"):
            aliases = [str(contract.get("name"))]
        matched_name = ""
        for alias in aliases:
            matched_name = lower_to_port.get(alias.lower(), "")
            if matched_name:
                break
        if not matched_name:
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": contract.get("name"),
                "aliases": aliases,
                "issue": "SSOT top IO port is missing from RTL top declaration",
            })
            continue
        actual = top_ports.get(matched_name, {})
        expected_direction = str(contract.get("direction") or "")
        actual_direction = str(actual.get("direction") or "")
        if expected_direction and actual_direction and expected_direction != actual_direction:
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": matched_name,
                "expected_direction": expected_direction,
                "actual_direction": actual_direction,
                "issue": "RTL top port direction does not match SSOT",
            })
        if not _width_matches_contract(str(actual.get("range") or ""), str(contract.get("width") or ""), top_params):
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": matched_name,
                "expected_width": contract.get("width"),
                "actual_range": actual.get("range") or "",
                "issue": "RTL top port width/range does not match SSOT",
            })

    return {
        "status": "pass" if not issues else "fail",
        "contracts": len(contracts),
        "roots": roots,
        "top_parameters": top_params,
        "declared_top_ports": sorted(top_ports),
        "issues": issues[:128],
    }


def _expr_references_signal(expr: str, signal: str) -> bool:
    return signal in _signal_terms(expr) or _normalize_expr(expr) == _normalize_expr(signal)


def _assignment_exprs_for_lhs(body: str, port: str) -> list[dict[str, Any]]:
    clean = _strip_sv_comments(body)
    escaped = re.escape(port)
    records: list[dict[str, Any]] = []
    lhs_pattern = rf"(?:\{{[^;}}]*\b{escaped}\b[^;}}]*\}}|\b{escaped}\b\s*(?:\[[^\]]+\])?)"
    for match in re.finditer(rf"\bassign\s+{lhs_pattern}\s*=\s*([^;]+);", clean, re.S):
        expr = " ".join(match.group(1).split())
        records.append({"kind": "continuous_assign", "expr": expr, "constant": _is_constant_expr(expr)})
    for match in re.finditer(rf"{lhs_pattern}\s*(?:<=|=)\s*([^;]+);", clean, re.S):
        prefix = clean[max(0, match.start() - 12):match.start()]
        if re.search(r"\bassign\s+$", prefix):
            continue
        expr = " ".join(match.group(1).split())
        context = clean[max(0, match.start() - 240):match.start()]
        records.append({
            "kind": "procedural_assign",
            "expr": expr,
            "constant": _is_constant_expr(expr),
            "control_context": bool(re.search(r"\b(?:if|else|case)\b", context)),
        })
    return records


def _child_output_drive_records(
    body: str,
    port: str,
    port_details_by_module: dict[str, dict[str, dict[str, str]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for instance in _sv_instance_named_port_maps(body):
        module = str(instance.get("module") or "")
        child_ports = port_details_by_module.get(module, {})
        for child_port, expr in (instance.get("ports") or {}).items():
            if not _expr_references_signal(str(expr), port):
                continue
            direction = str((child_ports.get(child_port) or {}).get("direction") or "")
            records.append({
                "kind": "child_output_connection",
                "module": module,
                "instance": instance.get("instance") or "",
                "child_port": child_port,
                "direction": direction,
                "accepted": direction in {"output", "inout"},
            })
    return records


def _sv_implementation_body(body: str) -> str:
    clean = _strip_sv_comments(body)
    header_match = re.search(r"\((?P<header>.*?)\)\s*;", clean, flags=re.S)
    if header_match:
        clean = clean[header_match.end():]
    return re.sub(r"\b(?:input|output|inout)\b[^;]*;", "", clean)


def _rhs_use_records_for_signal(body: str, signal: str) -> list[dict[str, Any]]:
    clean = _sv_implementation_body(body)
    records: list[dict[str, Any]] = []
    for match in re.finditer(r"\bassign\s+([A-Za-z_][A-Za-z0-9_]*(?:\s*\[[^\]]+\])?)\s*=\s*([^;]+);", clean, re.S):
        expr = " ".join(match.group(2).split())
        if _expr_references_signal(expr, signal):
            records.append({"kind": "continuous_rhs", "lhs": match.group(1).strip(), "expr": expr})
    for match in re.finditer(r"\b([A-Za-z_][A-Za-z0-9_]*(?:\s*\[[^\]]+\])?)\s*(?:<=|=)\s*([^;]+);", clean, re.S):
        prefix = clean[max(0, match.start() - 12):match.start()]
        if re.search(r"\bassign\s+$", prefix):
            continue
        expr = " ".join(match.group(2).split())
        if _expr_references_signal(expr, signal):
            records.append({"kind": "procedural_rhs", "lhs": match.group(1).strip(), "expr": expr})
    for keyword in ("if", "case", "for", "while"):
        for match in re.finditer(rf"\b{keyword}\s*\(([^)]*)\)", clean, re.S):
            expr = " ".join(match.group(1).split())
            if _expr_references_signal(expr, signal):
                records.append({"kind": f"{keyword}_condition", "expr": expr})
    return records


def _child_input_use_records(
    body: str,
    port: str,
    port_details_by_module: dict[str, dict[str, dict[str, str]]],
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for instance in _sv_instance_named_port_maps(body):
        module = str(instance.get("module") or "")
        child_ports = port_details_by_module.get(module, {})
        for child_port, expr in (instance.get("ports") or {}).items():
            if not _expr_references_signal(str(expr), port):
                continue
            direction = str((child_ports.get(child_port) or {}).get("direction") or "")
            records.append({
                "kind": "child_input_connection",
                "module": module,
                "instance": instance.get("instance") or "",
                "child_port": child_port,
                "direction": direction,
                "accepted": direction in {"input", "inout"},
            })
    return records


def _audit_top_output_drives(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    module_bodies: dict[str, str] = {}
    port_details_by_module: dict[str, dict[str, dict[str, str]]] = {}
    for text in sources.values():
        for module_name, body in _sv_module_bodies(text).items():
            module_bodies[module_name] = body
            port_details_by_module[module_name] = _sv_declared_port_details_from_module_body(body)

    top = str(plan.get("top") or ip_dir.name)
    roots = sorted(_top_aliases(top) & set(module_bodies))
    contracts = plan.get("ssot_top_io_contracts") if isinstance(plan.get("ssot_top_io_contracts"), list) else []
    output_contracts = [
        contract
        for contract in contracts
        if isinstance(contract, dict) and str(contract.get("direction") or "") in {"output", "inout"}
    ]
    issues: list[dict[str, Any]] = []
    checked = 0
    driven = 0

    if output_contracts and not roots:
        issues.append({
            "module": top,
            "issue": "SSOT top module is not declared, so output drive evidence cannot be checked",
        })
        return {"status": "fail", "checked": 0, "driven": 0, "roots": roots, "issues": issues}

    top_ports: dict[str, dict[str, str]] = {}
    for root in roots:
        top_ports.update(port_details_by_module.get(root, {}))
    lower_to_port = {name.lower(): name for name in top_ports}

    for contract in output_contracts:
        aliases = [str(item) for item in contract.get("aliases") or [] if str(item).strip()]
        if not aliases and contract.get("name"):
            aliases = [str(contract.get("name"))]
        port = ""
        for alias in aliases:
            port = lower_to_port.get(alias.lower(), "")
            if port:
                break
        if not port:
            continue
        checked += 1
        allow_constant = bool(contract.get("allow_constant"))
        assignment_records: list[dict[str, Any]] = []
        child_records: list[dict[str, Any]] = []
        for root in roots:
            body = module_bodies.get(root, "")
            assignment_records.extend(_assignment_exprs_for_lhs(body, port))
            child_records.extend(_child_output_drive_records(body, port, port_details_by_module))
        nonconstant_assigns = [record for record in assignment_records if not record.get("constant")]
        constant_assigns = [record for record in assignment_records if record.get("constant")]
        controlled_constant_values = {
            _normalize_expr(str(record.get("expr") or ""))
            for record in assignment_records
            if record.get("kind") == "procedural_assign" and record.get("constant") and record.get("control_context")
        }
        accepted_child = [record for record in child_records if record.get("accepted")]
        if nonconstant_assigns or accepted_child or len(controlled_constant_values) > 1:
            driven += 1
            continue
        if constant_assigns and allow_constant:
            driven += 1
            continue
        if constant_assigns:
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": port,
                "issue": "RTL top output is driven only by a constant without explicit SSOT tieoff allowance",
                "assignments": constant_assigns[:4],
            })
            continue
        rejected_child = [record for record in child_records if not record.get("accepted")]
        if rejected_child:
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": port,
                "issue": "RTL top output is connected only to child ports without declared output/inout direction",
                "connections": rejected_child[:4],
            })
            continue
        issues.append({
            "source_ref": contract.get("source_ref"),
            "port": port,
            "issue": "RTL top output has no nonconstant assignment or declared child-output drive evidence",
        })

    return {
        "status": "pass" if not issues else "fail",
        "checked": checked,
        "driven": driven,
        "roots": roots,
        "issues": issues[:128],
    }


def _is_clock_reset_contract(contract: dict[str, Any]) -> bool:
    source_ref = str(contract.get("source_ref") or "")
    if source_ref.startswith(("clocks[", "resets[", "io_list.clock_domains", "io_list.resets")):
        return True
    name = str(contract.get("name") or "").lower()
    return bool(re.fullmatch(r"(?:clk|clock|rst|reset|rst_n|reset_n|aresetn|aclk)", name))


def _audit_top_input_consumption(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    module_bodies: dict[str, str] = {}
    port_details_by_module: dict[str, dict[str, dict[str, str]]] = {}
    for text in sources.values():
        for module_name, body in _sv_module_bodies(text).items():
            module_bodies[module_name] = body
            port_details_by_module[module_name] = _sv_declared_port_details_from_module_body(body)

    top = str(plan.get("top") or ip_dir.name)
    roots = sorted(_top_aliases(top) & set(module_bodies))
    contracts = plan.get("ssot_top_io_contracts") if isinstance(plan.get("ssot_top_io_contracts"), list) else []
    input_contracts = [
        contract
        for contract in contracts
        if (
            isinstance(contract, dict)
            and str(contract.get("direction") or "") in {"input", "inout"}
            and not _is_clock_reset_contract(contract)
            and not bool(contract.get("allow_unused"))
        )
    ]
    issues: list[dict[str, Any]] = []
    checked = 0
    consumed = 0

    if input_contracts and not roots:
        issues.append({
            "module": top,
            "issue": "SSOT top module is not declared, so input consumption evidence cannot be checked",
        })
        return {"status": "fail", "checked": 0, "consumed": 0, "roots": roots, "issues": issues}

    top_ports: dict[str, dict[str, str]] = {}
    for root in roots:
        top_ports.update(port_details_by_module.get(root, {}))
    lower_to_port = {name.lower(): name for name in top_ports}

    for contract in input_contracts:
        aliases = [str(item) for item in contract.get("aliases") or [] if str(item).strip()]
        if not aliases and contract.get("name"):
            aliases = [str(contract.get("name"))]
        port = ""
        for alias in aliases:
            port = lower_to_port.get(alias.lower(), "")
            if port:
                break
        if not port:
            continue
        checked += 1
        rhs_records: list[dict[str, Any]] = []
        child_records: list[dict[str, Any]] = []
        for root in roots:
            body = module_bodies.get(root, "")
            rhs_records.extend(_rhs_use_records_for_signal(body, port))
            child_records.extend(_child_input_use_records(body, port, port_details_by_module))
        accepted_child = [record for record in child_records if record.get("accepted")]
        if rhs_records or accepted_child:
            consumed += 1
            continue
        rejected_child = [record for record in child_records if not record.get("accepted")]
        if rejected_child:
            issues.append({
                "source_ref": contract.get("source_ref"),
                "port": port,
                "issue": "RTL top input is connected only to child ports without declared input/inout direction",
                "connections": rejected_child[:4],
            })
            continue
        issues.append({
            "source_ref": contract.get("source_ref"),
            "port": port,
            "issue": "RTL top input has no RHS/control use or declared child-input consumption evidence",
        })

    return {
        "status": "pass" if not issues else "fail",
        "checked": checked,
        "consumed": consumed,
        "roots": roots,
        "issues": issues[:128],
    }


def _contract_allows_constant_tieoff(contracts: list[Any], module: str, port: str, expr: str) -> bool:
    expr_norm = _normalize_expr(expr)
    for item in contracts:
        if not isinstance(item, dict):
            continue
        if str(item.get("module") or "") != module or str(item.get("port") or "") != port:
            continue
        signal = str(item.get("signal") or "")
        if _is_constant_expr(signal) and _normalize_expr(signal) == expr_norm:
            return True
        raw = str(item.get("raw") or "").lower()
        if any(token in raw for token in ("tieoff", "tie-off", "constant", "fixed", "reserved")):
            return True
    return False


def _contract_allows_unconsumed_output(contracts: list[Any], module: str, port: str) -> bool:
    for item in contracts:
        if not isinstance(item, dict):
            continue
        if str(item.get("module") or "") != module or str(item.get("port") or "") != port:
            continue
        signal = str(item.get("signal") or "").strip().lower()
        raw = str(item.get("raw") or "").lower()
        if signal in {"unused", "reserved", "nc", "no_connect", "unconnected"}:
            return True
        if any(token in raw for token in ("unused", "reserved", "no_connect", "unconnected", "waive")):
            return True
    return False


def _manifest_child_module_aliases(plan: dict[str, Any]) -> set[str]:
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    modules = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    top = str(plan.get("top") or "")
    top_names = _top_aliases(top)
    child_modules: set[str] = set()
    for item in modules:
        if not isinstance(item, dict) or _skip_hierarchy_module(item):
            continue
        aliases = _hierarchy_module_aliases(item)
        if aliases & top_names:
            continue
        child_modules.update(aliases)
    return child_modules


def _signal_consumed_by_child_input(
    instances: list[dict[str, Any]],
    signal: str,
    port_details_by_module: dict[str, dict[str, dict[str, str]]],
    *,
    producer_instance: str,
    producer_port: str,
) -> bool:
    for instance in instances:
        module = str(instance.get("module") or "")
        child_ports = port_details_by_module.get(module, {})
        for child_port, expr in (instance.get("ports") or {}).items():
            if str(instance.get("instance") or "") == producer_instance and child_port == producer_port:
                continue
            if not _expr_references_signal(str(expr), signal):
                continue
            direction = str((child_ports.get(child_port) or {}).get("direction") or "")
            if direction in {"input", "inout"}:
                return True
    return False


def _audit_manifest_signal_flow(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    declarations: set[str] = set()
    graph: dict[str, set[str]] = {}
    instances_by_parent: dict[str, list[dict[str, Any]]] = {}
    bodies_by_module: dict[str, str] = {}
    port_details_by_module: dict[str, dict[str, dict[str, str]]] = {}
    for text in sources.values():
        for module_name, body in _sv_module_bodies(text).items():
            declarations.add(module_name)
            bodies_by_module[module_name] = body
            port_details_by_module[module_name] = _sv_declared_port_details_from_module_body(body)
            instances = _sv_instance_named_port_maps(body)
            instances_by_parent[module_name] = instances
            graph[module_name] = {str(instance.get("module") or "") for instance in instances if instance.get("module")}

    top = str(plan.get("top") or ip_dir.name)
    roots = sorted(_top_aliases(top) & declarations)
    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        for child in graph.get(current, set()):
            if child in declarations and child not in reachable:
                stack.append(child)

    manifest_children = _manifest_child_module_aliases(plan)
    contracts = plan.get("ssot_connection_contracts") if isinstance(plan.get("ssot_connection_contracts"), list) else []
    issues: list[dict[str, Any]] = []
    checked_inputs = 0
    checked_outputs = 0

    if manifest_children and not roots:
        issues.append({
            "module": top,
            "issue": "SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        })
        return {
            "status": "fail",
            "roots": roots,
            "reachable_modules": sorted(reachable),
            "checked_inputs": checked_inputs,
            "checked_outputs": checked_outputs,
            "issues": issues,
        }

    for parent in reachable:
        parent_body = bodies_by_module.get(parent, "")
        parent_ports = port_details_by_module.get(parent, {})
        instances = instances_by_parent.get(parent, [])
        for instance in instances:
            module = str(instance.get("module") or "")
            if module not in manifest_children or module not in reachable:
                continue
            child_ports = port_details_by_module.get(module, {})
            for child_port, expr_raw in (instance.get("ports") or {}).items():
                expr = str(expr_raw or "").strip()
                if not expr:
                    continue
                details = child_ports.get(child_port)
                if not details:
                    issues.append({
                        "parent": parent,
                        "module": module,
                        "instance": instance.get("instance") or "",
                        "port": child_port,
                        "expr": expr,
                        "issue": "Named port-map entry targets a port not declared by the child module",
                    })
                    continue
                direction = str(details.get("direction") or "")
                if direction in {"input", "inout"}:
                    checked_inputs += 1
                    if _is_constant_expr(expr) and not _contract_allows_constant_tieoff(contracts, module, child_port, expr):
                        issues.append({
                            "parent": parent,
                            "module": module,
                            "instance": instance.get("instance") or "",
                            "port": child_port,
                            "expr": expr,
                            "issue": "Manifest child input is tied to a constant without explicit SSOT tieoff allowance",
                        })
                if direction in {"output", "inout"}:
                    checked_outputs += 1
                    if _is_constant_expr(expr):
                        issues.append({
                            "parent": parent,
                            "module": module,
                            "instance": instance.get("instance") or "",
                            "port": child_port,
                            "expr": expr,
                            "issue": "Manifest child output is connected to a constant expression",
                        })
                        continue
                    signal_terms = sorted(_signal_terms(expr))
                    consumed = False
                    for signal in signal_terms:
                        if signal in parent_ports and str(parent_ports.get(signal, {}).get("direction") or "") in {"output", "inout"}:
                            consumed = True
                            break
                        if _rhs_use_records_for_signal(parent_body, signal):
                            consumed = True
                            break
                        if _signal_consumed_by_child_input(
                            instances,
                            signal,
                            port_details_by_module,
                            producer_instance=str(instance.get("instance") or ""),
                            producer_port=child_port,
                        ):
                            consumed = True
                            break
                    if not consumed and not _contract_allows_unconsumed_output(contracts, module, child_port):
                        issues.append({
                            "parent": parent,
                            "module": module,
                            "instance": instance.get("instance") or "",
                            "port": child_port,
                            "expr": expr,
                            "issue": "Manifest child output does not feed a top output, parent RTL logic, or another child input/inout",
                        })

    if manifest_children and not (checked_inputs or checked_outputs):
        issues.append({
            "module": top,
            "issue": "No reachable manifest child port flow evidence was found",
        })

    return {
        "status": "pass" if not issues else "fail",
        "roots": roots,
        "reachable_modules": sorted(reachable),
        "checked_inputs": checked_inputs,
        "checked_outputs": checked_outputs,
        "issues": issues[:128],
    }


def _audit_manifest_hierarchy(ip_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    sources = _read_rtl_sources(ip_dir)
    declarations: dict[str, str] = {}
    ports_by_module: dict[str, set[str]] = {}
    tokens_by_module: dict[str, set[str]] = {}
    graph: dict[str, set[str]] = {}
    instances_by_parent: dict[str, list[dict[str, Any]]] = {}
    for rel, text in sources.items():
        for module_name, body in _sv_module_bodies(text).items():
            declarations[module_name] = rel
            ports_by_module[module_name] = _sv_declared_ports_from_module_body(body)
            tokens_by_module[module_name] = _rtl_token_set(body)
            instances = _sv_instance_named_port_maps(body)
            instances_by_parent[module_name] = instances
            graph[module_name] = {str(instance.get("module") or "") for instance in instances if instance.get("module")}

    top = str(plan.get("top") or ip_dir.name)
    roots = sorted(_top_aliases(top) & set(declarations))
    reachable: set[str] = set()
    stack = list(roots)
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        for child in graph.get(current, set()):
            if child in declarations and child not in reachable:
                stack.append(child)

    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    modules = summary.get("owner_modules") if isinstance(summary.get("owner_modules"), list) else []
    policy = plan.get("policy") if isinstance(plan.get("policy"), dict) else {}
    profile = str(policy.get("rtl_quality_profile") or summary.get("rtl_quality_profile") or "standard")
    contracts = plan.get("ssot_connection_contracts") if isinstance(plan.get("ssot_connection_contracts"), list) else []
    issues: list[dict[str, Any]] = []
    if modules and not roots:
        issues.append({
            "module": top,
            "file": f"rtl/{top}.sv",
            "issue": "SSOT top module is not declared in listed RTL sources",
        })

    top_names = _top_aliases(top)
    port_issues: list[dict[str, Any]] = []
    connection_contract_issues: list[dict[str, Any]] = []
    reachable_instances = [
        instance
        for parent in reachable
        for instance in instances_by_parent.get(parent, [])
        if isinstance(instance, dict)
    ]
    manifest_child_modules: set[str] = set()
    for item in modules:
        if not isinstance(item, dict) or _skip_hierarchy_module(item):
            continue
        aliases = _hierarchy_module_aliases(item)
        if aliases & top_names:
            continue
        manifest_child_modules.update(aliases)
        declared = sorted(aliases & set(declarations))
        rel = str(item.get("file") or "")
        if not declared:
            issues.append({
                "module": str(item.get("name") or Path(rel).stem),
                "file": rel,
                "issue": "SSOT manifest child module is not declared in listed RTL sources",
            })
            continue
        if not (set(declared) & reachable):
            issues.append({
                "module": declared[0],
                "file": rel or declarations.get(declared[0], ""),
                "issue": "SSOT manifest child module is declared but not reachable from the top RTL hierarchy",
            })
            continue

        declared_ports = sorted(set().union(*(ports_by_module.get(name, set()) for name in declared)))
        if not declared_ports:
            continue
        child_instances = [
            instance
            for instance in reachable_instances
            if str(instance.get("module") or "") in set(declared)
        ]
        named_instances = [instance for instance in child_instances if instance.get("has_named_ports")]
        if not named_instances:
            port_issues.append({
                "module": declared[0],
                "file": rel or declarations.get(declared[0], ""),
                "issue": "Reachable child module has no machine-checkable named port map",
                "required_ports": declared_ports,
            })
            continue
        connected = {
            port
            for instance in named_instances
            for port, expr in (instance.get("ports") or {}).items()
            if str(expr).strip()
        }
        empty_ports = sorted({
            port
            for instance in named_instances
            for port, expr in (instance.get("ports") or {}).items()
            if not str(expr).strip()
        })
        missing_ports = sorted(set(declared_ports) - connected)
        if missing_ports or empty_ports:
            port_issues.append({
                "module": declared[0],
                "file": rel or declarations.get(declared[0], ""),
                "issue": "Reachable child instance has missing or empty named port connections",
                "missing_ports": missing_ports,
                "empty_ports": empty_ports,
            })

    machine_contracts = [item for item in contracts if isinstance(item, dict) and item.get("machine_readable")]
    if profile == "production" and manifest_child_modules and not machine_contracts:
        connection_contract_issues.append({
            "issue": "Production-profile multi-module RTL has no machine-readable SSOT connection contracts",
            "required_sources": ["integration.connections", "sub_modules[].connections"],
        })

    for contract in contracts:
        if not isinstance(contract, dict):
            continue
        if not contract.get("machine_readable"):
            connection_contract_issues.append({
                "source_ref": contract.get("source_ref"),
                "module": contract.get("module"),
                "issue": "SSOT connection contract is not machine-readable; use module/port/signal fields or a port_map mapping",
                "raw": contract.get("raw"),
            })
            continue
        module = str(contract.get("module") or "")
        port = str(contract.get("port") or "")
        if module in top_names:
            continue
        if module not in declarations:
            connection_contract_issues.append({
                "source_ref": contract.get("source_ref"),
                "module": module,
                "port": port,
                "issue": "SSOT connection contract targets a module not declared in RTL",
            })
            continue
        if module not in reachable:
            connection_contract_issues.append({
                "source_ref": contract.get("source_ref"),
                "module": module,
                "port": port,
                "issue": "SSOT connection contract targets a module not reachable from top RTL hierarchy",
            })
            continue
        matching_instances = [
            instance
            for instance in reachable_instances
            if str(instance.get("module") or "") == module
            and (not contract.get("instance") or str(instance.get("instance") or "") == str(contract.get("instance")))
        ]
        if not matching_instances:
            connection_contract_issues.append({
                "source_ref": contract.get("source_ref"),
                "module": module,
                "instance": contract.get("instance"),
                "port": port,
                "issue": "SSOT connection contract has no matching reachable RTL instance",
            })
            continue
        port_exprs = [
            str((instance.get("ports") or {}).get(port) or "").strip()
            for instance in matching_instances
            if isinstance(instance.get("ports"), dict)
        ]
        non_empty_exprs = [expr for expr in port_exprs if expr]
        if not non_empty_exprs:
            declared_ports = ports_by_module.get(module, set())
            module_tokens = tokens_by_module.get(module, set())
            expected_signal = str(contract.get("signal") or "").strip()
            expected_terms = set(contract.get("signal_terms") or [])
            # Integration contracts can describe a parent/wiring module's
            # internal connection point rather than a child instance port, for
            # example from child.data_out_reg -> top_int.gpio_out_drv.  Accept
            # that shape only when the target is not a declared port and both
            # the target connection point and expected signal are live RTL
            # tokens inside the module body.  Declared but unconnected ports
            # still fail above as real hierarchy wiring issues.
            if (
                port
                and port not in declared_ports
                and port in module_tokens
                and (
                    not expected_signal
                    or expected_signal in module_tokens
                    or bool(expected_terms & module_tokens)
                )
            ):
                continue
            connection_contract_issues.append({
                "source_ref": contract.get("source_ref"),
                "module": module,
                "port": port,
                "issue": "SSOT connection contract port is not connected by the RTL named port map",
            })
            continue
        expected_signal = str(contract.get("signal") or "").strip()
        expected_terms = set(contract.get("signal_terms") or [])
        if expected_signal:
            matched = False
            for expr in non_empty_exprs:
                expr_terms = _signal_terms(expr)
                if _normalize_expr(expr) == _normalize_expr(expected_signal) or (expected_terms and expected_terms & expr_terms):
                    matched = True
                    break
            if not matched:
                connection_contract_issues.append({
                    "source_ref": contract.get("source_ref"),
                    "module": module,
                    "port": port,
                    "expected_signal": expected_signal,
                    "rtl_exprs": non_empty_exprs,
                    "issue": "RTL named port-map expression does not match SSOT connection signal terms",
                })

    return {
        "status": "pass" if not issues else "fail",
        "port_connection_status": "pass" if not port_issues else "fail",
        "connection_contract_status": "pass" if not connection_contract_issues else "fail",
        "connection_contract_count": len(contracts),
        "sources": sorted(sources),
        "roots": roots,
        "declared_modules": sorted(declarations),
        "reachable_modules": sorted(reachable),
        "graph": {key: sorted(value) for key, value in sorted(graph.items())},
        "issues": issues[:128],
        "port_connection_issues": port_issues[:128],
        "connection_contract_issues": connection_contract_issues[:128],
    }


def _rtl_token_set(text: str) -> set[str]:
    clean = re.sub(r"/\*.*?\*/", "", text or "", flags=re.S)
    clean = re.sub(r"//.*", "", clean)
    tokens: set[str] = set()
    for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", clean):
        tokens.add(token)
        parts = [part for part in token.split("_") if part]
        tokens.update(parts)
        for idx in range(len(parts)):
            suffix = "_".join(parts[idx:])
            if suffix:
                tokens.add(suffix)
            for end in range(idx + 2, len(parts) + 1):
                phrase = "_".join(parts[idx:end])
                if phrase:
                    tokens.add(phrase)
    return tokens


def _source_tokens_for_owner(source_tokens: dict[str, set[str]], owner_file: str) -> tuple[set[str], str]:
    owner = str(owner_file or "").strip()
    if not owner:
        merged: set[str] = set()
        for tokens in source_tokens.values():
            merged.update(tokens)
        return merged, "all_sources_without_owner"
    if owner in source_tokens:
        return source_tokens[owner], owner
    for rel, tokens in source_tokens.items():
        if rel.endswith("/" + owner) or owner.endswith("/" + rel) or Path(rel).name == Path(owner).name:
            return tokens, rel
    return set(), owner


def _required_static_match_count(category: str, terms: list[str]) -> int:
    if not terms:
        return 0
    if len(terms) == 1:
        return 1
    rich_categories = (
        "workflow_todo.rtl_gen",
        "function_model.",
        "cycle_model.handshake_rules",
        "cycle_model.pipeline",
        "cycle_model.backpressure",
        "cycle_model.ordering",
        "fsm.transition",
        "dataflow.",
        "error_handling.",
        "security.",
    )
    if category == "workflow_todo.rtl_gen":
        return min(3, len(terms))
    if any(category.startswith(prefix) for prefix in rich_categories):
        return min(2, len(terms))
    return 1


def _audit_static_evidence(ip_dir: Path, plan: dict[str, Any]) -> None:
    sources = _read_rtl_sources(ip_dir)
    source_tokens = {rel: _rtl_token_set(text) for rel, text in sources.items()}
    missing: list[dict[str, Any]] = []
    checked = 0
    passed = 0
    for task in plan["tasks"]:
        if not task.get("requires_static_rtl_evidence"):
            task["static_evidence"] = {"required": False, "status": "not_required"}
            continue
        checked += 1
        terms = [term for term in task.get("evidence_terms") or [] if len(str(term)) > 1]
        owner_file = str(task.get("owner_file") or "")
        if (
            str(task.get("category") or "") == "function_model.invariant"
            and str(task.get("owner_match") or "") in {"", "control_owner_fallback", "top_fallback"}
        ):
            # Invariants can span multiple owner modules.  When ownership is
            # only a fallback, require live RTL evidence somewhere in the DUT
            # rather than falsely pinning the invariant to a control module.
            owner_file = ""
        tokens, source_scope = _source_tokens_for_owner(source_tokens, owner_file)
        lower_tokens = {token.lower() for token in tokens}
        matched = sorted({term for term in terms if term in tokens or term.lower() in lower_tokens})
        required_match_count = _required_static_match_count(str(task.get("category") or ""), terms)
        status = "pass" if len(matched) >= required_match_count else "missing"
        if status == "pass":
            passed += 1
        task["static_evidence"] = {
            "required": True,
            "status": status,
            "matched_terms": matched,
            "matched_count": len(matched),
            "required_match_count": required_match_count,
            "required_terms": terms,
            "source_scope": source_scope,
            "owner_file_scoped": bool(task.get("owner_file")),
        }
        if status != "pass":
            missing.append({
                "task_id": task["id"],
                "source_ref": task["source_ref"],
                "category": task["category"],
                "owner_file": task["owner_file"],
                "source_scope": source_scope,
                "matched_terms": matched,
                "matched_count": len(matched),
                "required_match_count": required_match_count,
                "required_terms": terms[:8],
            })
    plan["static_rtl_evidence"] = {
        "sources": sorted(sources),
        "checked": checked,
        "passed": passed,
        "missing": len(missing),
        "missing_tasks": missing[:128],
    }


def _gate_todo_completion(plan: dict[str, Any], ip_dir: Path, task: dict[str, Any], *, audit_rtl: bool) -> tuple[str, str, list[str]]:
    gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
    kind = str(gate.get("kind") or "")
    artifact = str(gate.get("artifact") or "")
    basis = [
        "rtl_todo_plan.json gate_todo.kind",
        "rtl_todo_plan.json task criteria",
    ]
    if artifact:
        basis.append(artifact)
    if not audit_rtl:
        return "planned", "RTL audit has not run yet.", basis

    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    blocker_ids = {str(item.get("id") or "") for item in blockers if isinstance(item, dict)}
    orphans = plan.get("orphans") if isinstance(plan.get("orphans"), list) else []
    static = plan.get("static_rtl_evidence") if isinstance(plan.get("static_rtl_evidence"), dict) else {}

    if kind == "ssot_required_sections":
        missing = sorted(item for item in blocker_ids if item.startswith("MISSING_FUNCTION_MODEL") or item.startswith("MISSING_CYCLE_MODEL"))
        if missing:
            return "open", "SSOT function_model/cycle_model blocker is still open: " + ", ".join(missing), basis
        return "pass", "SSOT function_model and cycle_model authority is present.", basis
    if kind == "ssot_workflow_todo_format":
        malformed = sorted(item for item in blocker_ids if item.startswith("MALFORMED_RTL_WORKFLOW_TODO"))
        if malformed:
            return "open", "Malformed SSOT workflow_todos.rtl-gen entries remain: " + ", ".join(malformed), basis
        return "pass", "SSOT-authored rtl-gen workflow TODOs are well formed.", basis
    if kind == "owner_traceability":
        if orphans:
            return "open", f"{len(orphans)} required SSOT-derived RTL task(s) still have no owner module.", basis
        return "pass", "Every required SSOT-derived RTL behavior has an owner module.", basis
    if kind == "common_ai_agent_authoring":
        path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing common_ai_agent RTL authoring provenance.", basis
        allowed_surfaces = {"atlas_ui", "textual_ui", "headless_common_engine"}
        todo_plan = ip_dir / "rtl" / "rtl_todo_plan.json"
        expected_hashes = {_sha256_file(todo_plan), _stable_json_sha256(todo_plan)} if todo_plan.is_file() else set()
        rtl_files = report.get("rtl_files") if isinstance(report.get("rtl_files"), list) else []
        issues = []
        if report.get("type") != "rtl_authoring_provenance":
            issues.append("type")
        if report.get("agent") != "common_ai_agent":
            issues.append("agent")
        if report.get("workflow") != "rtl-gen":
            issues.append("workflow")
        if report.get("surface") not in allowed_surfaces:
            issues.append("surface")
        if expected_hashes and report.get("todo_plan_sha256") not in expected_hashes:
            issues.append("todo_plan_sha256")
        if not rtl_files:
            issues.append("rtl_files")
        reported_files = _reported_rtl_file_set(ip_dir, report)
        manifest_files = _manifest_rtl_files_from_plan(plan)
        missing_manifest = sorted(manifest_files - reported_files)
        if missing_manifest:
            issues.append("rtl_files_missing_manifest:" + ",".join(missing_manifest[:6]))
        current_sources = {
            _normalize_rtl_rel(ip_dir, rel)
            for rel, _path in _rtl_source_paths(ip_dir)
            if _normalize_rtl_rel(ip_dir, rel).endswith((".v", ".sv"))
        }
        missing_current_sources = sorted(current_sources - reported_files)
        if missing_current_sources:
            issues.append("rtl_files_missing_filelist:" + ",".join(missing_current_sources[:6]))
        if issues:
            return "open", "RTL authoring provenance is incomplete: " + ", ".join(issues), basis
        return "pass", "RTL authoring provenance proves common_ai_agent rtl-gen ownership.", basis
    if kind == "target_scale_policy":
        target_scale = plan.get("target_scale") if isinstance(plan.get("target_scale"), dict) else {}
        candidate = _reference_target_scale_candidate(plan)
        waiver = plan.get("target_scale_waiver") if isinstance(plan.get("target_scale_waiver"), dict) else {}
        if target_scale:
            return "pass", "SSOT quality_gates.rtl_gen.target_scale contains human-locked structural scale minima.", basis
        if waiver.get("approved") is True and waiver.get("reason"):
            return "pass", "SSOT target_scale_waiver explicitly waives reference-scale enforcement.", basis
        if candidate:
            return (
                "open",
                "Reference profile provides suggested_ssot_target_scale, but SSOT target_scale is not locked and no approved waiver is present.",
                basis,
            )
        return "pass", "No reference-derived target scale candidate is present, so no target-scale policy lock is required.", basis
    if kind == "static_rtl_evidence":
        missing = int(static.get("missing") or 0)
        if missing:
            return "open", f"{missing} static-evidence-required task(s) still lack DUT RTL evidence.", basis
        return "pass", "Static DUT RTL evidence audit has no missing required task.", basis
    if kind == "owner_logic_structure_evidence":
        logic = plan.get("owner_logic_evidence") if isinstance(plan.get("owner_logic_evidence"), dict) else {}
        issues = logic.get("issues") if isinstance(logic.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('module') or item.get('file')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} owner logic structure issue(s) remain. {sample}".strip(), basis
        return "pass", "Behavior-owner RTL modules contain real implementation structure.", basis
    if kind == "rtl_placeholder_free_evidence":
        placeholders = plan.get("rtl_placeholder_free_evidence") if isinstance(plan.get("rtl_placeholder_free_evidence"), dict) else {}
        issues = placeholders.get("issues") if isinstance(placeholders.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('file')}:{item.get('line')}: {item.get('token')} ({item.get('issue')})"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} RTL placeholder/policy issue(s) remain. {sample}".strip(), basis
        return "pass", "RTL sources contain no placeholder markers or disallowed default-policy constructs.", basis
    if kind == "top_io_contract_evidence":
        top_io = plan.get("top_io_contract_evidence") if isinstance(plan.get("top_io_contract_evidence"), dict) else {}
        issues = top_io.get("issues") if isinstance(top_io.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('port') or item.get('module') or item.get('source_ref')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} top IO contract issue(s) remain. {sample}".strip(), basis
        return "pass", "SSOT top IO contracts match the RTL top declaration.", basis
    if kind == "top_output_drive_evidence":
        drives = plan.get("top_output_drive_evidence") if isinstance(plan.get("top_output_drive_evidence"), dict) else {}
        issues = drives.get("issues") if isinstance(drives.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('port') or item.get('module') or item.get('source_ref')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} top output drive issue(s) remain. {sample}".strip(), basis
        return "pass", "SSOT top outputs have non-placeholder RTL drive evidence.", basis
    if kind == "top_input_consumption_evidence":
        inputs = plan.get("top_input_consumption_evidence") if isinstance(plan.get("top_input_consumption_evidence"), dict) else {}
        issues = inputs.get("issues") if isinstance(inputs.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('port') or item.get('module') or item.get('source_ref')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} top input consumption issue(s) remain. {sample}".strip(), basis
        return "pass", "SSOT top inputs have RTL consumption evidence.", basis
    if kind == "manifest_hierarchy_integration":
        hierarchy = plan.get("manifest_hierarchy_evidence") if isinstance(plan.get("manifest_hierarchy_evidence"), dict) else {}
        if not hierarchy:
            hierarchy = _audit_manifest_hierarchy(ip_dir, plan)
        issues = hierarchy.get("issues") if isinstance(hierarchy.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('module') or item.get('file')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} manifest hierarchy integration issue(s) remain. {sample}".strip(), basis
        return "pass", "Every SSOT manifest-owned child module is declared and reachable from the top RTL hierarchy.", basis
    if kind == "manifest_port_connection_evidence":
        hierarchy = plan.get("manifest_hierarchy_evidence") if isinstance(plan.get("manifest_hierarchy_evidence"), dict) else {}
        if not hierarchy:
            hierarchy = _audit_manifest_hierarchy(ip_dir, plan)
        issues = hierarchy.get("port_connection_issues") if isinstance(hierarchy.get("port_connection_issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('module') or item.get('file')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} manifest port connection issue(s) remain. {sample}".strip(), basis
        return "pass", "Every reachable manifest child instance has named, non-empty port connections.", basis
    if kind == "manifest_signal_flow_evidence":
        flow = plan.get("manifest_signal_flow_evidence") if isinstance(plan.get("manifest_signal_flow_evidence"), dict) else {}
        issues = flow.get("issues") if isinstance(flow.get("issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('module') or item.get('parent')}: {item.get('port')}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} manifest signal-flow issue(s) remain. {sample}".strip(), basis
        return "pass", "Manifest child port maps carry live non-placeholder RTL signal flow.", basis
    if kind == "manifest_connection_contract_evidence":
        hierarchy = plan.get("manifest_hierarchy_evidence") if isinstance(plan.get("manifest_hierarchy_evidence"), dict) else {}
        if not hierarchy:
            hierarchy = _audit_manifest_hierarchy(ip_dir, plan)
        issues = hierarchy.get("connection_contract_issues") if isinstance(hierarchy.get("connection_contract_issues"), list) else []
        if issues:
            sample = "; ".join(
                f"{item.get('module') or item.get('source_ref') or 'connection'}: {item.get('issue')}"
                for item in issues[:3]
                if isinstance(item, dict)
            )
            return "open", f"{len(issues)} SSOT connection contract issue(s) remain. {sample}".strip(), basis
        return "pass", "SSOT connection contracts are satisfied by reachable RTL named port maps.", basis
    if kind == "dut_compile":
        path = ip_dir / "rtl" / "rtl_compile.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing canonical DUT compile artifact: rtl/rtl_compile.json.", basis
        passed = (
            report.get("passed") is True
            and report.get("dut_only") is True
            and int(report.get("errors") or 0) == 0
            and int(report.get("diagnostics") or 0) == 0
            and int(report.get("style_violations") or 0) == 0
        )
        if not passed:
            return "open", "DUT compile artifact is not clean.", basis
        freshness_issue = _artifact_freshness_issue(ip_dir, path, "DUT compile")
        if freshness_issue:
            return "open", freshness_issue, basis
        source_issue = _report_source_set_issue(ip_dir, report, "DUT compile", extensions=(".v", ".sv"))
        if source_issue:
            return "open", source_issue, basis
        return "pass", "DUT-only compile artifact passed with zero errors, diagnostics, and style violations.", basis
    if kind == "dut_lint":
        path = ip_dir / "lint" / "dut_lint.json"
        report = _safe_read_json(path)
        if not report:
            return "open", "Missing canonical DUT lint artifact: lint/dut_lint.json.", basis
        passed = (
            report.get("passed") is True
            and report.get("dut_only") is True
            and int(report.get("errors") or 0) == 0
            and int(report.get("warnings") or 0) == 0
            and int(report.get("suppression_violation_count") or 0) == 0
        )
        if not passed:
            return "open", "DUT lint artifact is not clean.", basis
        freshness_issue = _artifact_freshness_issue(ip_dir, path, "DUT lint")
        if freshness_issue:
            return "open", freshness_issue, basis
        source_issue = _report_source_set_issue(ip_dir, report, "DUT lint", extensions=(".v", ".sv", ".vh", ".svh"))
        if source_issue:
            return "open", source_issue, basis
        return "pass", "DUT-only lint artifact passed with zero errors, warnings, and suppression violations.", basis
    if kind == "golden_authority_artifacts":
        required_paths = [
            ip_dir / "governance" / "authority.json",
            ip_dir / "model" / "functional_model.py",
            ip_dir / "model" / "fl_model_check.json",
            ip_dir / "model" / "model_signature.json",
            ip_dir / "model" / "decomposition.json",
            ip_dir / "cov" / "fcov_plan.json",
            ip_dir / "verify" / "equivalence_goals.json",
        ]
        missing = [str(path.relative_to(ip_dir)) for path in required_paths if not path.is_file()]
        if missing:
            return "open", "Missing production golden authority artifact(s): " + ", ".join(missing), basis
        authority = _safe_read_json(ip_dir / "governance" / "authority.json")
        authority_issue = _authority_manifest_issue(authority, ip_dir.name)
        if authority_issue:
            return "open", authority_issue, basis
        fl_check = _safe_read_json(ip_dir / "model" / "fl_model_check.json")
        if fl_check.get("passed") is not True:
            return "open", "FunctionalModel self-check has not passed.", basis
        signature = _safe_read_json(ip_dir / "model" / "model_signature.json")
        signature_issue = _model_signature_issue(ip_dir, ip_dir.name, signature)
        if signature_issue:
            return "open", signature_issue, basis
        decomp = _safe_read_json(ip_dir / "model" / "decomposition.json")
        units = decomp.get("units") if isinstance(decomp.get("units"), list) else []
        if not units:
            return "open", "decomposition.json has no implementation units.", basis
        if decomp.get("complete") is not True:
            return "open", "decomposition.json is not complete=true.", basis
        blocked_units = [
            str(unit.get("name") or unit.get("rtl_file") or "unit")
            for unit in units
            if isinstance(unit, dict) and _truthy(unit.get("blocked"))
        ]
        if blocked_units:
            return "open", "decomposition.json still has blocked unit(s): " + ", ".join(blocked_units[:8]), basis
        fcov = _safe_read_json(ip_dir / "cov" / "fcov_plan.json")
        bins = fcov.get("bins") if isinstance(fcov.get("bins"), list) else []
        if not bins:
            return "open", "fcov_plan.json has no planned bins.", basis
        if fcov.get("planned_before_rtl") is not True:
            return "open", "fcov_plan.json is not planned_before_rtl=true.", basis
        goals = _safe_read_json(ip_dir / "verify" / "equivalence_goals.json")
        summary = goals.get("summary") if isinstance(goals.get("summary"), dict) else {}
        required_goal_ids = _required_unblocked_equivalence_goal_ids(goals)
        if not required_goal_ids:
            return "open", "equivalence_goals.json has no required unblocked goals.", basis
        if int(summary.get("blocked") or 0) > 0:
            return "open", "equivalence_goals.json still has blocked goals.", basis
        return "pass", "Production golden authority artifacts are locked, approved, current, and machine-readable.", basis
    if kind == "rtl_implementation_depth_evidence":
        depth = plan.get("rtl_implementation_depth_evidence") if isinstance(plan.get("rtl_implementation_depth_evidence"), dict) else {}
        issues = depth.get("issues") if isinstance(depth.get("issues"), list) else []
        aggregate = depth.get("aggregate") if isinstance(depth.get("aggregate"), dict) else {}
        thresholds = depth.get("thresholds") if isinstance(depth.get("thresholds"), dict) else {}
        if issues:
            sample = "; ".join(
                f"{item.get('issue')}: actual={item.get('actual')} required={item.get('required')}"
                if isinstance(item, dict) and "actual" in item
                else str(item.get("issue") if isinstance(item, dict) else item)
                for item in issues[:3]
            )
            return "open", f"{len(issues)} production RTL implementation-depth issue(s) remain. {sample}".strip(), basis
        return (
            "pass",
            "Production RTL implementation depth meets SSOT-derived/target-scale thresholds "
            f"(score={aggregate.get('depth_score')}, required={thresholds.get('min_depth_score')}).",
            basis,
        )
    if kind == "cycle_model_artifacts":
        model_path = ip_dir / "model" / "cycle_model.py"
        check = _safe_read_json(ip_dir / "model" / "cl_model_check.json")
        if not model_path.is_file():
            return "open", "Missing executable cycle model: model/cycle_model.py.", basis
        if check.get("passed") is not True:
            return "open", "Cycle model self-check has not passed.", basis
        return "pass", "Cycle model artifact and self-check are present.", basis
    if kind == "protocol_assertion_evidence":
        sva_path = ip_dir / "verify" / "protocol_assertions.sva"
        summary = _safe_read_json(ip_dir / "verify" / "protocol_assertions.summary.json")
        failures_path = ip_dir / "sim" / "assertion_failures.jsonl"
        if not sva_path.is_file():
            return "open", "Missing protocol assertion artifact: verify/protocol_assertions.sva.", basis
        if int(summary.get("assertions_total") or 0) <= 0:
            return "open", "protocol_assertions.summary.json has no generated assertions.", basis
        if not failures_path.is_file():
            return "open", "Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.", basis
        try:
            failure_rows = [line for line in failures_path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]
        except OSError as exc:
            return "open", f"Cannot read protocol assertion failures evidence: {exc}.", basis
        if failure_rows:
            return "open", f"Protocol assertion simulation reported {len(failure_rows)} failure record(s).", basis
        freshness_issue = _artifact_freshness_issue(ip_dir, failures_path, "protocol assertion simulation")
        if freshness_issue:
            return "open", freshness_issue, basis
        return "pass", "Protocol assertions were generated and simulation reported zero assertion failures.", basis
    if kind == "fl_rtl_goal_audit":
        report_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
        compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
        goals_path = ip_dir / "verify" / "equivalence_goals.json"
        report = _safe_read_json(report_path)
        if not report:
            return "open", "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.", basis
        summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
        blockers = summary.get("blockers") if isinstance(summary.get("blockers"), list) else []
        failed = int(summary.get("failed_checks") or 0)
        if not _json_report_passed(report) or failed or blockers:
            return "open", "FL-vs-RTL goal audit is not clean.", basis
        stop_condition = report.get("stop_condition") if isinstance(report.get("stop_condition"), dict) else {}
        if stop_condition:
            if stop_condition.get("fl_rtl_compare_complete") is not True:
                return "open", "FL-vs-RTL goal audit stop_condition does not prove compare completion.", basis
            if stop_condition.get("signoff_evidence_backed") is not True:
                return "open", "FL-vs-RTL goal audit stop_condition is not signoff_evidence_backed.", basis
        goals_doc = _safe_read_json(goals_path)
        compare = _safe_read_json(compare_path)
        coverage_issue = _fl_rtl_compare_goal_coverage_issue(goals_doc, compare)
        if coverage_issue:
            return "open", coverage_issue, basis
        compare_freshness_issue = _artifact_freshness_issue(ip_dir, compare_path, "FL-vs-RTL compare")
        if compare_freshness_issue:
            return "open", compare_freshness_issue, basis
        freshness_issue = _artifact_freshness_issue(ip_dir, report_path, "FL-vs-RTL goal audit")
        if freshness_issue:
            return "open", freshness_issue, basis
        return "pass", "FL-vs-RTL goal audit passed and compare covers every required unblocked equivalence goal.", basis
    if kind == "coverage_closure":
        report_path = ip_dir / "cov" / "coverage.json"
        report = _safe_read_json(report_path)
        if not report:
            return "open", "Missing coverage closure artifact: cov/coverage.json.", basis
        coverage_issue = _coverage_closure_issue(report)
        if coverage_issue:
            return "open", coverage_issue, basis
        freshness_issue = _artifact_freshness_issue(ip_dir, report_path, "coverage closure")
        if freshness_issue:
            return "open", freshness_issue, basis
        return "pass", "SSOT functional coverage closure passed with RTL-observed evidence.", basis
    if kind == "dynamic_todo_closure":
        return "deferred", "Dynamic TODO closure is evaluated after other required TODOs.", basis
    return "open", "Unknown RTL gate kind.", basis


def _owner_file_completion_issue(ip_dir: Path, task: dict[str, Any]) -> str:
    category = str(task.get("category") or "")
    if category == "rtl_flow.seed":
        return ""
    owner_file = str(task.get("owner_file") or "").strip()
    owner_module = str(task.get("owner_module") or "").strip()
    if not owner_file:
        return "Task has no RTL owner file."
    path = ip_dir / owner_file
    if not path.is_file():
        return f"Owner RTL file is missing: {owner_file}."
    if owner_file.endswith((".svh", ".vh")):
        return ""
    try:
        modules = _sv_module_bodies(path.read_text(encoding="utf-8", errors="replace"))
    except OSError as exc:
        return f"Cannot read owner RTL file {owner_file}: {exc}."
    aliases = {owner_module, Path(owner_file).stem} - {""}
    if aliases and not any(alias in modules for alias in aliases):
        return f"Owner RTL module {owner_module or Path(owner_file).stem} is not declared in {owner_file}."
    return ""


def _default_todo_completion(task: dict[str, Any], ip_dir: Path, *, audit_rtl: bool) -> tuple[str, str, list[str]]:
    static = task.get("static_evidence") if isinstance(task.get("static_evidence"), dict) else {}
    basis = [
        "rtl_todo_plan.json task criteria",
        "rtl_traceability.json source_ref mapping",
        "owner RTL file/module declaration evidence",
        "static RTL evidence audit when evidence_terms are required",
    ]
    if not audit_rtl:
        return "planned", "RTL audit has not run yet.", basis
    owner_issue = _owner_file_completion_issue(ip_dir, task)
    if owner_issue:
        return "open", owner_issue, basis
    if static.get("status") == "missing":
        return "open", "Required RTL static evidence is missing.", basis
    return "pass", "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.", basis


def _update_todo_completion(plan: dict[str, Any], ip_dir: Path, *, audit_rtl: bool) -> None:
    tasks = plan.get("tasks") if isinstance(plan.get("tasks"), list) else []
    closure_tasks: list[dict[str, Any]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("category") == "rtl_gate.rtl_gen":
            status, reason, basis = _gate_todo_completion(plan, ip_dir, task, audit_rtl=audit_rtl)
            if (task.get("gate_todo") or {}).get("kind") == "dynamic_todo_closure":
                closure_tasks.append(task)
        else:
            status, reason, basis = _default_todo_completion(task, ip_dir, audit_rtl=audit_rtl)
        task["todo_completion"] = {
            "status": status,
            "required": bool(task.get("required")),
            "criteria_total": len(task.get("criteria") or []),
            "evidence_basis": basis,
            "reason": reason,
        }

    def required_open_tasks(*, include_closure: bool) -> list[dict[str, Any]]:
        open_items: list[dict[str, Any]] = []
        for task in tasks:
            if not isinstance(task, dict) or not bool(task.get("required")):
                continue
            gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
            if not include_closure and gate.get("kind") == "dynamic_todo_closure":
                continue
            completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
            if completion.get("status") != "pass":
                open_items.append({
                    "task_id": task.get("id"),
                    "source_ref": task.get("source_ref"),
                    "category": task.get("category"),
                    "reason": completion.get("reason") or "Task is not closed.",
                })
        return open_items

    open_before_closure = required_open_tasks(include_closure=False)
    for task in closure_tasks:
        basis = list((task.get("todo_completion") or {}).get("evidence_basis") or [])
        if not audit_rtl:
            status = "planned"
            reason = "RTL audit has not run yet."
        elif open_before_closure:
            status = "open"
            reason = f"{len(open_before_closure)} required non-closure TODO(s) remain open."
        else:
            status = "pass"
            reason = "Every required non-closure TODO has pass status."
        task["todo_completion"] = {
            "status": status,
            "required": bool(task.get("required")),
            "criteria_total": len(task.get("criteria") or []),
            "evidence_basis": basis,
            "reason": reason,
        }

    open_required = required_open_tasks(include_closure=True)
    required_total = sum(1 for task in tasks if isinstance(task, dict) and bool(task.get("required")))
    passed_required = 0
    for task in tasks:
        if isinstance(task, dict) and bool(task.get("required")):
            completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
            if completion.get("status") == "pass":
                passed_required += 1
    plan["todo_completion"] = {
        "audit_rtl": audit_rtl,
        "required_total": required_total,
        "required_passed": passed_required,
        "open_required_tasks": len(open_required),
        "open_tasks": open_required[:128],
        "all_required_todos_pass": audit_rtl and not open_required,
        "rule": "rtl-gen may not claim PASS until every required SSOT-derived TODO has pass status.",
    }


def derive_plan(root: Path, ip: str, *, audit_rtl: bool = False) -> dict[str, Any]:
    ssot_path, doc = _load_ssot(root, ip)
    top = _top_name(doc, ip)
    ip_dir = root / ip
    reference_profile = _load_reference_profile(ip_dir)
    modules = _active_modules(doc, ip, top)
    top_owner = _owner_for("top_module", modules, top)
    quality_profile = _rtl_quality_profile(doc, ip)
    target_scale = _rtl_target_scale(doc)
    target_scale_waiver = _rtl_target_scale_waiver(doc)
    top_io_contracts = _collect_top_io_contracts(doc)
    connection_contracts = _collect_connection_contracts(doc, modules, top)
    tasks: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []

    _add_base_tasks(tasks, ip, top, top_owner)
    _add_rtl_gate_todo_tasks(tasks, top_owner, profile=quality_profile)
    _add_workflow_todo_tasks(tasks, blockers, doc, modules, top)
    _add_parameter_tasks(tasks, doc, modules, top)
    _add_io_tasks(tasks, doc, modules, top)
    _add_function_model_tasks(tasks, doc, modules, top)
    _add_cycle_model_tasks(tasks, doc, modules, top)
    _add_register_tasks(tasks, doc, modules, top)
    _add_section_list_tasks(tasks, doc, modules, top, section="memory", keys=("instances", "ports", "init", "maps"), label="memory item")
    _add_section_list_tasks(tasks, doc, modules, top, section="interrupts", keys=("sources", "outputs", "masks", "clears"), label="interrupt item")
    _add_fsm_tasks(tasks, doc, modules, top)
    _add_feature_dataflow_tasks(tasks, doc, modules, top)
    _add_section_list_tasks(tasks, doc, modules, top, section="error_handling", keys=("errors", "faults", "recovery", "responses"), label="error/fault item")
    _add_section_list_tasks(tasks, doc, modules, top, section="security", keys=("requirements", "assets", "checks", "policies"), label="security item")
    _add_section_list_tasks(tasks, doc, modules, top, section="debug_observability", keys=("signals", "status", "trace", "commands"), label="debug/observability item")
    _add_section_list_tasks(tasks, doc, modules, top, section="integration", keys=("dependencies", "interfaces", "address_map", "connections"), label="integration item")
    _add_section_list_tasks(tasks, doc, modules, top, section="dft", keys=("requirements", "scan", "test_points"), label="DFT item")
    _add_section_list_tasks(tasks, doc, modules, top, section="synthesis", keys=("constraints", "ppa_targets", "dont_touch"), label="synthesis item")
    _add_module_equivalence_tasks(tasks, modules, top)
    _add_test_coverage_tasks(tasks, doc, modules, top)
    _apply_rtl_contract_owner_overrides(
        tasks,
        _rtl_contract_owner_overrides(ip_dir, ip, modules),
    )
    _apply_memory_owner_from_function_tasks(tasks)

    for key in ("function_model", "cycle_model"):
        if not _present(doc.get(key)):
            blockers.append({
                "id": f"MISSING_{key.upper()}",
                "source_ref": key,
                "reason": f"SSOT must include non-empty {key} before RTL generation.",
                "owner": "ssot-gen",
            })

    orphans = [
        {
            "task_id": task["id"],
            "source_ref": task["source_ref"],
            "category": task["category"],
            "reason": "No RTL owner module could be inferred from SSOT sub_modules contracts.",
        }
        for task in tasks
        if task["required"]
        and task["category"].startswith(("function_model.", "cycle_model.", "registers.", "dataflow.", "fsm."))
        and not task.get("owner_module")
    ]

    counts = Counter(task["category"] for task in tasks)
    by_section = Counter(task["category"].split(".", 1)[0] for task in tasks)
    plan: dict[str, Any] = {
        "schema_version": 1,
        "type": "ssot_derived_rtl_todo_plan",
        "ip": ip,
        "top": top,
        "generated_at": _utc(),
        "source": str(ssot_path.relative_to(root)),
        "summary": {
            "total_tasks": len(tasks),
            "required_tasks": sum(1 for task in tasks if task.get("required")),
            "by_category": dict(sorted(counts.items())),
            "by_section": dict(sorted(by_section.items())),
            "ssot_workflow_todos": counts.get("workflow_todo.rtl_gen", 0),
            "rtl_gate_todos": counts.get("rtl_gate.rtl_gen", 0),
            "owner_modules": [
                {
                    "name": item["name"],
                    "file": item["file"],
                    "refs": item["refs"],
                    "wiring_only": bool((item.get("raw") or {}).get("wiring_only")),
                }
                for item in modules
            ],
            "blocking_questions": len(blockers),
            "orphan_tasks": len(orphans),
            "rtl_quality_profile": quality_profile,
            "reference_profile_present": bool(reference_profile),
            "target_scale_present": bool(target_scale),
            "target_scale_waived": bool(target_scale_waiver.get("approved")),
        },
        "policy": {
            "fixed_template_role": "seed_only",
            "rtl_quality_profile": quality_profile,
            "rtl_target_scale": target_scale,
            "rtl_target_scale_waiver": target_scale_waiver,
            "dynamic_task_rule": (
                "Use every required task in this file as the authoritative RTL implementation/evidence ledger. "
                "Expose Atlas/UI TodoTracker items as a flat one-to-one projection of this ledger so the "
                "existing flat TodoTracker executes one SSOT-derived RTL task at a time."
            ),
            "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
            "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
            "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
            "target_scale_rule": "Optional quality_gates.rtl_gen.target_scale is SSOT-locked human policy. It can be calibrated from a reference profile, but it is enforced as generic structural depth evidence, not as copied reference RTL.",
            "no_orphan_function_level": True,
            "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
        },
        "target_scale": target_scale,
        "target_scale_waiver": target_scale_waiver,
        "reference_profile": reference_profile,
        "ssot_connection_contracts": connection_contracts,
        "blockers": blockers,
        "orphans": orphans[:128],
        "ssot_top_io_contracts": top_io_contracts,
        "tasks": tasks,
        "static_rtl_evidence": {"sources": [], "checked": 0, "passed": 0, "missing": 0, "missing_tasks": []},
        "owner_logic_evidence": {"status": "not_run", "checked": 0, "issues": []},
        "rtl_placeholder_free_evidence": {"status": "not_run", "checked": 0, "issues": []},
        "rtl_implementation_depth_evidence": {"status": "not_run", "thresholds": {}, "aggregate": {}, "issues": []},
        "top_io_contract_evidence": {"status": "not_run", "contracts": len(top_io_contracts), "issues": []},
        "top_output_drive_evidence": {"status": "not_run", "checked": 0, "driven": 0, "issues": []},
        "top_input_consumption_evidence": {"status": "not_run", "checked": 0, "consumed": 0, "issues": []},
        "manifest_hierarchy_evidence": {"status": "not_run", "sources": [], "issues": []},
        "manifest_signal_flow_evidence": {"status": "not_run", "checked_inputs": 0, "checked_outputs": 0, "issues": []},
        "gate": {},
    }
    if audit_rtl:
        _audit_static_evidence(ip_dir, plan)
        plan["owner_logic_evidence"] = _audit_owner_logic_structure(ip_dir, plan)
        plan["rtl_placeholder_free_evidence"] = _audit_rtl_placeholder_free(ip_dir)
        plan["rtl_implementation_depth_evidence"] = _audit_rtl_implementation_depth(ip_dir, plan)
        plan["top_io_contract_evidence"] = _audit_top_io_contracts(ip_dir, plan)
        plan["top_output_drive_evidence"] = _audit_top_output_drives(ip_dir, plan)
        plan["top_input_consumption_evidence"] = _audit_top_input_consumption(ip_dir, plan)
        plan["manifest_hierarchy_evidence"] = _audit_manifest_hierarchy(ip_dir, plan)
        plan["manifest_signal_flow_evidence"] = _audit_manifest_signal_flow(ip_dir, plan)
    plan["reference_scale_gap"] = _reference_scale_gap_summary(plan)
    plan["connection_contract_suggestions"] = _draft_connection_contract_suggestions(ip_dir, plan)
    _update_todo_completion(plan, ip_dir, audit_rtl=audit_rtl)
    static_missing = int((plan.get("static_rtl_evidence") or {}).get("missing") or 0)
    open_todos = int((plan.get("todo_completion") or {}).get("open_required_tasks") or 0)
    gate_status = "pass"
    if blockers:
        gate_status = "blocked"
    elif orphans:
        gate_status = "blocked"
    elif audit_rtl and static_missing:
        gate_status = "fail"
    elif audit_rtl and open_todos:
        gate_status = "fail"
    elif not audit_rtl:
        gate_status = "planned"
    plan["gate"] = {
        "status": gate_status,
        "audit_rtl": audit_rtl,
        "blocking_questions": len(blockers),
        "orphan_tasks": len(orphans),
        "static_missing": static_missing,
        "open_required_todos": open_todos,
        "all_required_todos_pass": bool((plan.get("todo_completion") or {}).get("all_required_todos_pass")),
        "criteria": [
            task["content"]
            for task in tasks
            if task.get("category") == "rtl_gate.rtl_gen"
        ],
    }
    _write_outputs(ip_dir, plan)
    _write_dynamic_blocker(ip_dir, plan)
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    ap.add_argument("--ip-root", "--ip_root", dest="ip_root", default=os.environ.get("ATLAS_IP_ROOT") or "")
    ap.add_argument("--audit-rtl", action="store_true")
    ns = ap.parse_args()
    plan = derive_plan(_resolve_project_root(ns.root, ns.ip_root, ns.ip), ns.ip, audit_rtl=ns.audit_rtl)
    summary = plan.get("summary") or {}
    gate = plan.get("gate") or {}
    print(
        "[derive_rtl_todos] "
        f"{ns.ip}: tasks={summary.get('total_tasks', 0)} "
        f"blockers={summary.get('blocking_questions', 0)} "
        f"orphans={summary.get('orphan_tasks', 0)} "
        f"gate={gate.get('status')}"
    )
    if gate.get("status") == "blocked":
        return 2
    return 1 if gate.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
