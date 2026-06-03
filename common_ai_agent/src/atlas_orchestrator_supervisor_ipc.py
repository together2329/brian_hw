from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from src.orchestrator.loop import OrchestratorContext, RunOutcome
from src.orchestrator.supervisor_wake import FileBackedSupervisorRunner


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
    source_root = str(request.get("source_root") or os.environ.get("ATLAS_SOURCE_ROOT") or Path(__file__).resolve().parents[1])
    session_id = str(request.get("session_id") or "").strip()
    ip_name = str(request.get("ip_name") or request.get("ip") or "").strip()
    ip_id = str(request.get("ip_id") or ip_name).strip()
    os.environ["ATLAS_PROJECT_ROOT"] = project_root
    os.environ["ATLAS_SOURCE_ROOT"] = source_root
    os.environ.setdefault("ATLAS_WORKFLOW_ROOT", str(Path(source_root) / "workflow"))
    os.environ["ATLAS_EXEC_MODE"] = "orchestrator"
    os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1"
    os.environ["ATLAS_WORKER_TRANSPORT"] = "ipc"
    os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "0"
    if session_id:
        os.environ["ATLAS_ACTIVE_SESSION"] = session_id
        os.environ["ATLAS_SESSION_ID"] = session_id
    if ip_name:
        os.environ["ATLAS_ACTIVE_IP"] = ip_name
    if ip_id:
        os.environ["ATLAS_IP_ID"] = ip_id
    if source_root not in sys.path:
        sys.path.insert(0, source_root)


def _build_loop(db: Any, ctx: OrchestratorContext, initial_user_message: str) -> Any:
    from src.orchestrator.react_bridge import OrchestratorReactLoop

    return OrchestratorReactLoop(db, ctx, initial_user_message=initial_user_message)


def _payload(
    *,
    request: dict[str, Any],
    outcome: RunOutcome,
    started_at: float,
    finished_at: float,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "orchestrator-supervisor",
        "run_id": str(request.get("run_id") or ""),
        "status": outcome.status,
        "final_state": outcome.final_state or "",
        "error": outcome.error or "",
        "steps_taken": outcome.steps_taken,
        "child_job_ids": [],
        "started_at": started_at,
        "finished_at": finished_at,
        "duration_ms": int(max(0.0, finished_at - started_at) * 1000),
    }


def run_request(request: dict[str, Any], *, run_id: str) -> dict[str, Any]:
    _configure_env(request)

    AtlasDB = importlib.import_module("core.atlas_db").AtlasDB
    started_at = time.time()
    db = AtlasDB(str(request.get("db_path") or ""))
    try:
        ctx = OrchestratorContext(
            run_id=run_id,
            user_id=str(request.get("db_user_id") or request.get("user_id") or ""),
            ip_id=str(request.get("ip_id") or ""),
            ip_name=str(request.get("ip_name") or ""),
            workspace_id=str(request.get("workspace_id") or ""),
            session_id=str(request.get("session_id") or ""),
            project_root=Path(str(request.get("project_root") or ".")).resolve(),
            runner=FileBackedSupervisorRunner(
                wake_path=Path(str(request.get("wake_path") or "")),
                cancel_path=Path(str(request.get("cancel_path") or "")),
            ),
        )
        loop = _build_loop(db, ctx, str(request.get("initial_user_message") or ""))
        outcome = loop.run()
        return _payload(
            request={**request, "run_id": run_id},
            outcome=outcome,
            started_at=started_at,
            finished_at=time.time(),
        )
    finally:
        db.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="atlas_orchestrator_supervisor_ipc")
    parser.add_argument("--request", required=True)
    parser.add_argument("--response", required=True)
    parser.add_argument("--run-id", default="")
    args = parser.parse_args(argv)

    request_path = Path(args.request)
    response_path = Path(args.response)
    run_id = str(args.run_id or "").strip()
    try:
        request = _read_request(request_path)
        run_id = run_id or str(request.get("run_id") or "").strip()
        if not run_id:
            raise ValueError("run_id required")
        response = run_request(request, run_id=run_id)
        _write_response(response_path, response)
        return 0 if response.get("status") == "completed" else 2
    except Exception as exc:
        error_response = {
            "schema_version": 1,
            "kind": "orchestrator-supervisor",
            "run_id": run_id,
            "status": "error",
            "final_state": "",
            "error": f"{type(exc).__name__}: {exc}",
            "steps_taken": 0,
            "child_job_ids": [],
            "finished_at": time.time(),
            "traceback": traceback.format_exc(),
        }
        try:
            _write_response(response_path, error_response)
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
