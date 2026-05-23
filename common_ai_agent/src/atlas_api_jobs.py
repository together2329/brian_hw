"""ATLAS jobs API — extracted from atlas_ui.py (phase 6 of split).

Holds the HTTP-worker dispatch tracker: state, helpers, and all
/api/job* + /api/jobs* + /api/pipeline/* routes.  The host
(atlas_ui.py) wires routes via ``register_jobs_routes`` and injects
callables for runtime values so this module never reaches into the
host's mutable globals.

Exposed helpers
---------------
get_jobs_state() -> tuple[dict, threading.Lock]
    Returns (_jobs, _jobs_lock) so atlas_ui.py routes that need to
    read job state (e.g. /api/session/state) can do so without
    reaching into this module's globals directly.
"""
from __future__ import annotations

import atexit
import json
import logging
import logging.handlers
import os
import re
import shlex
import hashlib
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import uuid
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.orchestrator.profile import (
    ORCHESTRATOR_MODEL,
    ORCHESTRATOR_REASONING_EFFORT,
    orchestrator_profile_name,
)

# ── Module-level state ──────────────────────────────────────────────
_jobs_lock = threading.Lock()
_jobs: dict[str, dict[str, Any]] = {}   # job_id (uuid hex) → job metadata
_SOURCE_ROOT = Path(__file__).resolve().parents[1]
_LAZY_WORKER_LOCK = threading.Lock()
_LAZY_WORKER_PROCS: dict[str, subprocess.Popen] = {}
_LAZY_WORKER_ATEXIT_REGISTERED = False
# Per-URL locks so concurrent dispatches to *different* worker URLs do
# not serialize through a single global lock during cold-start storms.
_LAZY_WORKER_URL_LOCKS: dict[str, threading.RLock] = {}
# Bounds the number of simultaneous `python3 main.py --serve` spawns so
# 12-way cold-start does not thrash import I/O and exhaust the 15s
# ATLAS_LAZY_WORKER_START_TIMEOUT for every worker at once.
_LAZY_WORKER_SPAWN_SEM = threading.Semaphore(
    max(1, int(os.environ.get("ATLAS_LAZY_WORKER_SPAWN_PARALLEL", "4") or 4))
)
# Reaper thread state: detects workers that died after dispatch so the
# associated `_jobs` entries can be marked failed instead of sitting in
# "running" forever.
_LAZY_WORKER_REAPER_STARTED = False
_LAZY_WORKER_REAPER_INTERVAL = float(
    os.environ.get("ATLAS_LAZY_WORKER_REAPER_INTERVAL", "5.0") or 5.0
)
# Short-lived cache for /health probes used by the UI fan-out at
# /api/orchestrator/workers. Dispatch path still calls the uncached
# probe so cold-start detection remains accurate.
_HEALTH_CACHE_LOCK = threading.Lock()
_HEALTH_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_HEALTH_CACHE_TTL = float(
    os.environ.get("ATLAS_HEALTH_PROBE_CACHE_SEC", "1.5") or 1.5
)


def _dispatch_logger() -> logging.Logger:
    """Module logger with stdout + rotating-file handlers.

    Replaces the previous `print(..., flush=True)` calls in the dispatch
    and lazy-worker paths. Keeps terminal visibility unchanged while
    routing every event to `.session/atlas-dispatch.log` (5MB × 3
    backups) so a slow tty cannot stall a dispatch thread on the
    parent's stdout PIPE buffer.
    """
    log = logging.getLogger("atlas.dispatch")
    if getattr(log, "_atlas_configured", False):
        return log
    log.setLevel(logging.INFO)
    log.propagate = False
    fmt = logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")
    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(fmt)
    log.addHandler(stream)
    try:
        log_dir = Path(os.environ.get("ATLAS_PROJECT_ROOT") or ".") / ".session"
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_dir / "atlas-dispatch.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        fh.setFormatter(fmt)
        log.addHandler(fh)
    except Exception:
        pass
    log._atlas_configured = True  # type: ignore[attr-defined]
    return log


_LOG = _dispatch_logger()


def _resolve_workflow_root(raw: str | Path | None = None) -> Path:
    value = str(raw or os.environ.get("ATLAS_WORKFLOW_ROOT") or "").strip()
    base = Path(os.path.expandvars(value)).expanduser() if value else _SOURCE_ROOT / "workflow"
    if not base.is_absolute():
        base = _SOURCE_ROOT / base
    if (base / "ssot-gen").is_dir():
        return base.resolve()
    if (base / "workflow" / "ssot-gen").is_dir():
        return (base / "workflow").resolve()
    return base.resolve()


_WORKFLOW_ROOT = _resolve_workflow_root()


def _workflow_root_for_project(project_root: Path) -> Path:
    local = _resolve_workflow_root(project_root)
    if (local / "ssot-gen").is_dir():
        return local
    return _WORKFLOW_ROOT


def _configured_ip_root(project_root: Path, ip: str) -> Path | None:
    raw = os.environ.get("ATLAS_IP_ROOT", "").strip()
    if not raw:
        return None
    try:
        root = Path(os.path.expandvars(raw)).expanduser()
        if not root.is_absolute():
            root = project_root / root
        root = root.resolve()
    except Exception:
        return None
    if not root.is_dir():
        return None
    if root.name == ip:
        return root
    yaml_dir = root / "yaml"
    if yaml_dir.is_dir():
        for name in (f"{ip}.ssot.yaml", f"{ip}_ssot.yaml", f"{ip}.ssot.yml"):
            if (yaml_dir / name).is_file():
                return root
    nested = root / ip
    if nested.is_dir():
        return nested
    try:
        root.relative_to(project_root.resolve())
    except Exception:
        return None
    return None


def _ip_dir_for(project_root: Path, ip: str) -> Path:
    configured = _configured_ip_root(project_root, ip)
    if configured is not None:
        return configured
    direct = project_root / ip
    if direct.exists():
        return direct
    examples = project_root / "ip_examples" / ip
    if examples.exists():
        return examples
    return direct


def _tool_project_root_for_ip(project_root: Path, ip: str) -> Path:
    ip_dir = _ip_dir_for(project_root, ip)
    try:
        if ip_dir.resolve() != (project_root / ip).resolve() and ip_dir.parent.is_dir():
            return ip_dir.parent
    except Exception:
        pass
    return project_root

_PIPELINE_STAGES = [
    {"id": "ssot",        "workflow": "ssot-gen",     "label": "SSOT gen"},
    {"id": "fl-model",    "workflow": "fl-model-gen", "label": "FL model"},
    {"id": "cl-model",    "workflow": "fl-model-gen", "label": "CL model"},
    {"id": "equivalence", "workflow": "fl-model-gen", "label": "Equiv goals"},
    {"id": "rtl",         "workflow": "rtl-gen",      "label": "RTL gen"},
    {"id": "lint",        "workflow": "lint",         "label": "Lint"},
    {"id": "tb",          "workflow": "tb-gen",       "label": "TB gen"},
    {"id": "sim",         "workflow": "sim",          "label": "Simulation"},
    {"id": "coverage",    "workflow": "coverage",     "label": "Coverage"},
    {"id": "sim-debug",   "workflow": "sim_debug",    "label": "Sim debug"},
    {"id": "syn",         "workflow": "syn",          "label": "Synthesis"},
    {"id": "sta",         "workflow": "sta",          "label": "Pre-route STA"},
    {"id": "pnr",         "workflow": "pnr",          "label": "PnR"},
    {"id": "sta-post",    "workflow": "sta-post",     "label": "Post-route STA"},
    {"id": "goal-audit",  "workflow": "sim_debug",    "label": "Goal audit"},
]
_PIPELINE_BY_ID       = {s["id"]: s       for s in _PIPELINE_STAGES}
_PIPELINE_BY_WORKFLOW: dict[str, dict[str, str]] = {}
for _stage in _PIPELINE_STAGES:
    _PIPELINE_BY_WORKFLOW.setdefault(_stage["workflow"], _stage)
_PIPELINE_ALIASES: dict[str, str] = {
    "ssot-gen": "ssot",
    "fl": "fl-model",
    "fl-model-gen": "fl-model",
    "cl": "cl-model",
    "cl-model-gen": "cl-model",
    "cycle-model": "cl-model",
    "ssot-cycle-model": "cl-model",
    "equiv": "equivalence",
    "equiv-goals": "equivalence",
    "equivalence-goals": "equivalence",
    "ssot-equiv-goals": "equivalence",
    "rtl-gen": "rtl",
    "tb-gen": "tb",
    "sim_debug": "sim-debug",
    "sim-debug": "sim-debug",
    "debug": "sim-debug",
    "psta": "sta-post",
    "post-sta": "sta-post",
}


def _resolve_pipeline_stage(key: str) -> dict[str, str] | None:
    name = str(key or "").strip()
    if not name:
        return None
    alias = _PIPELINE_ALIASES.get(name) or _PIPELINE_ALIASES.get(name.lower())
    if alias:
        return _PIPELINE_BY_ID.get(alias)
    return _PIPELINE_BY_ID.get(name) or _PIPELINE_BY_WORKFLOW.get(name)

_PIPELINE_STAGE_ORDER = {stage["id"]: idx for idx, stage in enumerate(_PIPELINE_STAGES)}
_PIPELINE_STAGE_DEPS: dict[str, tuple[str, ...]] = {
    "ssot": (),
    "fl-model": ("ssot",),
    "cl-model": ("ssot",),
    "equivalence": ("fl-model", "cl-model"),
    "rtl": ("equivalence",),
    "lint": ("rtl",),
    "tb": ("rtl",),
    "syn": ("rtl",),
    "sim": ("tb",),
    "coverage": ("sim",),
    "sim-debug": ("sim",),
    "sta": ("syn",),
    "pnr": ("syn",),
    "sta-post": ("pnr",),
}
_PIPELINE_ALLOWED_FAILED_DEPS: dict[str, tuple[str, ...]] = {
    # sim-debug is the diagnostic consumer for failed simulation evidence.
    # A sim error caused by scoreboard/FL-vs-RTL mismatch must route into
    # sim-debug instead of blocking the very classifier that owns repair routing.
    "sim-debug": ("sim",),
}
_RTL_VERSION_DOWNSTREAM_STAGES = {
    "lint", "tb", "sim", "coverage", "sim-debug",
    "syn", "sta", "pnr", "sta-post", "goal-audit",
}
_STAGE_ARTIFACT_TYPES = {
    "ssot": "ssot",
    "rtl": "rtl",
    "tb": "tb",
}


def _junit_counts(results_xml: Path) -> tuple[int, int, int]:
    """Return (tests, failures, errors) for testsuite or testsuites XML."""
    root = ET.parse(str(results_xml)).getroot()
    suite_nodes = [node for node in root.iter() if node.tag.endswith("testsuite")]
    if root.tag.endswith("testsuite"):
        suite_nodes = [root]

    tests = failures = errors = 0
    for node in suite_nodes:
        tests += int(float(node.get("tests", 0) or 0))
        failures += int(float(node.get("failures", 0) or 0))
        errors += int(float(node.get("errors", 0) or 0))

    if tests == 0:
        tests = int(float(root.get("tests", 0) or 0))
    if failures == 0:
        failures = int(float(root.get("failures", 0) or 0))
    if errors == 0:
        errors = int(float(root.get("errors", 0) or 0))

    cases = [node for node in root.iter() if node.tag.endswith("testcase")]
    if tests == 0 and cases:
        tests = len(cases)
    if failures == 0 and cases:
        failures = sum(
            1 for case in cases
            if any(child.tag.endswith("failure") for child in list(case))
        )
    if errors == 0 and cases:
        errors = sum(
            1 for case in cases
            if any(child.tag.endswith("error") for child in list(case))
        )
    return tests, failures, errors
_RUN_MODES = ("starter", "engineering", "signoff")
_EXEC_MODES = ("single-worker", "orchestrator")
_WORKER_MODEL_DEFAULTS = {
    "orchestrator": "gpt-5.5",
    "ssot-gen": "gpt-5.5",
    "fl-model-gen": "gpt-5.5",
    "rtl-gen": "gpt-5.3-codex",
    "tb-gen": "deepseek",
    "sim_debug": "kimi",
    "lint": "deepseek",
    "sim": "gpt-5.3-codex",
    "coverage": "gpt-5.3-codex",
    "goal-audit": "gpt-5.5",
    "syn": "gpt-5.3-codex",
    "sta": "gpt-5.3-codex",
    "pnr": "gpt-5.3-codex",
    "sta-post": "gpt-5.3-codex",
}
_WORKER_REASONING_EFFORT_DEFAULTS = {
    "orchestrator": "high",
}
_WORKFLOW_TOOLCHAIN_DEFAULTS = {
    "lint": "pyslang + verilator",
    "sim": "icarus/verilator",
    "coverage": "verilator coverage + VCD",
    "sim_debug": "pyslang + verilator + VCD",
    "syn": "yosys",
    "sta": "opensta",
    "pnr": "openroad",
    "sta-post": "opensta",
}


def _workflow_env_suffix(workflow: str) -> str:
    return str(workflow or "").upper().replace("-", "_")


def _worker_model_for(workflow: str) -> str:
    wf = str(workflow or "").strip()
    suffix = _workflow_env_suffix(wf)
    return (
        os.environ.get(f"ATLAS_WORKER_MODEL_{suffix}", "")
        or os.environ.get(f"ATLAS_{suffix}_MODEL", "")
        or os.environ.get(f"WORKER_MODEL_{suffix}", "")
        or _WORKER_MODEL_DEFAULTS.get(wf, "")
    )


def _recent_chat_context_for_ip(
    db: Any,
    *,
    ip_name: str,
    owner_user_ids: list[str],
    limit: int = 8,
) -> list[dict[str, Any]]:
    """Return recent chat rows for one IP and owner identity.

    Older DB rows may have been written with the login name in
    ``workspaces.owner_user_id`` / ``trace_events.actor_user_id`` before Atlas
    started using canonical DB UUIDs.  Read both identities, scoped by IP name
    and workspace owner, so worker prompts keep the user's latest requirement
    without crossing into another user's workspace for the same IP name.
    """
    ip = str(ip_name or "").strip()
    owners = [str(item or "").strip() for item in owner_user_ids if str(item or "").strip()]
    owners = list(dict.fromkeys(owners))
    if not ip or not owners:
        return []
    placeholders = ",".join("?" for _ in owners)
    rows = db._fetchall(
        f"""
        SELECT te.*
          FROM trace_events te
          JOIN ip_blocks i ON i.id = te.ip_id
          JOIN workspaces w ON w.id = i.workspace_id
         WHERE te.event_type = 'chat_message'
           AND i.ip_name = ?
           AND w.owner_user_id IN ({placeholders})
         ORDER BY te.created_at DESC, te.id DESC
         LIMIT ?
        """,
        tuple([ip, *owners, int(limit)]),
    )
    return [db._row_to_dict(row, "trace_events") for row in rows]


def _worker_reasoning_effort_for(workflow: str) -> str:
    wf = str(workflow or "").strip()
    suffix = _workflow_env_suffix(wf)
    return (
        os.environ.get(f"ATLAS_WORKER_REASONING_EFFORT_{suffix}", "")
        or os.environ.get(f"ATLAS_WORKER_REASONING_{suffix}", "")
        or os.environ.get(f"ATLAS_{suffix}_REASONING_EFFORT", "")
        or os.environ.get(f"ATLAS_{suffix}_EFFORT", "")
        or os.environ.get(f"WORKER_REASONING_EFFORT_{suffix}", "")
        or _WORKER_REASONING_EFFORT_DEFAULTS.get(wf, "")
    )


def _workflow_toolchain_for(workflow: str) -> str:
    wf = str(workflow or "").strip()
    suffix = _workflow_env_suffix(wf)
    return (
        os.environ.get(f"ATLAS_WORKFLOW_TOOLCHAIN_{suffix}", "")
        or os.environ.get(f"WORKFLOW_TOOLCHAIN_{suffix}", "")
        or _WORKFLOW_TOOLCHAIN_DEFAULTS.get(wf, "")
    )


def _atlas_job_db_path(project_root: Path) -> str:
    return (
        os.environ.get("ATLAS_TRACE_DB_PATH")
        or os.environ.get("ATLAS_DB_PATH")
        or str(Path.home() / ".common_ai_agent" / "atlas.db")
    )


_UUID_RE = re.compile(r"^[a-f0-9]{32}$")


def _canonical_user_id(db: Any, identifier: str) -> str:
    """Resolve username/email/UUID to the canonical UUID from the users table.

    UUID pass-through: if identifier already looks like a 32-hex UUID, return it.
    Username/email lookup: query users table; return UUID if found.
    Unknown identifier: return identifier as-is (e.g. "local-admin" sentinel).
    """
    ident = str(identifier or "").strip()
    if not ident:
        return ident
    if _UUID_RE.match(ident):
        return ident
    try:
        row = db.get_user_by_username(ident)
        if row and row.get("id"):
            return str(row["id"])
        row = db.get_user_by_email(ident)
        if row and row.get("id"):
            return str(row["id"])
    except Exception:
        pass
    return ident


def _resolve_db_user_id(db: Any, owner_name: str, explicit_user_id: str = "") -> str:
    if explicit_user_id:
        return _canonical_user_id(db, explicit_user_id)
    owner = str(owner_name or "").strip()
    return _canonical_user_id(db, owner) or "local-admin"


def _record_job_db_start(job: dict[str, Any]) -> None:
    project_root = Path(job.get("project_root") or ".").resolve()
    owner_name = str(job.get("user_id") or "").strip()
    try:
        from core.atlas_db import AtlasDB

        with AtlasDB(_atlas_job_db_path(project_root)) as db:
            db_user_id = _resolve_db_user_id(db, owner_name, str(job.get("db_user_id") or ""))
            workspace = db.upsert_workspace(
                project_root.name or "default",
                owner_user_id=db_user_id,
                local_path=str(project_root),
            )
            ip_name = str(job.get("ip") or "").strip()
            ip_row = db.upsert_ip_block(
                workspace["id"],
                ip_name or "soc",
                ssot_path=f"{ip_name}/yaml/{ip_name}.ssot.yaml" if ip_name else "",
            )
            db_session_id = str(job.get("db_session_id") or "").strip()
            if not db_session_id:
                created = db.create_session(
                    db_user_id,
                    f"{ip_name or 'soc'} pipeline {job.get('pipeline_id') or job.get('job_id')}",
                    ip_name,
                )
                db_session_id = created["id"]
            summary = {
                "ip": ip_name,
                "workflow": "pipeline" if job.get("pipeline_id") else job.get("workflow"),
                "stage_id": job.get("stage_id") or "",
                "pipeline_run_id": job.get("pipeline_run_id") or job.get("pipeline_id") or "",
                "pipeline_id": job.get("pipeline_id") or "",
                "job_id": job.get("job_id") or "",
                "user_id": owner_name,
                "worker_session": job.get("session") or "",
                "model": job.get("model") or "",
                "toolchain": job.get("toolchain") or "",
                "run_mode": job.get("run_mode") or "",
                "exec_mode": job.get("exec_mode") or "",
                "project_root": str(project_root),
            }
            try:
                db.update_session(
                    db_session_id,
                    project_id=ip_name,
                    summary=summary,
                )
            except Exception:
                pass
            status = "running" if job.get("status") in {"pending", "running"} else "queued"
            run = db.start_workflow_run(
                session_id=db_session_id,
                workspace_id=workspace["id"],
                ip_id=ip_row["id"],
                rtl_version_id=str(job.get("rtl_version_id") or ""),
                workflow=str(job.get("workflow") or ""),
                mode=str(job.get("exec_mode") or "orchestrator"),
                model_profile=str(job.get("model") or ""),
                reasoning_effort=str(job.get("reasoning_effort") or ""),
                trigger="pipeline_dispatch" if job.get("pipeline_id") else "job_dispatch",
                input_summary=json.dumps(summary, ensure_ascii=False),
                status=status,
                trigger_source=str(job.get("trigger_source") or ""),
                orchestrator_run_id=str(job.get("orchestrator_run_id") or ""),
            )
            job["workflow_run_id"] = run.get("id") or ""
            job["db_session_id"] = db_session_id
            job["db_user_id"] = db_user_id
            job["db_workspace_id"] = workspace["id"]
            job["db_ip_id"] = ip_row["id"]
            db.record_trace_event(
                event_type="workflow_dispatch",
                payload=summary,
                session_id=db_session_id,
                workspace_id=workspace["id"],
                ip_id=ip_row["id"],
                workflow=str(job.get("workflow") or ""),
                run_id=str(job.get("workflow_run_id") or ""),
                stage_id=str(job.get("stage_id") or ""),
                actor_user_id=db_user_id,
                idempotency_key=f"dispatch:{job.get('job_id')}",
            )
    except Exception as exc:
        job["db_error"] = str(exc)


def _record_job_db_running(job: dict[str, Any]) -> None:
    run_id = str(job.get("workflow_run_id") or "")
    if not run_id:
        return
    try:
        from core.atlas_db import AtlasDB

        project_root = Path(job.get("project_root") or ".").resolve()
        with AtlasDB(_atlas_job_db_path(project_root)) as db:
            db._execute(
                "UPDATE workflow_runs SET status = ?, updated_at = ? WHERE id = ?",
                ("running", time.time(), run_id),
            )
            db.record_trace_event(
                event_type="worker_started",
                payload={
                    "job_id": job.get("job_id") or "",
                    "worker_run_id": job.get("run_id") or "",
                    "pipeline_run_id": job.get("pipeline_run_id") or job.get("pipeline_id") or "",
                    "model": job.get("model") or "",
                    "toolchain": job.get("toolchain") or "",
                },
                session_id=str(job.get("db_session_id") or ""),
                workspace_id=str(job.get("db_workspace_id") or ""),
                ip_id=str(job.get("db_ip_id") or ""),
                workflow=str(job.get("workflow") or ""),
                run_id=run_id,
                stage_id=str(job.get("stage_id") or ""),
                actor_user_id=str(job.get("db_user_id") or ""),
                idempotency_key=f"worker-start:{job.get('job_id')}",
            )
    except Exception as exc:
        job["db_error"] = str(exc)


def _finish_job_db_run(job: dict[str, Any], status: str | None = None, error_summary: str | None = None) -> None:
    run_id = str(job.get("workflow_run_id") or "")
    if not run_id:
        return
    final_status = str(status or job.get("status") or "").strip()
    if final_status == "completed":
        final_status = "completed"
    elif final_status in {"error", "failed"}:
        final_status = "error"
    elif final_status == "blocked":
        final_status = "blocked"
    elif final_status == "cancelled":
        final_status = "cancelled"
    else:
        return
    if job.get("_db_finished_status") == final_status:
        return
    try:
        from core.atlas_db import AtlasDB

        project_root = Path(job.get("project_root") or ".").resolve()
        error_text = error_summary if error_summary is not None else str(job.get("error") or "")
        with AtlasDB(_atlas_job_db_path(project_root)) as db:
            db.finish_workflow_run(run_id, final_status, error_summary=error_text or None)
            db.record_trace_event(
                event_type="workflow_finished",
                payload={
                    "job_id": job.get("job_id") or "",
                    "worker_run_id": job.get("run_id") or "",
                    "pipeline_run_id": job.get("pipeline_run_id") or job.get("pipeline_id") or "",
                    "status": final_status,
                    "result_summary": job.get("result_summary") or "",
                    "error": error_text or "",
                    "files_modified": job.get("files_modified") or [],
                },
                session_id=str(job.get("db_session_id") or ""),
                workspace_id=str(job.get("db_workspace_id") or ""),
                ip_id=str(job.get("db_ip_id") or ""),
                workflow=str(job.get("workflow") or ""),
                run_id=run_id,
                stage_id=str(job.get("stage_id") or ""),
                actor_user_id=str(job.get("db_user_id") or ""),
                idempotency_key=f"worker-finish:{job.get('job_id')}:{final_status}",
            )
            for item in _artifact_versions_map(job).values():
                artifact_version_id = item.get("id") or ""
                if artifact_version_id:
                    db.attach_run_artifact_version(
                        run_id,
                        artifact_version_id,
                        stage_id=str(job.get("stage_id") or ""),
                        role="output" if item.get("artifact_type") == _STAGE_ARTIFACT_TYPES.get(str(job.get("stage_id") or "")) else "input",
                        metadata={"job_id": job.get("job_id") or ""},
                    )
        job["_db_finished_status"] = final_status
    except Exception as exc:
        job["db_error"] = str(exc)


def _normalize_run_mode(value: Any) -> str:
    mode = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "start": "starter",
        "first-green": "starter",
        "firstgreen": "starter",
        "eng": "engineering",
        "engineer": "engineering",
        "sign-off": "signoff",
        "sign off": "signoff",
    }
    mode = aliases.get(mode, mode)
    return mode if mode in _RUN_MODES else ""


def _current_run_mode() -> str:
    return _normalize_run_mode(os.environ.get("ATLAS_RUN_MODE")) or "engineering"


def _normalize_exec_mode(value: Any) -> str:
    mode = str(value or "").strip().lower().replace("_", "-")
    aliases = {
        "single": "single-worker",
        "single-worker": "single-worker",
        "single worker": "single-worker",
        "worker": "single-worker",
        "serial": "single-worker",
        "orch": "orchestrator",
        "orchestrator-mode": "orchestrator",
        "multi-worker": "orchestrator",
        "multi worker": "orchestrator",
    }
    mode = aliases.get(mode, mode)
    return mode if mode in _EXEC_MODES else ""


def _current_exec_mode() -> str:
    if os.environ.get("ATLAS_ORCHESTRATOR_MODE") is not None:
        return "orchestrator" if _truthy_env("ATLAS_ORCHESTRATOR_MODE") else "single-worker"
    explicit = _normalize_exec_mode(os.environ.get("ATLAS_EXEC_MODE"))
    if explicit:
        return explicit
    explicit = _normalize_exec_mode(os.environ.get("ATLAS_DEFAULT_EXEC_MODE"))
    if explicit:
        return explicit
    return "orchestrator" if _orchestrator_mode_enabled() else "single-worker"


def _provenance_summary(ip_dir: Path, run_mode: str) -> dict[str, Any]:
    """Summarize sidecar SSOT provenance without loading it into the main YAML.

    The sidecar format is intentionally permissive while the policy is still
    settling: accept either a path->entry map, {"fields": {...}}, or
    {"entries": [...]}. The UI only needs counts and a small reason list.
    """
    summary: dict[str, Any] = {
        "generated_defaults": 0,
        "review_needed": 0,
        "user": 0,
        "derived": 0,
        "tool_evidence": 0,
        "critical_generated_defaults": 0,
        "signoff_blocked": False,
        "source": "",
        "examples": [],
    }
    yaml_dir = ip_dir / "yaml"
    if not yaml_dir.is_dir():
        return summary
    paths = sorted(yaml_dir.glob("*.ssot.provenance.json"))
    if not paths:
        paths = sorted(yaml_dir.glob("*provenance*.json"))
    if not paths:
        return summary

    path = paths[0]
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        summary["source"] = path.relative_to(ip_dir).as_posix()
        return summary
    summary["source"] = path.relative_to(ip_dir).as_posix()

    entries: list[tuple[str, dict[str, Any]]] = []
    if isinstance(doc, dict):
        fields = doc.get("fields")
        if isinstance(fields, dict):
            entries = [(str(k), v) for k, v in fields.items() if isinstance(v, dict)]
        elif isinstance(doc.get("entries"), list):
            entries = [
                (str(v.get("path") or v.get("field") or f"entry_{i}"), v)
                for i, v in enumerate(doc["entries"])
                if isinstance(v, dict)
            ]
        else:
            entries = [(str(k), v) for k, v in doc.items() if isinstance(v, dict)]
    elif isinstance(doc, list):
        entries = [
            (str(v.get("path") or v.get("field") or f"entry_{i}"), v)
            for i, v in enumerate(doc)
            if isinstance(v, dict)
        ]

    examples: list[dict[str, str]] = []
    authority_counts = {
        "user": "user",
        "derived": "derived",
        "generated_default": "generated_defaults",
        "generated-default": "generated_defaults",
        "review_needed": "review_needed",
        "review-needed": "review_needed",
        "tool_evidence": "tool_evidence",
        "tool-evidence": "tool_evidence",
    }
    critical_paths = {
        "cycle_model",
        "dft",
        "error_handling",
        "pnr",
        "quality_gates",
        "security.assets",
        "synthesis",
        "test_requirements.coverage_goals",
        "timing.io_delays",
    }

    def _norm_field_path(raw: str) -> str:
        return str(raw or "").strip().lstrip("/").replace("/", ".")

    def _is_signoff_critical_path(raw: str) -> bool:
        field = _norm_field_path(raw)
        for prefix in critical_paths:
            if field == prefix or field.startswith(prefix + ".") or field.startswith(prefix + "["):
                return True
        return False

    for field_path, entry in entries:
        authority = str(entry.get("authority") or entry.get("origin") or "").strip().lower()
        count_key = authority_counts.get(authority)
        if count_key:
            summary[count_key] += 1
        if authority == "generated-default":
            authority = "generated_default"
        elif authority == "review-needed":
            authority = "review_needed"
        elif authority == "tool-evidence":
            authority = "tool_evidence"

        mode_allowed = entry.get("mode_allowed")
        allowed = {str(v).strip().lower().replace("_", "-") for v in mode_allowed} if isinstance(mode_allowed, list) else set()
        signoff_critical = bool(entry.get("signoff_critical") or entry.get("critical") or _is_signoff_critical_path(field_path))
        signoff_blocks = (
            run_mode == "signoff"
            and authority in {"generated_default", "review_needed"}
            and (signoff_critical or (allowed and "signoff" not in allowed))
        )
        if signoff_blocks:
            summary["critical_generated_defaults"] += 1
            summary["signoff_blocked"] = True
        if len(examples) < 5 and authority in {"generated_default", "review_needed"}:
            examples.append({
                "path": field_path,
                "authority": authority,
                "review": str(entry.get("review") or entry.get("reason") or ""),
            })
    summary["examples"] = examples
    return summary


def _job_dependency_ids(job: dict[str, Any]) -> list[str]:
    deps = job.get("depends_on")
    if isinstance(deps, list):
        return [str(dep) for dep in deps if str(dep)]
    if isinstance(deps, str) and deps:
        return [deps]
    return []


def _pipeline_stage_dependencies(
    stage_id: str,
    selected_stage_ids: list[str],
    *,
    schedule: str = "dag",
) -> list[str]:
    if schedule == "serial":
        idx = selected_stage_ids.index(stage_id)
        return [selected_stage_ids[idx - 1]] if idx > 0 else []
    selected = set(selected_stage_ids)
    if stage_id == "goal-audit":
        return [sid for sid in selected_stage_ids if sid != stage_id]

    def nearest_selected_upstream(current: str, seen: set[str]) -> list[str]:
        deps: list[str] = []
        for dep in _PIPELINE_STAGE_DEPS.get(current, ()):
            if dep in seen:
                continue
            seen.add(dep)
            if dep in selected:
                deps.append(dep)
            else:
                deps.extend(nearest_selected_upstream(dep, seen))
        return deps

    ordered: list[str] = []
    for dep in nearest_selected_upstream(stage_id, set()):
        if dep not in ordered:
            ordered.append(dep)
    return ordered


def _job_allows_failed_dependency(candidate: dict[str, Any], dependency: dict[str, Any]) -> bool:
    if dependency.get("status") != "error":
        return False
    allowed = _PIPELINE_ALLOWED_FAILED_DEPS.get(str(candidate.get("stage_id") or ""), ())
    return str(dependency.get("stage_id") or "") in allowed


def _resolve_pipeline_schedule(requested_schedule: str, stages: list[dict[str, str]]) -> str:
    if requested_schedule in {"dag", "serial"}:
        return requested_schedule
    worker_urls = {
        _resolve_worker_url(str(stage.get("workflow") or ""))
        for stage in stages
    }
    return "dag" if len(worker_urls) > 1 else "serial"


def _ordered_pipeline_stages(stages: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(stages, key=lambda stage: _PIPELINE_STAGE_ORDER.get(stage["id"], 999))


def _mark_downstream_blocked_locked(pipeline_id: str, failed_job_id: str, reason: str) -> None:
    blocked_ids = {failed_job_id}
    changed = True
    while changed:
        changed = False
        jobs_by_id = {
            str(j.get("job_id")): j
            for j in _jobs.values()
            if j.get("pipeline_id") == pipeline_id
        }
        for queued in _jobs.values():
            if queued.get("pipeline_id") != pipeline_id:
                continue
            if queued.get("status") not in {"queued", "pending"}:
                continue
            blocking_deps = [
                dep for dep in _job_dependency_ids(queued)
                if dep in blocked_ids and not _job_allows_failed_dependency(queued, jobs_by_id.get(dep, {}))
            ]
            if not blocking_deps:
                continue
            queued["status"] = "blocked"
            queued["error"] = reason
            queued["finished_at"] = time.time()
            _finish_job_db_run(queued, "blocked", reason)
            blocked_ids.add(queued.get("job_id", ""))
            changed = True


def get_jobs_state() -> tuple[dict[str, dict[str, Any]], threading.Lock]:
    """Return (_jobs, _jobs_lock) for callers in atlas_ui.py that need
    read access to the job tracker (e.g. /api/session/state)."""
    return _jobs, _jobs_lock


def _summarize_worker_progress(ip_jobs: list[dict[str, Any]]) -> dict[str, Any]:
    now = time.time()
    active_states = {"pending", "queued", "running", "blocked"}
    status_counts: dict[str, int] = {}
    for job in ip_jobs:
        status = str(job.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    def _job_item(job: dict[str, Any]) -> dict[str, Any]:
        started_at = float(job.get("started_at") or 0.0)
        finished_at = float(job.get("finished_at") or 0.0)
        last_polled = float(job.get("_last_polled") or 0.0)
        item: dict[str, Any] = {
            "job_id": job.get("job_id") or "",
            "run_id": job.get("run_id") or "",
            "pipeline_id": job.get("pipeline_id") or "",
            "pipeline_run_id": job.get("pipeline_run_id") or job.get("pipeline_id") or "",
            "pipeline_index": job.get("pipeline_index"),
            "workflow": job.get("workflow") or "",
            "stage_id": job.get("stage_id") or "",
            "status": job.get("status") or "",
            "worker": job.get("worker") or "",
            "model": job.get("model") or "",
            "toolchain": job.get("toolchain") or "",
            "user_id": job.get("user_id") or "",
            "session": job.get("session") or "",
            "scope_path": job.get("scope_path") or "",
            "depends_on": job.get("depends_on") or "",
            "iterations": job.get("iterations") or 0,
            "result_summary": (job.get("result_summary") or "")[-300:],
            "error": job.get("error") or "",
        }
        if started_at:
            item["started_at_epoch"] = started_at
            item["elapsed_sec"] = round(max(0.0, (finished_at or now) - started_at), 3)
        if finished_at:
            item["finished_at_epoch"] = finished_at
        if last_polled:
            item["last_polled_age_sec"] = round(max(0.0, now - last_polled), 3)
        return item

    active = [
        _job_item(job)
        for job in sorted(ip_jobs, key=lambda j: float(j.get("started_at") or 0.0), reverse=True)
        if str(job.get("status") or "") in active_states
    ]
    latest = [
        _job_item(job)
        for job in sorted(
            ip_jobs,
            key=lambda j: float(j.get("finished_at") or j.get("started_at") or 0.0),
            reverse=True,
        )[:8]
    ]

    if active:
        state = "running_worker_jobs"
        severity = "info"
        message = f"{len(active)} worker job(s) active."
    elif ip_jobs:
        state = "worker_jobs_idle"
        severity = "info"
        message = "No active worker jobs; latest worker records are available."
    else:
        state = "no_worker_jobs"
        severity = "info"
        message = "No worker jobs are registered for this IP in the current UI process."

    return {
        "diagnosis": {"state": state, "severity": severity, "message": message},
        "status_counts": status_counts,
        "active": active,
        "latest": latest,
    }


def _combine_progress_debug(headless: dict[str, Any], worker: dict[str, Any]) -> dict[str, Any]:
    worker_state = ((worker.get("diagnosis") or {}).get("state") or "")
    headless_diag = headless.get("diagnosis") if isinstance(headless.get("diagnosis"), dict) else {}
    if worker_state in {"running_worker_jobs", "worker_jobs_idle"}:
        diagnosis = worker.get("diagnosis") or {}
    else:
        diagnosis = headless_diag or worker.get("diagnosis") or {}
    return {
        "diagnosis": diagnosis,
        "worker": worker,
        "headless": headless,
    }


# ── Internal helpers ────────────────────────────────────────────────

def _truthy_env(name: str) -> bool:
    return str(os.environ.get(name, "")).strip().lower() in {"1", "true", "yes", "on"}


def _safe_git_commit(project_root: Path) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            check=False,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        return ""
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _git_tag_exists(project_root: Path, tag: str) -> bool:
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_root), "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=2,
        )
    except Exception:
        return False
    return proc.returncode == 0


def _maybe_create_git_tag(project_root: Path, tag: str) -> str:
    if not tag or not _safe_git_commit(project_root):
        return ""
    if _git_tag_exists(project_root, tag):
        return tag
    if not _truthy_env("ATLAS_RTL_VERSION_CREATE_GIT_TAG"):
        return ""
    try:
        proc = subprocess.run(
            ["git", "-C", str(project_root), "tag", tag],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
    except Exception:
        return ""
    return tag if proc.returncode == 0 or _git_tag_exists(project_root, tag) else ""


def _file_tree_manifest(
    project_root: Path,
    roots: list[Path],
    patterns: tuple[str, ...],
    primary_candidates: tuple[Path, ...] = (),
) -> tuple[list[dict[str, Any]], str, str]:
    files: list[Path] = []
    if not any(root.is_dir() for root in roots):
        return [], "", ""
    for root in roots:
        if root.is_file():
            files.append(root)
            continue
        if not root.is_dir():
            continue
        for pattern in patterns:
            files.extend(root.rglob(pattern))
    for candidate in primary_candidates:
        if candidate.is_file():
            files.append(candidate)
    manifest: list[dict[str, Any]] = []
    tree_hasher = hashlib.sha256()
    for path in sorted({p.resolve() for p in files}):
        if not path.is_file():
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        try:
            rel = path.relative_to(project_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        digest = hashlib.sha256(data).hexdigest()
        size = len(data)
        manifest.append({"path": rel, "sha256": digest, "size_bytes": size})
        tree_hasher.update(rel.encode("utf-8"))
        tree_hasher.update(b"\0")
        tree_hasher.update(digest.encode("ascii"))
        tree_hasher.update(b"\0")
        tree_hasher.update(str(size).encode("ascii"))
        tree_hasher.update(b"\n")
    if not manifest:
        return [], "", ""
    primary_path = ""
    for candidate in primary_candidates:
        if candidate.is_file():
            try:
                primary_path = candidate.relative_to(project_root).as_posix()
            except ValueError:
                primary_path = candidate.as_posix()
            break
    return manifest, tree_hasher.hexdigest(), primary_path


def _rtl_artifact_manifest(project_root: Path, ip: str) -> tuple[list[dict[str, Any]], str, str]:
    ip_dir = _ip_dir_for(project_root, ip)
    rtl_root = ip_dir / "rtl"
    filelist = ip_dir / "list" / f"{ip}.f"
    return _file_tree_manifest(
        project_root,
        [rtl_root],
        ("*.sv", "*.svh", "*.v", "*.vh"),
        (filelist,),
    )


def _stage_artifact_manifest(
    project_root: Path,
    ip: str,
    artifact_type: str,
) -> tuple[list[dict[str, Any]], str, str, str]:
    ip_dir = _ip_dir_for(project_root, ip)
    if artifact_type == "ssot":
        root = ip_dir / "yaml"
        primary = (
            root / f"{ip}.ssot.yaml",
            root / f"{ip}.ssot.yml",
            root / f"{ip}.yaml",
            root / f"{ip}.yml",
        )
        manifest, digest, primary_path = _file_tree_manifest(
            project_root,
            [root],
            ("*.yaml", "*.yml", "*.json", "*.md"),
            primary,
        )
        return manifest, digest, primary_path, f"{ip}/yaml"
    if artifact_type == "tb":
        root = ip_dir / "tb"
        primary = (
            root / "run_tests.py",
            root / "cocotb" / "run_tests.py",
            root / f"{ip}_tb.sv",
            root / "tb_top.sv",
        )
        manifest, digest, primary_path = _file_tree_manifest(
            project_root,
            [root],
            ("*.py", "*.sv", "*.svh", "*.v", "*.vh", "*.yaml", "*.yml", "*.json", "*.md"),
            primary,
        )
        return manifest, digest, primary_path, f"{ip}/tb"
    return [], "", "", ""


def _next_rtl_version_name(existing: list[dict[str, Any]]) -> str:
    max_seen = 0
    for row in existing:
        match = re.fullmatch(r"rtl-v(\d+)", str(row.get("version") or ""))
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return f"rtl-v{max_seen + 1:03d}"


def _next_artifact_version_name(existing: list[dict[str, Any]], artifact_type: str) -> str:
    prefix = str(artifact_type or "artifact").replace("_", "-")
    max_seen = 0
    for row in existing:
        match = re.fullmatch(rf"{re.escape(prefix)}-v(\d+)", str(row.get("version") or ""))
        if match:
            max_seen = max(max_seen, int(match.group(1)))
    return f"{prefix}-v{max_seen + 1:03d}"


def _artifact_version_summary(row: dict[str, Any]) -> dict[str, Any]:
    artifact_type = row.get("artifact_type") or row.get("type") or ""
    return {
        "id": row.get("id") or row.get("artifact_version_id") or "",
        "artifact_type": artifact_type,
        "type": artifact_type,
        "version": row.get("version") or "",
        "label": row.get("label") or "",
        "sha256_tree": row.get("sha256_tree") or "",
        "git_commit": row.get("git_commit") or "",
        "git_tag": row.get("git_tag") or "",
        "root_path": row.get("root_path") or row.get("rtl_root") or "",
        "primary_path": row.get("primary_path") or row.get("filelist_path") or "",
        "status": row.get("status") or "",
        "role": row.get("role") or "input",
    }


def _artifact_versions_map(job: dict[str, Any]) -> dict[str, dict[str, Any]]:
    existing = job.get("artifact_versions") or {}
    result: dict[str, dict[str, Any]] = {}
    if isinstance(existing, dict):
        iterable = existing.values()
    elif isinstance(existing, list):
        iterable = existing
    else:
        iterable = []
    for item in iterable:
        if not isinstance(item, dict):
            continue
        summary = _artifact_version_summary(item)
        artifact_type = summary.get("artifact_type") or ""
        if summary.get("id") and artifact_type:
            result[artifact_type] = summary
    return result


def _set_artifact_version_context(job: dict[str, Any], row: dict[str, Any]) -> None:
    summary = _artifact_version_summary(row)
    artifact_type = summary.get("artifact_type") or ""
    if not artifact_type or not summary.get("id"):
        return
    versions = _artifact_versions_map(job)
    versions[artifact_type] = summary
    job["artifact_versions"] = versions


def _job_db_workspace_and_ip(
    db: Any,
    job: dict[str, Any],
    project_root: Path,
    ip: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    workspace = None
    ip_row = None
    workspace_id = str(job.get("db_workspace_id") or "")
    ip_id = str(job.get("db_ip_id") or "")
    if workspace_id:
        try:
            workspace = db.get_workspace(workspace_id)
        except Exception:
            workspace = None
    if ip_id:
        try:
            ip_row = db.get_ip_block(ip_id)
        except Exception:
            ip_row = None
    if workspace is None:
        workspace = db.upsert_workspace(
            project_root.name or "default",
            owner_user_id=_canonical_user_id(db, str(job.get("db_user_id") or "") or "local-admin"),
            local_path=str(project_root),
        )
        job["db_workspace_id"] = workspace["id"]
    if ip_row is None or ip_row.get("workspace_id") != workspace["id"]:
        ip_row = db.upsert_ip_block(workspace["id"], ip)
        job["db_ip_id"] = ip_row["id"]
    return workspace, ip_row


def _ensure_rtl_version_for_job(job: dict[str, Any], project_root: Path) -> dict[str, Any] | None:
    if job.get("rtl_version_id") or job.get("stage_id") != "rtl":
        return None
    ip = str(job.get("ip") or "").strip()
    if not ip or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
        return None
    manifest, sha256_tree, filelist_path = _rtl_artifact_manifest(project_root, ip)
    if not manifest or not sha256_tree:
        return None
    try:
        from core.atlas_db import AtlasDB

        db_path = os.environ.get("ATLAS_TRACE_DB_PATH") or os.environ.get("ATLAS_DB_PATH")
        with (AtlasDB(db_path) if db_path else AtlasDB()) as db:
            workspace, ip_row = _job_db_workspace_and_ip(db, job, project_root, ip)
            version = _next_rtl_version_name(db.list_rtl_versions(ip_id=ip_row["id"]))
            git_commit = _safe_git_commit(project_root)
            git_tag = _maybe_create_git_tag(project_root, f"atlas/{ip}/{version}") if git_commit else ""
            rtl_version = db.register_rtl_version(
                ip_id=ip_row["id"],
                workspace_id=workspace["id"],
                source_run_id=str(job.get("run_id") or ""),
                source_stage_id=str(job.get("job_id") or ""),
                version=version,
                label=f"{ip} {version}",
                rtl_root=f"{ip}/rtl",
                filelist_path=filelist_path,
                top_module=ip,
                artifact_manifest=manifest,
                sha256_tree=sha256_tree,
                git_commit=git_commit,
                git_tag=git_tag,
                status="generated",
                metadata={
                    "job_id": job.get("job_id") or "",
                    "pipeline_id": job.get("pipeline_id") or "",
                    "stage_id": job.get("stage_id") or "",
                    "workflow": job.get("workflow") or "",
                    "worker_run_id": job.get("run_id") or "",
                },
            )
            inputs = _artifact_versions_map(job)
            ssot_input = inputs.get("ssot")
            if ssot_input and ssot_input.get("id") and rtl_version.get("artifact_version_id"):
                db.link_artifact_versions(
                    ssot_input["id"],
                    rtl_version["artifact_version_id"],
                    "generated_from",
                    metadata={"stage_id": job.get("stage_id") or "", "job_id": job.get("job_id") or ""},
                )
    except Exception as exc:
        job["rtl_version_error"] = str(exc)
        return None
    job["rtl_version_id"] = rtl_version.get("id") or ""
    job["rtl_version"] = rtl_version.get("version") or version
    job["rtl_sha256_tree"] = rtl_version.get("sha256_tree") or sha256_tree
    job["rtl_git_commit"] = rtl_version.get("git_commit") or git_commit
    job["rtl_git_tag"] = rtl_version.get("git_tag") or git_tag
    job["rtl_filelist_path"] = rtl_version.get("filelist_path") or filelist_path
    job["rtl_top_module"] = rtl_version.get("top_module") or ip
    if rtl_version.get("artifact_version_id"):
        _set_artifact_version_context(job, {
            "id": rtl_version["artifact_version_id"],
            "artifact_type": "rtl",
            "version": rtl_version.get("version") or version,
            "label": rtl_version.get("label") or "",
            "root_path": rtl_version.get("rtl_root") or f"{ip}/rtl",
            "primary_path": rtl_version.get("filelist_path") or filelist_path,
            "sha256_tree": rtl_version.get("sha256_tree") or sha256_tree,
            "git_commit": rtl_version.get("git_commit") or git_commit,
            "git_tag": rtl_version.get("git_tag") or git_tag,
            "status": rtl_version.get("status") or "generated",
        })
    return rtl_version


def _copy_rtl_version_context(dst: dict[str, Any], src: dict[str, Any]) -> None:
    for key in (
        "rtl_version_id", "rtl_version", "rtl_sha256_tree", "rtl_git_commit",
        "rtl_git_tag", "rtl_filelist_path", "rtl_top_module",
    ):
        if src.get(key) and not dst.get(key):
            dst[key] = src[key]


def _copy_artifact_version_context(dst: dict[str, Any], src: dict[str, Any]) -> None:
    merged = _artifact_versions_map(dst)
    for artifact_type, summary in _artifact_versions_map(src).items():
        merged.setdefault(artifact_type, summary)
    if merged:
        dst["artifact_versions"] = merged
    _copy_rtl_version_context(dst, src)


def _coerce_bool(value: Any, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "pass", "passed", "ok"}:
        return True
    if text in {"0", "false", "no", "n", "fail", "failed", "error"}:
        return False
    return default


def _timing_wns_doc(ip_dir: Path, stage: str) -> tuple[dict[str, Any] | None, str]:
    rel = "sta-post/out/wns.json" if stage == "sta-post" else "sta/out/wns.json"
    path = ip_dir / rel
    if not path.is_file():
        return None, ""
    try:
        return json.loads(path.read_text(encoding="utf-8")), rel
    except Exception:
        return None, f"unparseable artifact: {rel}"


def _timing_artifact_failure(ip_dir: Path, stage: str) -> str:
    doc, rel_or_error = _timing_wns_doc(ip_dir, stage)
    if doc is None:
        return rel_or_error
    summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else doc
    clocks = [c for c in (doc.get("clocks") or []) if isinstance(c, dict)]
    def _clock_met(clock: dict[str, Any], wns_key: str, viol_key: str) -> bool:
        try:
            wns = float(clock.get(wns_key) or 0)
        except Exception:
            wns = 0.0
        try:
            violations = int(clock.get(viol_key) or 0)
        except Exception:
            violations = 0
        return wns >= 0 and violations == 0

    setup_ok = _coerce_bool(summary.get("all_setup_met"), default=True)
    hold_ok = _coerce_bool(summary.get("all_hold_met"), default=True)
    if "all_setup_met" not in summary and clocks:
        setup_ok = all(_clock_met(c, "setup_wns_ns", "setup_violations") for c in clocks)
    if "all_hold_met" not in summary and clocks:
        hold_ok = all(_clock_met(c, "hold_wns_ns", "hold_violations") for c in clocks)
    if setup_ok and hold_ok:
        return ""
    reasons: list[str] = []
    for clock in clocks:
        name = clock.get("name") or "clock"
        if not setup_ok:
            reasons.append(
                f"{name} setup WNS={clock.get('setup_wns_ns', '?')} "
                f"viol={clock.get('setup_violations', '?')}"
            )
        if not hold_ok:
            reasons.append(
                f"{name} hold WNS={clock.get('hold_wns_ns', '?')} "
                f"viol={clock.get('hold_violations', '?')}"
            )
    if not reasons:
        if not setup_ok:
            reasons.append("setup timing not met")
        if not hold_ok:
            reasons.append("hold timing not met")
    return "; ".join(reasons)


def _timing_artifact_summary(ip_dir: Path, stage: str) -> tuple[str, str]:
    doc, _ = _timing_wns_doc(ip_dir, stage)
    if not doc:
        return "", ""
    clocks = [c for c in (doc.get("clocks") or []) if isinstance(c, dict)]
    if not clocks:
        return "", ""
    worst_setup = min((c.get("setup_wns_ns") for c in clocks if c.get("setup_wns_ns") is not None), default="?")
    worst_hold = min((c.get("hold_wns_ns") for c in clocks if c.get("hold_wns_ns") is not None), default="?")
    setup_viol = sum(int(c.get("setup_violations") or 0) for c in clocks)
    hold_viol = sum(int(c.get("hold_violations") or 0) for c in clocks)
    mode = "post-route" if stage == "sta-post" else "pre-route"
    return (
        f"{mode} setup WNS={worst_setup} viol={setup_viol}",
        f"hold WNS={worst_hold} viol={hold_viol}",
    )


def _synthesis_artifact_failure(ip_dir: Path) -> str:
    """Phase 5 evidence gate for the SYN stage.

    A synthesis run is only considered passed when the mapped netlist exists
    AND, when an area/error report is present, it reports zero errors. This
    prevents a "worker returned completed" outcome from silently masking a
    synthesis failure that left no usable netlist on disk.
    """
    syn_out = ip_dir / "syn" / "out"
    if not syn_out.is_dir():
        # Recovery layer is responsible for the "directory missing" case;
        # here we only validate when the dir exists but content is bad.
        return ""

    # Mapped netlist must exist (any .v under syn/out/).
    netlists = list(syn_out.glob("*.v")) + list(syn_out.glob("**/*.v"))
    if not netlists:
        return "mapped netlist missing under syn/out/*.v"

    # Optional report files — if present, must report zero errors.
    for rel in ("synth_errors.json", "area.json", "synth_summary.json"):
        path = syn_out / rel
        if not path.is_file():
            continue
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return f"unparseable artifact: syn/out/{rel}"
        try:
            errors = int(doc.get("errors") or doc.get("error_count") or 0)
        except Exception:
            errors = 0
        if errors > 0:
            return f"syn/out/{rel} errors={errors}"
        status = str(doc.get("status") or "").strip().lower()
        if status and status not in ("pass", "ok", "completed", "success"):
            return f"syn/out/{rel} status={status}"
    return ""


def _pnr_artifact_failure(ip_dir: Path) -> str:
    drc_path = ip_dir / "pnr" / "out" / "drc.json"
    if not drc_path.is_file():
        return ""
    try:
        doc = json.loads(drc_path.read_text(encoding="utf-8"))
    except Exception:
        return "unparseable artifact: pnr/out/drc.json"
    try:
        drc_count = int(doc.get("drc_count", 0))
    except Exception:
        drc_count = 0
    if drc_count > 0:
        return f"drc_count={drc_count}"
    return ""


def _pnr_artifact_summary(ip_dir: Path) -> tuple[str, str]:
    drc_path = ip_dir / "pnr" / "out" / "drc.json"
    if not drc_path.is_file():
        return "", ""
    try:
        doc = json.loads(drc_path.read_text(encoding="utf-8"))
    except Exception:
        return "", ""
    drc_count = doc.get("drc_count", "?")
    spef_ready = (ip_dir / "pnr" / "out" / "routed.spef").is_file()
    return (f"DRC={drc_count}", "SPEF ready" if spef_ready else "SPEF missing")


def _ensure_stage_artifact_version_for_job(
    job: dict[str, Any],
    project_root: Path,
) -> dict[str, Any] | None:
    stage_id = str(job.get("stage_id") or "").strip()
    artifact_type = _STAGE_ARTIFACT_TYPES.get(stage_id)
    if not artifact_type:
        return None
    if artifact_type == "rtl":
        return _ensure_rtl_version_for_job(job, project_root)
    if _artifact_versions_map(job).get(artifact_type):
        return None
    ip = str(job.get("ip") or "").strip()
    if not ip or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
        return None
    manifest, sha256_tree, primary_path, root_path = _stage_artifact_manifest(
        project_root, ip, artifact_type,
    )
    if not manifest or not sha256_tree:
        return None
    try:
        from core.atlas_db import AtlasDB

        db_path = os.environ.get("ATLAS_TRACE_DB_PATH") or os.environ.get("ATLAS_DB_PATH")
        with (AtlasDB(db_path) if db_path else AtlasDB()) as db:
            workspace, ip_row = _job_db_workspace_and_ip(db, job, project_root, ip)
            existing = db.list_artifact_versions(ip_id=ip_row["id"], artifact_type=artifact_type)
            version = _next_artifact_version_name(existing, artifact_type)
            git_commit = _safe_git_commit(project_root)
            git_tag = _maybe_create_git_tag(project_root, f"atlas/{ip}/{version}") if git_commit else ""
            artifact = db.register_artifact_version(
                ip_id=ip_row["id"],
                workspace_id=workspace["id"],
                source_run_id=str(job.get("run_id") or ""),
                source_stage_id=str(job.get("job_id") or ""),
                artifact_type=artifact_type,
                version=version,
                label=f"{ip} {version}",
                root_path=root_path,
                primary_path=primary_path,
                manifest=manifest,
                sha256_tree=sha256_tree,
                git_commit=git_commit,
                git_tag=git_tag,
                status="generated",
                metadata={
                    "job_id": job.get("job_id") or "",
                    "pipeline_id": job.get("pipeline_id") or "",
                    "stage_id": stage_id,
                    "workflow": job.get("workflow") or "",
                    "worker_run_id": job.get("run_id") or "",
                },
            )
            inputs = _artifact_versions_map(job)
            if artifact_type == "tb":
                for parent_type, relation in (("ssot", "generated_from"), ("rtl", "verified_against")):
                    parent = inputs.get(parent_type)
                    if parent and parent.get("id"):
                        db.link_artifact_versions(
                            parent["id"], artifact["id"], relation,
                            metadata={"stage_id": stage_id, "job_id": job.get("job_id") or ""},
                        )
    except Exception as exc:
        job[f"{artifact_type}_version_error"] = str(exc)
        return None
    _set_artifact_version_context(job, artifact)
    return artifact


_DEFAULT_SINGLE_MAIN_LOOP_PORT = 5601

_DEFAULT_WORKER_PORTS: dict[str, int] = {
    # Canonical port map (matches doc/wiki/atlas-browser-control-runbook.md).
    # Used when no ATLAS_WORKER_URL_<SUFFIX> / WORKER_URL_<SUFFIX> env var is
    # set so a freshly-launched atlas_ui.py can reach the per-workflow workers
    # that the operator started on the documented ports without requiring a
    # full env file. Env vars still win when present.
    "ssot-gen":     5621,
    "fl-model-gen": 5622,
    "rtl-gen":      5623,
    "lint":         5624,
    "tb-gen":       5625,
    "sim":          5626,
    "coverage":     5627,
    "sim_debug":    5628,
    "syn":          5629,
    "sta":          5630,
    "pnr":          5631,
    "sta-post":     5632,
}


def _worker_model_default_for(workflow: str) -> str:
    return _WORKER_MODEL_DEFAULTS.get(str(workflow or "").strip(), "")


def _worker_reasoning_effort_default_for(workflow: str) -> str:
    return _WORKER_REASONING_EFFORT_DEFAULTS.get(str(workflow or "").strip(), "")


def _workflow_specific_worker_url(workflow: str) -> str:
    if not workflow:
        return ""
    suffix = _workflow_env_suffix(workflow)
    for key in (
        f"ATLAS_WORKER_URL_{suffix}",
        f"ATLAS_{suffix}_WORKER_URL",
        f"WORKER_URL_{suffix}",
    ):
        url = os.environ.get(key)
        if url:
            return url
    return ""


def _worker_url_is_shared_default(workflow: str, worker_url: str) -> bool:
    default_url = os.environ.get("WORKER_URL_DEFAULT", "").strip().rstrip("/")
    if not default_url or not worker_url:
        return False
    return not _workflow_specific_worker_url(workflow) and worker_url.rstrip("/") == default_url


def _resolve_worker_url(workflow: str) -> str:
    """Same precedence as core.delegate_runner.HTTPWorkerDelegate."""
    if _truthy_env("ATLAS_SINGLE_MAIN_LOOP") or _current_exec_mode() == "single-worker":
        return f"http://127.0.0.1:{_DEFAULT_SINGLE_MAIN_LOOP_PORT}"
    if workflow:
        url = _workflow_specific_worker_url(workflow)
        if url:
            return url
        default_url = os.environ.get("WORKER_URL_DEFAULT")
        if default_url:
            return default_url
        port = _DEFAULT_WORKER_PORTS.get(str(workflow).strip())
        if port:
            return f"http://127.0.0.1:{port}"
    return os.environ.get("WORKER_URL_DEFAULT", "http://localhost:8001")


def _lazy_workers_enabled() -> bool:
    raw = (
        os.environ.get("ATLAS_LAZY_WORKERS")
        or os.environ.get("ATLAS_WORKER_LAZY_START")
        or ""
    ).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _local_worker_target(worker_url: str) -> tuple[str, int] | None:
    try:
        parsed = urllib.parse.urlparse(worker_url)
    except Exception:
        return None
    if parsed.scheme not in {"http", "https"}:
        return None
    host = (parsed.hostname or "").strip().lower()
    if host not in {"127.0.0.1", "localhost", "::1"}:
        return None
    if parsed.port is None:
        return None
    return ("127.0.0.1" if host in {"localhost", "127.0.0.1"} else "::1", int(parsed.port))


def _probe_worker_health_cached(worker_url: str, timeout: float = 1.0,
                                ttl: float | None = None) -> dict[str, Any]:
    """Cached variant for UI fan-out (/api/orchestrator/workers).

    Multiple browser tabs polling every 3s would otherwise hammer each
    of the 12 workers with redundant probes. Hold each result for
    `ttl` seconds (default `_HEALTH_CACHE_TTL`, 1.5s). The dispatch
    path uses `_probe_worker_health` directly to avoid stale results
    during cold-start.
    """
    cache_ttl = _HEALTH_CACHE_TTL if ttl is None else float(ttl)
    if cache_ttl <= 0:
        return _probe_worker_health(worker_url, timeout=timeout)
    key = worker_url.rstrip("/")
    now = time.monotonic()
    with _HEALTH_CACHE_LOCK:
        hit = _HEALTH_CACHE.get(key)
        if hit and (now - hit[0]) < cache_ttl:
            return hit[1]
    result = _probe_worker_health(worker_url, timeout=timeout)
    with _HEALTH_CACHE_LOCK:
        _HEALTH_CACHE[key] = (now, result)
    return result


def _probe_worker_health(worker_url: str, timeout: float = 1.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(
            f"{worker_url.rstrip('/')}/health",
            headers={"Accept": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            health = json.loads(response.read().decode("utf-8"))
        if not isinstance(health, dict):
            return {"status": "unreachable", "error": "non-dict health response"}
        status = str(health.get("status") or "").strip().lower()
        if health.get("ok") is True or status in {"ok", "healthy", "ready"}:
            health["status"] = "ok"
        return health
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc)[:160]}


def _worker_workflow_mismatch(workflow: str, health: dict[str, Any]) -> str:
    if str(health.get("status") or "") != "ok":
        return ""
    if health.get("all_workflows") is True:
        return ""
    bound = str(health.get("workflow") or "").strip()
    requested = str(workflow or "").strip()
    if bound and requested and bound != requested:
        return f"bound workflow {bound!r} cannot run {requested!r}"
    return ""


def _lazy_worker_command(
    *,
    job: dict[str, Any],
    host: str,
    port: int,
    all_workflows: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(_SOURCE_ROOT / "src" / "main.py"),
        "--serve",
        "--host",
        host,
        "--port",
        str(port),
    ]
    if all_workflows:
        cmd.extend(["--all-workflows", "--worker-name", "atlas-shared"])
    else:
        workflow = str(job.get("workflow") or "")
        cmd.extend(["--workflow", workflow, "--worker-name", workflow])
    session_name = str(job.get("session") or "").strip()
    if session_name:
        cmd.extend(["--session", session_name])
    model = str(job.get("model") or "").strip()
    if model:
        cmd.extend(["--model", model])
    effort = str(job.get("reasoning_effort") or "").strip()
    if effort:
        cmd.extend(["--effort", effort])
    return cmd


def _terminate_lazy_workers() -> None:
    with _LAZY_WORKER_LOCK:
        procs = list(_LAZY_WORKER_PROCS.items())
        _LAZY_WORKER_PROCS.clear()
    for _key, proc in procs:
        try:
            if proc.poll() is None:
                _LOG.info(f"[lazy-worker] terminate pid={proc.pid} url={_key}")
                proc.terminate()
        except Exception:
            pass


def lazy_worker_snapshot() -> list[dict[str, Any]]:
    """Cheap point-in-time view of lazy workers for the stdin status panel."""
    with _LAZY_WORKER_LOCK:
        items = list(_LAZY_WORKER_PROCS.items())
    out: list[dict[str, Any]] = []
    for url, proc in items:
        rc = proc.poll()
        out.append({
            "url": url,
            "pid": proc.pid,
            "alive": rc is None,
            "returncode": rc,
        })
    return out


def _get_url_lock(url: str) -> threading.RLock:
    """One lock per worker URL. Created on demand under the global
    registry lock. Lets two cold-start dispatches to *different* worker
    URLs run their Popen + ready-wait in parallel; same-URL dispatches
    still serialize so we never double-spawn the same port."""
    key = url.rstrip("/")
    with _LAZY_WORKER_LOCK:
        lock = _LAZY_WORKER_URL_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _LAZY_WORKER_URL_LOCKS[key] = lock
        return lock


def _mark_jobs_failed_for_worker(worker_url: str, reason: str) -> int:
    """Mark any `_jobs` entries dispatched to a dead worker as error.

    Returns the number of jobs that were transitioned out of `running`.
    Used by the reaper when it notices `proc.poll() != None`.
    """
    key = worker_url.rstrip("/")
    failed = 0
    now = time.time()
    with _jobs_lock:
        for jid, job in _jobs.items():
            if str(job.get("status") or "") != "running":
                continue
            if str(job.get("worker") or "").rstrip("/") != key:
                continue
            job["status"] = "error"
            job["error"] = f"worker process died: {reason}"
            job["finished_at"] = now
            try:
                _finish_job_db_run(job, "error", job["error"])
            except Exception:
                pass
            failed += 1
    return failed


def _lazy_worker_reaper_loop() -> None:
    """Background thread: poll lazy worker procs and reap dead ones.

    Without this, a worker that crashes mid-job leaves its job stuck in
    `_jobs[...]["status"] == "running"` forever because dispatch returns
    successfully once `/run` accepts the POST. The next call to
    `_ensure_lazy_worker` would respawn the worker but never reconcile
    the orphaned job state.
    """
    while True:
        try:
            time.sleep(_LAZY_WORKER_REAPER_INTERVAL)
            with _LAZY_WORKER_LOCK:
                items = list(_LAZY_WORKER_PROCS.items())
            for url, proc in items:
                try:
                    rc = proc.poll()
                except Exception:
                    rc = None
                if rc is None:
                    continue
                with _LAZY_WORKER_LOCK:
                    cur = _LAZY_WORKER_PROCS.get(url)
                    if cur is proc:
                        _LAZY_WORKER_PROCS.pop(url, None)
                failed = _mark_jobs_failed_for_worker(url, f"rc={rc}")
                _LOG.info(
                    f"[lazy-worker] reap url={url} pid={proc.pid} rc={rc} "
                    f"jobs_marked_error={failed}"
                )
        except Exception as exc:
            _LOG.info(f"[lazy-worker] reaper error: {exc}")


def _ensure_lazy_worker_reaper() -> None:
    global _LAZY_WORKER_REAPER_STARTED
    with _LAZY_WORKER_LOCK:
        if _LAZY_WORKER_REAPER_STARTED:
            return
        _LAZY_WORKER_REAPER_STARTED = True
    t = threading.Thread(
        target=_lazy_worker_reaper_loop, name="atlas-lazy-reaper", daemon=True
    )
    t.start()


def _register_lazy_worker_atexit() -> None:
    global _LAZY_WORKER_ATEXIT_REGISTERED
    if _LAZY_WORKER_ATEXIT_REGISTERED:
        return
    _LAZY_WORKER_ATEXIT_REGISTERED = True
    atexit.register(_terminate_lazy_workers)


def _ensure_lazy_worker(job: dict[str, Any]) -> None:
    if not _lazy_workers_enabled():
        return
    workflow = str(job.get("workflow") or "").strip()
    worker_url = str(job.get("worker") or "").strip()
    if not worker_url:
        return
    health = _probe_worker_health(worker_url, timeout=0.7)
    mismatch = _worker_workflow_mismatch(workflow, health)
    if mismatch:
        raise RuntimeError(f"worker mismatch at {worker_url}: {mismatch}")
    if str(health.get("status") or "") == "ok":
        return
    target = _local_worker_target(worker_url)
    if target is None:
        return
    host, port = target
    all_workflows = _worker_url_is_shared_default(workflow, worker_url)
    key = worker_url.rstrip("/")
    url_lock = _get_url_lock(key)
    # Per-URL lock: same-URL spawns serialize (no double-spawn), but
    # spawns to *different* URLs proceed in parallel. Re-check health
    # under the lock — another thread for the same URL may have just
    # finished spawning while we were queued.
    with url_lock:
        health = _probe_worker_health(worker_url, timeout=0.7)
        if str(health.get("status") or "") == "ok":
            return
        with _LAZY_WORKER_LOCK:
            proc = _LAZY_WORKER_PROCS.get(key)
        if proc is not None and proc.poll() is None:
            # A prior call started the process; just wait on /health.
            pass
        else:
            # Global spawn throttle: prevents 12-way import-storm cold
            # starts from all exceeding ATLAS_LAZY_WORKER_START_TIMEOUT.
            with _LAZY_WORKER_SPAWN_SEM:
                cmd = _lazy_worker_command(
                    job=job, host=host, port=port, all_workflows=all_workflows,
                )
                env = os.environ.copy()
                env["ATLAS_PROJECT_ROOT"] = str(
                    job.get("project_root") or env.get("ATLAS_PROJECT_ROOT") or "."
                )
                env["ATLAS_SOURCE_ROOT"] = str(_SOURCE_ROOT)
                env.setdefault("ATLAS_WORKFLOW_ROOT", str(_WORKFLOW_ROOT))
                env["ATLAS_EXEC_MODE"] = "orchestrator"
                env["ATLAS_ORCHESTRATOR_MODE"] = "1"
                env["ATLAS_SINGLE_MAIN_LOOP"] = "0"
                py_path = str(_SOURCE_ROOT)
                env["PYTHONPATH"] = (
                    f"{py_path}{os.pathsep}{env.get('PYTHONPATH', '')}"
                ).rstrip(os.pathsep)
                log_dir = (
                    Path(str(job.get("project_root") or "."))
                    / ".session" / "workers"
                )
                try:
                    log_dir.mkdir(parents=True, exist_ok=True)
                    log_file = log_dir / f"{workflow or 'shared'}-{port}.log"
                    log_fh = log_file.open("ab")
                except Exception:
                    log_fh = None
                try:
                    proc = subprocess.Popen(
                        cmd,
                        cwd=str(job.get("project_root") or _SOURCE_ROOT),
                        env=env,
                        stdout=log_fh or subprocess.DEVNULL,
                        stderr=subprocess.STDOUT if log_fh else subprocess.DEVNULL,
                    )
                finally:
                    if log_fh is not None:
                        try:
                            log_fh.close()
                        except Exception:
                            pass
                with _LAZY_WORKER_LOCK:
                    _LAZY_WORKER_PROCS[key] = proc
                _register_lazy_worker_atexit()
                _ensure_lazy_worker_reaper()
                _LOG.info(
                    f"[lazy-worker] spawn pid={proc.pid} url={key} "
                    f"workflow={workflow or '-'} all_workflows={all_workflows} "
                    f"job={job.get('id') or job.get('run_id') or '-'}"
                )
        timeout_s = float(
            os.environ.get("ATLAS_LAZY_WORKER_START_TIMEOUT", "15") or "15"
        )
        deadline = time.monotonic() + max(1.0, timeout_s)
        t0 = time.monotonic()
        while time.monotonic() < deadline:
            # If the proc died while we were waiting, surface that and
            # let the reaper clean up. Avoids a confusing "timeout"
            # after a fast crash.
            with _LAZY_WORKER_LOCK:
                cur = _LAZY_WORKER_PROCS.get(key)
            if cur is not None and cur.poll() is not None:
                rc = cur.poll()
                _LOG.info(
                    f"[lazy-worker] died-during-start url={worker_url} "
                    f"pid={cur.pid} rc={rc}"
                )
                raise RuntimeError(
                    f"lazy worker exited during start at {worker_url} (rc={rc})"
                )
            health = _probe_worker_health(worker_url, timeout=0.7)
            mismatch = _worker_workflow_mismatch(workflow, health)
            if mismatch:
                _LOG.info(
                    f"[lazy-worker] mismatch url={worker_url} reason={mismatch}"
                )
                raise RuntimeError(
                    f"lazy worker mismatch at {worker_url}: {mismatch}"
                )
            if str(health.get("status") or "") == "ok":
                _LOG.info(
                    f"[lazy-worker] ready url={worker_url} "
                    f"after={time.monotonic() - t0:.2f}s"
                )
                return
            time.sleep(0.25)
        # Timeout: terminate the partially-started proc so it does not
        # become an orphan that races against the next dispatch.
        with _LAZY_WORKER_LOCK:
            stale = _LAZY_WORKER_PROCS.pop(key, None)
        if stale is not None and stale.poll() is None:
            try:
                stale.terminate()
            except Exception:
                pass
        _LOG.info(
            f"[lazy-worker] timeout url={worker_url} after={timeout_s:.1f}s "
            f"(partial proc terminated)"
        )
        raise RuntimeError(
            f"lazy worker did not become healthy at {worker_url}"
        )


def _ensure_lazy_worker_for_direct_dispatch(
    worker_url: str,
    workflow: str,
    project_root_value: str = "",
) -> None:
    """Lazy-start a worker for core.tools' direct dispatch fallback.

    The normal /api/pipeline/dispatch path already builds a full job object
    before calling _ensure_lazy_worker(). The direct fallback only has the
    target workflow/URL, so normalize that small contract here instead of
    duplicating worker-spawn details in core.tools.
    """
    wf = str(workflow or "").strip()
    url = str(worker_url or "").strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = _resolve_worker_url(wf or url)
    pr = str(project_root_value or os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    job = {
        "job_id": f"direct-{wf or 'worker'}",
        "worker": url,
        "workflow": wf,
        "session": f"direct/{wf}" if wf else "direct",
        "project_root": pr,
        "model": _worker_model_default_for(wf),
        "reasoning_effort": _worker_reasoning_effort_default_for(wf),
    }
    _ensure_lazy_worker(job)


def _worker_launch_command(
    worker_url: str,
    workflow: str,
    session_name: str,
    project_root: Path,
    model: str = "",
    reasoning_effort: str = "",
) -> str:
    """Return the operator command that starts a worker on the same artifact root.

    atlas_ui.py can serve an arbitrary --root, for example common_ai_agent/gpio.
    The worker still needs imports from the common_ai_agent source tree, but
    its cwd/ATLAS_PROJECT_ROOT must be the served project root so relative file
    tools operate on the same IP directory the UI is showing.
    """

    port = worker_url.rsplit(":", 1)[-1].split("/", 1)[0]
    py_path = str(_SOURCE_ROOT / "src" / "main.py")
    model_arg = f" --model {shlex.quote(model)}" if model else ""
    effort_arg = f" --effort {shlex.quote(reasoning_effort)}" if reasoning_effort else ""
    return (
        f"cd {shlex.quote(str(project_root))} && "
        f"ATLAS_PROJECT_ROOT={shlex.quote(str(project_root))} "
        f"PYTHONPATH={shlex.quote(str(_SOURCE_ROOT))}:$PYTHONPATH "
        f"python3 {shlex.quote(py_path)} --serve --port {shlex.quote(port)} "
        f"--workflow {shlex.quote(workflow)} "
        f"--worker-name {shlex.quote(workflow)} --session {shlex.quote(session_name)}"
        f"{model_arg}{effort_arg}"
    )


def _default_workflow_prompt(workflow: str, ip: str, stage_id: str = "") -> str:
    stage_prompt_for = {
        "ssot": (
            "[ATLAS_PIPELINE_SSOT_DIRECT_WRITE]\n"
            f"create or refresh {ip}/yaml/{ip}.ssot.yaml as the canonical SSOT for IP `{ip}`. "
            "Use the orchestrator chat goal as the source requirement. This is an ATLAS pipeline "
            "worker run, not an exploratory interview: do not read, grep, or list repository files "
            "before writing the SSOT unless the write path is impossible. If no architect handoff "
            "or imported requirement exists yet, bootstrap a complete engineering draft from the "
            "visible goal instead of searching indefinitely. The first successful content-changing "
            f"tool call should write {ip}/yaml/{ip}.ssot.yaml with concrete draft sections, including "
            "machine-readable function_model output_rules/state_updates and sub_modules ownership refs. "
            f"Then run python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/repair_ssot_schema.py\" {ip} --root \"$ATLAS_PROJECT_ROOT\" --mode engineering "
            f"and python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py\" {ip} --root \"$ATLAS_PROJECT_ROOT\" --mode engineering. "
            f"If {ip}/rtl/rtl_blocked.json exists, answer each blocker inline so SSOT-gen can incorporate "
            "the decisions, then rerun /repair-ssot and validation before handing back to rtl-gen. "
            "Finish with an [SSOT HANDOFF] summarizing assumptions, remaining TBDs, validation evidence, "
            "and downstream RTL/TB obligations."
        ),
        "fl-model": (
            f"run /ssot-fl-model {ip}; generate the SSOT-derived FunctionalModel, "
            "decomposition manifest, FL self-check, and function coverage plan"
        ),
        "cl-model": (
            f"run /ssot-cycle-model {ip} and /ssot-dual-fcov {ip}; generate the SSOT-derived "
            "cycle model when cycle_model requires executable CL, and split FL/CL coverage bins"
        ),
        "equivalence": (
            f"run /ssot-equiv-goals {ip}; derive SSOT-traced FL-vs-RTL goals for "
            "scoreboards, sim_debug, and coverage closure"
        ),
        "rtl": (
            f"run /ssot-rtl {ip}; regenerate RTL from yaml/{ip}.ssot.yaml in the active IP root "
            "and close dynamic RTL TODOs, compile, and lint gates"
        ),
        "lint": f"run /lint-ip {ip}; report and fix root-cause RTL lint errors and warnings",
        "tb": (
            f"run /ssot-tb-cocotb {ip}; generate or repair the goal-driven cocotb/pyuvm "
            "testbench and scoreboard from SSOT, FL/CL model artifacts, and equivalence goals"
        ),
        "sim": f"run /ssot-sim {ip}; execute the generated TB and emit pass/fail plus scoreboard evidence",
        "coverage": (
            f"run /ssot-coverage {ip}; report function_model and cycle_model coverage separately "
            "using SSOT coverage goals and fresh simulation evidence"
        ),
        "sim-debug": f"run /sim-debug {ip}; compare FL/CL expectations against RTL waveform/scoreboard evidence",
        "syn": f"run /syn-auto {ip}; synthesize the RTL using SSOT timing/synthesis policy and the configured PDK",
        "sta": f"run /sta-auto {ip}; generate SDC and run pre-route STA on the synthesized netlist",
        "pnr": f"run /pnr-auto {ip}; run floorplan, place, CTS, route, and SPEF handoff generation",
        "sta-post": f"run /sta-post-auto {ip}; run post-route STA using routed netlist plus SPEF",
        "goal-audit": f"run /goal-audit {ip}; audit SSOT, model, RTL, TB, sim, coverage, and EDA handoff evidence",
    }
    if stage_id in stage_prompt_for:
        return stage_prompt_for[stage_id]
    prompt_for = {
        "architect":  f"review and update the SoC architecture contract for {ip or 'the whole SoC'}; emit handoff notes for ssot-gen",
        "ssot-gen":   f"refresh SSOT for {ip} from the architect handoff and current SoC context",
        "rtl-gen":    f"regenerate RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml",
        "lint":       f"lint {ip}/rtl/*.sv and fix root-cause errors and warnings",
        "tb-gen":     f"generate or update the testbench for {ip}",
        "sim":        f"run simulation for {ip} and report pass/fail counts",
        "syn":        f"synthesise {ip} and emit gate netlist plus area/timing summary",
        "dft":        f"run DFT checks or scan-insertion preparation for {ip}",
        "sta":        f"run pre-route STA for {ip} using the synthesized netlist and SDC",
        "pnr":        f"run PnR for {ip}, producing routed DEF/netlist/SPEF reports",
        "sta-post":   f"run post-route STA for {ip} using routed netlist and SPEF",
    }
    return prompt_for.get(workflow, f"run {workflow}" + (f" on {ip}" if ip else ""))


def _workflow_prompt_with_stage_driver(
    *,
    workflow: str,
    ip: str,
    stage_id: str,
    prompt: str,
) -> str:
    """Preserve canonical slash-command stage drivers under custom prompts.

    Orchestrator tool calls often include a natural-language prompt such as
    "equivalence is done; generate RTL now".  Some workers, notably rtl-gen,
    rely on the stage driver command (/ssot-rtl) to preload dynamic ledgers and
    run disk gates.  Keep that driver in front of user/orchestrator intent.
    """
    default_prompt = _default_workflow_prompt(workflow, ip, stage_id)
    custom_prompt = str(prompt or "").strip()
    if not custom_prompt:
        return default_prompt

    driver_match = re.search(r"run\s+(/[A-Za-z0-9_\-]+)", default_prompt)
    driver = driver_match.group(1) if driver_match else ""
    if driver and _prompt_contains_executable_driver(custom_prompt, driver):
        return custom_prompt

    rtl_blocker_terms = (
        "rtl_blocked.json",
        "rtl_module_contracts",
        "rtl_dynamic_todo_ownership",
        "ssot_behavior_ownership",
        "missing ssot module contracts",
    )
    if workflow == "ssot-gen" and any(term in custom_prompt.lower() for term in rtl_blocker_terms):
        return (
            f"answer the {ip}/rtl/rtl_blocked.json questions inline so SSOT-gen records them; "
            f"then run /resolve-rtl-blockers {ip} --use-recommended-defaults; "
            f"then run /repair-ssot {ip}; "
            f"then python3 \"$ATLAS_WORKFLOW_ROOT/ssot-gen/scripts/verify_ssot.py\" {ip} --root \"$ATLAS_PROJECT_ROOT\" --mode engineering. "
            "This is an RTL blocker repair pass; do not rewrite the IP from scratch.\n\n"
            "[Orchestrator worker instruction]\n"
            + custom_prompt
        )

    if workflow == "ssot-gen" and "[ATLAS_PIPELINE_SSOT_DIRECT_WRITE]" in custom_prompt:
        return custom_prompt

    return (
        default_prompt
        + "\n\n[Orchestrator worker instruction]\n"
        + custom_prompt
    )


def _prompt_contains_executable_driver(prompt: str, driver: str) -> bool:
    """Return True only when *driver* appears as an executable command line."""
    if not driver:
        return False
    text = str(prompt or "")
    if driver not in text:
        return False
    text = re.sub(r"\s+(?:and|then)\s+/", "\n/", text, flags=re.IGNORECASE)
    text = text.replace(";", "\n")
    pattern = re.compile(rf"^{re.escape(driver)}(?:\s|$)")
    for raw in text.splitlines():
        line = raw.strip()
        if line.lower().startswith("run "):
            line = line[4:].strip()
        if pattern.match(line):
            return True
    return False


def _default_todo_template_for_job(workflow: str, stage_id: str, ip: str) -> str:
    if not ip:
        return ""
    if stage_id == "ssot":
        return "atlas-pipeline-ssot"
    if workflow == "ssot-gen":
        return "new-ip"
    if stage_id == "fl-model":
        return "ssot-fl-model"
    if stage_id == "cl-model":
        return ""
    if stage_id == "equivalence":
        return "ssot-equiv-goals"
    if workflow == "rtl-gen" or stage_id == "rtl":
        # RTL owns a dynamic ledger that can contain hundreds of SSOT-derived
        # tasks. The worker should run /ssot-rtl and read the ledger from disk,
        # not receive it as an HTTP todo template payload.
        return ""
    if stage_id == "lint":
        return "lint-fix"
    if workflow == "tb-gen" or stage_id == "tb":
        return "ssot-tb-cocotb"
    if stage_id == "coverage":
        return "coverage_iter"
    if stage_id == "syn":
        return "syn-default"
    if stage_id == "sta":
        return "sta-default"
    if stage_id == "pnr":
        return "pnr-default"
    if stage_id == "sta-post":
        return "sta-post-default"
    return ""


def _dispatch_job_to_worker(job: dict[str, Any]) -> None:
    try:
        import urllib.request as _u
        _ensure_lazy_worker(job)
        context = job["prompt"].split("\n\n", 1)[0]
        if job.get("rtl_version_id"):
            context += (
                "\n[RTL VERSION CONTEXT]\n"
                f"- rtl_version_id: {job.get('rtl_version_id')}\n"
                f"- rtl_version: {job.get('rtl_version') or '(external)'}\n"
                f"- rtl_sha256_tree: {job.get('rtl_sha256_tree') or ''}\n"
                f"- rtl_git_tag: {job.get('rtl_git_tag') or ''}\n"
            )
        artifact_versions = _artifact_versions_map(job)
        if artifact_versions:
            context += "\n[ARTIFACT VERSION CONTEXT]\n"
            for artifact_type in sorted(artifact_versions):
                item = artifact_versions[artifact_type]
                context += (
                    f"- {artifact_type}: {item.get('version') or ''} "
                    f"({item.get('id') or ''})"
                )
                if item.get("git_tag"):
                    context += f" tag={item['git_tag']}"
                if item.get("sha256_tree"):
                    context += f" tree={item['sha256_tree']}"
                context += "\n"
        body = {
            "task":     job["prompt"],
            "workflow": job["workflow"],
            "session":  job.get("session", ""),
            "model":    job.get("model", ""),
            "reasoning_effort": job.get("reasoning_effort", ""),
            "toolchain": job.get("toolchain", ""),
            "run_mode": job.get("run_mode", ""),
            "exec_mode": job.get("exec_mode", ""),
            "context":  context,
            "project_root": job.get("project_root", ""),
            "source_root": job.get("source_root", ""),
            "sync":     False,
            "job_id":    job.get("job_id", ""),
            "stage_id":  job.get("stage_id", ""),
            "pipeline_id": job.get("pipeline_id", ""),
            "pipeline_run_id": job.get("pipeline_run_id") or job.get("pipeline_id", ""),
            "pipeline_index": job.get("pipeline_index", 0),
            "scope_path": job.get("scope_path", ""),
            "user_id":   job.get("user_id", ""),
        }
        if job.get("template"):
            body["template"] = job["template"]
        if job.get("ip"):
            body["ip"] = job["ip"]
        if job.get("rtl_version_id"):
            body["rtl_version_id"] = job["rtl_version_id"]
        if artifact_versions:
            body["artifact_versions"] = list(artifact_versions.values())
        payload = json.dumps(body).encode("utf-8")
        req = _u.Request(
            f"{job['worker'].rstrip('/')}/run",
            data=payload, method="POST",
            headers={"Content-Type": "application/json"},
        )
        with _u.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
        run_id = resp_data.get("run_id", "")
        if not run_id:
            raise RuntimeError(f"worker did not return run_id: {resp_data}")
        _LOG.info(
            f"[dispatch] job={job.get('job_id') or '-'} "
            f"workflow={job.get('workflow') or '-'} "
            f"-> {job['worker'].rstrip('/')} run_id={run_id}"
        )
        with _jobs_lock:
            live = _jobs.get(job["job_id"], job)
            live["run_id"]     = run_id
            live["status"]     = "running"
            live["started_at"] = time.time()
            live["error"]      = ""
            _record_job_db_running(live)
    except Exception as e:
        _LOG.info(
            f"[dispatch] FAIL job={job.get('job_id') or '-'} "
            f"workflow={job.get('workflow') or '-'} "
            f"worker={job.get('worker')} error={e}"
        )
        with _jobs_lock:
            live = _jobs.get(job["job_id"], job)
            live["status"]      = "error"
            live["error"]       = f"worker dispatch failed at {job.get('worker')}: {e}"
            live["finished_at"] = time.time()
            _finish_job_db_run(live, "error", live["error"])


def _advance_pipeline_from(job: dict[str, Any]) -> None:
    # Wake any orchestrator yield_run waker watching this job. Lazy/defensive:
    # the runner singleton may not be initialised (CLI runs, isolated tests),
    # and a failed notify must never block pipeline progression.
    job_id = str(job.get("job_id") or "")
    job_status = str(job.get("status") or "")
    if job_id and job_status in ("completed", "error", "cancelled", "blocked"):
        try:
            from src.orchestrator.runner import notify_job_complete

            notify_job_complete(job_id, job_status)
        except Exception:
            pass

    pipeline_id = job.get("pipeline_id") or ""
    if not pipeline_id:
        return
    if job.get("status") in ("error", "cancelled", "blocked"):
        reason = f"blocked by {job.get('workflow')} {job.get('status')}"
        with _jobs_lock:
            _mark_downstream_blocked_locked(pipeline_id, job.get("job_id", ""), reason)
        if job.get("status") != "error":
            return
    elif job.get("status") != "completed":
        return
    else:
        _ensure_stage_artifact_version_for_job(job, Path(job.get("project_root") or ".").resolve())
    ready_jobs: list[dict[str, Any]] = []
    with _jobs_lock:
        jobs_by_id = {
            str(j.get("job_id")): j
            for j in _jobs.values()
            if j.get("pipeline_id") == pipeline_id
        }
        candidates = [j for j in jobs_by_id.values() if j.get("status") == "queued"]
        candidates.sort(key=lambda j: j.get("pipeline_index", 0))
        for candidate in candidates:
            deps = _job_dependency_ids(candidate)
            dep_jobs = [jobs_by_id.get(dep, {}) for dep in deps]
            dep_statuses = [dep_job.get("status", "") for dep_job in dep_jobs]
            blocked_by_dependency = False
            for dep_job in dep_jobs:
                status = dep_job.get("status", "")
                if status not in {"error", "cancelled", "blocked"}:
                    continue
                if _job_allows_failed_dependency(candidate, dep_job):
                    continue
                blocked_by_dependency = True
                break
            if blocked_by_dependency:
                candidate["status"] = "blocked"
                candidate["error"] = "blocked by failed dependency"
                candidate["finished_at"] = time.time()
                _finish_job_db_run(candidate, "blocked", candidate["error"])
                continue
            if deps and all(
                status == "completed" or _job_allows_failed_dependency(candidate, dep_job)
                for status, dep_job in zip(dep_statuses, dep_jobs)
            ):
                for dep in deps:
                    upstream = jobs_by_id.get(dep, {})
                    if upstream:
                        _copy_artifact_version_context(candidate, upstream)
                if candidate.get("stage_id") in _RTL_VERSION_DOWNSTREAM_STAGES:
                    for dep in deps:
                        upstream = jobs_by_id.get(dep, {})
                        if upstream.get("rtl_version_id"):
                            _copy_rtl_version_context(candidate, upstream)
                            break
                candidate["status"] = "pending"
                ready_jobs.append(candidate)
    for ready_job in ready_jobs:
        _dispatch_job_to_worker(ready_job)


def _orchestrator_mode_enabled() -> bool:
    if os.environ.get("ATLAS_ORCHESTRATOR_MODE") is not None:
        return _truthy_env("ATLAS_ORCHESTRATOR_MODE")
    explicit = _normalize_exec_mode(os.environ.get("ATLAS_EXEC_MODE"))
    if explicit:
        return explicit == "orchestrator"
    explicit = _normalize_exec_mode(os.environ.get("ATLAS_DEFAULT_EXEC_MODE"))
    if explicit:
        return explicit == "orchestrator"
    if os.environ.get("ATLAS_ORCHESTRATOR_MODE") is None:
        return True
    return _truthy_env("ATLAS_ORCHESTRATOR_MODE")


def _orchestrator_block(
    ip_dir: Path,
    *,
    scope_filter: dict | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Compute the `orchestrator` and `handoffs_by_workflow` payload sections.

    Shape matches `doc/wiki/orchestrator-worker-handoff.md` §UI Contract.
    Counts are always read from disk so the UI shows accurate queue state
    even when `ATLAS_ORCHESTRATOR_MODE` is off (orchestrator.enabled=False).

    `scope_filter` is forwarded to the queue readers so multi-user callers
    only see their own handoffs. Pipeline-level Review Decision Needed
    records are NOT scope-aware today (the file format predates the scope
    contract), so `decisions_needed` remains a global count.
    """
    try:
        from src.handoff_queue import queue_totals, summary_by_workflow
        from src.review_decisions import count_open_decisions, list_open_decisions
    except ModuleNotFoundError:
        from handoff_queue import queue_totals, summary_by_workflow  # type: ignore[no-redef]
        from review_decisions import count_open_decisions, list_open_decisions  # type: ignore[no-redef]

    totals = queue_totals(ip_dir, scope_filter=scope_filter)
    open_decisions = count_open_decisions(ip_dir)
    decision_items = list_open_decisions(ip_dir)
    handoffs = summary_by_workflow(ip_dir, scope_filter=scope_filter)

    enabled = _orchestrator_mode_enabled()
    # Mode resolution: a gateway/lease layer is not built yet, so we cannot
    # detect "worker" or "mixed" — when the env flag is on we report "json"
    # (durable queue path) until the gateway lands.
    mode = "json" if enabled else None

    orchestrator = {
        "enabled": enabled,
        "mode": mode,
        "pending_handoffs": totals["pending_handoffs"],
        "claimed_handoffs": totals["claimed_handoffs"],
        "review_decisions": totals["review_decisions"],
        "decisions_needed": open_decisions,
        "decision_items": [
            {
                "path": item.get("path") or "",
                "workflow": item.get("workflow") or item.get("owner") or "",
                "topic": item.get("topic") or item.get("signature") or "",
                "status": item.get("status") or "",
                "severity": item.get("severity") or "",
                "decision_needed": item.get("decision_needed") or item.get("reason") or "",
                "recommended_option": item.get("recommended_option") or "",
                "evidence": item.get("evidence") if isinstance(item.get("evidence"), dict) else {},
                "options": item.get("options") if isinstance(item.get("options"), list) else [],
            }
            for item in decision_items[:8]
        ],
        "workers": {},
    }
    return orchestrator, handoffs


def _public_job(job: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in job.items() if not k.startswith("_")}


_ACTIVE_DISPATCH_STATES = {"pending", "queued", "running"}


def _active_job_conflicts(
    *,
    ip: str,
    stage_ids: list[str] | set[str] | tuple[str, ...],
    workflows: list[str] | set[str] | tuple[str, ...] = (),
    user_id: str = "",
    db_user_id: str = "",
) -> list[dict[str, Any]]:
    """Return active jobs that would duplicate the same scoped worker lane."""
    ip_name = str(ip or "").strip()
    stage_set = {str(item or "").strip() for item in stage_ids if str(item or "").strip()}
    workflow_set = {str(item or "").strip() for item in workflows if str(item or "").strip()}
    user_name = str(user_id or "").strip()
    db_user = str(db_user_id or "").strip()
    conflicts: list[dict[str, Any]] = []
    with _jobs_lock:
        for job in _jobs.values():
            status = str(job.get("status") or "").strip()
            if status not in _ACTIVE_DISPATCH_STATES:
                continue
            if ip_name and str(job.get("ip") or "").strip() != ip_name:
                continue
            job_db_user = str(job.get("db_user_id") or "").strip()
            if db_user and job_db_user and job_db_user != db_user:
                continue
            job_user = str(job.get("user_id") or "").strip()
            if not db_user and user_name and job_user and job_user != user_name:
                continue
            job_stage = str(job.get("stage_id") or "").strip()
            job_workflow = str(job.get("workflow") or "").strip()
            if stage_set and job_stage not in stage_set and job_workflow not in stage_set:
                continue
            if workflow_set and job_workflow not in workflow_set and job_stage not in workflow_set:
                continue
            conflicts.append(_public_job(job))
    return conflicts


def _dedupe_payload(conflicts: list[dict[str, Any]], *, ip: str) -> dict[str, Any]:
    pipeline_ids = sorted({
        str(job.get("pipeline_run_id") or job.get("pipeline_id") or "")
        for job in conflicts
        if str(job.get("pipeline_run_id") or job.get("pipeline_id") or "")
    })
    return {
        "ok": True,
        "deduped": True,
        "status": "already_running",
        "ip": ip,
        "pipeline_id": pipeline_ids[0] if len(pipeline_ids) == 1 else "",
        "pipeline_run_id": pipeline_ids[0] if len(pipeline_ids) == 1 else "",
        "existing_jobs": conflicts,
        "jobs": conflicts,
        "reply": (
            f"{ip} already has active worker job(s): "
            + ", ".join(
                f"{job.get('stage_id') or job.get('workflow')}:{job.get('status')}"
                for job in conflicts[:6]
            )
        ),
    }


def _refresh_rtl_authoring_provenance_for_job(job: dict[str, Any], project_root: Path) -> bool:
    stage = str(job.get("stage_id") or "").strip()
    workflow = str(job.get("workflow") or "").strip()
    if stage != "rtl" and workflow != "rtl-gen":
        return False
    ip = str(job.get("ip") or "").strip()
    if not ip or ".." in ip or "/" in ip or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
        return False
    ip_dir = _ip_dir_for(project_root, ip)
    if not ip_dir.is_dir():
        return False
    provenance_path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
    filelist_path = ip_dir / "list" / f"{ip}.f"
    if provenance_path.is_file() and filelist_path.is_file():
        return False
    if job.get("_rtl_provenance_refresh_attempted"):
        return False
    job["_rtl_provenance_refresh_attempted"] = True
    try:
        try:
            from src.headless_workflow import HeadlessWorkflowRunner
        except ModuleNotFoundError:
            from headless_workflow import HeadlessWorkflowRunner  # type: ignore[no-redef]

        runner = HeadlessWorkflowRunner(
            root=str(_tool_project_root_for_ip(project_root, ip)),
            model=str(job.get("model") or ""),
            run_mode=str(job.get("run_mode") or _current_run_mode()),
        )
        ok = bool(runner._refresh_rtl_filelist_and_provenance(ip))
    except Exception as exc:
        job["rtl_provenance_error"] = str(exc)
        return False
    if ok:
        job["rtl_provenance_refreshed"] = True
    return ok


def _job_artifact_recovery(
    job: dict[str, Any],
    project_root: Path,
) -> tuple[bool, str]:
    """Recover UI job state when an HTTP worker forgot an old run_id.

    Worker runs are in-memory, while Architect state is filesystem-backed.
    If a worker restarts or drops a run, /status/{run_id} returns 404 even
    though the stage may have already produced valid artifacts.  Use the same
    coarse filesystem contract as /api/soc so the web UI does not leave
    completed work blinking as "running" forever.
    """
    ip = str(job.get("ip") or "").strip()
    if not ip or ".." in ip or "/" in ip:
        return False, ""
    ip_dir = _ip_dir_for(project_root, ip)
    if not ip_dir.is_dir():
        return False, ""
    stage    = str(job.get("stage_id") or job.get("workflow") or "").strip()
    workflow = str(job.get("workflow") or "").strip()
    def _any_file(*rel_paths: str) -> tuple[bool, str]:
        for rel in rel_paths:
            if (ip_dir / rel).is_file():
                return True, f"recovered from artifact: {ip}/{rel}"
        return False, ""
    if stage == "ssot" or workflow == "ssot-gen":
        ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            return False, ""
        checker = _workflow_root_for_project(project_root) / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        if not checker.is_file():
            return False, f"SSOT checker missing: {checker}"
        try:
            proc = subprocess.run(
                ["bash", str(checker), ip, "--mode", _current_run_mode()],
                cwd=str(_tool_project_root_for_ip(project_root, ip)),
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=30,
                check=False,
            )
        except Exception as exc:
            return False, f"SSOT validator failed to run: {type(exc).__name__}: {exc}"
        if proc.returncode == 0:
            return True, f"recovered from validated artifact: {ip}/yaml/{ip}.ssot.yaml"
        detail = (proc.stdout or "").strip().splitlines()
        tail = detail[-1] if detail else f"rc={proc.returncode}"
        return False, f"SSOT artifact failed validator: {tail}"
    if stage == "fl-model":
        return _any_file(
            "model/functional_model.py",
            "model/fl_model_check.json",
            "cov/fcov_plan.json",
        )
    if stage == "cl-model":
        return _any_file(
            "model/cycle_model.py",
            "model/cl_model_check.json",
            "cov/cl_fcov_plan.json",
        )
    if stage == "equivalence":
        return _any_file("verify/equivalence_goals.json")
    if stage == "rtl" or workflow == "rtl-gen":
        _refresh_rtl_authoring_provenance_for_job(job, project_root)
        filelist  = ip_dir / "list" / f"{ip}.f"
        rtl_dir   = ip_dir / "rtl"
        rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
        return bool(filelist.is_file() and rtl_files), f"recovered from artifact: {ip}/list/{ip}.f"
    if stage == "lint" or workflow == "lint":
        return _any_file("lint/dut_lint.json", "lint/lint_report.json")
    if stage == "tb" or workflow == "tb-gen":
        tb_dir = ip_dir / "tb"
        if not tb_dir.is_dir():
            return False, ""
        artifacts = (
            list(tb_dir.rglob("*.py"))
            + list(tb_dir.rglob("*.sv"))
            + list(tb_dir.rglob("*.v"))
        )
        return bool(artifacts), f"recovered from artifact: {ip}/tb"
    if stage == "sim" or workflow == "sim":
        return _any_file(
            "sim/results.xml",
            "tb/cocotb/results.xml",
            "sim/scoreboard_events.jsonl",
            "sim/sim_report.txt",
        )
    if stage == "coverage" or workflow == "coverage":
        return _any_file(
            "cov/coverage.json",
            "cov/coverage_ssot.json",
            "cov/coverage_functional.json",
            "sim/coverage_report.md",
        )
    if stage == "goal-audit":
        audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
        if not audit_path.is_file():
            return False, ""
        try:
            doc = json.loads(audit_path.read_text(encoding="utf-8"))
        except Exception:
            return False, f"unparseable artifact: {ip}/sim/fl_rtl_goal_audit.json"
        if str(doc.get("status") or "").lower() == "pass":
            return True, f"recovered from passing artifact: {ip}/sim/fl_rtl_goal_audit.json"
        return False, f"non-passing artifact: {ip}/sim/fl_rtl_goal_audit.json"
    if stage == "sim-debug" or (workflow == "sim_debug" and stage != "goal-audit"):
        sim_dir   = ip_dir / "sim"
        cov_dir   = ip_dir / "cov"
        artifacts: list = []
        if sim_dir.is_dir():
            artifacts.extend([p for p in (
                sim_dir / "mismatch_classification.json",
                sim_dir / "debug_tap.json",
                sim_dir / "rtl_elaboration.json",
                sim_dir / "source_tracking.json",
            ) if p.is_file()])
            artifacts.extend(list(sim_dir.rglob("*.vcd")))
            artifacts.extend(list(sim_dir.rglob("coverage_report.*")))
        if cov_dir.is_dir():
            artifacts.extend(list(cov_dir.rglob("coverage.json")))
            artifacts.extend(list(cov_dir.rglob("toggle.json")))
        return bool(artifacts), f"recovered from artifact: {ip}/sim + {ip}/cov"
    if stage == "syn" or workflow == "syn":
        return _any_file("syn/out/synth.v", "syn/out/syn.report.md", "syn/out/area.json")
    if stage == "sta" or workflow == "sta":
        return _any_file("sta/out/wns.json", "sta/out/sta.report.md", f"sta/out/{ip}.sdc")
    if stage == "pnr" or workflow == "pnr":
        return _any_file("pnr/out/routed.spef", "pnr/out/routed.v", "pnr/out/pnr.report.md")
    if stage == "sta-post" or workflow == "sta-post":
        return _any_file("sta-post/out/wns.json", "sta-post/out/sta.report.md")
    return False, ""


def _rtl_gate_failure_reason(ip_dir: Path, ip: str) -> str:
    """Return a concise RTL gate failure reason from stage/todo evidence."""

    def _read_json(rel: str) -> tuple[dict[str, Any] | None, str]:
        path = ip_dir / rel
        if not path.is_file():
            return None, ""
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None, f"unparseable artifact: {ip}/{rel}"
        return doc if isinstance(doc, dict) else {}, ""

    def _gate_reason(rel: str, gate: Any, *, force: bool = False) -> str:
        if not isinstance(gate, dict):
            return ""
        status = str(gate.get("status") or "").strip().lower()
        try:
            open_required = int(gate.get("open_required_todos") or gate.get("open_required_count") or 0)
        except Exception:
            open_required = 0
        try:
            static_missing = int(gate.get("static_missing") or gate.get("static_missing_count") or 0)
        except Exception:
            static_missing = 0
        try:
            blocking_questions = int(gate.get("blocking_questions") or 0)
        except Exception:
            blocking_questions = 0
        all_required = gate.get("all_required_todos_pass")
        failed = (
            status in {"fail", "failed", "error", "blocked", "human_gate"}
            or force
            or (all_required is False and (open_required or static_missing or blocking_questions))
        )
        if not failed:
            return ""
        details = [f"gate status={status or 'fail'}"]
        if open_required:
            details.append(f"open_required_todos={open_required}")
        if static_missing:
            details.append(f"static_missing={static_missing}")
        if blocking_questions:
            details.append(f"blocking_questions={blocking_questions}")
        return f"{ip}/{rel} " + " ".join(details)

    stage_doc, error = _read_json("logs/stage_engine/ssot-rtl.json")
    if error:
        return error
    if stage_doc is not None:
        metadata = stage_doc.get("metadata") if isinstance(stage_doc.get("metadata"), dict) else {}
        rtl_plan = metadata.get("rtl_todo_plan") if isinstance(metadata.get("rtl_todo_plan"), dict) else {}
        gate = rtl_plan.get("gate") if isinstance(rtl_plan, dict) else None
        reason = _gate_reason("logs/stage_engine/ssot-rtl.json", gate)
        if reason:
            return reason
        status = str(stage_doc.get("status") or "").strip().lower()
        if status in {"fail", "failed", "error", "blocked", "human_gate"}:
            headline = str(stage_doc.get("headline") or stage_doc.get("message") or "").strip()
            if headline:
                headline = headline.splitlines()[0][:180]
                return f"{ip}/logs/stage_engine/ssot-rtl.json status={status} {headline}"
            return f"{ip}/logs/stage_engine/ssot-rtl.json status={status}"

    todo_doc, error = _read_json("rtl/rtl_todo_plan.json")
    if error:
        return error
    if todo_doc is not None:
        reason = _gate_reason("rtl/rtl_todo_plan.json", todo_doc.get("gate"))
        if reason:
            return reason
    return ""


def _job_artifact_failure(
    job: dict[str, Any],
    project_root: Path,
) -> tuple[bool, str]:
    ip = str(job.get("ip") or "").strip()
    if not ip or ".." in ip or "/" in ip:
        return False, ""
    ip_dir = _ip_dir_for(project_root, ip)
    if not ip_dir.is_dir():
        return False, ""
    stage = str(job.get("stage_id") or job.get("workflow") or "").strip()
    workflow = str(job.get("workflow") or "").strip()
    if stage == "lint" or workflow == "lint":
        for rel in ("lint/dut_lint.json", "lint/lint_report.json"):
            path = ip_dir / rel
            if not path.is_file():
                continue
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return True, f"unparseable artifact: {ip}/{rel}"
            errors = doc.get("errors", doc.get("error_count", doc.get("errorCount", 0)))
            try:
                error_count = int(errors)
            except Exception:
                error_count = 0
            if error_count > 0:
                return True, f"{ip}/{rel} errors={error_count}"
            return False, ""
    if stage == "sim" or workflow == "sim":
        results_xml = ip_dir / "sim" / "results.xml"
        if not results_xml.is_file():
            results_xml = ip_dir / "tb" / "cocotb" / "results.xml"
        if results_xml.is_file():
            try:
                _tests, failures, errors = _junit_counts(results_xml)
                failures += errors
            except Exception:
                return True, f"unparseable artifact: {ip}/{results_xml.relative_to(ip_dir).as_posix()}"
            if failures > 0:
                return True, f"{ip}/{results_xml.relative_to(ip_dir).as_posix()} failures={failures}"
            return False, ""
    if stage == "rtl" or workflow == "rtl-gen":
        rtl_dir = ip_dir / "rtl"
        gate_reason = _rtl_gate_failure_reason(ip_dir, ip)
        if gate_reason:
            return True, gate_reason
        blocked_path = rtl_dir / "rtl_blocked.json"
        if blocked_path.is_file():
            try:
                blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
            except Exception:
                return True, f"unparseable artifact: {ip}/rtl/rtl_blocked.json"
            if isinstance(blocked_doc, dict) and blocked_doc:
                reason = str(blocked_doc.get("reason") or "rtl_blocked").strip()
                questions = blocked_doc.get("questions")
                question_ids: list[str] = []
                if isinstance(questions, list):
                    for item in questions:
                        if isinstance(item, dict):
                            qid = str(item.get("id") or "").strip()
                            if qid:
                                question_ids.append(qid)
                suffix = f"; questions={','.join(question_ids)}" if question_ids else ""
                return True, f"{ip}/rtl/rtl_blocked.json {reason}{suffix}"
        if rtl_dir.is_dir():
            placeholder_hits: list[str] = []
            for path in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v"))):
                try:
                    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                        if re.search(r"\b(TBD|TODO|PLACEHOLDER|stub)\b", line, flags=re.IGNORECASE):
                            rel = path.relative_to(ip_dir).as_posix()
                            placeholder_hits.append(f"{rel}:{line_no}")
                            break
                except Exception:
                    rel = path.relative_to(ip_dir).as_posix()
                    return True, f"unreadable RTL source: {ip}/{rel}"
            if placeholder_hits:
                return True, "placeholder RTL markers: " + ", ".join(placeholder_hits[:6])
        has_rtl_evidence = (
            rtl_dir.is_dir()
            or (ip_dir / "list" / f"{ip}.f").is_file()
            or (ip_dir / "rtl" / "rtl_compile.json").is_file()
            or (ip_dir / "lint" / "dut_lint.json").is_file()
            or (ip_dir / "logs" / "stage_engine" / "ssot-rtl.json").is_file()
        )
        checker = _workflow_root_for_project(project_root) / "rtl-gen" / "scripts" / "check_rtl_disk.sh"
        if has_rtl_evidence and checker.is_file():
            try:
                proc = subprocess.run(
                    ["bash", str(checker), ip],
                    cwd=str(_tool_project_root_for_ip(project_root, ip)),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=45,
                    check=False,
                )
            except Exception as exc:
                return True, f"RTL validator failed to run: {type(exc).__name__}: {exc}"
            if proc.returncode != 0:
                detail = (proc.stdout or "").strip().splitlines()
                tail = detail[-1] if detail else f"rc={proc.returncode}"
                return True, f"RTL validator failed: {tail}"
        return False, ""
    if stage == "syn" or workflow == "syn":
        reason = _synthesis_artifact_failure(ip_dir)
        if reason:
            return True, f"{ip}/{reason}"
        return False, ""
    if stage == "sta" or workflow == "sta":
        reason = _timing_artifact_failure(ip_dir, "sta")
        if reason:
            return True, f"{ip}/sta/out/wns.json {reason}"
        return False, ""
    if stage == "pnr" or workflow == "pnr":
        reason = _pnr_artifact_failure(ip_dir)
        if reason:
            return True, f"{ip}/pnr/out/drc.json {reason}"
        return False, ""
    if stage == "sta-post" or workflow == "sta-post":
        reason = _timing_artifact_failure(ip_dir, "sta-post")
        if reason:
            return True, f"{ip}/sta-post/out/wns.json {reason}"
        return False, ""
    if stage != "goal-audit":
        return False, ""
    audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
    if not audit_path.is_file():
        return False, ""
    try:
        doc = json.loads(audit_path.read_text(encoding="utf-8"))
    except Exception:
        return True, f"unparseable artifact: {ip}/sim/fl_rtl_goal_audit.json"
    status = str(doc.get("status") or "").lower()
    if status != "pass":
        blockers = doc.get("summary", {}).get("blockers") if isinstance(doc.get("summary"), dict) else []
        if isinstance(blockers, list) and blockers:
            return True, "blockers=" + ",".join(str(item) for item in blockers)
        return True, f"status={status or 'missing'}"
    return False, ""


def _job_requires_completion_evidence(job: dict[str, Any]) -> bool:
    stage_id = str(job.get("stage_id") or "").strip()
    if stage_id in _PIPELINE_BY_ID:
        return True
    workflow = str(job.get("workflow") or "").strip()
    return workflow in _PIPELINE_BY_WORKFLOW


def _enforce_completion_evidence_gate(job: dict[str, Any], project_root: Path) -> None:
    if job.get("status") != "completed" or not _job_requires_completion_evidence(job):
        return
    failed, failure_reason = _job_artifact_failure(job, project_root)
    if failed:
        job["status"] = "error"
        job["error"] = f"stage evidence failed: {failure_reason}"
        job["finished_at"] = job.get("finished_at") or time.time()
        return
    ok, evidence_summary = _job_artifact_recovery(job, project_root)
    if ok:
        job["evidence_summary"] = evidence_summary
        return
    stage_id = str(job.get("stage_id") or job.get("workflow") or "").strip()
    job["status"] = "error"
    job["error"] = (
        f"missing required evidence for {stage_id}; "
        "worker reported completed but no stage artifact was found"
    )
    job["finished_at"] = job.get("finished_at") or time.time()


def _refresh_tracked_jobs(project_root_path: Path | None = None) -> tuple[list[dict[str, Any]], bool]:
    """Poll running workers and advance ready pipeline jobs.

    `/api/jobs` used to be the only endpoint that performed this refresh. The
    pipeline UI mainly polls `/api/pipeline/state`, so a run-to-green pipeline
    could stay visually stuck on the first running stage until another widget
    happened to hit `/api/jobs`.
    """
    pr = project_root_path or project_root()
    now = time.time()
    changed = False
    with _jobs_lock:
        snapshot = list(_jobs.values())
    for job in snapshot:
        # Poll both "running" and "pending" jobs that have an assigned run_id.
        # An assigned run_id means dispatch_job_to_worker reached the worker and
        # received a server-side run id back — but the worker thread for the
        # actual task may not have transitioned the run from "pending" to
        # "running" yet. Without polling "pending" here, the local view stays
        # stuck on "pending" forever once the first poll observed it; we then
        # miss the eventual "completed" transition entirely.
        if (
            job.get("run_id")
            and job["status"] in ("running", "pending")
            and (now - job.get("_last_polled", 0)) > 1.5
        ):
            try:
                import urllib.request as _u
                req = _u.Request(
                    f"{job['worker'].rstrip('/')}/status/{job['run_id']}",
                    method="GET",
                )
                with _u.urlopen(req, timeout=5) as resp:
                    s = json.loads(resp.read().decode("utf-8"))
                job["_last_polled"] = now
                before = job.get("status")
                job["status"] = s.get("status", job["status"])
                changed = changed or job.get("status") != before
                if isinstance(s.get("iterations"), int):
                    job["iterations"] = s["iterations"]
                if s.get("status") in ("completed", "error", "cancelled"):
                    try:
                        req2 = _u.Request(
                            f"{job['worker'].rstrip('/')}/result/{job['run_id']}",
                            method="GET",
                        )
                        with _u.urlopen(req2, timeout=5) as r2:
                            rr = json.loads(r2.read().decode("utf-8"))
                        job["files_modified"] = rr.get("files_modified") or []
                        job["result_summary"] = (rr.get("result") or "")[:600]
                        job["error"] = rr.get("error") or ""
                        job["finished_at"] = now
                        if rr.get("execution_time_ms"):
                            job["duration_ms"] = rr["execution_time_ms"]
                    except Exception:
                        pass
                    _enforce_completion_evidence_gate(job, pr)
                    if job.get("status") == "completed":
                        _ensure_stage_artifact_version_for_job(job, pr)
                    _finish_job_db_run(job, job.get("status"))
                    _advance_pipeline_from(job)
            except Exception as e:
                recovered, detail = _job_artifact_recovery(job, pr)
                if recovered:
                    job["status"] = "completed"
                    job["error"] = ""
                    job["result_summary"] = detail
                    job["finished_at"] = now
                    _finish_job_db_run(job, "completed")
                    _advance_pipeline_from(job)
                    changed = True
                else:
                    job["error"] = f"poll failed: {e}"
        if job.get("status") == "completed":
            before_gate = job.get("status")
            _enforce_completion_evidence_gate(job, pr)
            changed = changed or job.get("status") != before_gate
            if job.get("status") == "completed":
                _ensure_stage_artifact_version_for_job(job, pr)
        if job.get("status") in ("completed", "error", "cancelled"):
            _finish_job_db_run(job, job.get("status"))
            _advance_pipeline_from(job)
    return snapshot, changed


# ── Factory ─────────────────────────────────────────────────────────

def register_jobs_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    normalize_session_name: Callable[[str], str],
    persist_config_values: Callable[[dict[str, str]], None] | None = None,
) -> None:
    """Mount all /api/job* and /api/jobs* and /api/pipeline/* routes onto *app*.

    project_root and normalize_session_name are passed as callables so the
    routes always see the live values — the --root flag in atlas_ui.main()
    rebinds PROJECT_ROOT after this module is imported.
    """

    def _multi_user_enabled() -> bool:
        raw = os.environ.get("ATLAS_MULTI_USER")
        if raw is None or not raw.strip():
            return True
        return raw.strip().lower() not in ("0", "false", "no", "off")

    def _request_username(request: Request) -> str:
        user = request.scope.get("user") or {}
        return normalize_session_name(str(user.get("username") or user.get("id") or ""))

    def _request_db_user_id(request: Request) -> str:
        user = request.scope.get("user") or {}
        return str(user.get("id") or "").strip()

    def _default_job_session_for_owner(owner: str, ip: str, workflow: str) -> str:
        if _multi_user_enabled() and owner and owner != "local-admin":
            return f"{owner}/{ip}/{workflow}" if ip else f"{owner}/{workflow}"
        return f"{ip}/{workflow}" if ip else workflow

    def _default_job_session(request: Request, ip: str, workflow: str) -> str:
        return _default_job_session_for_owner(_request_username(request), ip, workflow)

    def _pipeline_session_prefix_for_owner(owner: str, ip: str, pipeline_id: str) -> str:
        ip_name = ip or "soc"
        if _multi_user_enabled() and owner and owner != "local-admin":
            return f"{owner}/{ip_name}/pipeline/{pipeline_id}"
        return f"{ip_name}/pipeline/{pipeline_id}"

    def _pipeline_session_prefix(request: Request, ip: str, pipeline_id: str) -> str:
        return _pipeline_session_prefix_for_owner(_request_username(request), ip, pipeline_id)

    def _assert_ip_access(db_user_id: str, ip: str) -> bool:
        """Return True if db_user_id may access ip.

        An IP is owned by the user whose workspace holds the earliest
        workflow_run for that IP name. If no workflow_run exists yet the IP
        is unclaimed and any authenticated user may claim it. If workflow_runs
        exist, the requesting user must be the owner of the workspace that
        holds those runs, or have an explicit ip_permissions grant.

        Only enforced when multi-user mode is on and the request carries a real
        user identity (not empty / local-admin).
        """
        if not _multi_user_enabled():
            return True
        if not db_user_id or db_user_id == "local-admin":
            return True
        pr = project_root()
        try:
            from core.atlas_db import AtlasDB
            with AtlasDB(_atlas_job_db_path(pr)) as _db:
                canonical = _canonical_user_id(_db, db_user_id) or db_user_id
                # Check explicit permission grant first (covers shared IPs)
                grant = _db._fetchone(
                    """
                    SELECT p.id FROM ip_permissions p
                      JOIN ip_blocks i ON i.id = p.ip_id
                     WHERE p.grantee_user_id = ?
                       AND i.ip_name = ?
                       AND (p.expires_at IS NULL OR p.expires_at > ?)
                    LIMIT 1
                    """,
                    (canonical, ip, __import__("time").time()),
                )
                if grant is not None:
                    return True
                # Find the workspace that owns the earliest workflow_run for
                # this IP. That workspace's owner is the de-facto IP owner.
                first_run = _db._fetchone(
                    """
                    SELECT w.owner_user_id
                      FROM workflow_runs wr
                      JOIN ip_blocks i ON i.id = wr.ip_id
                      JOIN workspaces w ON w.id = wr.workspace_id
                     WHERE i.ip_name = ?
                       AND w.owner_user_id != ''
                     ORDER BY wr.started_at ASC
                     LIMIT 1
                    """,
                    (ip,),
                )
                if first_run is None:
                    # No workflow_run yet — IP is unclaimed, allow access
                    return True
                ip_owner = str(first_run["owner_user_id"] or "")
                return ip_owner == canonical
        except Exception:
            return True

    def _active_tool_owner() -> str:
        session_name = normalize_session_name(os.environ.get("ATLAS_ACTIVE_SESSION", ""))
        if session_name and "/" in session_name:
            return normalize_session_name(session_name.split("/", 1)[0])
        raw = os.environ.get("ATLAS_ACTIVE_USER") or ""
        return normalize_session_name(raw)

    def _make_job_record(
        *, workflow: str, ip: str, prompt: str, model: str = "",
        session_name: str = "", stage_id: str = "", pipeline_id: str = "",
        pipeline_index: int = 0, depends_on: str | list[str] = "",
        worker_override: str = "", auto_start: bool = True, template: str = "",
        pipeline_schedule: str = "", rtl_version_id: str = "",
        run_mode: str = "", exec_mode: str = "", user_id: str = "",
        db_user_id: str = "", db_session_id: str = "",
        trigger_source: str = "", orchestrator_run_id: str = "",
    ) -> dict[str, Any]:
        pr = project_root()
        stage_id    = stage_id or (_PIPELINE_BY_WORKFLOW.get(workflow, {}).get("id") or workflow)
        template    = template or _default_todo_template_for_job(workflow, stage_id, ip)
        run_mode    = _normalize_run_mode(run_mode) or _current_run_mode()
        exec_mode   = _normalize_exec_mode(exec_mode) or _current_exec_mode()
        model       = str(model or "").strip() or _worker_model_for(workflow)
        reasoning_effort = _worker_reasoning_effort_for(workflow)
        toolchain   = _workflow_toolchain_for(workflow)
        session_name = normalize_session_name(session_name or (f"{ip}/{workflow}" if ip else workflow))
        if not session_name:
            raise ValueError("invalid session namespace")
        scope_path = str(_ip_dir_for(pr, ip).resolve()) if ip else str(pr)
        try:
            rel_scope = str(Path(scope_path).relative_to(pr))
        except Exception:
            rel_scope = ip or "."
        session_dir = pr / ".session" / session_name
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        worker_url = worker_override or _resolve_worker_url(workflow)
        boundary = (
            f"[ATLAS ARCHITECT WORKFLOW CONTEXT]\n"
            f"- ip: {ip or '(soc)'}\n"
            f"- workflow: {workflow}\n"
            f"- stage_id: {stage_id or workflow}\n"
            f"- pipeline_id: {pipeline_id or '(single-job)'}\n"
            f"- pipeline_run_id: {pipeline_id or '(single-job)'}\n"
            f"- session_namespace: .session/{session_name}\n"
            f"- project_root: {pr}\n"
            f"- source_root: {_SOURCE_ROOT}\n"
            f"- run_mode: {run_mode}\n"
            f"- exec_mode: {exec_mode}\n"
            f"- model: {model or '(default)'}\n"
            f"- reasoning_effort: {reasoning_effort or '(default)'}\n"
            f"- scope_path: {rel_scope}\n"
            f"- write_boundary: only modify files under {rel_scope}/, "
            f"except workflow-owned status/session files under .session/{session_name}/. "
            f"Do not edit other IP directories or unrelated workflows.\n"
            f"- parallelism: assume other IP/workflow jobs may be running; never revert or overwrite their files.\n\n"
        )
        job: dict[str, Any] = {
            "job_id":         uuid.uuid4().hex[:12],
            "run_id":         "",
            "worker":         worker_url,
            "workflow":       workflow,
            "stage_id":       stage_id,
            "template":       template,
            "ip":             ip,
            "model":          model,
            "reasoning_effort": reasoning_effort,
            "toolchain":      toolchain,
            "session":        session_name,
            "session_dir":    session_dir.relative_to(pr).as_posix(),
            "scope_path":     rel_scope,
            "project_root":    str(pr),
            "source_root":     str(_SOURCE_ROOT),
            "worker_command": _worker_launch_command(worker_url, workflow, session_name, pr, model, reasoning_effort),
            "prompt":         boundary + (prompt or _default_workflow_prompt(workflow, ip, stage_id)),
            "started_at":     time.time() if auto_start else 0.0,
            "status":         "pending" if auto_start else "queued",
            "iterations":     0,
            "files_modified": [],
            "result_summary": "",
            "error":          "",
            "pipeline_id":    pipeline_id,
            "pipeline_index": pipeline_index,
            "depends_on":     depends_on,
            "pipeline_schedule": pipeline_schedule,
            "rtl_version_id":  rtl_version_id,
            "run_mode":        run_mode,
            "exec_mode":       exec_mode,
            "_last_polled":   0.0,
            "pipeline_run_id": pipeline_id,
            "trigger_source":  trigger_source or ("pipeline_button" if pipeline_id else "job_dispatch"),
            "orchestrator_run_id": orchestrator_run_id,
            "user_id":         user_id,
            "db_user_id":      db_user_id,
            "db_session_id":   db_session_id,
            "workflow_run_id": "",
        }
        _record_job_db_start(job)
        with _jobs_lock:
            _jobs[job["job_id"]] = job
        if auto_start:
            _dispatch_job_to_worker(job)
        return job

    # ── /api/job/dispatch ──────────────────────────────────────────

    @app.post("/api/job/dispatch")
    async def api_job_dispatch(request: Request):
        """Dispatch a workflow onto an IP via an HTTP worker.

        Body: `{workflow: 'rtl-gen', ip: 'counter', prompt?: '...',
                model?: '...', session?: 'counter/rtl-gen',
                worker?: 'http://127.0.0.1:8001'}`

        Defaults the prompt to a workflow-specific template so the user
        can just click the block menu without typing.  Returns
        `{job_id, run_id, worker, status: 'queued'}` immediately; the
        frontend polls /api/jobs to track progress.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        workflow        = (body.get("workflow") or "").strip()
        ip              = (body.get("ip")       or "").strip()
        prompt          = (body.get("prompt")   or "").strip()
        model           = (body.get("model")    or "").strip()
        template        = (body.get("template") or "").strip()
        rtl_version_id  = (body.get("rtl_version_id") or "").strip()
        run_mode        = _normalize_run_mode(body.get("run_mode"))
        exec_mode       = _normalize_exec_mode(body.get("exec_mode"))
        stage_raw       = (body.get("stage_id") or body.get("stage") or "").strip()
        session_raw     = (body.get("session")  or "").strip()
        session_name    = normalize_session_name(session_raw or _default_job_session(request, ip, workflow))
        worker_override = (body.get("worker")   or "").strip()
        if not workflow:
            return JSONResponse({"error": "missing 'workflow'"}, status_code=400)
        if not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
            return JSONResponse({"error": f"invalid workflow {workflow!r}"}, status_code=400)
        if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
            return JSONResponse({"error": f"invalid template {template!r}"}, status_code=400)
        if stage_raw and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", stage_raw):
            return JSONResponse({"error": f"invalid stage_id {stage_raw!r}"}, status_code=400)
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
            return JSONResponse({"error": f"invalid model {model!r}"}, status_code=400)
        if rtl_version_id and not re.match(r"^[A-Za-z0-9_.:\-]+$", rtl_version_id):
            return JSONResponse({"error": f"invalid rtl_version_id {rtl_version_id!r}"}, status_code=400)
        if body.get("run_mode") is not None and not run_mode:
            return JSONResponse({"error": "run_mode must be starter, engineering, or signoff"}, status_code=400)
        if body.get("exec_mode") is not None and not exec_mode:
            return JSONResponse({"error": "exec_mode must be single-worker or orchestrator"}, status_code=400)
        if not session_name:
            return JSONResponse({"error": f"invalid session {session_raw!r}"}, status_code=400)
        if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
            return JSONResponse({"error": f"invalid worker {worker_override!r}"}, status_code=400)

        stage_id = stage_raw or (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
        _, _ = _refresh_tracked_jobs(project_root())
        request_user = _request_username(request)
        request_db_user = _request_db_user_id(request)
        conflicts = _active_job_conflicts(
            ip=ip,
            stage_ids=[stage_id],
            workflows=[workflow],
            user_id=request_user,
            db_user_id=request_db_user,
        )
        if conflicts:
            payload = _dedupe_payload(conflicts, ip=ip)
            first = conflicts[0]
            payload.update({
                "job_id": first.get("job_id", ""),
                "run_id": first.get("run_id", ""),
                "worker": first.get("worker", ""),
                "session": first.get("session", ""),
                "session_dir": first.get("session_dir", ""),
                "scope_path": first.get("scope_path", ""),
                "stage_id": first.get("stage_id", stage_id),
                "workflow": first.get("workflow", workflow),
                "model": first.get("model", ""),
                "reasoning_effort": first.get("reasoning_effort", ""),
                "toolchain": first.get("toolchain", ""),
                "run_mode": first.get("run_mode", run_mode or _current_run_mode()),
                "exec_mode": first.get("exec_mode", exec_mode or _current_exec_mode()),
                "user_id": first.get("user_id", request_user),
                "workflow_run_id": first.get("workflow_run_id", ""),
                "db_session_id": first.get("db_session_id", ""),
                "worker_command": first.get("worker_command", ""),
            })
            return JSONResponse(payload)
        job = _make_job_record(
            workflow=workflow, ip=ip, prompt=prompt, model=model,
            session_name=session_name, stage_id=stage_id,
            worker_override=worker_override, auto_start=True, template=template,
            rtl_version_id=rtl_version_id, run_mode=run_mode, exec_mode=exec_mode,
            user_id=request_user,
            db_user_id=request_db_user,
        )
        if job.get("status") == "error":
            return JSONResponse({"error": job.get("error"), "worker": job.get("worker")}, status_code=502)
        return JSONResponse({
            "ok":             True,
            "job_id":         job["job_id"],
            "run_id":         job["run_id"],
            "worker":         job["worker"],
            "session":        job["session"],
            "session_dir":    job["session_dir"],
            "scope_path":     job["scope_path"],
            "stage_id":       job["stage_id"],
            "model":          job["model"],
            "reasoning_effort": job.get("reasoning_effort", ""),
            "toolchain":      job.get("toolchain", ""),
            "run_mode":       job["run_mode"],
            "exec_mode":      job["exec_mode"],
            "user_id":        job["user_id"],
            "workflow_run_id": job.get("workflow_run_id", ""),
            "db_session_id":   job.get("db_session_id", ""),
            "worker_command": job["worker_command"],
            "status":         job["status"],
        })

    # ── /api/jobs/dispatch_many ────────────────────────────────────

    @app.post("/api/jobs/dispatch_many")
    async def api_jobs_dispatch_many(request: Request):
        """Dispatch multiple independent jobs in parallel.

        Body:
          `{jobs: [{workflow, ip, prompt?, model?, session?, worker?}, ...]}`

        This is the API shape the Architect/orchestrator should use for
        "run ssot/rtl on these IPs with different models" requests.  Each job
        still keeps its own `.session/<ip>/<workflow>` namespace and write
        boundary; the only shared object is this top-level tracker.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        items = body.get("jobs") if isinstance(body, dict) else None
        if not isinstance(items, list) or not items:
            return JSONResponse({"error": "expected non-empty jobs list"}, status_code=400)
        if len(items) > 32:
            return JSONResponse({"error": "too many jobs; max 32"}, status_code=400)

        created: list = []
        errors:  list = []
        _, _ = _refresh_tracked_jobs(project_root())
        request_user = _request_username(request)
        request_db_user = _request_db_user_id(request)
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({"index": idx, "error": "job must be an object"})
                continue
            workflow        = (item.get("workflow") or "").strip()
            ip              = (item.get("ip")       or "").strip()
            prompt          = (item.get("prompt")   or "").strip()
            model           = (item.get("model")    or "").strip()
            template        = (item.get("template") or "").strip()
            rtl_version_id  = (item.get("rtl_version_id") or "").strip()
            run_mode        = _normalize_run_mode(item.get("run_mode"))
            exec_mode       = _normalize_exec_mode(item.get("exec_mode"))
            stage_raw       = (item.get("stage_id") or item.get("stage") or "").strip()
            session_raw     = (item.get("session")  or "").strip()
            session_name    = normalize_session_name(session_raw or _default_job_session(request, ip, workflow))
            worker_override = (item.get("worker")   or "").strip()

            if not workflow or not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
                errors.append({"index": idx, "error": f"invalid workflow {workflow!r}"})
                continue
            if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
                errors.append({"index": idx, "error": f"invalid template {template!r}"})
                continue
            if stage_raw and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", stage_raw):
                errors.append({"index": idx, "error": f"invalid stage_id {stage_raw!r}"})
                continue
            if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
                errors.append({"index": idx, "error": f"invalid ip {ip!r}"})
                continue
            if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
                errors.append({"index": idx, "error": f"invalid model {model!r}"})
                continue
            if rtl_version_id and not re.match(r"^[A-Za-z0-9_.:\-]+$", rtl_version_id):
                errors.append({"index": idx, "error": f"invalid rtl_version_id {rtl_version_id!r}"})
                continue
            if item.get("run_mode") is not None and not run_mode:
                errors.append({"index": idx, "error": "run_mode must be starter, engineering, or signoff"})
                continue
            if item.get("exec_mode") is not None and not exec_mode:
                errors.append({"index": idx, "error": "exec_mode must be single-worker or orchestrator"})
                continue
            if session_raw and not session_name:
                errors.append({"index": idx, "error": f"invalid session {session_raw!r}"})
                continue
            if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
                errors.append({"index": idx, "error": f"invalid worker {worker_override!r}"})
                continue

            stage_id = stage_raw or (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
            conflicts = _active_job_conflicts(
                ip=ip,
                stage_ids=[stage_id],
                workflows=[workflow],
                user_id=request_user,
                db_user_id=request_db_user,
            )
            if conflicts:
                payload = _dedupe_payload(conflicts, ip=ip)
                payload["index"] = idx
                created.append(payload)
                continue
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=prompt, model=model,
                session_name=session_name, stage_id=stage_id,
                worker_override=worker_override, auto_start=True, template=template,
                rtl_version_id=rtl_version_id, run_mode=run_mode, exec_mode=exec_mode,
                user_id=request_user,
                db_user_id=request_db_user,
            )
            created.append(_public_job(job))

        status = 207 if errors else 200
        return JSONResponse(
            {"ok": not errors, "jobs": created, "errors": errors, "count": len(created)},
            status_code=status,
        )

    # ── /api/pipeline/stages ───────────────────────────────────────

    @app.get("/api/pipeline/stages")
    async def api_pipeline_stages():
        return JSONResponse({"stages": _PIPELINE_STAGES})

    @app.get("/api/pipeline/progress-debug")
    async def api_pipeline_progress_debug(ip: str = ""):
        ip = ip.strip()
        if not ip or len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": "invalid or missing ip"}, status_code=400)
        pr = project_root()
        try:
            from src.progress_debug import summarize_headless_progress
        except ModuleNotFoundError:
            from progress_debug import summarize_headless_progress
        with _jobs_lock:
            ip_jobs = [dict(j) for j in _jobs.values() if j.get("ip") == ip]
        headless_debug = summarize_headless_progress(pr, ip)
        worker_debug = _summarize_worker_progress(ip_jobs)
        return JSONResponse(_combine_progress_debug(headless_debug, worker_debug))

    # ── /api/pipeline/state ────────────────────────────────────────

    # 2-second response micro-cache keyed by (ip). The frontend polls
    # this endpoint every 2 s per open tab; without a cache, N tabs ×
    # 30 polls/min would each do a workspace upsert + ip_block upsert +
    # DB query + 15 FS stat checks. With the cache, only the first call
    # in a 2 s window does the work; the others reuse the JSON.
    _state_cache: dict[str, tuple[float, Any]] = {}
    _STATE_CACHE_TTL = 2.0

    @app.get("/api/pipeline/state")
    async def api_pipeline_state(request: Request, ip: str = ""):
        ip = ip.strip()
        # Strict length cap so a 500-char ip can't cascade into raw
        # OSError [Errno 63: file name too long] at downstream stat() calls.
        # Surfaced by deep^6 round T44.
        if not ip or len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": "invalid or missing ip"}, status_code=400)

        # Multi-user isolation: derive the scope from the authenticated user
        # so user_a polling the same IP cannot see user_b's handoffs. The
        # state cache key is also (ip, user_id) so cached payloads don't
        # leak across users either. Surfaced by deep^6 round T41.
        scoped_user = request.scope.get("user") or {}
        user_id = str(scoped_user.get("username") or scoped_user.get("id") or "")
        db_user_id = _request_db_user_id(request) or user_id
        if not _assert_ip_access(db_user_id, ip):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        scope_filter = {"user_id": user_id} if user_id else None
        cache_key = (ip, user_id)

        pr = project_root()
        _, jobs_changed = _refresh_tracked_jobs(pr)
        if jobs_changed:
            for k in list(_state_cache.keys()):
                if isinstance(k, tuple) and k[0] == ip:
                    _state_cache.pop(k, None)

        import time as _t
        cached = _state_cache.get(cache_key)
        if cached and (_t.monotonic() - cached[0]) < _STATE_CACHE_TTL:
            return JSONResponse(cached[1])

        ip_dir = _ip_dir_for(pr, ip)
        run_mode = _current_run_mode()
        exec_mode = _current_exec_mode()
        provenance_summary = _provenance_summary(ip_dir, run_mode)

        try:
            from src.workflow_stage_surface import compute_kpi_dots, compute_kpi_dots_labeled
        except ModuleNotFoundError:
            from workflow_stage_surface import compute_kpi_dots, compute_kpi_dots_labeled
        try:
            from src.progress_debug import summarize_headless_progress
        except ModuleNotFoundError:
            from progress_debug import summarize_headless_progress
        progress_debug = summarize_headless_progress(pr, ip)

        # latest rtl_version_id + DB-first state snapshot from workflow_runs.
        # DB is the source of truth for state (idle/running/passed/failed);
        # filesystem is consulted only as a fallback for hand-placed artifacts.
        rtl_version_id: str | None = None
        db_state_by_workflow: dict[str, dict[str, Any]] = {}
        try:
            import os as _os
            db_path = _os.environ.get("ATLAS_DB_PATH") or str(Path.home() / ".common_ai_agent" / "atlas.db")
            from core.atlas_db import AtlasDB
            with AtlasDB(db_path) as _db:
                versions = _db.list_rtl_versions()
                # workspace + ip_block lookup (creates rows if missing — same
                # pattern as register_rtl_version in this file)
                try:
                    workspace_candidates: list[dict[str, Any]] = []
                    if db_user_id:
                        workspace_candidates.append(_db.upsert_workspace(
                            pr.name or "default",
                            owner_user_id=db_user_id,
                            local_path=str(pr),
                        ))
                    legacy_ws = _db.upsert_workspace(
                        pr.name or "default",
                        owner_user_id="",
                        local_path=str(pr),
                    )
                    if not workspace_candidates or legacy_ws["id"] != workspace_candidates[0]["id"]:
                        workspace_candidates.append(legacy_ws)
                    for _ws in workspace_candidates:
                        _ipb = _db.upsert_ip_block(_ws["id"], ip)
                        _runs = _db._fetchall(
                            """
                            SELECT workflow, status, error_summary, started_at, ended_at,
                                   trigger_source, orchestrator_run_id
                            FROM workflow_runs
                            WHERE workspace_id = ? AND ip_id = ?
                            ORDER BY started_at DESC
                            """,
                            (_ws["id"], _ipb["id"]),
                        )
                        # First (latest) row per workflow wins. User-scoped
                        # workspace rows are considered before legacy
                        # ownerless rows for backward compatibility.
                        for _r in _runs:
                            wf = _r["workflow"]
                            if wf not in db_state_by_workflow:
                                db_state_by_workflow[wf] = dict(_r)
                except Exception:
                    pass
            ip_versions = [v for v in versions if v.get("ip") == ip or v.get("ip_id")]
            if ip_versions:
                rtl_version_id = ip_versions[-1].get("version") or ip_versions[-1].get("id")
        except Exception:
            pass

        def _state_from_db(workflow_name: str) -> tuple[str | None, str | None]:
            """Return (state, error_summary) from the latest workflow_runs
            row for this IP+workflow, or (None, None) when no row exists."""
            row = db_state_by_workflow.get(workflow_name)
            if not row:
                return (None, None)
            st = (row.get("status") or "").lower()
            if st == "running":
                return ("running", None)
            if st in ("completed", "success", "ok"):
                return ("passed", None)
            if st in ("error", "failed", "blocked", "cancelled"):
                return ("failed", row.get("error_summary"))
            return (None, None)

        # snapshot of running jobs for this ip
        with _jobs_lock:
            ip_jobs = [dict(j) for j in _jobs.values() if j.get("ip") == ip]
        progress_debug = _combine_progress_debug(
            progress_debug,
            _summarize_worker_progress(ip_jobs),
        )

        def _running_job_for(stage_id: str) -> dict[str, Any] | None:
            for j in ip_jobs:
                if j.get("stage_id") == stage_id and j.get("status") in {"running", "pending"}:
                    return j
            return None

        def _latest_completed_job(stage_id: str) -> dict[str, Any] | None:
            matches = [j for j in ip_jobs if j.get("stage_id") == stage_id
                       and j.get("status") in {"completed", "error", "cancelled"}]
            if not matches:
                return None
            return max(matches, key=lambda j: j.get("started_at", 0))

        # blame: read mismatch_classification for sim failures
        blame_workflow: str | None = None
        _blame_path = ip_dir / "sim" / "mismatch_classification.json"
        if _blame_path.is_file():
            try:
                _blame_doc = json.loads(_blame_path.read_text(encoding="utf-8"))
                blame_workflow = _blame_doc.get("owner_workflow") or None
            except Exception:
                pass

        # rtl blocked flag
        _rtl_blocked = False
        _rtl_blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
        if _rtl_blocked_path.is_file():
            try:
                _rtl_blocked_doc = json.loads(_rtl_blocked_path.read_text(encoding="utf-8"))
                _rtl_blocked = bool(_rtl_blocked_doc)
            except Exception:
                pass

        _GLYPHS: dict[str, str] = {
            "idle": "◯", "ready": "◯", "running": "▶", "passed": "✓",
            "failed": "!", "blocked": "⏸", "stale": "⊘", "locked": "⊘",
        }

        def _stage_top_secondary(stage_id: str, ip_dir: Path, ip: str) -> tuple[str, str]:
            if stage_id in ("rtl", "rtl-gen"):
                try:
                    from src.workflow_stage_surface import _rtl_authoring_summary
                except ModuleNotFoundError:
                    from workflow_stage_surface import _rtl_authoring_summary
                summary = _rtl_authoring_summary(pr, ip)
                return (f"rtl/{ip}.sv (authoring)", summary or "")
            if stage_id == "ssot":
                ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
                if ssot_path.is_file():
                    size_kb = ssot_path.stat().st_size // 1024
                    lines = ssot_path.read_text(encoding="utf-8").splitlines()
                    sections = sum(1 for ln in lines if ln.startswith("  - name:") or ln.startswith("- name:"))
                    tbds = sum(1 for ln in lines if "TBD" in ln)
                    return (f"yaml/{ip}.ssot.yaml · {size_kb} KB · {sections} sect",
                            f"{tbds} TBD")
            if stage_id == "lint":
                try:
                    doc = json.loads((ip_dir / "lint" / "dut_lint.json").read_text(encoding="utf-8"))
                    errs = doc.get("errors", doc.get("error_count", "?"))
                    warns = doc.get("warnings", doc.get("warning_count", "?"))
                    return (f"errors={errs} warnings={warns}", "")
                except Exception:
                    pass
            if stage_id == "sim":
                results_xml = ip_dir / "sim" / "results.xml"
                if not results_xml.is_file():
                    results_xml = ip_dir / "tb" / "cocotb" / "results.xml"
                if results_xml.is_file():
                    try:
                        tests, failures, errors = _junit_counts(results_xml)
                        failures += errors
                        return (f"{tests} tests · {failures} failures", "")
                    except Exception:
                        pass
            if stage_id == "coverage":
                try:
                    doc = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
                    bins_hit = doc.get("bins_hit", "?")
                    bins_total = doc.get("bins_total", doc.get("total_bins", "?"))
                    return (f"bins {bins_hit}/{bins_total}", "")
                except Exception:
                    pass
            if stage_id == "syn":
                try:
                    doc = json.loads((ip_dir / "syn" / "out" / "area.json").read_text(encoding="utf-8"))
                    cells = doc.get("total_cells", "?")
                    area = doc.get("total_area_um2", "?")
                    return (f"cells={cells}", f"area={area} um2")
                except Exception:
                    pass
            if stage_id == "pnr":
                top, secondary = _pnr_artifact_summary(ip_dir)
                if top or secondary:
                    return top, secondary
            if stage_id in ("sta", "sta-post"):
                top, secondary = _timing_artifact_summary(ip_dir, stage_id)
                if top or secondary:
                    return top, secondary
            return ("", "")

        def _stage_history(stage_id: str) -> list[dict[str, Any]]:
            matches = [j for j in ip_jobs if j.get("stage_id") == stage_id]
            history = []
            for j in sorted(matches, key=lambda x: x.get("started_at", 0), reverse=True)[:3]:
                duration = None
                if j.get("finished_at") and j.get("started_at"):
                    duration = round(j["finished_at"] - j["started_at"])
                history.append({
                    "run_id": j.get("run_id") or j.get("job_id"),
                    "state": j.get("status"),
                    "duration_s": duration,
                    "model": j.get("model"),
                    "cost": j.get("cost"),
                })
            return history

        # determine which stages have passing artifacts (filesystem truth)
        passed_stages: set[str] = set()
        failed_stages: dict[str, str] = {}
        for stage in _PIPELINE_STAGES:
            sid = stage["id"]
            fake_job = {"ip": ip, "stage_id": sid, "workflow": stage["workflow"]}
            failed, failure_reason = _job_artifact_failure(fake_job, pr)
            ok, _ = _job_artifact_recovery(fake_job, pr)
            if failed:
                failed_stages[sid] = failure_reason
            elif ok:
                passed_stages.add(sid)

        # Compute the orchestrator block once up front so each stage card can
        # carry its own per-workflow handoff summary (avoids a second loop
        # and lets the frontend StageCard render [take] / [save handoff] /
        # pending-count without threading the whole pipeline state down).
        orchestrator_block, handoffs_by_workflow = _orchestrator_block(
            ip_dir, scope_filter=scope_filter,
        )

        stages_out: dict[str, Any] = {}
        for stage in _PIPELINE_STAGES:
            sid = stage["id"]
            running_job = _running_job_for(sid)
            last_job = _latest_completed_job(sid)

            # determine state — DB-first, FS-fallback
            state: str
            db_state, db_error = _state_from_db(stage["workflow"])
            source = "none"
            if running_job:
                state = "running"
                source = "db" if db_state is not None else "memory"
            elif sid in failed_stages:
                state = "failed"  # explicit artifact failure overrides stale/optimistic DB success
                source = "fs"
            elif db_state == "failed" and sid in passed_stages:
                state = "passed"
                source = "fs"
            elif db_state is not None:
                state = db_state  # DB is source of truth for completed runs
                source = "db"
            elif sid in passed_stages:
                state = "passed"  # FS evidence without a DB row (hand-placed)
                source = "fs"
            elif sid == "rtl" and _rtl_blocked:
                state = "blocked"
                source = "fs"
            else:
                # check if all deps are passed (ready) or any dep missing (locked)
                deps = _PIPELINE_STAGE_DEPS.get(sid, ())
                if not deps:
                    state = "idle"
                elif all(dep in passed_stages for dep in deps):
                    state = "ready"
                else:
                    state = "locked"

            # locked-reason: name the missing upstream so the card can say
            # "(needs ssot)" instead of just "LOCKED".
            locked_reason: str | None = None
            if state == "locked":
                deps = _PIPELINE_STAGE_DEPS.get(sid, ())
                missing = [d for d in deps if d not in passed_stages]
                if missing:
                    locked_reason = "needs " + " + ".join(missing)

            # running iter info
            iter_str: str | None = None
            progress: float | None = None
            live_tail: str | None = None
            abortable = False
            if running_job:
                iters = running_job.get("iterations", 0)
                iter_str = str(iters) if iters else None
                abortable = True
                live_tail = (running_job.get("result_summary") or "")[-120:] or None

            # evidence paths
            evidence_paths: list[str] = []
            _evidence_map: dict[str, list[str]] = {
                "ssot": [f"yaml/{ip}.ssot.yaml"],
                "fl-model": ["model/fl_model_check.json", "cov/fcov_plan.json"],
                "cl-model": ["model/cl_model_check.json"],
                "equivalence": ["verify/equivalence_goals.json"],
                "rtl": ["rtl/rtl_compile.json", "lint/dut_lint.json",
                        "rtl/rtl_contract.json", "rtl/rtl_todo_plan.json", "rtl/rtl_authoring_provenance.json"],
                "lint": ["lint/dut_lint.json"],
                "tb": ["tb/cocotb/"],
                "sim": ["sim/results.xml", "sim/fl_rtl_compare.json"],
                "coverage": ["cov/coverage.json"],
                "sim-debug": ["sim/mismatch_classification.json"],
                "goal-audit": ["sim/fl_rtl_goal_audit.json"],
                "syn": ["syn/out/"],
                "sta": ["sta/out/"],
                "pnr": ["pnr/out/"],
                "sta-post": ["sta-post/out/"],
            }
            for rel in _evidence_map.get(sid, []):
                if (ip_dir / rel).exists():
                    evidence_paths.append(f"{ip}/{rel}")

            scoresheet = compute_kpi_dots_labeled(ip, sid, root=pr)
            top, secondary = _stage_top_secondary(sid, ip_dir, ip)

            stage_blame: str | None = None
            if state == "failed" and sid == "sim" and blame_workflow:
                stage_blame = blame_workflow

            model = (running_job or last_job or {}).get("model") or None
            toolchain = (running_job or last_job or {}).get("toolchain") or _workflow_toolchain_for(stage["workflow"]) or None
            effort = (running_job or last_job or {}).get("effort") or None

            stage_workflow = stage["workflow"]
            stage_handoffs = handoffs_by_workflow.get(
                stage_workflow,
                {"pending": 0, "claimed": 0, "done": 0, "review": 0, "latest": None},
            )
            db_row = db_state_by_workflow.get(stage_workflow) or {}
            stages_out[sid] = {
                "state": state,
                "glyph": _GLYPHS.get(state, "◯"),
                "scoresheet": scoresheet,
                "iter": iter_str,
                "progress": progress,
                "live_tail": live_tail,
                "top": top,
                "secondary": secondary,
                "evidence_paths": evidence_paths,
                "abortable": abortable,
                "model": model,
                "toolchain": toolchain,
                "effort": effort,
                "history": _stage_history(sid),
                "blame": stage_blame,
                "locked_reason": locked_reason,
                "error_summary": db_error if state == "failed" and db_error else failed_stages.get(sid),
                "source": source,
                "workflow": stage_workflow,
                "handoffs": stage_handoffs,
                # Phase 3 provenance — read by frontend StageCard `pipe-stage-orch-pill`
                # (renders when trigger_source === 'orchestrator_chat') and any future
                # cross-link from stage card to its orchestrator run detail.
                "trigger_source": db_row.get("trigger_source") or None,
                "orchestrator_run_id": db_row.get("orchestrator_run_id") or None,
            }

        payload = {
            "ip": ip,
            "rtl_version_id": rtl_version_id,
            "mode": "pipeline",
            "run_mode": run_mode,
            "exec_mode": exec_mode,
            "policy": {
                "run_mode": run_mode,
                "exec_mode": exec_mode,
                "provenance_summary": provenance_summary,
            },
            "provenance_summary": provenance_summary,
            "stages": stages_out,
            "progress_debug": progress_debug,
        }
        payload["orchestrator"] = orchestrator_block
        payload["handoffs_by_workflow"] = handoffs_by_workflow
        _state_cache[cache_key] = (_t.monotonic(), payload)
        return JSONResponse(payload)

    # ── /api/pipeline/dispatch ─────────────────────────────────────

    def _create_pipeline_db_session_for_request(
        request: Request,
        *,
        ip: str,
        pipeline_id: str,
        run_mode: str,
        exec_mode: str,
        selected_stage_ids: list[str],
        prompt: str = "",
    ) -> str:
        db_user_id = _request_db_user_id(request)
        if not db_user_id:
            return ""
        pr = project_root()
        try:
            from core.atlas_db import AtlasDB

            with AtlasDB(_atlas_job_db_path(pr)) as db:
                created = db.create_session(
                    db_user_id,
                    f"{ip or 'soc'} pipeline {pipeline_id}",
                    ip,
                )
                db.update_session(
                    created["id"],
                    summary={
                        "ip": ip,
                        "workflow": "pipeline",
                        "pipeline_run_id": pipeline_id,
                        "pipeline_id": pipeline_id,
                        "run_mode": run_mode,
                        "exec_mode": exec_mode,
                        "stages": selected_stage_ids,
                        "prompt": prompt[:400],
                        "project_root": str(pr),
                    },
                )
                return str(created["id"] or "")
        except Exception:
            return ""

    def _orchestrator_db_session_for_request(
        db: Any,
        request: Request,
        *,
        body: dict[str, Any],
        db_user_id: str,
        workspace_id: str,
        ip_id: str,
        ip: str,
        project_root: Path,
    ) -> str:
        owner = _request_username(request)
        raw_session = normalize_session_name(str(
            body.get("session")
            or body.get("namespace")
            or body.get("active_session")
            or body.get("session_id")
            or ""
        ))
        session_row = db.get_session_for_user(db_user_id, raw_session) if raw_session else None
        session_id = str((session_row or {}).get("id") or "")
        if not session_id:
            owner_tokens = {owner, db_user_id, "default", "local-admin", ""}
            if raw_session and ("/" in raw_session or raw_session not in owner_tokens):
                session_id = raw_session
            else:
                session_id = _default_job_session(request, ip, "orchestrator")
        session = db.upsert_runtime_session(
            session_id,
            db_user_id,
            owner=owner or db_user_id,
            workspace_id=workspace_id,
            ip_id=ip_id,
            ip=ip,
            workflow="orchestrator",
            project_id=ip,
            directory=str(project_root),
            title=f"{ip} orchestrator",
            status="active",
            summary={
                "ip": ip,
                "workflow": "orchestrator",
                "exec_mode": "orchestrator",
                "source": "pipeline_orchestrator_chat",
                "project_root": str(project_root),
            },
        )
        return str(session.get("id") or session_id)

    @app.post("/api/pipeline/dispatch")
    async def api_pipeline_dispatch(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        ip         = (body.get("ip")     or "").strip()
        model      = (body.get("model")  or "").strip()
        rtl_version_id = (body.get("rtl_version_id") or "").strip()
        user_prompt = (body.get("prompt") or "").strip()
        # Direct-dispatch path (UI button, WS pipeline dispatch) was missing the
        # seed propagation that the orchestrator-chat path got in f17e66c41. The
        # caller may send the user's concrete requirement either as the
        # dedicated ``user_seed`` field or — for legacy callers that only have
        # ``prompt`` — as ``prompt``. Either way the worker must see it under
        # ``[USER REQUIREMENT]`` so e.g. ssot-gen actually builds the FIFO the
        # user asked for instead of a default CMUX.
        user_seed_text = (body.get("user_seed") or user_prompt or "").strip()
        requested_schedule = (body.get("schedule") or "auto").strip().lower()
        run_mode = _normalize_run_mode(body.get("run_mode")) or _current_run_mode()
        exec_mode = _normalize_exec_mode(body.get("exec_mode")) or _current_exec_mode()
        if ip and (len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip)):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        if requested_schedule not in {"auto", "dag", "serial"}:
            return JSONResponse({"error": "schedule must be 'auto', 'dag', or 'serial'"}, status_code=400)
        if rtl_version_id and not re.match(r"^[A-Za-z0-9_.:\-]+$", rtl_version_id):
            return JSONResponse({"error": f"invalid rtl_version_id {rtl_version_id!r}"}, status_code=400)
        if body.get("run_mode") is not None and not _normalize_run_mode(body.get("run_mode")):
            return JSONResponse({"error": "run_mode must be starter, engineering, or signoff"}, status_code=400)
        if body.get("exec_mode") is not None and not _normalize_exec_mode(body.get("exec_mode")):
            return JSONResponse({"error": "exec_mode must be single-worker or orchestrator"}, status_code=400)
        if len(user_prompt) > 100_000:
            return JSONResponse({"error": "prompt too large (max 100 000 chars)"}, status_code=400)
        requested = body.get("stages") or [s["id"] for s in _PIPELINE_STAGES]
        if not isinstance(requested, list) or not requested:
            return JSONResponse({"error": "stages must be a non-empty list"}, status_code=400)
        resolved = []
        for item in requested:
            key   = str(item).strip()
            stage = _resolve_pipeline_stage(key)
            if not stage:
                return JSONResponse({"error": f"unknown pipeline stage {key!r}"}, status_code=400)
            if not any(s["id"] == stage["id"] for s in resolved):
                resolved.append(stage)
        schedule = "serial" if requested_schedule == "auto" and exec_mode == "single-worker" else _resolve_pipeline_schedule(requested_schedule, resolved)
        resolved = _ordered_pipeline_stages(resolved)
        owner_user_id    = _request_username(request)
        selected_stage_ids = [stage["id"] for stage in resolved]
        db_user_id = _request_db_user_id(request)
        if ip and not _assert_ip_access(db_user_id, ip):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        _, _ = _refresh_tracked_jobs(project_root())
        conflicts = _active_job_conflicts(
            ip=ip,
            stage_ids=selected_stage_ids,
            workflows=[stage["workflow"] for stage in resolved],
            user_id=owner_user_id,
            db_user_id=db_user_id,
        )
        if conflicts:
            payload = _dedupe_payload(conflicts, ip=ip)
            payload.update({
                "schedule": schedule,
                "requested_schedule": requested_schedule,
                "run_mode": run_mode,
                "exec_mode": exec_mode,
                "user_id": owner_user_id,
                "stages": resolved,
            })
            return JSONResponse(payload)

        pipeline_id      = uuid.uuid4().hex[:12]
        jobs: list       = []
        stage_job_ids: dict[str, str] = {}
        db_session_id = _create_pipeline_db_session_for_request(
            request,
            ip=ip,
            pipeline_id=pipeline_id,
            run_mode=run_mode,
            exec_mode=exec_mode,
            selected_stage_ids=selected_stage_ids,
            prompt=user_prompt,
        )
        for idx, stage in enumerate(resolved):
            workflow     = stage["workflow"]
            stage_prompt = _default_workflow_prompt(workflow, ip, stage["id"])
            stage_prompt += (
                "\n\n[ATLAS RUN POLICY]\n"
                f"- run_mode: {run_mode}\n"
                f"- exec_mode: {exec_mode}\n"
            )
            if user_prompt and user_prompt != user_seed_text:
                stage_prompt += f"\n\n[User pipeline goal]\n{user_prompt}"
            # Same propagation pattern as ``_dispatch_workflow_tool_bridge``:
            # workers parse [USER REQUIREMENT] as the authoritative seed, so
            # always emit this section when a seed is present.
            if user_seed_text:
                stage_prompt += f"\n\n[USER REQUIREMENT]\n{user_seed_text}"
            session = f"{_pipeline_session_prefix(request, ip, pipeline_id)}/{idx + 1:02d}-{workflow}"
            dep_stage_ids = _pipeline_stage_dependencies(
                stage["id"], selected_stage_ids, schedule=schedule,
            )
            dep_job_ids = [stage_job_ids[dep] for dep in dep_stage_ids if dep in stage_job_ids]
            depends_on: str | list[str]
            depends_on = dep_job_ids[0] if schedule == "serial" and dep_job_ids else dep_job_ids
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=stage_prompt, model=model,
                session_name=session, stage_id=stage["id"], pipeline_id=pipeline_id,
                pipeline_index=idx, depends_on=depends_on,
                auto_start=(not dep_job_ids), pipeline_schedule=schedule,
                rtl_version_id=rtl_version_id if stage["id"] in _RTL_VERSION_DOWNSTREAM_STAGES else "",
                run_mode=run_mode, exec_mode=exec_mode,
                user_id=owner_user_id,
                db_user_id=db_user_id,
                db_session_id=db_session_id,
            )
            stage_job_ids[stage["id"]] = job["job_id"]
            jobs.append(_public_job(job))
        return JSONResponse({
            "ok":         True,
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_id,
            "user_id":     owner_user_id,
            "schedule":    schedule,
            "requested_schedule": requested_schedule,
            "run_mode":    run_mode,
            "exec_mode":   exec_mode,
            "ip":          ip,
            "stages":      resolved,
            "jobs":        jobs,
        })

    def _extract_ip_from_orchestrator_message(message: str, fallback: str = "") -> str:
        # Prefer an IP token spelled out in the message body over the dropdown
        # fallback. Patterns: `for ip <ip>`, `for <ip>`, `ip=<ip>`, `on <ip>`.
        # The handler downstream still validates the result against
        # `^[A-Za-z][A-Za-z0-9_]*$`, so only tokens shaped that way are
        # accepted here — otherwise we fall back to the dropdown ip.
        candidate = ""
        msg = str(message or "")
        token_re = r"([A-Za-z][A-Za-z0-9_]*)"
        patterns = (
            rf"\bfor\s+ip\s+{token_re}\b",
            rf"\bip\s*=\s*{token_re}\b",
            rf"\bfor\s+{token_re}\b",
            rf"\bon\s+{token_re}\b",
        )
        for pat in patterns:
            m = re.search(pat, msg)
            if m:
                candidate = m.group(1).strip()
                break
        if not candidate:
            candidate = str(fallback or "").strip()
        # `default` is the placeholder IP that the IP dropdown shows when
        # nothing real is selected. The orchestrator's job is to progress
        # a *specific* IP's pipeline; with the placeholder, every tool
        # call's `ip` argument would be meaningless and the loop ends
        # silently after one no-op iteration. Surfacing this as an
        # empty result lets the handler return a clear 400 instead.
        if candidate.lower() == "default":
            return ""
        return candidate

    def _record_orchestrator_chat(
        request: Request,
        *,
        ip: str,
        message: str,
        reply: str = "",
        pipeline_id: str = "",
    ) -> None:
        try:
            from core.atlas_db import AtlasDB

            pr = project_root()
            user = request.scope.get("user") or {}
            _raw_user_id = _request_db_user_id(request) or str(user.get("username") or "local-admin")
            with AtlasDB(_atlas_job_db_path(pr)) as db:
                db_user_id = _canonical_user_id(db, _raw_user_id)
                workspace = db.upsert_workspace(
                    pr.name or "default",
                    owner_user_id=db_user_id,
                    local_path=str(pr),
                )
                ip_row = db.upsert_ip_block(
                    workspace["id"],
                    ip or "soc",
                    ssot_path=f"{ip}/yaml/{ip}.ssot.yaml" if ip else "",
                )
                if message:
                    db.record_chat_message(
                        ip_row["id"],
                        db_user_id,
                        message,
                        display_name=str(user.get("username") or ""),
                        workspace_id=workspace["id"],
                    )
                if reply:
                    db.record_trace_event(
                        event_type="chat_response",
                        payload={"content": reply, "pipeline_run_id": pipeline_id},
                        workspace_id=workspace["id"],
                        ip_id=ip_row["id"],
                        workflow="orchestrator",
                        actor_user_id=db_user_id,
                    )
        except Exception:
            return

    @app.post("/api/pipeline/orchestrator/chat")
    async def api_pipeline_orchestrator_chat(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)

        message = str(body.get("message") or body.get("text") or "").strip()
        if not message:
            return JSONResponse({"error": "message required"}, status_code=400)
        ip = _extract_ip_from_orchestrator_message(message, str(body.get("ip") or ""))
        if not ip or len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": "valid ip required"}, status_code=400)

        # Persist user chat first so the trace ledger has the message regardless
        # of what the loop does.
        _record_orchestrator_chat(request, ip=ip, message=message)

        from core.atlas_db import AtlasDB
        from src.orchestrator.runner import get_runner

        pr = project_root()
        user = request.scope.get("user") or {}
        _raw_user_id = _request_db_user_id(request) or str(user.get("username") or "local-admin")
        with AtlasDB(_atlas_job_db_path(pr)) as db:
            db_user_id = _canonical_user_id(db, _raw_user_id)
            workspace = db.upsert_workspace(
                pr.name or "default",
                owner_user_id=db_user_id,
                local_path=str(pr),
            )
            ip_row = db.upsert_ip_block(
                workspace["id"], ip, ssot_path=f"{ip}/yaml/{ip}.ssot.yaml"
            )
            try:
                db_session_id = _orchestrator_db_session_for_request(
                    db,
                    request,
                    body=body,
                    db_user_id=db_user_id,
                    workspace_id=str(workspace["id"] or ""),
                    ip_id=str(ip_row["id"] or ""),
                    ip=ip,
                    project_root=pr,
                )
            except ValueError as exc:
                return JSONResponse({"error": str(exc)}, status_code=403)

        runner = get_runner(_atlas_job_db_path(pr))
        outcome = runner.submit_or_attach(
            user_id=db_user_id,
            ip_id=ip_row["id"],
            ip_name=ip,
            workspace_id=str(workspace["id"] or ""),
            session_id=db_session_id,
            chat_message_id=str(body.get("chat_message_id") or ""),
            message_text=message,
            model=ORCHESTRATOR_MODEL,
            reasoning_effort=ORCHESTRATOR_REASONING_EFFORT,
        )
        return JSONResponse({
            "ok": True,
            "ip": ip,
            "run_id": outcome.run_id,
            "status": outcome.status,
            "model": ORCHESTRATOR_MODEL,
            "reasoning_effort": ORCHESTRATOR_REASONING_EFFORT,
        })

    @app.get("/api/orchestrator/runs/{run_id}")
    async def api_orchestrator_run_detail(run_id: str):
        from core.atlas_db import AtlasDB

        pr = project_root()
        with AtlasDB(_atlas_job_db_path(pr)) as db:
            run = db.get_orchestrator_run(run_id)
            if run is None:
                return JSONResponse({"error": f"unknown run {run_id!r}"}, status_code=404)
            steps = db.list_orchestrator_steps(run_id)
        return JSONResponse({"ok": True, "run": run, "steps": steps})

    @app.get("/api/orchestrator/active_run")
    async def api_orchestrator_active_run(request: Request):
        """Active orchestrator_run + latest step for the (calling user, ip).

        Powers the "Human decision waiting" banner: when ``latest_step.verdict``
        is ``awaiting_user``, the UI renders the question.
        """
        params = dict(request.query_params)
        ip = (params.get("ip") or "").strip()
        if not ip:
            return JSONResponse({"error": "ip query param required"}, status_code=400)
        from core.atlas_db import AtlasDB

        pr = project_root()
        user = request.scope.get("user") or {}
        _raw_user_id = _request_db_user_id(request) or str(user.get("username") or "local-admin")
        with AtlasDB(_atlas_job_db_path(pr)) as db:
            db_user_id = _canonical_user_id(db, _raw_user_id)
            workspace = db.upsert_workspace(
                pr.name or "default",
                owner_user_id=db_user_id,
                local_path=str(pr),
            )
            ip_row = db.upsert_ip_block(workspace["id"], ip)
            run = db.find_active_run_for(user_id=db_user_id, ip_id=ip_row["id"])
            latest_step = db.latest_orchestrator_step(run["id"]) if run else None
        return JSONResponse({
            "ok": True,
            "ip": ip,
            "run": run,
            "latest_step": latest_step,
        })

    def _dispatch_workflow_tool_bridge(
        *,
        workflow: str = "",
        scope: str = "",
        prompt: str = "",
        ip: str = "",
        stages: Any = None,
        payload: Any = None,
        schedule: str = "auto",
        model: str = "",
        run_mode: str = "",
        exec_mode: str = "",
        reason: str = "",
    ) -> dict[str, Any]:
        """Bridge the orchestrator LLM tool to the pipeline job creator.

        This is the non-HTTP twin of /api/pipeline/dispatch. It runs inside
        the Atlas UI process, so it can use the live job registry without a
        browser cookie while still keeping the same session/pipeline identity.
        """
        body = payload if isinstance(payload, dict) else {}
        ip_name = (
            str(ip or body.get("ip") or "").strip()
            or os.environ.get("ATLAS_ACTIVE_IP", "").strip()
        )
        if not ip_name and scope:
            ip_name = Path(str(scope).rstrip("/")).name
        if ip_name and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip_name):
            return {"ok": False, "error": f"invalid ip {ip_name!r}"}

        requested: Any = stages or body.get("stages")
        wf = str(workflow or body.get("workflow") or "").strip()
        if not requested:
            if wf.lower() in {"pipeline", "full", "full-ip", "run-to-green", "run_to_green", "all"}:
                requested = [s["id"] for s in _PIPELINE_STAGES]
            elif wf:
                requested = [wf]
        if isinstance(requested, str):
            requested = [x.strip() for x in re.split(r"[,\s]+", requested) if x.strip()]
        if not isinstance(requested, list) or not requested:
            return {"ok": False, "error": "workflow or stages is required"}

        req_schedule = str(schedule or body.get("schedule") or "auto").strip().lower()
        if req_schedule not in {"auto", "dag", "serial"}:
            return {"ok": False, "error": "schedule must be 'auto', 'dag', or 'serial'"}
        run_mode_resolved = _normalize_run_mode(run_mode or body.get("run_mode")) or _current_run_mode()
        exec_mode_resolved = _normalize_exec_mode(exec_mode or body.get("exec_mode")) or _current_exec_mode()
        model_resolved = str(model or body.get("model") or "").strip()
        prompt_text = str(
            prompt
            or body.get("prompt")
            or body.get("user_goal")
            or body.get("goal")
            or body.get("requirement")
            or ""
        ).strip()
        reason_text = str(reason or body.get("reason") or "").strip()
        # Phase 1: dispatch_workflow tool injects trigger_source + orchestrator_run_id
        # into payload; lift them out so _make_job_record can persist them on
        # the workflow_runs row. Default to "orchestrator_chat" when this
        # bridge runs (it only fires from inside the orchestrator loop).
        trigger_source_resolved = str(
            body.get("trigger_source") or "orchestrator_chat"
        ).strip()
        orchestrator_run_id_resolved = str(body.get("orchestrator_run_id") or "").strip()
        # Chat seed = latest user message from the orchestrator chat. Plumbed
        # through payload.user_seed by react_bridge so workers always see the
        # user's concrete requirement, even when the LLM omits ``prompt``.
        user_seed_text = str(body.get("user_seed") or "").strip()

        resolved = []
        for item in requested:
            key = str(item).strip()
            stage = _resolve_pipeline_stage(key)
            if not stage:
                return {"ok": False, "error": f"unknown pipeline stage {key!r}"}
            if not any(s["id"] == stage["id"] for s in resolved):
                resolved.append(stage)
        resolved = _ordered_pipeline_stages(resolved)
        dispatch_schedule = (
            "serial"
            if req_schedule == "auto" and exec_mode_resolved == "single-worker"
            else _resolve_pipeline_schedule(req_schedule, resolved)
        )

        _raw_owner = _active_tool_owner()
        owner_display_id = normalize_session_name(_raw_owner) or "local-admin"
        owner_user_id = _raw_owner
        chat_context = ""
        try:
            from core.atlas_db import AtlasDB

            pr_for_chat = project_root()
            with AtlasDB(_atlas_job_db_path(pr_for_chat)) as db:
                owner_user_id = _canonical_user_id(db, _raw_owner)
                db.upsert_workspace(
                    pr_for_chat.name or "default",
                    owner_user_id=owner_user_id,
                    local_path=str(pr_for_chat),
                )
                rows = _recent_chat_context_for_ip(
                    db,
                    ip_name=ip_name,
                    owner_user_ids=[owner_user_id, _raw_owner],
                    limit=8,
                )
                rows = list(reversed(rows))
            rendered: list[str] = []
            for row in rows:
                payload_row = row.get("payload") if isinstance(row, dict) else {}
                content = str((payload_row or {}).get("content") or "").strip()
                if not content:
                    continue
                actor = str(row.get("actor_user_id") or owner_user_id or "user").strip()
                rendered.append(f"- {actor}: {content}")
            if rendered:
                chat_context = "\n".join(rendered)[-6000:]
        except Exception:
            chat_context = ""
        selected_stage_ids = [stage["id"] for stage in resolved]
        _, _ = _refresh_tracked_jobs(project_root())
        conflicts = _active_job_conflicts(
            ip=ip_name,
            stage_ids=selected_stage_ids,
            workflows=[stage["workflow"] for stage in resolved],
            user_id=owner_display_id,
            db_user_id=owner_user_id,
        )
        if conflicts:
            payload = _dedupe_payload(conflicts, ip=ip_name)
            payload.update({
                "source": "dispatch_workflow_tool",
                "schedule": dispatch_schedule,
                "requested_schedule": req_schedule,
                "run_mode": run_mode_resolved,
                "exec_mode": exec_mode_resolved,
                "stages": resolved,
                "user_id": owner_display_id,
                "db_user_id": owner_user_id,
            })
            return payload

        pipeline_id = uuid.uuid4().hex[:12]
        jobs: list[dict[str, Any]] = []
        stage_job_ids: dict[str, str] = {}
        for idx, stage in enumerate(resolved):
            stage_workflow = stage["workflow"]
            stage_prompt = _workflow_prompt_with_stage_driver(
                workflow=stage_workflow,
                ip=ip_name,
                stage_id=stage["id"],
                prompt=prompt_text,
            )
            if chat_context:
                stage_prompt += f"\n\n[Orchestrator chat context]\n{chat_context}"
            if prompt_text and prompt_text not in stage_prompt:
                stage_prompt += f"\n\n[Orchestrator payload goal]\n{prompt_text}"
            # Always inject the user's chat seed when present. This is the
            # last-resort propagation path: even if the LLM forgets to pass
            # ``prompt`` to dispatch_workflow, the worker still sees the
            # concrete requirement (e.g. "8-entry async FIFO, top=beta_fifo")
            # the user typed into the orchestrator chat.
            if user_seed_text and user_seed_text not in stage_prompt:
                stage_prompt += f"\n\n[USER REQUIREMENT]\n{user_seed_text}"
            stage_prompt += (
                "\n\n[ATLAS RUN POLICY]\n"
                f"- run_mode: {run_mode_resolved}\n"
                f"- exec_mode: {exec_mode_resolved}\n"
            )
            if reason_text:
                stage_prompt += f"\n\n[Orchestrator dispatch reason]\n{reason_text}"
            session = (
                f"{_pipeline_session_prefix_for_owner(owner_display_id, ip_name, pipeline_id)}/"
                f"{idx + 1:02d}-{stage_workflow}"
            )
            dep_stage_ids = _pipeline_stage_dependencies(
                stage["id"], selected_stage_ids, schedule=dispatch_schedule,
            )
            dep_job_ids = [stage_job_ids[dep] for dep in dep_stage_ids if dep in stage_job_ids]
            depends_on: str | list[str]
            depends_on = dep_job_ids[0] if dispatch_schedule == "serial" and dep_job_ids else dep_job_ids
            job = _make_job_record(
                workflow=stage_workflow,
                ip=ip_name,
                prompt=stage_prompt,
                model=model_resolved,
                session_name=session,
                stage_id=stage["id"],
                pipeline_id=pipeline_id,
                pipeline_index=idx,
                depends_on=depends_on,
                auto_start=(not dep_job_ids),
                pipeline_schedule=dispatch_schedule,
                run_mode=run_mode_resolved,
                exec_mode=exec_mode_resolved,
                user_id=owner_display_id,
                db_user_id=owner_user_id,
                trigger_source=trigger_source_resolved,
                orchestrator_run_id=orchestrator_run_id_resolved,
            )
            stage_job_ids[stage["id"]] = job["job_id"]
            jobs.append(_public_job(job))

        return {
            "ok": True,
            "source": "dispatch_workflow_tool",
            "pipeline_id": pipeline_id,
            "pipeline_run_id": pipeline_id,
            "user_id": owner_display_id,
            "db_user_id": owner_user_id,
            "ip": ip_name,
            "schedule": dispatch_schedule,
            "requested_schedule": req_schedule,
            "run_mode": run_mode_resolved,
            "exec_mode": exec_mode_resolved,
            "stages": resolved,
            "jobs": jobs,
        }

    def _read_pipeline_state_tool_bridge(
        *,
        ip: str = "",
        scope: str = "",
        include_jobs: bool = True,
    ) -> dict[str, Any]:
        """Return a compact in-process Pipeline state snapshot for LLM tools.

        The orchestrator agent runs inside the Atlas UI process, so it should
        not guess HTTP ports or depend on browser auth cookies just to inspect
        the live job registry. This bridge exposes the state it needs for
        routing decisions while keeping the public /api/pipeline/state endpoint
        authenticated.
        """
        ip_name = (
            str(ip or "").strip()
            or (Path(str(scope).rstrip("/")).name if scope else "")
            or os.environ.get("ATLAS_ACTIVE_IP", "").strip()
        )
        if not ip_name or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip_name):
            return {"ok": False, "error": f"invalid or missing ip {ip_name!r}"}

        pr = project_root()
        ip_dir = _ip_dir_for(pr, ip_name)
        with _jobs_lock:
            ip_jobs = [dict(j) for j in _jobs.values() if j.get("ip") == ip_name]

        artifact_map: dict[str, list[str]] = {
            "ssot": [f"yaml/{ip_name}.ssot.yaml"],
            "fl-model": ["model/fl_model_check.json", "cov/fcov_plan.json"],
            "cl-model": ["model/cl_model_check.json"],
            "equivalence": ["verify/equivalence_goals.json"],
            "rtl": ["rtl/rtl_compile.json", "lint/dut_lint.json", "rtl/rtl_contract.json", "rtl/rtl_todo_plan.json", "rtl/rtl_authoring_provenance.json"],
            "lint": ["lint/dut_lint.json"],
            "tb": ["tb/cocotb/"],
            "sim": ["sim/results.xml", "sim/fl_rtl_compare.json"],
            "coverage": ["cov/coverage.json"],
            "sim-debug": ["sim/mismatch_classification.json"],
            "goal-audit": ["sim/fl_rtl_goal_audit.json"],
            "syn": ["syn/out/"],
            "sta": ["sta/out/"],
            "pnr": ["pnr/out/"],
            "sta-post": ["sta-post/out/"],
        }

        def _stage_jobs(stage_id: str) -> list[dict[str, Any]]:
            return [j for j in ip_jobs if j.get("stage_id") == stage_id]

        def _public_latest(stage_id: str) -> dict[str, Any] | None:
            jobs = _stage_jobs(stage_id)
            if not jobs:
                return None
            latest = max(jobs, key=lambda j: j.get("started_at", 0) or 0)
            return _public_job(latest)

        passed: set[str] = set()
        failed: dict[str, str] = {}
        for stage in _PIPELINE_STAGES:
            sid = stage["id"]
            fake_job = {"ip": ip_name, "stage_id": sid, "workflow": stage["workflow"]}
            bad, why = _job_artifact_failure(fake_job, pr)
            ok, _ = _job_artifact_recovery(fake_job, pr)
            if bad:
                failed[sid] = why
            elif ok:
                passed.add(sid)

        stages_out: dict[str, Any] = {}
        for stage in _PIPELINE_STAGES:
            sid = stage["id"]
            jobs = _stage_jobs(sid)
            active = [j for j in jobs if j.get("status") in {"pending", "running"}]
            latest = _public_latest(sid)
            evidence_paths = [
                f"{ip_name}/{rel}"
                for rel in artifact_map.get(sid, [])
                if (ip_dir / rel).exists()
            ]
            if active:
                state = "running" if any(j.get("status") == "running" for j in active) else "pending"
            elif latest and latest.get("status") == "completed":
                state = "passed" if sid in passed or evidence_paths else "completed_no_gate"
            elif sid in passed:
                state = "passed"
            elif latest and latest.get("status") in {"error", "failed", "cancelled"}:
                state = "failed"
            elif sid in failed:
                state = "failed"
            else:
                deps = _PIPELINE_STAGE_DEPS.get(sid, ())
                state = "idle" if not deps else ("ready" if all(dep in passed for dep in deps) else "locked")

            stages_out[sid] = {
                "state": state,
                "workflow": stage["workflow"],
                "evidence_paths": evidence_paths,
                "failure": failed.get(sid, ""),
                "toolchain": _workflow_toolchain_for(stage["workflow"]),
                "latest_job": latest if include_jobs else None,
                "active_jobs": [_public_job(j) for j in active] if include_jobs else [],
            }

        active_jobs = [
            _public_job(j) for j in ip_jobs
            if j.get("status") in {"pending", "running"}
        ]
        passed_ids = [sid for sid, data in stages_out.items() if data.get("state") == "passed"]
        running_ids = [
            sid for sid, data in stages_out.items()
            if data.get("state") in {"pending", "running"}
        ]
        ready_ids = [sid for sid, data in stages_out.items() if data.get("state") == "ready"]
        locked_ids = [sid for sid, data in stages_out.items() if data.get("state") == "locked"]
        return {
            "ok": True,
            "source": "read_pipeline_state_tool",
            "ip": ip_name,
            "project_root": str(pr),
            "run_mode": _current_run_mode(),
            "exec_mode": _current_exec_mode(),
            "active_jobs": active_jobs if include_jobs else [],
            "passed": passed_ids,
            "failed": failed,
            "running": running_ids,
            "ready": ready_ids,
            "locked": locked_ids,
            "status_counts": _summarize_worker_progress(ip_jobs).get("status_counts", {}),
            "stages": stages_out,
        }

    try:
        from core import tools as _atlas_tools
    except Exception:
        _atlas_tools = None
    if _atlas_tools is not None and hasattr(_atlas_tools, "set_dispatch_workflow_callback"):
        _atlas_tools.set_dispatch_workflow_callback(_dispatch_workflow_tool_bridge)
    if _atlas_tools is not None and hasattr(_atlas_tools, "set_read_pipeline_state_callback"):
        _atlas_tools.set_read_pipeline_state_callback(_read_pipeline_state_tool_bridge)
    if _atlas_tools is not None and hasattr(_atlas_tools, "set_ensure_lazy_worker_callback"):
        def _ensure_lazy_worker_for_direct(worker_url: str, workflow: str, pr_path: str) -> None:
            _ensure_lazy_worker_for_direct_dispatch(
                worker_url,
                workflow,
                pr_path or str(project_root() or ""),
            )
        _atlas_tools.set_ensure_lazy_worker_callback(_ensure_lazy_worker_for_direct)

    # ── /api/pipeline/orchestrator_mode ───────────────────────────

    @app.get("/api/pipeline/orchestrator_mode")
    async def api_pipeline_orchestrator_mode_get():
        enabled = _orchestrator_mode_enabled()
        return JSONResponse({"enabled": enabled, "mode": "json" if enabled else None})

    @app.post("/api/pipeline/orchestrator_mode")
    async def api_pipeline_orchestrator_mode_set(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict) or "enabled" not in body:
            return JSONResponse({"error": "expected JSON body with 'enabled' bool"}, status_code=400)
        if not isinstance(body["enabled"], bool):
            return JSONResponse({"error": "'enabled' must be a JSON bool"}, status_code=400)
        os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1" if body["enabled"] else "0"
        os.environ["ATLAS_EXEC_MODE"] = "orchestrator" if body["enabled"] else "single-worker"
        os.environ["ATLAS_DEFAULT_EXEC_MODE"] = os.environ["ATLAS_EXEC_MODE"]
        if persist_config_values is not None:
            try:
                persist_config_values({
                    "ATLAS_EXEC_MODE": os.environ["ATLAS_EXEC_MODE"],
                    "ATLAS_DEFAULT_EXEC_MODE": os.environ["ATLAS_DEFAULT_EXEC_MODE"],
                    "ATLAS_ORCHESTRATOR_MODE": os.environ["ATLAS_ORCHESTRATOR_MODE"],
                })
            except Exception:
                pass
        # Bust the /api/pipeline/state micro-cache for every (ip, user_id)
        # so each user's next poll reflects the new mode immediately
        # instead of waiting up to 2 s.
        _state_cache.clear()
        enabled = _orchestrator_mode_enabled()
        return JSONResponse({"enabled": enabled, "mode": "json" if enabled else None})

    # ── /api/orchestrator/trace ─────────────────────────────────────
    #
    # Read the append-only orchestrator trace log for an IP. Powers the
    # Pipeline UI's right-side debug strip and the `jq`-friendly CLI use case.

    @app.get("/api/orchestrator/trace")
    async def api_orchestrator_trace_get(request: Request):
        params = dict(request.query_params)
        ip = (params.get("ip") or "").strip()
        if not ip:
            return JSONResponse({"error": "ip query param required"}, status_code=400)
        _trace_db_user = _request_db_user_id(request)
        if not _assert_ip_access(_trace_db_user, ip):
            return JSONResponse({"error": "forbidden"}, status_code=403)
        try:
            limit = int(params.get("limit") or "100")
        except Exception:
            limit = 100
        corr = (params.get("corr") or "").strip() or None
        lens = (params.get("lens") or "").strip() or None
        try:
            from core.orchestrator_trace import read_trace
            events = read_trace(ip, limit=max(1, min(1000, limit)), corr=corr, lens=lens)
        except Exception as e:
            return JSONResponse({"error": str(e), "events": []}, status_code=500)
        return JSONResponse({"ip": ip, "count": len(events), "events": events})

    # ── /api/orchestrator/chat/messages ────────────────────────────
    #
    # Poll natural-language chat messages (role=assistant/user/tool) for an IP.
    # Frontend polls every 1.5s while orchestrator is active.

    _CHAT_IP_RE = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

    @app.get("/api/orchestrator/chat/messages")
    async def api_orchestrator_chat_messages(request: Request):
        user_id = _request_db_user_id(request)
        if not user_id:
            return JSONResponse({"error": "not authenticated"}, status_code=401)
        params = dict(request.query_params)
        ip = (params.get("ip") or "").strip()
        if not ip or not _CHAT_IP_RE.match(ip):
            return JSONResponse({"error": "ip param missing or invalid"}, status_code=400)
        try:
            since = float(params["since"]) if params.get("since") else None
        except (ValueError, TypeError):
            return JSONResponse({"error": "since must be a unix timestamp"}, status_code=400)
        try:
            limit = int(params.get("limit") or "100")
            limit = max(1, min(500, limit))
        except Exception:
            limit = 100
        try:
            from core.atlas_db import AtlasDB
            pr = project_root()
            db_path = _atlas_job_db_path(pr)
            db_user_id = user_id
            with AtlasDB(db_path) as db:
                workspace = db.upsert_workspace(
                    pr.name or "default",
                    owner_user_id=db_user_id,
                    local_path=str(pr),
                )
                ip_row = db.upsert_ip_block(workspace["id"], ip)
                rows = db.list_chat_messages(ip_id=ip_row["id"], limit=limit, since=since)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        # rows are newest-first; reverse for chronological order
        rows = list(reversed(rows))
        next_since = max((r.get("created_at") or 0) for r in rows) if rows else (since or 0)
        return JSONResponse({"ok": True, "messages": rows, "next_since": next_since})

    @app.delete("/api/orchestrator/trace")
    async def api_orchestrator_trace_clear(request: Request):
        params = dict(request.query_params)
        ip = (params.get("ip") or "").strip()
        if not ip:
            return JSONResponse({"error": "ip query param required"}, status_code=400)
        try:
            from core.orchestrator_trace import clear_trace
            ok = clear_trace(ip)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({"ip": ip, "cleared": bool(ok)})

    # ── /api/orchestrator/workers ─────────────────────────────────────
    #
    # Aggregated live worker status — orchestrator's view of its workers.
    # Powers the Pipeline screen WorkerStatusBar (orchestra view).
    #
    # For each known workflow (ssot-gen, rtl-gen, fl-model-gen, tb-gen,
    # sim_debug, lint, sim, coverage, goal-audit) we read WORKER_URL_<wf>
    # from env and probe /health. The response is small enough to poll
    # every 3 s from the UI.

    @app.get("/api/orchestrator/workers")
    async def api_orchestrator_workers(request: Request):
        import asyncio

        params = dict(request.query_params)
        ip = (params.get("ip") or "").strip()

        # Workflows the orchestrator can dispatch. Order matches canonical pipeline.
        workflows = list(_DEFAULT_WORKER_PORTS.keys())

        def _probe(url: str) -> dict[str, Any]:
            # Cached fan-out: with N UI tabs polling every 3s, this dropped
            # probe traffic ~Nx without changing user-visible latency.
            return _probe_worker_health_cached(url, timeout=2.0)

        async def _gather() -> list[dict[str, Any]]:
            loop = asyncio.get_event_loop()
            tasks = []
            for wf in workflows:
                url = _resolve_worker_url(wf)
                tasks.append((wf, url, loop.run_in_executor(None, _probe, url)))
            out = []
            for wf, url, t in tasks:
                health = await t
                running = health.get("running") if isinstance(health, dict) else []
                running_list = running if isinstance(running, list) else []
                health_status = str(health.get("status", "unreachable"))
                default_model = _worker_model_default_for(wf)
                expected_model = _worker_model_for(wf)
                default_effort = _worker_reasoning_effort_default_for(wf)
                expected_effort = _worker_reasoning_effort_for(wf)
                bound_workflow = health.get("workflow")
                workflow_mismatch = _worker_workflow_mismatch(wf, health)
                health_model = str(health.get("model") or "").strip()
                running_models = [
                    str(item).strip()
                    for item in (health.get("running_models") or [])
                    if str(item).strip()
                ]
                model_mismatch = (
                    health_status == "ok"
                    and bool(expected_model)
                    and bool(health_model)
                    and health_model != expected_model
                    and expected_model not in running_models
                )
                mismatch_reasons = []
                if workflow_mismatch:
                    mismatch_reasons.append(workflow_mismatch)
                if model_mismatch:
                    mismatch_reasons.append(
                        f"health model {health_model!r} differs from configured dispatch model {expected_model!r}"
                    )
                status = "mismatch" if mismatch_reasons else health_status
                out.append({
                    "workflow": wf,
                    "url": url,
                    "status": status,
                    "health_status": health_status,
                    "bound_workflow": bound_workflow,
                    "all_workflows": bool(health.get("all_workflows")),
                    "default_model": default_model,
                    "expected_model": expected_model,
                    "configured_model": expected_model,
                    "default_reasoning_effort": default_effort,
                    "expected_reasoning_effort": expected_effort,
                    "configured_reasoning_effort": expected_effort,
                    "model": expected_model or health.get("model"),
                    "reasoning_effort": expected_effort,
                    "worker_health_model": health.get("model"),
                    "worker_running_models": running_models,
                    "worker_health_reasoning_effort": health.get("reasoning_effort"),
                    "workflow_mismatch": bool(workflow_mismatch),
                    "model_mismatch": bool(model_mismatch),
                    "mismatch_reasons": mismatch_reasons,
                    "toolchain": _workflow_toolchain_for(wf),
                    "profile": health.get("profile"),
                    "uptime_s": health.get("uptime_s"),
                    "total_runs": health.get("runs"),
                    "running": running_list,
                    "running_count": len(running_list),
                    "error": health.get("error"),
                })
            return out

        try:
            workers = await _gather()
        except Exception as e:
            return JSONResponse({"error": str(e), "workers": []}, status_code=500)

        # Orchestrator block — read last trace event to infer current activity.
        orch_active_target = None
        orch_active_corr = None
        orch_last_kind = None
        if ip:
            try:
                from core.orchestrator_trace import read_trace
                recent = read_trace(ip, limit=20)
                for ev in reversed(recent):
                    actor = ev.get("actor") or ""
                    kind = ev.get("kind") or ""
                    if kind == "http_send" or (kind == "http_recv" and actor.endswith("-worker")):
                        # Worker that received a recent dispatch
                        bound = actor.replace("-worker", "")
                        orch_active_target = bound
                        orch_active_corr = ev.get("corr")
                        orch_last_kind = kind
                        break
            except Exception:
                pass

        return JSONResponse({
            "ip": ip or None,
            "orchestrator": {
                "enabled": _orchestrator_mode_enabled(),
                "mode": "json" if _orchestrator_mode_enabled() else None,
                "active_target": orch_active_target,
                "active_corr": orch_active_corr,
                "last_kind": orch_last_kind,
                "model": ORCHESTRATOR_MODEL,
                "reasoning_effort": ORCHESTRATOR_REASONING_EFFORT,
                "profile": orchestrator_profile_name(),
            },
            "workers": workers,
            "count": len(workers),
        })

    # ── /api/pipeline/run_policy ────────────────────────────────────

    def _run_policy_payload() -> dict[str, Any]:
        exec_mode = _current_exec_mode()
        return {
            "run_mode": _current_run_mode(),
            "exec_mode": exec_mode,
            "orchestrator_enabled": exec_mode == "orchestrator",
            "run_modes": list(_RUN_MODES),
            "exec_modes": list(_EXEC_MODES),
        }

    @app.get("/api/pipeline/run_policy")
    async def api_pipeline_run_policy_get():
        return JSONResponse(_run_policy_payload())

    @app.post("/api/pipeline/run_policy")
    async def api_pipeline_run_policy_set(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)

        if "run_mode" in body:
            run_mode = _normalize_run_mode(body.get("run_mode"))
            if not run_mode:
                return JSONResponse({"error": "run_mode must be starter, engineering, or signoff"}, status_code=400)
            os.environ["ATLAS_RUN_MODE"] = run_mode
            if persist_config_values is not None:
                try:
                    persist_config_values({"ATLAS_RUN_MODE": run_mode})
                except Exception:
                    pass

        if "exec_mode" in body:
            exec_mode = _normalize_exec_mode(body.get("exec_mode"))
            if not exec_mode:
                return JSONResponse({"error": "exec_mode must be single-worker or orchestrator"}, status_code=400)
            os.environ["ATLAS_EXEC_MODE"] = exec_mode
            os.environ["ATLAS_DEFAULT_EXEC_MODE"] = exec_mode
            os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1" if exec_mode == "orchestrator" else "0"
            if persist_config_values is not None:
                try:
                    persist_config_values({
                        "ATLAS_EXEC_MODE": exec_mode,
                        "ATLAS_DEFAULT_EXEC_MODE": exec_mode,
                        "ATLAS_ORCHESTRATOR_MODE": "1" if exec_mode == "orchestrator" else "0",
                    })
                except Exception:
                    pass

        _state_cache.clear()
        return JSONResponse(_run_policy_payload())

    # ── /api/handoff/* ─────────────────────────────────────────────
    # User-driven actions for the orchestrator/handoff queue. Each request
    # is scope-filtered by the authenticated user so user_a cannot list,
    # claim, or write into user_b's queue.

    def _handoff_modules():
        try:
            from src import handoff_queue as _hq
        except ModuleNotFoundError:
            import handoff_queue as _hq  # type: ignore[no-redef]
        return _hq

    def _request_scope(
        request: Request,
        *,
        ip: str = "",
        workflow: str = "orchestrator",
        payload: dict | None = None,
    ) -> dict:
        u = request.scope.get("user") or {}
        body = payload or {}
        owner = normalize_session_name(str(u.get("username") or u.get("id") or ""))
        session_raw = str(
            body.get("session_id")
            or body.get("session")
            or u.get("session_id")
            or ""
        )
        session_id = normalize_session_name(session_raw)
        if not session_id:
            session_id = (
                _default_job_session(request, ip, workflow or "orchestrator")
                if ip else (owner or "default")
            )
        pipeline_run_id = str(
            body.get("pipeline_run_id")
            or body.get("pipeline_id")
            or u.get("pipeline_run_id")
            or ""
        ).strip() or "manual"
        scope = {
            "user_id": owner,
            "session_id": session_id,
            "pipeline_run_id": pipeline_run_id,
        }
        for key in ("workspace_id", "lease_id"):
            if body.get(key) is not None:
                scope[key] = str(body.get(key) or "")
        return scope

    def _scope_filter_from(scope: dict) -> dict | None:
        uid = scope.get("user_id") or ""
        return {"user_id": uid} if uid else None

    def _resolve_ip_dir(ip: str) -> Path | None:
        if not ip or len(ip) > 64 or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return None
        return project_root() / ip

    @app.get("/api/handoff/list")
    async def api_handoff_list(
        request: Request,
        ip: str = "",
        workflow: str = "",
        session_id: str = "",
        pipeline_run_id: str = "",
        pipeline_id: str = "",
    ):
        ip_dir = _resolve_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "invalid or missing ip"}, status_code=400)
        hq = _handoff_modules()
        scope = _request_scope(
            request,
            ip=ip,
            workflow="orchestrator",
            payload={
                "session_id": session_id,
                "pipeline_run_id": pipeline_run_id,
                "pipeline_id": pipeline_id,
            },
        )
        sf = _scope_filter_from(scope)

        def _filter_workflow(rows):
            if workflow:
                return [r for r in rows if r.get("to_workflow") == workflow]
            return rows

        def _filter_scope(rows):
            if not sf:
                return rows
            return [r for r in rows if all(r.get("scope", {}).get(k) == v for k, v in sf.items())]

        return JSONResponse({
            "ip": ip,
            "workflow": workflow or None,
            "scope": scope,
            "pending": _filter_scope(_filter_workflow(hq.list_state(ip_dir, "pending"))),
            "claimed": _filter_scope(_filter_workflow(hq.list_state(ip_dir, "claimed"))),
            "done":    _filter_scope(_filter_workflow(hq.list_state(ip_dir, "done"))),
            "review":  _filter_scope(_filter_workflow(hq.list_state(ip_dir, "review"))),
        })

    @app.post("/api/handoff/save")
    async def api_handoff_save(request: Request):
        """Write a new pending handoff. The orchestrator-driven equivalent of
        the StageCard `[ save handoff ]` button. Required body fields:
        `ip`, `from_workflow`, `to_workflow`. Optional: `reason`, `goal_ids`,
        `evidence`, `suffix`."""
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        ip = str(body.get("ip") or "").strip()
        ip_dir = _resolve_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "invalid or missing ip"}, status_code=400)
        from_workflow = str(body.get("from_workflow") or "").strip()
        to_workflow   = str(body.get("to_workflow") or "").strip()
        if not from_workflow or not to_workflow:
            return JSONResponse(
                {"error": "from_workflow and to_workflow are required"},
                status_code=400,
            )
        suffix = str(body.get("suffix") or body.get("reason") or "user").strip()
        hq = _handoff_modules()
        scope = _request_scope(request, ip=ip, workflow="orchestrator", payload=body)
        record = {
            "schema": hq.SCHEMA,
            "handoff_id": hq.make_handoff_id(ip, from_workflow, to_workflow, suffix),
            "ip": ip,
            "from_workflow": from_workflow,
            "to_workflow": to_workflow,
            "scope": scope,
            "reason": str(body.get("reason") or "user-saved handoff"),
            "goal_ids": list(body.get("goal_ids") or []),
            "evidence": dict(body.get("evidence") or {}),
        }
        try:
            path = hq.write_pending(ip_dir, record)
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=400)
        # Invalidate per-(ip,user) state cache so the next poll reflects the new pending.
        for k in list(_state_cache.keys()):
            if isinstance(k, tuple) and k[0] == ip:
                _state_cache.pop(k, None)
        return JSONResponse({
            "ok": True,
            "handoff_id": record["handoff_id"],
            "state": "pending",
            "path": str(path.relative_to(project_root())) if path.is_relative_to(project_root()) else str(path),
            "scope": scope,
        })

    @app.post("/api/handoff/take")
    async def api_handoff_take(request: Request):
        """Claim the oldest pending handoff for the given workflow within the
        authenticated user's scope. StageCard `[ take ]` button. Body:
        {ip, workflow}."""
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        ip = str(body.get("ip") or "").strip()
        ip_dir = _resolve_ip_dir(ip)
        if ip_dir is None:
            return JSONResponse({"error": "invalid or missing ip"}, status_code=400)
        workflow = str(body.get("workflow") or "").strip()
        if not workflow:
            return JSONResponse({"error": "workflow is required"}, status_code=400)
        hq = _handoff_modules()
        scope = _request_scope(request, ip=ip, workflow="orchestrator", payload=body)
        sf = _scope_filter_from(scope)
        scoped_user = request.scope.get("user") or {}
        claimant = f"ui-{scoped_user.get('username') or 'anon'}"
        record = hq.claim_next(ip_dir, workflow, claimant=claimant, scope_filter=sf)
        for k in list(_state_cache.keys()):
            if isinstance(k, tuple) and k[0] == ip:
                _state_cache.pop(k, None)
        if record is None:
            return JSONResponse({"ok": True, "status": "none_available"})
        return JSONResponse({"ok": True, "status": "claimed", "handoff": record})

    # ── /api/jobs ──────────────────────────────────────────────────

    @app.get("/api/jobs")
    async def api_jobs():
        """Aggregate job status across all dispatched workers.

        For each tracked job, poll the worker's /status/{run_id} (with a
        small 1.5s per-job cache to avoid hammering during a 2-second
        frontend poll cycle) and return the merged list.  Sorted by
        started_at descending so the most-recent job is first.
        """
        pr  = project_root()
        snapshot, _ = _refresh_tracked_jobs(pr)
        out = [_public_job(job) for job in snapshot]
        out.sort(key=lambda j: j.get("started_at", 0), reverse=True)
        return JSONResponse({"jobs": out, "count": len(out)})

    # ── /api/job/{job_id}/log ──────────────────────────────────────

    @app.get("/api/job/{job_id}/log")
    async def api_job_log(job_id: str, since: int = 0, tail: int = 0):
        """Proxy a worker run transcript into the Architect chat.

        The frontend knows Atlas job ids, not worker run ids.  Keep that
        mapping server-side so users can click a job/status-grid pill and
        inspect the live ReAct transcript without leaving the Architect view.
        """
        pr = project_root()
        with _jobs_lock:
            job = dict(_jobs.get(job_id) or {})
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)

        def _session_history_log():
            session = normalize_session_name(str(job.get("session") or ""))
            if not session:
                return None
            path = pr / ".session" / session / "conversation.json"
            if not path.is_file():
                return None
            try:
                messages = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None
            if isinstance(messages, dict):
                messages = messages.get("messages") or []
            if not isinstance(messages, list):
                return None
            entries = []
            for i, m in enumerate(messages[-120:]):
                if not isinstance(m, dict):
                    continue
                role    = m.get("role") or ""
                content = str(m.get("content") or "")
                stripped = content.strip()
                if not stripped:
                    continue
                typ = "response"
                if role == "user":
                    if stripped.startswith("Observation:"):
                        typ = "observation"
                    elif stripped.startswith("[Context]"):
                        typ = "context"
                    else:
                        typ = "task"
                elif role == "assistant" and stripped.startswith("Action:"):
                    typ = "action"
                entries.append({
                    "index":     i,
                    "type":      typ,
                    "role":      role,
                    "content":   content,
                    "timestamp": m.get("timestamp") or job.get("finished_at") or job.get("started_at") or 0,
                    "source":    "session",
                })
            if since > 0:
                entries = [e for e in entries if e["index"] >= since]
            if tail > 0:
                entries = entries[-tail:]
            return {
                "run_id":        job.get("run_id") or "",
                "status":        job.get("status") or "unknown",
                "total_entries": len(entries),
                "entries":       entries,
                "source":        "session",
                "session_path":  path.relative_to(pr).as_posix(),
                "job":           {k: v for k, v in job.items() if not k.startswith("_")},
            }

        try:
            import urllib.parse as _p
            import urllib.request as _u
            qs  = _p.urlencode({k: v for k, v in {"since": since, "tail": tail}.items() if v})
            url = f"{job['worker'].rstrip('/')}/log/{job['run_id']}" + (f"?{qs}" if qs else "")
            req = _u.Request(url, method="GET")
            with _u.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            fallback = _session_history_log()
            if fallback is not None:
                fallback["worker_log_error"] = str(e)
                return JSONResponse(fallback)
            return JSONResponse({"error": f"log fetch failed: {e}", "job": job}, status_code=502)
        data["job"] = {k: v for k, v in job.items() if not k.startswith("_")}
        return JSONResponse(data)

    # ── /api/job/{job_id}/cancel ───────────────────────────────────

    @app.post("/api/job/{job_id}/cancel")
    async def api_job_cancel(job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)
        if job["status"] != "running":
            return JSONResponse({"error": f"job already {job['status']}"}, status_code=400)
        try:
            import urllib.request as _u
            req = _u.Request(
                f"{job['worker'].rstrip('/')}/cancel/{job['run_id']}",
                method="POST",
            )
            with _u.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            return JSONResponse({"error": f"cancel failed: {e}"}, status_code=502)
        with _jobs_lock:
            job["status"] = "cancelled"
            job["finished_at"] = time.time()
            _finish_job_db_run(job, "cancelled")
        return JSONResponse({"ok": True})

    # ── /api/jobs/clear ────────────────────────────────────────────

    @app.post("/api/jobs/clear")
    async def api_jobs_clear():
        """Drop completed/cancelled/failed jobs from the tracker."""
        with _jobs_lock:
            for jid in list(_jobs.keys()):
                if _jobs[jid]["status"] != "running":
                    _jobs.pop(jid, None)
        return JSONResponse({"ok": True})
