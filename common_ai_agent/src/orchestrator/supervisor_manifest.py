from __future__ import annotations

import importlib
import os
import secrets
import time
from pathlib import Path
from typing import Any


def resolve_ip_workflow_root(project_root: Path, source_root: Path, ip_name: str = "") -> Path:
    resolver = importlib.import_module("core.atlas_context").resolve_ip_workflow_root
    return resolver(project_root, source_root, ip_name)


def supervisor_request_payload(
    *,
    db: Any,
    project_root: Path,
    source_root: Path,
    paths: dict[str, Path],
    data: dict[str, str],
) -> dict[str, Any]:
    run_id = data["run_id"]
    return {
        "schema_version": 1,
        "kind": "orchestrator-supervisor",
        "run_id": run_id,
        "resume": False,
        "project_root": str(project_root),
        "source_root": str(source_root),
        "db_path": str(getattr(db, "db_path", "") or getattr(db, "path", "")),
        "user_id": data["user_id"],
        "db_user_id": data["user_id"],
        "workspace_id": data.get("workspace_id", ""),
        "ip_id": data["ip_id"],
        "ip_name": data["ip_name"],
        "session_id": data.get("session_id", ""),
        "chat_message_id": data.get("chat_message_id", ""),
        "initial_user_message": data.get("message_text", ""),
        "model": data.get("model", ""),
        "reasoning_effort": data.get("reasoning_effort", ""),
        "control_dir": str(paths["control"]),
        "wake_path": str(paths["wake"]),
        "cancel_path": str(paths["cancel"]),
        "response_path": str(paths["response"]),
        "tool_bridge_dir": str(paths["bridge"]),
        "tool_bridge_token": secrets.token_urlsafe(32),
    }


def supervisor_process_env(
    *,
    project_root: Path,
    source_root: Path,
    ip_name: str = "",
) -> dict[str, str]:
    env = os.environ.copy()
    env["ATLAS_PROJECT_ROOT"] = str(project_root)
    env["ATLAS_SOURCE_ROOT"] = str(source_root)
    env["ATLAS_WORKFLOW_ROOT"] = str(resolve_ip_workflow_root(project_root, source_root, ip_name))
    env["ATLAS_EXEC_MODE"] = "orchestrator"
    env["ATLAS_ORCHESTRATOR_MODE"] = "1"
    env["ATLAS_WORKER_TRANSPORT"] = "ipc"
    env["ATLAS_SINGLE_MAIN_LOOP"] = "0"
    env["ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR"] = ""
    env["PYTHONPATH"] = f"{source_root}{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep)
    return env


def supervisor_job_metadata(
    *,
    project_root: Path,
    job_id: str,
    process_key: str,
    paths: dict[str, Path],
    proc: Any,
    data: dict[str, str],
) -> dict[str, Any]:
    return {
        "job_id": job_id,
        "run_id": process_key,
        "job_kind": "orchestrator-supervisor",
        "workflow": "orchestrator",
        "worker_transport": "ipc",
        "status": "running",
        "started_at": time.time(),
        "project_root": str(project_root),
        "db_user_id": data["user_id"],
        "db_ip_id": data["ip_id"],
        "ip": data["ip_name"],
        "orchestrator_run_id": data["run_id"],
        "worker_pid": getattr(proc, "pid", ""),
        "worker_request_path": _rel(project_root, paths["request"]),
        "worker_response_path": _rel(project_root, paths["response"]),
        "worker_log_path": _rel(project_root, paths["log"]),
    }


def _rel(project_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(project_root).as_posix()
    except Exception:
        return str(path)
