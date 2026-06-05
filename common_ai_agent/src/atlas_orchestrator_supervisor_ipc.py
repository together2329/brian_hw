from __future__ import annotations

import argparse
import importlib
import json
import os
import re
import sys
import time
import traceback
from pathlib import Path
from typing import Any

from src.orchestrator.ipc_tool_bridge import call_bridge, write_json_atomic
from src.orchestrator.loop import OrchestratorContext, RunOutcome
from src.orchestrator.supervisor_wake import FileBackedSupervisorRunner, safe_run_id

_SAFE_IP_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")


def _read_request(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    if not isinstance(data, dict):
        raise ValueError("request JSON must be an object")
    return data


def _reject_symlink_chain(path: Path) -> None:
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError(f"orchestrator supervisor IPC path must not be a symlink: {candidate}")
        if candidate.name == ".session":
            return
    raise ValueError("orchestrator supervisor IPC path must stay under .session")


def _request_path(project_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / path


def _request_control_dir(request: dict[str, Any], project_root: Path) -> Path:
    control_raw = str(request.get("control_dir") or "").strip()
    if control_raw:
        return _request_path(project_root, control_raw)
    return (
        project_root
        / ".session"
        / "orchestrators-ipc"
        / safe_run_id(str(request.get("run_id") or "run"))
    )


def _validate_tool_bridge_dir(request: dict[str, Any], project_root: Path, control_root: Path) -> None:
    bridge_raw = str(request.get("tool_bridge_dir") or "").strip()
    if not bridge_raw:
        return
    bridge_dir = _request_path(project_root, bridge_raw)
    expected_bridge = control_root / "tool-bridge"
    for path in (bridge_dir, bridge_dir / "requests", bridge_dir / "responses"):
        _reject_symlink_chain(path)
    if bridge_dir.resolve() != expected_bridge.resolve():
        raise ValueError("orchestrator supervisor tool bridge path must stay in the control directory")


def _validate_ipc_paths(request_path: Path, response_path: Path, request: dict[str, Any]) -> None:
    project_root = Path(request.get("project_root") or os.environ.get("ATLAS_PROJECT_ROOT") or ".").resolve()
    control_dir = _request_control_dir(request, project_root)
    for path in (request_path, response_path, control_dir):
        _reject_symlink_chain(path)
    control_root = control_dir.resolve()
    supervisor_root = (project_root / ".session" / "orchestrators-ipc").resolve()
    try:
        control_root.relative_to(supervisor_root)
    except ValueError as exc:
        raise ValueError("orchestrator supervisor IPC paths must stay under the project supervisor root") from exc
    if request_path.parent.resolve() != control_root:
        raise ValueError("orchestrator supervisor request path must stay in the control directory")
    if response_path.parent.resolve() != control_root:
        raise ValueError("orchestrator supervisor response path must stay in the control directory")
    expected_response_raw = str(request.get("response_path") or "").strip()
    if expected_response_raw:
        expected_response = _request_path(project_root, expected_response_raw)
        if expected_response.resolve() != response_path.resolve():
            raise ValueError("orchestrator supervisor response path does not match request")
    _validate_tool_bridge_dir(request, project_root, control_root)


def _write_response(path: Path, payload: dict[str, Any]) -> None:
    _reject_symlink_chain(path)
    if not path.parent.is_dir():
        raise ValueError(f"orchestrator supervisor response parent does not exist: {path.parent}")
    write_json_atomic(path, payload, create_parent=False)


def _resolve_ip_workflow_root(project_root: str, source_root: str, ip: str) -> Path:
    resolver = importlib.import_module("core.atlas_context").resolve_ip_workflow_root
    return resolver(project_root, source_root, ip)


def _configure_env(request: dict[str, Any]) -> None:
    project_root = str(request.get("project_root") or os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    source_root = str(request.get("source_root") or os.environ.get("ATLAS_SOURCE_ROOT") or Path(__file__).resolve().parents[1])
    session_id = str(request.get("session_id") or "").strip()
    ip_name = str(request.get("ip_name") or request.get("ip") or "").strip()
    if ip_name and not _SAFE_IP_RE.fullmatch(ip_name):
        raise ValueError(f"invalid IPC ip {ip_name!r}")
    ip_id = str(request.get("ip_id") or ip_name).strip()
    project_root_path = Path(project_root).expanduser().resolve()
    ip_root = ""
    if ip_name:
        ip_root_path = project_root_path if project_root_path.name == ip_name else project_root_path / ip_name
        ip_root = str(ip_root_path.resolve())
    db_path = str(request.get("db_path") or "").strip()
    tool_bridge_dir = str(request.get("tool_bridge_dir") or "").strip()
    tool_bridge_token = str(request.get("tool_bridge_token") or "").strip()
    os.environ["ATLAS_PROJECT_ROOT"] = project_root
    os.environ["ATLAS_SOURCE_ROOT"] = source_root
    os.environ["ATLAS_WORKFLOW_ROOT"] = str(_resolve_ip_workflow_root(project_root, source_root, ip_name))
    os.environ["ATLAS_EXEC_MODE"] = "orchestrator"
    os.environ["ATLAS_ORCHESTRATOR_MODE"] = "1"
    os.environ["ATLAS_WORKER_TRANSPORT"] = "ipc"
    os.environ["ATLAS_SINGLE_MAIN_LOOP"] = "0"
    if db_path:
        os.environ["ATLAS_DB_PATH"] = db_path
        os.environ["ATLAS_MEMORY_DB_PATH"] = db_path
    if tool_bridge_dir:
        os.environ["ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR"] = tool_bridge_dir
    else:
        os.environ.pop("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR", None)
    if tool_bridge_token:
        os.environ["ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TOKEN"] = tool_bridge_token
    else:
        os.environ.pop("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TOKEN", None)
    if session_id:
        os.environ["ATLAS_ACTIVE_SESSION"] = session_id
        os.environ["ATLAS_SESSION_ID"] = session_id
        owner = session_id.split("/", 1)[0].strip()
        if owner:
            os.environ["ATLAS_MEMORY_USER"] = owner
    if ip_name:
        os.environ["ATLAS_ACTIVE_IP"] = ip_name
        os.environ["ATLAS_IP_ROOT"] = ip_root
    if ip_id:
        os.environ["ATLAS_IP_ID"] = ip_id
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
    source_src = str(Path(source_root) / "src")
    if source_src not in sys.path:
        sys.path.insert(0, source_src)


def _bridge_timeout() -> float:
    raw = os.environ.get("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TIMEOUT", "120")
    try:
        return max(1.0, float(raw))
    except ValueError:
        return 120.0


def _bridge_dict_result(tool: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    bridge_dir = os.environ.get("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR", "").strip()
    if not bridge_dir:
        return {"ok": False, "error": "orchestrator tool bridge unavailable"}
    response = call_bridge(
        bridge_dir,
        tool=tool,
        kwargs=kwargs,
        timeout_s=_bridge_timeout(),
    )
    result = response.get("result") if isinstance(response, dict) else None
    if isinstance(result, dict):
        return result
    return {
        "ok": False,
        "error": str(response.get("error") if isinstance(response, dict) else "invalid bridge response"),
    }


def _workspace_session_from_request(request: dict[str, Any]) -> str:
    explicit = str(request.get("workspace_session") or "").strip()
    if explicit:
        return explicit
    session_id = str(request.get("session_id") or "").strip()
    parts = [part for part in session_id.split("/") if part]
    if len(parts) >= 4:
        return parts[1]
    return "default"


def _enrich_dispatch_kwargs(kwargs: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(kwargs)
    body = enriched.get("payload")
    payload = dict(body) if isinstance(body, dict) else {}
    payload["db_user_id"] = str(request.get("db_user_id") or request.get("user_id") or "")
    payload["orchestrator_session_id"] = str(request.get("session_id") or "")
    payload["workspace_session"] = _workspace_session_from_request(request)
    payload["orchestrator_run_id"] = str(request.get("run_id") or "")
    payload["trigger_source"] = "orchestrator_chat"
    if str(request.get("ip_name") or "").strip():
        payload["ip"] = str(request.get("ip_name") or "").strip()
    enriched["payload"] = payload
    if str(request.get("ip_name") or "").strip():
        enriched["ip"] = str(request.get("ip_name") or "")
    if not str(enriched.get("model") or "").strip():
        enriched["model"] = str(request.get("model") or "")
    enriched["exec_mode"] = "orchestrator"
    return enriched


def _enrich_read_pipeline_state_kwargs(
    kwargs: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    enriched = dict(kwargs)
    enriched["db_user_id"] = str(request.get("db_user_id") or request.get("user_id") or "")
    enriched["scope"] = str(request.get("session_id") or "")
    if str(request.get("ip_name") or "").strip():
        enriched["ip"] = str(request.get("ip_name") or "").strip()
    return enriched


def _install_tool_bridge(request: dict[str, Any]) -> None:
    core_tools = importlib.import_module("core.tools")
    bridge_dir = os.environ.get("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR", "").strip()
    if not bridge_dir:
        core_tools.set_dispatch_workflow_callback(None)
        core_tools.set_read_pipeline_state_callback(None)
        return
    core_tools.set_dispatch_workflow_callback(
        lambda **kwargs: _bridge_dict_result(
            "dispatch_workflow",
            _enrich_dispatch_kwargs(dict(kwargs), request),
        )
    )
    core_tools.set_read_pipeline_state_callback(
        lambda **kwargs: _bridge_dict_result(
            "read_pipeline_state",
            _enrich_read_pipeline_state_kwargs(dict(kwargs), request),
        )
    )


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
    _install_tool_bridge(request)

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
    response_path_validated = False
    try:
        _reject_symlink_chain(request_path)
        _reject_symlink_chain(response_path)
        request = _read_request(request_path)
        _validate_ipc_paths(request_path, response_path, request)
        response_path_validated = True
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
        if response_path_validated:
            try:
                _write_response(response_path, error_response)
            except OSError:
                pass
            except ValueError:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
