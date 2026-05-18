"""Deterministic failure classifier for the orchestrator loop.

Extracts the routing matrix from ``workflow/orchestrator/system_prompt.md``
into a callable, testable function so the LLM loop never has to re-derive
owner -> next-workflow mappings from prose.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


HUMAN_ESCALATION = "human-review-escalation"

# Owner classification -> repair workflow.
# Matches the table at workflow/orchestrator/system_prompt.md:50-61.
_OWNER_ROUTES: Dict[str, str] = {
    "rtl_bug": "rtl-gen",
    "tb_bug": "tb-gen",
    "frontier": HUMAN_ESCALATION,
    "coverage_gap": "tb-gen",
    "lint_violation": "rtl-gen",
    "compile_error": "rtl-gen",
    "timing_setup": HUMAN_ESCALATION,
    "timing_hold": "rtl-gen",
    "ssot_gap": "ssot-gen",
    "pnr_setup": "pnr",
}

_COMPILE_HINTS = ("syntax error", "error:", "compile", "elaboration", "undefined")
_LINT_HINTS = ("violation", "warning", "lint", "style")
_TIMING_HOLD_HINTS = ("hold", "min delay", "th violation")
_TIMING_SETUP_HINTS = ("setup", "wns", "tns", "max delay")
_SSOT_GAP_HINTS = (
    "ssot tbd",
    "ssot gap",
    "missing required",
    "missing explicit",
    "missing synthesis",
    "synthesis technology",
    "technology/corner/library",
    "corner/library",
    "library policy",
    "quality_gates.eda",
)
_RTL_SSOT_CONTRACT_HINTS = (
    "ssot behavior is not concrete enough",
    "ssot-derived dynamic rtl todo gate",
    "rtl_dynamic_todo_ownership",
    "rtl_module_contracts",
    "owner_traceability",
    "module contract",
    "manifest-owned rtl",
    "module contracts",
    "required ssot-derived rtl task",
    "sub_modules into a module contract ledger",
)
_RTL_MISSING_ARTIFACT_HINTS = (
    "llm-authored rtl evidence is missing or stale",
    "llm_rtl_implementation_required",
    "generate real rtl from ssot-derived todos",
    "missing rtl files",
    "filelist references missing file",
    "filelist missing",
    "missing canonical dut compile artifact",
    "missing canonical dut lint artifact",
    "missing rtl/rtl_compile.json",
    "missing lint/dut_lint.json",
    "ssot top module is not declared",
    "manifest child module is not declared",
    "no listed rtl source files were readable",
)
_PNR_SETUP_HINTS = (
    "pnr",
    "openroad",
    "floorplan",
    "place",
    "cts",
    "route",
    "routed.def",
    "routed.v",
    "routed.spef",
    "pdk",
    "lef",
    "def",
)


def _text_has_any(text: str, hints) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(h in lowered for h in hints)


def _read_owner_from_evidence(evidence: Dict[str, Any]) -> Optional[str]:
    """Lift owner classification out of ``sim_debug`` evidence if present."""
    if not evidence:
        return None
    mc = evidence.get("mismatch_classification")
    if isinstance(mc, dict):
        owner = mc.get("owner")
        if isinstance(owner, str) and owner:
            return owner
    if isinstance(mc, list) and mc:
        # Multiple mismatches: dispatch the highest-precedence owner.
        precedence = ("frontier", "ssot_gap", "rtl_bug", "tb_bug", "coverage_gap")
        owners = {item.get("owner") for item in mc if isinstance(item, dict)}
        for tier in precedence:
            if tier in owners:
                return tier
    owner = evidence.get("owner")
    if isinstance(owner, str) and owner:
        return owner
    return None


def classify_failure(
    stage_id: str,
    evidence: Optional[Dict[str, Any]] = None,
    error_text: str = "",
) -> Dict[str, Any]:
    """Map a failed stage + evidence to a repair workflow.

    Returns a dict with keys ``owner``, ``next_workflow``, ``reason``,
    ``confidence``. ``confidence`` is ``high`` when the classification comes
    from explicit evidence (sim_debug owner, lint violation), ``medium`` when
    a stage-specific rule fires, ``low`` when defaulting to human review.
    """
    evidence = evidence or {}
    stage = (stage_id or "").lower()

    # 1. Explicit owner classification wins.
    owner = _read_owner_from_evidence(evidence)
    if owner and owner in _OWNER_ROUTES:
        return {
            "owner": owner,
            "next_workflow": _OWNER_ROUTES[owner],
            "reason": f"owner={owner} from {stage} evidence",
            "confidence": "high",
        }

    # 2. Stage-specific deterministic rules.
    if stage in ("rtl", "rtl-gen"):
        if _text_has_any(error_text, _RTL_SSOT_CONTRACT_HINTS):
            return {
                "owner": "ssot_gap",
                "next_workflow": "ssot-gen",
                "reason": "rtl-gen blocked on missing SSOT module contracts",
                "confidence": "high",
            }
        if _text_has_any(error_text, _RTL_MISSING_ARTIFACT_HINTS):
            return {
                "owner": "compile_error",
                "next_workflow": "rtl-gen",
                "reason": "RTL artifact/filelist is incomplete; rerun rtl-gen after preserving evidence",
                "confidence": "high",
            }
        if _text_has_any(error_text, _COMPILE_HINTS):
            return {
                "owner": "compile_error",
                "next_workflow": "rtl-gen",
                "reason": "compile/elaboration error in RTL output",
                "confidence": "high",
            }
    if stage == "lint":
        return {
            "owner": "lint_violation",
            "next_workflow": "rtl-gen",
            "reason": "lint stage failed; RTL hygiene fix required",
            "confidence": "high",
        }
    if stage == "sim":
        return {
            "owner": "tb_bug",
            "next_workflow": "sim_debug",
            "reason": "sim failed; sim_debug must classify mismatches before repair",
            "confidence": "medium",
        }
    if stage == "sim_debug":
        return {
            "owner": "frontier",
            "next_workflow": HUMAN_ESCALATION,
            "reason": "sim_debug ran without producing an owner classification",
            "confidence": "low",
        }
    if stage == "coverage":
        return {
            "owner": "coverage_gap",
            "next_workflow": "tb-gen",
            "reason": "coverage bins missing; tb-gen → sim → coverage loop",
            "confidence": "high",
        }
    if stage in ("sta", "sta-post", "psta"):
        if _text_has_any(error_text, _TIMING_HOLD_HINTS):
            return {
                "owner": "timing_hold",
                "next_workflow": "rtl-gen",
                "reason": "hold violation; RTL pipelining or buffering change",
                "confidence": "medium",
            }
        if _text_has_any(error_text, _TIMING_SETUP_HINTS):
            return {
                "owner": "timing_setup",
                "next_workflow": HUMAN_ESCALATION,
                "reason": "setup/WNS failure; needs SSOT/RTL/constraint triage",
                "confidence": "medium",
            }
        return {
            "owner": "timing_setup",
            "next_workflow": HUMAN_ESCALATION,
            "reason": "timing stage failed without a parseable category",
            "confidence": "low",
        }
    if stage == "pnr":
        if _text_has_any(error_text, _SSOT_GAP_HINTS):
            return {
                "owner": "ssot_gap",
                "next_workflow": "ssot-gen",
                "reason": "PnR preflight reported missing SSOT physical/EDA policy",
                "confidence": "high",
            }
        if _text_has_any(error_text, _PNR_SETUP_HINTS):
            return {
                "owner": "pnr_setup",
                "next_workflow": "pnr",
                "reason": "PnR failed inside physical implementation/tool handoff; retry pnr after preserving evidence",
                "confidence": "medium",
            }
        return {
            "owner": "pnr_setup",
            "next_workflow": "pnr",
            "reason": "PnR stage failed; keep the loop in pnr before escalating",
            "confidence": "medium",
        }
    if stage in ("ssot", "ssot-gen"):
        return {
            "owner": "ssot_gap",
            "next_workflow": HUMAN_ESCALATION,
            "reason": "ssot stage failed; specification gap must be resolved by human",
            "confidence": "medium",
        }
    if stage in ("syn",):
        if _text_has_any(error_text, _SSOT_GAP_HINTS):
            return {
                "owner": "ssot_gap",
                "next_workflow": "ssot-gen",
                "reason": "synthesis preflight reported missing SSOT synthesis/EDA policy",
                "confidence": "high",
            }
        return {
            "owner": "rtl_bug",
            "next_workflow": "rtl-gen",
            "reason": "synthesis failure typically indicates illegal RTL construct",
            "confidence": "medium",
        }

    # 3. Default: escalate frontier.
    return {
        "owner": "frontier",
        "next_workflow": HUMAN_ESCALATION,
        "reason": f"no deterministic rule for stage={stage_id}; escalate to human",
        "confidence": "low",
    }
