"""Orchestrator tool layer.

Each tool returns ``(result_dict, evidence_summary)`` where the summary is a
short string (<= 2 KB) suitable for persisting to ``orchestrator_steps``.
Tools wrap existing helpers — they do not re-implement dispatch, state read,
or handoff logic.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Tuple

from src.orchestrator.classify import HUMAN_ESCALATION, classify_failure


ToolResult = Tuple[Dict[str, Any], str]


_EVIDENCE_CAP = 2_000


def _truncate(text: str, cap: int = _EVIDENCE_CAP) -> str:
    if text is None:
        return ""
    text = str(text)
    if len(text) <= cap:
        return text
    return text[: cap - 20] + "\n…[truncated]"


def _safe_json(value: Any, cap: int = _EVIDENCE_CAP) -> str:
    try:
        return _truncate(json.dumps(value, ensure_ascii=False, sort_keys=True), cap)
    except Exception:
        return _truncate(repr(value), cap)


# ----------------------------------------------------------------------
# Bridge resolution — read_pipeline_state / dispatch_workflow live in
# core.tools as module-level callbacks installed by register_jobs_routes.
# ----------------------------------------------------------------------


def _read_pipeline_state_bridge() -> Optional[Callable]:
    try:
        from core import tools as core_tools  # type: ignore
    except Exception:
        return None
    return getattr(core_tools, "_read_pipeline_state_callback", None)


def _dispatch_workflow_bridge() -> Optional[Callable]:
    try:
        from core import tools as core_tools  # type: ignore
    except Exception:
        return None
    return getattr(core_tools, "_dispatch_workflow_callback", None)


def _jobs_registry() -> Optional[Tuple[Dict[str, Any], Any]]:
    """Return (_jobs, _jobs_lock) from src.atlas_api_jobs, or None."""
    try:
        from src import atlas_api_jobs  # type: ignore
    except Exception:
        return None
    jobs = getattr(atlas_api_jobs, "_jobs", None)
    lock = getattr(atlas_api_jobs, "_jobs_lock", None)
    if jobs is None or lock is None:
        return None
    return jobs, lock


def _pipeline_stage_deps() -> Dict[str, Tuple[str, ...]]:
    try:
        from src import atlas_api_jobs  # type: ignore

        return getattr(atlas_api_jobs, "_PIPELINE_STAGE_DEPS", {})
    except Exception:
        return {}


# ----------------------------------------------------------------------
# Tools
# ----------------------------------------------------------------------


def read_pipeline_state(ip: str, include_jobs: bool = True) -> ToolResult:
    bridge = _read_pipeline_state_bridge()
    if bridge is None:
        return (
            {"ok": False, "error": "read_pipeline_state bridge not registered"},
            "bridge unavailable",
        )
    result = bridge(ip=ip, scope="", include_jobs=bool(include_jobs))
    summary = _safe_json(
        {
            "ip": ip,
            "passed": result.get("passed") if isinstance(result, dict) else None,
            "failed": result.get("failed") if isinstance(result, dict) else None,
            "running": result.get("running") if isinstance(result, dict) else None,
        }
    )
    return result if isinstance(result, dict) else {"ok": False, "raw": str(result)}, summary


def dispatch_workflow(
    *,
    workflow: str,
    ip: str,
    payload: Optional[Dict[str, Any]] = None,
    schedule: str = "auto",
    reason: str = "",
    orchestrator_run_id: str = "",
    model: str = "",
    run_mode: str = "",
    exec_mode: str = "",
) -> ToolResult:
    bridge = _dispatch_workflow_bridge()
    if bridge is None:
        return (
            {"ok": False, "error": "dispatch_workflow bridge not registered"},
            "bridge unavailable",
        )
    body = dict(payload or {})
    if orchestrator_run_id:
        body.setdefault("orchestrator_run_id", orchestrator_run_id)
        body.setdefault("trigger_source", "orchestrator_chat")
    if reason:
        body.setdefault("reason", reason)
    result = bridge(
        workflow=workflow,
        ip=ip,
        payload=body,
        schedule=schedule,
        reason=reason,
        model=model,
        run_mode=run_mode,
        exec_mode=exec_mode,
    )
    if not isinstance(result, dict):
        return {"ok": False, "raw": str(result)}, "non-dict result"
    job_ids = [j.get("job_id") for j in (result.get("jobs") or []) if isinstance(j, dict)]
    summary = _safe_json(
        {
            "ok": result.get("ok"),
            "pipeline_run_id": result.get("pipeline_run_id"),
            "job_ids": job_ids,
            "error": result.get("error"),
        }
    )
    return result, summary


def wait_job(job_id: str) -> ToolResult:
    """Non-blocking snapshot of a job by id.

    Returns the current state immediately. The loop is expected to call this
    again on the next iteration if the job is still running, so a long-running
    worker never holds an orchestrator thread.
    """
    registry = _jobs_registry()
    if registry is None:
        return (
            {"ok": False, "error": "job registry unavailable"},
            "registry unavailable",
        )
    jobs, lock = registry
    with lock:
        job = jobs.get(job_id)
        snapshot = dict(job) if job else None
    if snapshot is None:
        return ({"ok": False, "error": f"unknown job {job_id!r}"}, f"missing {job_id}")
    summary = _safe_json(
        {
            "job_id": snapshot.get("job_id"),
            "status": snapshot.get("status"),
            "workflow": snapshot.get("workflow"),
            "stage_id": snapshot.get("stage_id"),
        }
    )
    return {"ok": True, "job": snapshot}, summary


def read_artifact(ip: str, stage: str, project_root: Optional[Path] = None) -> ToolResult:
    """Read canonical evidence for ``stage`` under ``<ip>/...``.

    Resolves the canonical path map used by the pipeline state reader.
    JSON files are parsed; other files return a head-of-file text slice.
    """
    pr = Path(project_root) if project_root else Path(
        os.environ.get("ATLAS_PROJECT_ROOT") or "."
    )
    ip_dir = pr / ip
    artifact_map: Dict[str, Tuple[str, ...]] = {
        "ssot": ("yaml/{ip}.ssot.yaml",),
        "fl-model": ("model/fl_model_check.json", "cov/fcov_plan.json"),
        "cl-model": ("model/cl_model_check.json",),
        "equivalence": ("verify/equivalence_goals.json",),
        "rtl": (
            "rtl/rtl_compile.json",
            "lint/dut_lint.json",
            "rtl/rtl_todo_plan.json",
        ),
        "lint": ("lint/dut_lint.json",),
        "tb": ("tb/cocotb/",),
        "sim": ("sim/results.xml", "sim/fl_rtl_compare.json"),
        "coverage": ("cov/coverage.json",),
        "sim-debug": ("sim/mismatch_classification.json",),
        "goal-audit": ("sim/fl_rtl_goal_audit.json",),
        "syn": ("syn/out/",),
        "sta": ("sta/out/",),
        "pnr": ("pnr/out/",),
        "sta-post": ("sta-post/out/",),
    }
    relatives = artifact_map.get(stage, ())
    artifacts: list = []
    for rel in relatives:
        path = ip_dir / rel.format(ip=ip)
        entry: Dict[str, Any] = {"rel": rel, "path": str(path), "exists": path.exists()}
        if path.is_file():
            try:
                if path.suffix == ".json":
                    entry["data"] = json.loads(path.read_text(encoding="utf-8"))
                else:
                    entry["head"] = path.read_text(encoding="utf-8", errors="replace")[:8_000]
            except Exception as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
        elif path.is_dir():
            try:
                entry["entries"] = sorted(p.name for p in path.iterdir())[:50]
            except Exception as exc:
                entry["error"] = f"{type(exc).__name__}: {exc}"
        artifacts.append(entry)
    result = {"ok": True, "ip": ip, "stage": stage, "artifacts": artifacts}
    summary = _safe_json(
        {
            "stage": stage,
            "files": [a["rel"] for a in artifacts if a["exists"]],
            "missing": [a["rel"] for a in artifacts if not a["exists"]],
        }
    )
    return result, summary


def classify_failure_tool(
    *,
    stage: str,
    evidence: Optional[Dict[str, Any]] = None,
    error_text: str = "",
) -> ToolResult:
    decision = classify_failure(stage, evidence=evidence, error_text=error_text)
    summary = _safe_json(decision)
    return decision, summary


def ask_user(
    *,
    db: Any,
    run_id: str,
    ip_id: str,
    user_id: str,
    session_id: str,
    question: str,
    context: Optional[Dict[str, Any]] = None,
) -> ToolResult:
    """Record a human-decision-required event and mark the run paused.

    The accompanying step (written by the loop) records ``verdict="awaiting_user"``;
    this tool's job is to surface the question on the trace ledger so the UI
    chat stream can render it.
    """
    payload = {
        "run_id": run_id,
        "question": question,
        "context": context or {},
    }
    db.record_trace_event(
        event_type="orchestrator_ask_user",
        payload=payload,
        session_id=session_id,
        ip_id=ip_id,
        actor_user_id=user_id,
        correlation_id=run_id,
    )
    db.update_orchestrator_run(run_id, status="paused")
    return ({"ok": True, "state": "paused", "question": question}, _truncate(question))


def write_handoff(
    *,
    ip: str,
    workflow: str,
    payload: Dict[str, Any],
    reason: str,
    user_id: str,
    session_id: str,
    pipeline_run_id: str,
    orchestrator_run_id: str = "",
    from_workflow: str = "orchestrator",
    project_root: Optional[Path] = None,
) -> ToolResult:
    from src import handoff_queue

    pr = Path(project_root) if project_root else Path(
        os.environ.get("ATLAS_PROJECT_ROOT") or "."
    )
    ip_dir = pr / ip
    scope = handoff_queue.make_scope(
        user_id=user_id,
        session_id=session_id,
        pipeline_run_id=pipeline_run_id,
    )
    handoff_id = handoff_queue.make_handoff_id(
        ip=ip,
        from_workflow=from_workflow,
        to_workflow=workflow,
        suffix=(orchestrator_run_id[:8] if orchestrator_run_id else ""),
    )
    record = {
        "handoff_id": handoff_id,
        "ip": ip,
        "from_workflow": from_workflow,
        "to_workflow": workflow,
        "scope": scope,
        "reason": reason,
        "payload": payload,
    }
    if orchestrator_run_id:
        record["orchestrator_run_id"] = orchestrator_run_id
    written = handoff_queue.write_pending(ip_dir, record)
    summary = _safe_json({"handoff_id": handoff_id, "path": str(written)})
    return ({"ok": True, "handoff_id": handoff_id, "path": str(written)}, summary)


def mark_downstream_stale(
    *,
    db: Any,
    ip_id: str,
    from_stage: str,
    run_id: str = "",
    session_id: str = "",
) -> ToolResult:
    """Emit stage_stale trace events for every downstream stage of from_stage."""
    deps = _pipeline_stage_deps()
    if not deps:
        return (
            {"ok": False, "error": "pipeline stage graph unavailable"},
            "graph missing",
        )
    downstream: list = []
    seen: set = set()
    frontier = [
        s for s, parents in deps.items() if from_stage in parents
    ]
    while frontier:
        cur = frontier.pop()
        if cur in seen:
            continue
        seen.add(cur)
        downstream.append(cur)
        frontier.extend(
            s for s, parents in deps.items() if cur in parents and s not in seen
        )
    for stage in downstream:
        db.record_trace_event(
            event_type="stage_stale",
            payload={"from_stage": from_stage, "stale_stage": stage, "run_id": run_id},
            ip_id=ip_id,
            session_id=session_id,
            stage_id=stage,
            correlation_id=run_id,
        )
    return (
        {"ok": True, "from_stage": from_stage, "stale": downstream},
        _safe_json({"from": from_stage, "stale": downstream}),
    )
