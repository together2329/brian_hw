#!/usr/bin/env python3
"""Aggregate per-IP TODO entries for the TodoTracker.

Produces one TodoItem per equivalence goal plus self-check failures,
SSOT-TBD escalations, and conditional augmentation TODOs.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

# ── Allowed TodoItem keys (must match todo_tracker.py TodoItem dataclass) ──
_ALLOWED_KEYS: frozenset[str] = frozenset({
    "content", "activeForm", "active_form", "status", "priority",
    "completed_at", "detail", "criteria", "rejection_reason",
    "approved_reason", "loop", "max_loop_iterations", "exit_condition",
    "loop_count", "loop_exit_reason", "validator", "delegate",
    "delegate_result", "workflow", "tools_since_in_progress",
    "tools_since_completed", "rejection_count", "notes", "command",
    "on_reject", "on_success", "on_condition", "command_logs",
})

_ALLOWED_STATUS: frozenset[str] = frozenset({
    "pending", "in_progress", "completed", "approved", "rejected",
})

_ALLOWED_PRIORITY: frozenset[str] = frozenset({"high", "medium", "low"})

# ── Priority mapping by goal kind ──
_KIND_PRIORITY: dict[str, str] = {
    "module": "high",
    "transaction": "high",
    "error": "high",
    "protocol": "medium",
    "timing": "medium",
    "state": "medium",
    "register": "medium",
    "memory": "medium",
    "coverage": "low",
}


# ─────────────────────────────────────────────
# Loaders
# ─────────────────────────────────────────────

def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


# ─────────────────────────────────────────────
# Source A: equivalence goals
# ─────────────────────────────────────────────

def _goal_priority(goal: dict[str, Any]) -> str:
    if goal.get("blocked"):
        return "high"
    return _KIND_PRIORITY.get(str(goal.get("kind") or "").lower(), "medium")


def _todos_from_goals(goals_doc: dict[str, Any]) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []
    for g in _as_list(goals_doc.get("goals")):
        if not isinstance(g, dict):
            continue
        gid = str(g.get("goal_id") or "")
        title = str(g.get("title") or "")
        blocked = bool(g.get("blocked"))
        prefix = "[BLOCKED] " if blocked else ""
        content = f"{prefix}GLD_GOAL_{gid} — {title}"

        scope = g.get("scope")
        scope_str = json.dumps(scope) if isinstance(scope, dict) else str(scope or "")

        ssot_refs = ", ".join(str(r) for r in _as_list(g.get("ssot_refs")))
        decomp_refs = ", ".join(str(r) for r in _as_list(g.get("decomposition_refs")))
        cov_refs = ", ".join(str(r) for r in _as_list(g.get("coverage_refs")))

        expected_contract = g.get("expected_contract") or {}
        model_api = str(expected_contract.get("model_api") or "FunctionalModel.apply")

        owner_on_fail = g.get("owner_on_fail") or {}
        owner_default = str(owner_on_fail.get("default") or "")

        detail_lines = [
            f"kind: {g.get('kind', '')}",
            f"scope: {scope_str}",
            f"ssot_refs: {ssot_refs}",
            f"decomposition_refs: {decomp_refs}",
            f"coverage_refs: {cov_refs}",
            f"expected via: {model_api}",
            f"owner_on_fail: {owner_default}",
        ]
        detail = "\n".join(detail_lines)

        criteria = "\n".join(str(c) for c in _as_list(g.get("pass_criteria")))
        rejection_reason = str(g.get("blocker") or "") if blocked else ""

        todos.append({
            "content": content,
            "activeForm": f"Closing equivalence goal GLD_GOAL_{gid}",
            "status": "pending",
            "priority": _goal_priority(g),
            "detail": detail,
            "criteria": criteria,
            "rejection_reason": rejection_reason,
            "approved_reason": "",
            "loop": False,
            "max_loop_iterations": 0,
            "exit_condition": "",
            "loop_count": 0,
            "loop_exit_reason": "",
            "validator": "",
            "delegate": "",
            "delegate_result": "",
            "workflow": "fl-model-gen",
            "tools_since_in_progress": 0,
            "tools_since_completed": 0,
            "rejection_count": 0,
            "notes": [f"owner_on_fail: {owner_default}"],
            "command": "",
            "on_reject": 0,
            "on_success": 0,
            "on_condition": None,
            "command_logs": [],
        })
    return todos


# ─────────────────────────────────────────────
# Source B: self-check failures
# ─────────────────────────────────────────────

def _todos_from_self_check(
    ip: str,
    check_doc: dict[str, Any],
    prefix: str,
) -> list[dict[str, Any]]:
    """Emit todos for failed self-check transaction rows."""
    self_check = check_doc.get("self_check")
    if not isinstance(self_check, dict):
        return []
    # If overall passed and no failures, emit nothing
    if self_check.get("passed") and not _as_list(self_check.get("transaction_results")):
        return []

    todos: list[dict[str, Any]] = []
    for row in _as_list(self_check.get("transaction_results")):
        if not isinstance(row, dict):
            continue
        if row.get("passed"):
            continue
        row_id = str(row.get("id") or "")
        row_name = str(row.get("name") or "")
        content = f"{prefix}{row_id} — FL self-check failed: {row_name}"
        active_form = f"Repairing FL self-check for {row_id}"
        detail = json.dumps(row, indent=2)
        criteria = (
            f"FunctionalModel.apply with kind={row_id} returns RESP_OKAY\n"
            "result matches SSOT-derived expected"
        )
        # Build validator: determine module path from prefix
        mod_prefix = "fl" if prefix.startswith("GLD_FL") else "cl"
        validator = (
            f"python3 -c \"from {ip}.model.functional_model import run_self_check; "
            f"r=run_self_check(); raise SystemExit(0 if next("
            f"(t for t in r['transaction_results'] if t['id']=='{row_id}' and t['passed']),"
            f"None) else 1)\""
        )
        todos.append({
            "content": content,
            "activeForm": active_form,
            "status": "pending",
            "priority": "high",
            "detail": detail,
            "criteria": criteria,
            "rejection_reason": "",
            "approved_reason": "",
            "loop": True,
            "max_loop_iterations": 5,
            "exit_condition": "",
            "loop_count": 0,
            "loop_exit_reason": "",
            "validator": validator,
            "delegate": "",
            "delegate_result": "",
            "workflow": "fl-model-gen",
            "tools_since_in_progress": 0,
            "tools_since_completed": 0,
            "rejection_count": 0,
            "notes": [],
            "command": "",
            "on_reject": 0,
            "on_success": 0,
            "on_condition": None,
            "command_logs": [],
        })
    return todos


# ─────────────────────────────────────────────
# Source C: SSOT TBD escalations
# ─────────────────────────────────────────────

def _has_handshake_bus(ssot: dict[str, Any]) -> bool:
    """Return True if any io_list port/bus name mentions axi/ahb/apb/axis."""
    bus_keywords = ("axi", "ahb", "apb", "axis")
    for port in _as_list(ssot.get("io_list")):
        if not isinstance(port, dict):
            continue
        hay = " ".join(
            str(port.get(k) or "") for k in ("name", "bus", "type", "description")
        ).lower()
        if any(kw in hay for kw in bus_keywords):
            return True
    # Also check top-level description and interface references
    desc = str(ssot.get("top_module", {}).get("description") or "").lower()
    if any(kw in desc for kw in bus_keywords):
        return True
    return False


def _todos_from_ssot_tbd(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    todos: list[dict[str, Any]] = []

    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    err = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    syn = ssot.get("synthesis") if isinstance(ssot.get("synthesis"), dict) else {}

    transactions = _as_list(fm.get("transactions"))
    invariants = _as_list(fm.get("invariants"))
    handshake_rules = _as_list(cm.get("handshake_rules"))
    latency = cm.get("latency")
    error_sources = _as_list(err.get("error_sources"))
    ppa_targets = syn.get("ppa_targets") if isinstance(syn.get("ppa_targets"), dict) else {}
    cm_targets = cm.get("targets")

    def _make_tbd(
        content: str,
        active_section: str,
        gap_text: str,
        human_desc: str,
    ) -> dict[str, Any]:
        return {
            "content": content,
            "activeForm": f"Awaiting SSOT fix for {active_section}",
            "status": "pending",
            "priority": "high",
            "detail": "",
            "criteria": "",
            "rejection_reason": gap_text,
            "approved_reason": "",
            "loop": False,
            "max_loop_iterations": 0,
            "exit_condition": "",
            "loop_count": 0,
            "loop_exit_reason": "",
            "validator": "",
            "delegate": "",
            "delegate_result": "",
            "workflow": "fl-model-gen",
            "tools_since_in_progress": 0,
            "tools_since_completed": 0,
            "rejection_count": 0,
            "notes": ["owner: ssot-gen"],
            "command": "",
            "on_reject": 0,
            "on_success": 0,
            "on_condition": None,
            "command_logs": [],
        }

    # 1) function_model.invariants empty but transactions non-empty
    if transactions and not invariants:
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_INVARIANTS_TBD — function_model.invariants is empty despite transactions being defined",
            "function_model.invariants",
            "function_model.invariants is empty; function_model.transactions is non-empty",
            "Add invariants that constrain the transaction space",
        ))

    # 2) cycle_model.latency empty but handshake_rules non-empty
    if handshake_rules and not latency:
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_LATENCY_TBD — cycle_model.latency is empty despite handshake_rules being defined",
            "cycle_model.latency",
            "cycle_model.latency is empty; cycle_model.handshake_rules is non-empty",
            "Define latency bounds for each handshake rule",
        ))

    # 3) cycle_model.handshake_rules empty but io_list mentions a bus
    if not handshake_rules and _has_handshake_bus(ssot):
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_HANDSHAKE_TBD — cycle_model.handshake_rules is empty despite bus interface in io_list",
            "cycle_model.handshake_rules",
            "cycle_model.handshake_rules is empty; io_list references axi/ahb/apb/axis bus",
            "Define handshake_rules for the bus interface",
        ))

    # 4) error_handling.error_sources empty but any transaction has error_cases
    has_error_cases = any(
        _as_list(tx.get("error_cases")) for tx in transactions if isinstance(tx, dict)
    )
    if has_error_cases and not error_sources:
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_ERROR_SOURCES_TBD — error_handling.error_sources is empty despite transactions having error_cases",
            "error_handling.error_sources",
            "error_handling.error_sources is empty; at least one transaction defines error_cases",
            "Populate error_handling.error_sources from transaction error_cases",
        ))

    # 5) synthesis.ppa_targets.frequency_mhz_min null but cycle_model.targets exists
    #    OR cycle_model.latency.*.max_cycles == null
    latency_has_null_max = False
    if isinstance(latency, dict):
        for entry in latency.values():
            if isinstance(entry, dict) and entry.get("max_cycles") is None:
                latency_has_null_max = True
                break
    fmax_null = ppa_targets.get("frequency_mhz_min") is None
    if fmax_null and (cm_targets or latency_has_null_max):
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_PPA_FMAX_TBD — synthesis.ppa_targets.frequency_mhz_min is not set",
            "synthesis.ppa_targets.frequency_mhz_min",
            "synthesis.ppa_targets.frequency_mhz_min is null; cycle_model.targets exists or latency has unbounded max_cycles",
            "Set frequency_mhz_min in synthesis.ppa_targets",
        ))

    # 6) function_model section absent — always check
    if not isinstance(ssot.get("function_model"), dict):
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_FM_TBD — function_model section is absent from SSOT",
            "function_model",
            "function_model section is absent from SSOT",
            "Add function_model with transactions to SSOT",
        ))

    # 7) cycle_model section absent but io_list mentions a handshake bus
    if not isinstance(ssot.get("cycle_model"), dict) and _has_handshake_bus(ssot):
        todos.append(_make_tbd(
            "[SSOT-TBD] GLD_SSOT_CM_TBD — cycle_model section is absent despite bus interface in io_list",
            "cycle_model",
            "cycle_model section is absent; io_list references axi/ahb/apb/axis bus",
            "Add cycle_model with handshake_rules to SSOT",
        ))

    return todos


# ─────────────────────────────────────────────
# Source D: conditional augmentation TODOs
# ─────────────────────────────────────────────

def _eval_trigger(trigger: str, ssot: dict[str, Any]) -> bool:
    """Evaluate augmentation trigger string against SSOT dict.

    Dispatch by literal trigger text — no eval().
    """
    t = trigger.strip()

    if t == "always":
        return True

    if t == "ssot.cycle_model has handshake_rules OR ordering OR arbitration OR outstanding>1":
        cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
        if _as_list(cm.get("handshake_rules")):
            return True
        if _as_list(cm.get("ordering")):
            return True
        if _as_list(cm.get("arbitration")):
            return True
        outstanding = cm.get("outstanding")
        if outstanding is not None:
            try:
                return int(outstanding) > 1
            except (TypeError, ValueError):
                pass
        return False

    if t == "ssot.synthesis.ppa_targets has any of {area_um2_max, power_mw_max, frequency_mhz_min}":
        syn = ssot.get("synthesis") if isinstance(ssot.get("synthesis"), dict) else {}
        ppa = syn.get("ppa_targets") if isinstance(syn.get("ppa_targets"), dict) else {}
        return any(ppa.get(k) is not None for k in ("area_um2_max", "power_mw_max", "frequency_mhz_min"))

    if t == "ssot.security has assets OR threats":
        sec = ssot.get("security") if isinstance(ssot.get("security"), dict) else {}
        if _as_list(sec.get("assets")):
            return True
        if _as_list(sec.get("threats")):
            return True
        return False

    if t == "ssot.memory.instances non-empty":
        mem = ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {}
        return bool(_as_list(mem.get("instances")))

    # Unknown trigger — default false
    return False


# Hardcoded fallback augmentation templates (matches golden-ip-augment.template.json)
_HARDCODED_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "GLD_AUG_CL_EMIT",
        "trigger": "ssot.cycle_model has handshake_rules OR ordering OR arbitration OR outstanding>1",
        "content_pattern": "GLD_AUG_CL_EMIT — Generate executable CL model for ${ip}",
        "activeForm": "Verifying executable CL exists for ${ip}",
        "detail": "Cycle-level model wraps FunctionalModel; provides .drive(), .tick(), .observe(), .coverage(). CL must NEVER re-evaluate output_rules/state_updates.",
        "criteria": "<ip>/model/cycle_model.py exists\nFile contains zero occurrences of output_rules / state_updates / _eval_rule_expr\nCycleModel API smoke test passes",
        "validator": "test -f ${ip}/model/cycle_model.py && ! grep -E 'output_rules|state_updates|_eval_rule_expr' ${ip}/model/cycle_model.py",
        "priority": "high",
        "loop": False,
    },
    {
        "id": "GLD_AUG_PPA_SWEEP",
        "trigger": "ssot.synthesis.ppa_targets has any of {area_um2_max, power_mw_max, frequency_mhz_min}",
        "content_pattern": "GLD_AUG_PPA_SWEEP — Drive PPA sweep through CL.tick and report measured area/power/fmax",
        "activeForm": "Running PPA sweep via CL",
        "detail": "Use CycleModel to produce activity vectors fed into syn / sta-post / pnr workers; capture measured PPA.",
        "criteria": "<ip>/reports/ppa_sweep.json exists with measured_area_um2, measured_power_mw, measured_fmax_mhz\nMeasured values within budgets defined by SSOT, or escalation noted",
        "validator": "python3 ${ip}/verify/check_ppa.py",
        "priority": "medium",
        "loop": True,
        "max_loop_iterations": 5,
    },
    {
        "id": "GLD_AUG_SECURITY_GOALS",
        "trigger": "ssot.security has assets OR threats",
        "content_pattern": "GLD_AUG_SECURITY_GOALS — Add EQ_SECURITY_* goals for ${ip}",
        "activeForm": "Generating EQ_SECURITY_* equivalence goals",
        "detail": "Each declared asset/threat should produce a security equivalence goal with stimulus + observable.",
        "criteria": "equivalence_goals.json contains at least one EQ_SECURITY_* goal\nEach asset/threat from SSOT is referenced",
        "validator": "python3 -c \"import json; g=json.load(open('${ip}/verify/equivalence_goals.json')); raise SystemExit(0 if any(x['goal_id'].startswith('EQ_SECURITY_') for x in g['goals']) else 1)\"",
        "priority": "high",
        "loop": False,
    },
    {
        "id": "GLD_AUG_MEMORY_BOUNDARY",
        "trigger": "ssot.memory.instances non-empty",
        "content_pattern": "GLD_AUG_MEMORY_BOUNDARY — Drive memory boundary scoreboard via CL.observe for ${ip}",
        "activeForm": "Validating memory boundary against FL+CL",
        "detail": "Observable memory state must match FunctionalModel state for read/write/byte-strobe/boundary cases.",
        "criteria": "<ip>/verify/check_memory_boundary.py exists and exits 0\nReports per-instance status",
        "validator": "python3 ${ip}/verify/check_memory_boundary.py",
        "priority": "medium",
        "loop": True,
        "max_loop_iterations": 5,
    },
    {
        "id": "GLD_AUG_SIGNATURE",
        "trigger": "always",
        "content_pattern": "GLD_AUG_SIGNATURE — Emit and verify model_signature.json for ${ip}",
        "activeForm": "Verifying model_signature.json freshness for ${ip}",
        "detail": "Signature must be fresh after every SSOT change; --check mode detects drift.",
        "criteria": "<ip>/model/model_signature.json exists\npython3 emit_model_signature.py ${ip} --root . --check returns 0",
        "validator": "test -f ${ip}/model/model_signature.json && python3 workflow/fl-model-gen/scripts/emit_model_signature.py ${ip} --root . --check",
        "priority": "medium",
        "loop": False,
    },
    {
        "id": "GLD_AUG_COCOTB_RUN",
        "trigger": "always",
        "content_pattern": "GLD_AUG_COCOTB_RUN — Run cocotb harness fl_cl_rtl end-to-end for ${ip}",
        "activeForm": "Running cocotb fl_cl_rtl harness",
        "detail": "Full DUT + FL + CL co-simulation; scoreboard compares RTL observable to FunctionalModel.apply expected.",
        "criteria": "make -C ${ip}/verify -f Makefile.sim fl_cl_rtl exits 0\nCoverage report written under ${ip}/cov/",
        "validator": "make -C ${ip}/verify -f Makefile.sim fl_cl_rtl",
        "priority": "high",
        "loop": True,
        "max_loop_iterations": 5,
    },
    {
        "id": "GLD_AUG_LOOP_MAP",
        "trigger": "always",
        "content_pattern": "GLD_AUG_LOOP_MAP — Emit human-vs-LLM loop_map.svg for ${ip}",
        "activeForm": "Generating human-vs-LLM loop diagram",
        "detail": "Render <ip>/model/loop_map.mmd from authority_contract; convert to SVG.",
        "criteria": "<ip>/model/loop_map.svg exists",
        "validator": "test -f ${ip}/model/loop_map.svg",
        "priority": "low",
        "loop": False,
    },
]


def _todos_from_augmentation(
    ip: str,
    ssot: dict[str, Any],
    template_path: Path,
) -> list[dict[str, Any]]:
    """Emit conditional augmentation todos from template file or hardcoded fallback."""
    if template_path.is_file():
        try:
            doc = json.loads(template_path.read_text(encoding="utf-8"))
            templates = _as_list(doc.get("templates"))
        except Exception:
            templates = _HARDCODED_TEMPLATES
    else:
        templates = _HARDCODED_TEMPLATES

    todos: list[dict[str, Any]] = []
    for tmpl in templates:
        if not isinstance(tmpl, dict):
            continue
        trigger = str(tmpl.get("trigger") or "always").strip()
        if not _eval_trigger(trigger, ssot):
            continue

        def _sub(s: str) -> str:
            return s.replace("${ip}", ip)

        content = _sub(str(tmpl.get("content_pattern") or tmpl.get("id") or ""))
        active_form = _sub(str(tmpl.get("activeForm") or content))
        validator = _sub(str(tmpl.get("validator") or ""))
        detail = str(tmpl.get("detail") or "")
        criteria = str(tmpl.get("criteria") or "")
        priority = str(tmpl.get("priority") or "medium")
        loop = bool(tmpl.get("loop", False))
        max_loop_iterations = int(tmpl.get("max_loop_iterations") or 0)

        todos.append({
            "content": content,
            "activeForm": active_form,
            "status": "pending",
            "priority": priority if priority in _ALLOWED_PRIORITY else "medium",
            "detail": detail,
            "criteria": criteria,
            "rejection_reason": "",
            "approved_reason": "",
            "loop": loop,
            "max_loop_iterations": max_loop_iterations,
            "exit_condition": "",
            "loop_count": 0,
            "loop_exit_reason": "",
            "validator": validator,
            "delegate": "",
            "delegate_result": "",
            "workflow": "fl-model-gen",
            "tools_since_in_progress": 0,
            "tools_since_completed": 0,
            "rejection_count": 0,
            "notes": [],
            "command": "",
            "on_reject": 0,
            "on_success": 0,
            "on_condition": None,
            "command_logs": [],
        })
    return todos


# ─────────────────────────────────────────────
# Dedup
# ─────────────────────────────────────────────

def _dedup(todos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep first occurrence, keyed on content."""
    seen: dict[str, dict[str, Any]] = {}
    for t in todos:
        key = str(t.get("content") or "")
        if key not in seen:
            seen[key] = t
    return list(seen.values())


# ─────────────────────────────────────────────
# Pre-emit validation
# ─────────────────────────────────────────────

def _validate(todos: list[dict[str, Any]]) -> None:
    """Validate todos against schema. Prints error and raises SystemExit(1) on failure."""
    errors: list[str] = []
    for idx, t in enumerate(todos):
        extra = set(t.keys()) - _ALLOWED_KEYS
        if extra:
            errors.append(
                f"todo[{idx}] '{str(t.get('content',''))[:60]}': unsupported keys {extra}"
            )
        status = t.get("status", "")
        if status not in _ALLOWED_STATUS:
            errors.append(
                f"todo[{idx}] '{str(t.get('content',''))[:60]}': bad status '{status}'"
            )
        priority = t.get("priority", "")
        if priority not in _ALLOWED_PRIORITY:
            errors.append(
                f"todo[{idx}] '{str(t.get('content',''))[:60]}': bad priority '{priority}'"
            )
        # Augmentation todos must have non-empty validator
        content = str(t.get("content") or "")
        if content.startswith("GLD_AUG_") and not t.get("validator"):
            errors.append(
                f"todo[{idx}] '{content[:60]}': augmentation todo missing validator"
            )
    if errors:
        for e in errors:
            print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        raise SystemExit(1)


# ─────────────────────────────────────────────
# Main emit
# ─────────────────────────────────────────────

def emit(ip: str, root: Path) -> int:
    ip_dir = root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    fl_check_path = ip_dir / "model" / "fl_model_check.json"
    cl_check_path = ip_dir / "model" / "cl_model_check.json"
    template_path = root / "workflow" / "fl-model-gen" / "todo_templates" / "golden-ip-augment.template.json"

    ssot = _load_yaml(ssot_path)
    goals_doc = _load_json(goals_path)
    fl_check = _load_json(fl_check_path)
    cl_check = _load_json(cl_check_path)  # gracefully empty if absent

    # Source A
    todos_goals = _todos_from_goals(goals_doc)

    # Source B FL
    todos_fl = _todos_from_self_check(ip, fl_check, "GLD_FL_FAIL_")

    # Source B CL (gracefully skip if absent)
    todos_cl: list[dict[str, Any]] = []
    if cl_check_path.is_file():
        todos_cl = _todos_from_self_check(ip, cl_check, "GLD_CL_FAIL_")

    # Source C
    todos_ssot = _todos_from_ssot_tbd(ssot)

    # Source D
    todos_aug = _todos_from_augmentation(ip, ssot, template_path)

    # Combine and dedup
    all_todos = _dedup(todos_goals + todos_fl + todos_cl + todos_ssot + todos_aug)

    # Validate before writing
    _validate(all_todos)

    # Summary counts
    n_goals = len(todos_goals)
    n_self_check = len(todos_fl) + len(todos_cl)
    n_ssot = len(todos_ssot)
    n_aug = len(todos_aug)
    # After dedup some may be dropped; total = actual written
    n_total = len(all_todos)

    # Output directory
    golden_dir = ip_dir / "golden"
    golden_dir.mkdir(parents=True, exist_ok=True)

    # Audit ledger
    ledger: dict[str, Any] = {
        "ip": ip,
        "schema_version": 1,
        "type": "golden_todos",
        "source_of_truth": {
            "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
            "equivalence_goals": f"{ip}/verify/equivalence_goals.json",
            "fl_model_check": f"{ip}/model/fl_model_check.json",
            "cl_model_check": f"{ip}/model/cl_model_check.json",
        },
        "summary": {
            "total": n_total,
            "from_goals": n_goals,
            "from_self_check": n_self_check,
            "from_ssot_tbd": n_ssot,
            "from_augmentation": n_aug,
        },
        "todos": all_todos,
    }
    ledger_path = golden_dir / "golden_todos.json"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")

    # Tracker shape
    tracker: dict[str, Any] = {"todos": all_todos}
    tracker_path = golden_dir / "golden_todos_tracker.json"
    tracker_path.write_text(json.dumps(tracker, indent=2) + "\n", encoding="utf-8")

    print(
        f"[emit_golden_todos] wrote {ip}/golden/golden_todos.json "
        f"and {ip}/golden/golden_todos_tracker.json"
    )
    print(
        f"[emit_golden_todos] total={n_total} "
        f"from_goals={n_goals} from_self_check={n_self_check} "
        f"from_ssot_tbd={n_ssot} from_augmentation={n_aug}"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit golden TodoTracker entries for a given IP."
    )
    parser.add_argument("ip", help="IP name (e.g. smbus)")
    parser.add_argument("--root", default=".", help="Repository root directory")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    try:
        return emit(args.ip, root)
    except SystemExit as exc:
        code = exc.code
        if isinstance(code, int):
            return code
        return 1
    except Exception as exc:
        print(f"[emit_golden_todos] ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
