#!/usr/bin/env python3
"""UI-neutral adapter around the shared workflow stage engine.

The engine owns execution and disk-truth validation.  This module owns the
small amount of surface policy that every UI needs to agree on: session name,
workflow name, repair prompts, and human-gate signals.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from src.workflow_stage_engine import STAGE_WORKFLOW, WorkflowStageEngine, canonical_stage
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from workflow_stage_engine import STAGE_WORKFLOW, WorkflowStageEngine, canonical_stage


COMMON_ENGINE_STAGES = {
    "ssot-fl-model",
    "ssot-cycle-model",
    "ssot-dual-fcov",
    "ssot-equiv-goals",
    "ssot-rtl",
    "lint",
    "ssot-tb",
    "ssot-tb-cocotb",
    "coverage",
    "sim",
    "sim-debug",
    "goal-audit",
}


LLM_RTL_BLOCKERS = {
    "RTL_TODO_PLAN_MISSING",
    "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
    "LLM_RTL_IMPLEMENTATION_REQUIRED",
    "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
}

RTL_DRAFT_COMPATIBLE_BLOCKERS = LLM_RTL_BLOCKERS | {
    "RTL_TARGET_SCALE_POLICY",
}


def _is_llm_rtl_blocker(doc: Any) -> bool:
    if not isinstance(doc, dict):
        return False
    questions = doc.get("questions")
    if not isinstance(questions, list) or not questions:
        return False
    ids = {
        str(question.get("id") or "")
        for question in questions
        if isinstance(question, dict)
    }
    return bool(ids & LLM_RTL_BLOCKERS) and ids <= RTL_DRAFT_COMPATIBLE_BLOCKERS


@dataclass
class StageSurfaceResult:
    handled: bool
    alias: str
    workflow: str = ""
    session: str = ""
    message: str = ""
    status: str = ""
    queue_prompts: list[str] = field(default_factory=list)
    rtl_blocked: bool = False
    sim_human_gate_doc: dict[str, Any] | None = None
    keep_running: bool = False


def is_common_stage(alias: str) -> bool:
    return canonical_stage(alias) in COMMON_ENGINE_STAGES


def _rtl_authoring_summary(project_root: Path, ip: str) -> str:
    path = project_root / ip / "rtl" / "rtl_authoring_plan.json"
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    if not summary:
        return ""
    parts = []
    for key in (
        "packets",
        "module_packets",
        "sliced_module_packets",
        "required_tasks",
        "max_packet_required_tasks",
        "target_scale_present",
        "deferred_human_qa_allowed",
        "pass_allowed",
        "recommended_packet_batch_limit",
        "llm_actionable_packets",
        "llm_actionable_tasks",
        "human_locked_packets",
        "human_locked_tasks",
    ):
        if key in summary:
            parts.append(f"{key}={summary[key]}")
    next_packets = summary.get("next_llm_packets") if isinstance(summary.get("next_llm_packets"), list) else []
    if next_packets:
        parts.append("next_llm_packets=" + "|".join(str(item) for item in next_packets[:5]))
    reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
    suggested = reference_profile.get("suggested_ssot_target_scale") if isinstance(reference_profile.get("suggested_ssot_target_scale"), dict) else {}
    if suggested and not bool(summary.get("target_scale_present")):
        parts.append("reference_target_scale_candidate=true")
    return ", ".join(parts)


def run_common_stage_surface(
    *,
    project_root: str | Path,
    source_root: str | Path | None,
    alias: str,
    ip: str,
    template: str = "",
) -> StageSurfaceResult:
    """Run a common stage and return UI-neutral side-effect instructions."""
    engine_alias = canonical_stage(alias)
    if engine_alias not in COMMON_ENGINE_STAGES:
        return StageSurfaceResult(handled=False, alias=engine_alias)

    result = WorkflowStageEngine(project_root, source_root=source_root).run_stage(engine_alias, ip)
    workflow = STAGE_WORKFLOW.get(engine_alias, engine_alias)
    template = template or engine_alias
    surface = StageSurfaceResult(
        handled=True,
        alias=engine_alias,
        workflow=workflow,
        session=f"{ip}/{workflow}",
        message=result.message,
        status=result.status,
    )
    metadata = result.metadata if isinstance(result.metadata, dict) else {}
    project_root_path = Path(project_root)

    if engine_alias == "ssot-rtl" and _is_llm_rtl_blocker(metadata.get("rtl_blocked")):
        authoring_summary = _rtl_authoring_summary(project_root_path, ip)
        surface.queue_prompts = [
            "/mode normal",
            "/wf rtl-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Implement RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml and the dynamic "
                f"TodoTracker list loaded from {ip}/rtl/rtl_todo_tracker.json.\n"
                f"Use {ip}/rtl/rtl_authoring_plan.json and open packets under "
                f"{ip}/rtl/authoring_packets/ as the work queue; review "
                f"{ip}/rtl/rtl_authoring_status.md for a human-readable queue preview"
                f"{f' ({authoring_summary})' if authoring_summary else ''}. Process module packets first, "
                "then unowned tasks, then rtl_gate_closure. For sliced packets, merge into the same "
                "owner_file and preserve prior slice logic; start from next_llm_packets when listed "
                "and skip packets whose llm_actionable_open_count is zero.\n\n"
                "Write only RTL-owned "
                "artifacts, keep SSOT/function model/coverage/interface targets locked, write "
                "rtl/rtl_authoring_provenance.json with common_ai_agent rtl-gen provenance, then rerun "
                "/ssot-rtl until the dynamic TODO gate, DUT-only compile, and DUT-only lint pass.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-rtl" and metadata.get("rtl_blocked"):
        surface.rtl_blocked = True
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-rtl" and metadata.get("needs_repair"):
        authoring_summary = _rtl_authoring_summary(project_root_path, ip)
        surface.queue_prompts = [
            "/mode normal",
            "/wf rtl-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Repair generated RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml using the "
                "common stage-engine evidence below. Repair only RTL-owned artifacts; do not "
                "change SSOT semantics and do not use fixed IP templates. Use "
                f"{ip}/rtl/rtl_authoring_plan.json and open packets under {ip}/rtl/authoring_packets/"
                f"; review {ip}/rtl/rtl_authoring_status.md for the current queue preview"
                f"{f' ({authoring_summary})' if authoring_summary else ''}; merge sliced packet repairs into "
                "existing owner files instead of replacing earlier packet logic; start from next_llm_packets "
                "when listed and skip packets whose llm_actionable_open_count is zero. Rerun DUT-only compile "
                "and lint through the common engine before reporting DONE.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-tb-cocotb" and metadata.get("needs_repair"):
        surface.queue_prompts = [
            "/mode normal",
            "/wf tb-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Repair generated pyuvm/cocotb TB for {ip} using SSOT, FunctionalModel, "
                "equivalence_goals.json, rtl_contract.json, and the common stage-engine evidence "
                "below. Do not use fixed IP templates. Preserve EquivalenceScoreboard and rerun "
                "the common TB stage before reporting DONE.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "sim-debug" and isinstance(metadata.get("mismatch_classification"), dict):
        surface.sim_human_gate_doc = metadata["mismatch_classification"]
        surface.keep_running = True

    return surface
