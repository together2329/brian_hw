"""Portless ATLAS worker subprocess entrypoint.

The Atlas orchestrator writes one JSON request file, starts this module as a
subprocess, and reads one JSON response file when it exits. This preserves
process isolation without opening per-worker HTTP ports.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any


def _read_request(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(data, dict):
        raise ValueError("request JSON must be an object")
    return data


def _write_response(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    tmp.replace(path)


def _configure_env(request: dict[str, Any]) -> None:
    project_root = str(request.get("project_root") or os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    source_root = str(
        request.get("source_root")
        or os.environ.get("ATLAS_SOURCE_ROOT")
        or Path(__file__).resolve().parents[1]
    )
    workflow = str(request.get("workflow") or "").strip()
    session = str(request.get("session") or "").strip()
    ip = str(request.get("ip") or "").strip()

    os.environ["ATLAS_PROJECT_ROOT"] = project_root
    os.environ["ATLAS_SOURCE_ROOT"] = source_root
    os.environ.setdefault("ATLAS_WORKFLOW_ROOT", str(Path(source_root) / "workflow"))
    os.environ["ATLAS_WORKER_TRANSPORT"] = "ipc"
    os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1"
    os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "0"
    os.environ["ATLAS_EXEC_MODE"] = str(request.get("exec_mode") or "orchestrator")
    os.environ.setdefault("EXECUTION_NO_ACTION_GUARD", "false")
    os.environ.setdefault("AGENT_SERVER_MAX_CONCURRENT", "1")
    if workflow:
        os.environ["ATLAS_WORKFLOW"] = workflow
        os.environ["ACTIVE_WORKSPACE"] = workflow
    if session:
        os.environ["ATLAS_ACTIVE_SESSION"] = session
        os.environ["ATLAS_SESSION_ID"] = session
        os.environ["ATLAS_MEMORY_USER"] = session.split("/", 1)[0]
    if ip:
        os.environ["ATLAS_ACTIVE_IP"] = ip
        os.environ["ATLAS_IP_ID"] = ip
    if source_root not in sys.path:
        sys.path.insert(0, source_root)


def run_request(request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    _configure_env(request)

    from core.agent_server import RunEntry, _run_react_task  # type: ignore
    import core.agent_server as agent_server  # type: ignore

    workflow = str(request.get("workflow") or "").strip()
    session = str(request.get("session") or "").strip()
    agent_server._SERVER_WORKFLOW = workflow
    agent_server._SERVER_SESSION = session
    agent_server._SERVER_ACCEPT_ANY_WORKFLOW = False

    started_at = time.time()
    entry = RunEntry(
        run_id=run_id,
        task=str(request.get("task") or ""),
        model=str(request.get("model") or ""),
        created_at=started_at,
    )
    _run_react_task(
        entry,
        str(request.get("task") or ""),
        str(request.get("model") or ""),
        request.get("todos"),
        str(request.get("context") or ""),
        workflow,
        session,
        str(request.get("ip") or ""),
        str(request.get("rtl_version_id") or ""),
        str(request.get("project_root") or ""),
        request.get("artifact_versions") or [],
        str(request.get("reasoning_effort") or ""),
        str(request.get("system_prompt") or request.get("custom_system_prompt") or ""),
        request.get("allowed_tools") or request.get("custom_allowed_tools"),
        str(request.get("custom_agent") or request.get("agent") or ""),
        str(request.get("custom_agent_owner_id") or request.get("owner_user_id") or ""),
    )
    finished_at = time.time()
    result = entry.result if isinstance(entry.result, dict) else {}
    return {
        "run_id": entry.run_id,
        "status": entry.status,
        "error": entry.error or result.get("error") or "",
        "result": result,
        "entries": entry.get_log(),
        "started_at": entry.started_at or started_at,
        "finished_at": entry.finished_at or finished_at,
        "duration_ms": int(max(0.0, finished_at - started_at) * 1000),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas_worker_ipc")
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    request_path = Path(args.request)
    response_path = Path(args.response)
    run_id = str(args.run_id or "").strip()
    try:
        request = _read_request(request_path)
        run_id = run_id or str(request.get("run_id") or "").strip() or f"ipc-{int(time.time() * 1000)}"
        response = run_request(request, run_id=run_id)
        _write_response(response_path, response)
        return 0 if response.get("status") == "completed" else 2
    except Exception as exc:
        error_response = {
            "run_id": run_id,
            "status": "error",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback": traceback.format_exc(),
            "result": {
                "run_id": run_id,
                "status": "error",
                "error": str(exc),
                "files_modified": [],
                "files_examined": [],
                "iterations": 0,
            },
            "entries": [],
            "finished_at": time.time(),
        }
        try:
            _write_response(response_path, error_response)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
