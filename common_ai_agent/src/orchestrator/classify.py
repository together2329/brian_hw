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
    "rtl-gen": "rtl-gen",
    "tb-gen": "tb-gen",
    "fl-model-gen": "equivalence",
    "sim-debug": "sim_debug",
    "sim_debug": "sim_debug",
    "frontier": HUMAN_ESCALATION,
    "coverage_gap": "tb-gen",
    "lint_violation": "rtl-gen",
    "compile_error": "rtl-gen",
    "timing_setup": HUMAN_ESCALATION,
    "timing_hold": "rtl-gen",
    "ssot_gap": "ssot-gen",
    "ssot-gen": "ssot-gen",
    "pnr_setup": "pnr",
    "stale_oracle": "equivalence",
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
    "llm-authored rtl needs rtl-gen repair",
    "audit_rtl_todos",
    "open_required_todos",
    "static_missing_details",
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
_STALE_ORACLE_HINTS = (
    "classification=stale_oracle",
    '"classification": "stale_oracle"',
    "'classification': 'stale_oracle'",
    "stale oracle",
    "older than the current ssot",
    "older than current ssot",
    "derived fl/equivalence oracle artifacts are older",
    "regenerate functionalmodel",
    "regenerate functional model",
    "regenerate derived oracle artifacts",
)
_STALE_SIM_DEBUG_ARTIFACT_HINTS = (
    "freshness_status=stale_artifact",
    "freshness_status stale_artifact",
    "stale_artifact",
    "fl_rtl_compare.json older than sim/scoreboard_events",
    "mismatch_classification.json older than sim/scoreboard_events",
    "fl_rtl_compare.json is older than sim/scoreboard_events",
    "mismatch_classification.json is older than sim/scoreboard_events",
    "compare artifact older than fresh sim evidence",
    "classification artifact older than fresh sim evidence",
)
_TB_MISSING_EQUIVALENCE_HINTS = (
    "missing equivalence goals",
    "missing equivalence_goals",
    "missing verify/equivalence_goals.json",
    "verify/equivalence_goals.json is missing",
    "equivalence_goals.json missing",
    "tb_generator_input",
)
_TB_MISSING_FL_HINTS = (
    "missing functional model",
    "missing model/functional_model.py",
    "functional_model.py missing",
)


def _text_has_any(text: str, hints) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return any(h in lowered for h in hints)


def _is_stale_sim_debug_artifact(evidence: Any) -> bool:
    if not isinstance(evidence, dict):
        return False
    if evidence.get("freshness_status") == "stale_artifact":
        rel = str(evidence.get("rel") or evidence.get("path") or "").lower()
        if "sim/fl_rtl_compare.json" in rel or "sim/mismatch_classification.json" in rel:
            return True
        stale_against = evidence.get("stale_against")
        if isinstance(stale_against, list) and stale_against:
            return True
    for key in ("previews", "artifacts"):
        items = evidence.get(key)
        if isinstance(items, list):
            for item in items:
                if _is_stale_sim_debug_artifact(item):
                    return True
    return False


def _flatten_text(value: Any, *, _depth: int = 0, _limit: int = 24_000) -> str:
    if _depth > 6 or value is None or _limit <= 0:
        return ""
    if isinstance(value, str):
        return value[:_limit]
    if isinstance(value, (int, float, bool)):
        return str(value)
    chunks: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            chunks.append(str(key))
            chunks.append(_flatten_text(nested, _depth=_depth + 1, _limit=_limit))
            if sum(len(c) for c in chunks) > _limit:
                break
    elif isinstance(value, list):
        for item in value[:80]:
            chunks.append(_flatten_text(item, _depth=_depth + 1, _limit=_limit))
            if sum(len(c) for c in chunks) > _limit:
                break
    return " ".join(c for c in chunks if c)[:_limit]


def _owner_from_classification_items(items: Any) -> Optional[str]:
    if not isinstance(items, list) or not items:
        return None
    # Stale oracle evidence invalidates RTL/TB ownership until the derived
    # FL/equivalence artifacts are regenerated from the current SSOT.
    for item in items:
        if not isinstance(item, dict):
            continue
        classification = str(item.get("classification") or "").lower()
        owner = item.get("owner") or item.get("owner_workflow")
        if classification == "stale_oracle":
            return str(owner or "fl-model-gen")

    precedence = (
        "frontier",
        "ssot_gap",
        "ssot-gen",
        "fl-model-gen",
        "rtl_bug",
        "rtl-gen",
        "tb_bug",
        "tb-gen",
        "coverage_gap",
    )
    owners = {
        item.get("owner")
        or item.get("owner_workflow")
        or (
            str(item.get("classification")).lower()
            if str(item.get("classification") or "").lower() in _OWNER_ROUTES
            else None
        )
        for item in items
        if isinstance(item, dict)
    }
    for tier in precedence:
        if tier in owners:
            return tier
    return None


def _owner_from_single_classification(item: Any) -> Optional[str]:
    if not isinstance(item, dict):
        return None
    classification = str(item.get("classification") or "").lower()
    owner = item.get("owner") or item.get("owner_workflow")
    if classification == "stale_oracle":
        return str(owner or "fl-model-gen")
    if isinstance(owner, str) and owner:
        return owner
    if classification in _OWNER_ROUTES:
        return classification
    return None


def _read_owner_from_evidence(evidence: Dict[str, Any], *, _depth: int = 0) -> Optional[str]:
    """Lift owner classification out of ``sim_debug`` evidence if present."""
    if not evidence or _depth > 6:
        return None
    if _is_stale_sim_debug_artifact(evidence):
        return "sim-debug"
    owner = _owner_from_single_classification(evidence)
    if owner:
        return owner
    owner = _owner_from_classification_items(evidence.get("classifications"))
    if owner:
        return owner
    mc = evidence.get("mismatch_classification")
    if isinstance(mc, dict):
        owner = _owner_from_classification_items(mc.get("classifications"))
        if owner:
            return owner
        owner = mc.get("owner")
        if isinstance(owner, str) and owner:
            return owner
    if isinstance(mc, list) and mc:
        owner = _owner_from_classification_items(mc)
        if owner:
            return owner
    artifacts = evidence.get("artifacts")
    if isinstance(artifacts, list):
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            data = artifact.get("data")
            if isinstance(data, dict):
                owner = _read_owner_from_evidence(data, _depth=_depth + 1)
                if owner:
                    return owner
    owner = evidence.get("owner")
    if isinstance(owner, str) and owner:
        return owner
    for value in evidence.values():
        if isinstance(value, dict):
            owner = _read_owner_from_evidence(value, _depth=_depth + 1)
            if owner:
                return owner
        elif isinstance(value, list):
            owner = _owner_from_classification_items(value)
            if owner:
                return owner
            for item in value[:20]:
                if isinstance(item, dict):
                    owner = _read_owner_from_evidence(item, _depth=_depth + 1)
                    if owner:
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
    combined_error_text = " ".join(
        part for part in (error_text, _flatten_text(evidence)) if part
    )

    # 1. Explicit owner classification wins.
    owner = _read_owner_from_evidence(evidence)
    if owner and owner in _OWNER_ROUTES:
        return {
            "owner": owner,
            "next_workflow": _OWNER_ROUTES[owner],
            "reason": f"owner={owner} from {stage} evidence",
            "confidence": "high",
        }

    if _text_has_any(combined_error_text, _STALE_SIM_DEBUG_ARTIFACT_HINTS):
        return {
            "owner": "sim-debug",
            "next_workflow": "sim_debug",
            "reason": "sim_debug compare/classification artifact is older than fresh sim evidence; rerun sim_debug before owner routing",
            "confidence": "high",
        }

    if _text_has_any(combined_error_text, _STALE_ORACLE_HINTS):
        return {
            "owner": "fl-model-gen",
            "next_workflow": "equivalence",
            "reason": "stale FL/equivalence oracle evidence; rerun equivalence stage on the fl-model-gen worker before RTL/TB repair",
            "confidence": "high",
        }

    # 2. Stage-specific deterministic rules.
    if stage in ("rtl", "rtl-gen"):
        if _text_has_any(combined_error_text, _RTL_SSOT_CONTRACT_HINTS):
            return {
                "owner": "ssot_gap",
                "next_workflow": "ssot-gen",
                "reason": "rtl-gen blocked on missing SSOT module contracts",
                "confidence": "high",
            }
        if _text_has_any(combined_error_text, _RTL_MISSING_ARTIFACT_HINTS):
            return {
                "owner": "compile_error",
                "next_workflow": "rtl-gen",
                "reason": "RTL artifact/filelist is incomplete; rerun rtl-gen after preserving evidence",
                "confidence": "high",
            }
        if _text_has_any(combined_error_text, _COMPILE_HINTS):
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
    if stage in ("tb", "tb-gen", "ssot-tb", "ssot-tb-cocotb"):
        if _text_has_any(combined_error_text, _TB_MISSING_EQUIVALENCE_HINTS):
            return {
                "owner": "fl-model-gen",
                "next_workflow": "equivalence",
                "reason": "tb-gen is blocked on missing verify/equivalence_goals.json; generate FL/equivalence goals before TB repair",
                "confidence": "high",
            }
        if _text_has_any(combined_error_text, _TB_MISSING_FL_HINTS):
            return {
                "owner": "fl-model-gen",
                "next_workflow": "equivalence",
                "reason": "tb-gen is blocked on missing FunctionalModel/equivalence inputs; regenerate FL/equivalence artifacts first",
                "confidence": "high",
            }
        return {
            "owner": "tb_bug",
            "next_workflow": "tb-gen",
            "reason": "tb-gen failed after required upstream artifacts were present; repair TB artifacts",
            "confidence": "medium",
        }
    if stage in ("sim_debug", "sim-debug"):
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
        if _text_has_any(combined_error_text, _TIMING_SETUP_HINTS):
            return {
                "owner": "timing_setup",
                "next_workflow": HUMAN_ESCALATION,
                "reason": "setup/WNS failure; needs SSOT/RTL/constraint triage",
                "confidence": "medium",
            }
        if _text_has_any(combined_error_text, _TIMING_HOLD_HINTS):
            return {
                "owner": "timing_hold",
                "next_workflow": "rtl-gen",
                "reason": "hold violation; RTL pipelining or buffering change",
                "confidence": "medium",
            }
        return {
            "owner": "timing_setup",
            "next_workflow": HUMAN_ESCALATION,
            "reason": "timing stage failed without a parseable category",
            "confidence": "low",
        }
    if stage == "pnr":
        if _text_has_any(combined_error_text, _SSOT_GAP_HINTS):
            return {
                "owner": "ssot_gap",
                "next_workflow": "ssot-gen",
                "reason": "PnR preflight reported missing SSOT physical/EDA policy",
                "confidence": "high",
            }
        if _text_has_any(combined_error_text, _PNR_SETUP_HINTS):
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
        if _text_has_any(combined_error_text, _SSOT_GAP_HINTS):
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
