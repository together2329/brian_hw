from __future__ import annotations

import importlib
import json
import threading
import time
from pathlib import Path
from typing import Any, Protocol, final

from src.orchestrator.ipc_tool_bridge import safe_bridge_id, write_json_atomic


class PollableProcess(Protocol):
    def poll(self) -> int | None:
        ...


def prepare_tool_bridge_dir(bridge_dir: Path) -> None:
    for path in (bridge_dir, bridge_dir / "requests", bridge_dir / "responses"):
        if path.is_symlink():
            raise ValueError(f"tool bridge path must not be a symlink: {path}")
        path.mkdir(parents=True, exist_ok=True)
        try:
            path.chmod(0o700)
        except OSError:
            pass


def start_tool_bridge(
    *,
    run_id: str,
    proc: PollableProcess,
    bridge_dir: Path,
    token: str,
) -> None:
    prepare_tool_bridge_dir(bridge_dir)
    ToolBridgeServer(
        proc=proc,
        bridge_dir=bridge_dir,
        pinned_bridge_root=bridge_dir.resolve(),
        token=token,
    ).start(run_id)


@final
class ToolBridgeServer:
    __slots__ = ("bridge_dir", "pinned_bridge_root", "proc", "token")

    def __init__(
        self,
        *,
        proc: PollableProcess,
        bridge_dir: Path,
        pinned_bridge_root: Path,
        token: str,
    ) -> None:
        self.proc = proc
        self.bridge_dir = bridge_dir
        self.pinned_bridge_root = pinned_bridge_root
        self.token = token

    def start(self, run_id: str) -> None:
        threading.Thread(
            target=self.run,
            name=f"atlas-orchestrator-tool-bridge-{run_id[:8]}",
            daemon=True,
        ).start()

    def run(self) -> None:
        requests_dir = self.bridge_dir / "requests"
        while True:
            if self.bridge_dir.is_symlink() or self.bridge_dir.resolve() != self.pinned_bridge_root:
                return
            if requests_dir.is_symlink() or requests_dir.resolve() != self.pinned_bridge_root / "requests":
                return
            pending = sorted(requests_dir.glob("*.json"))
            for request_path in pending:
                self.handle_request(request_path)
            try:
                alive = self.proc.poll() is None
            except Exception:
                alive = False
            if not alive and not list(requests_dir.glob("*.json")):
                return
            time.sleep(0.05)

    def handle_request(self, request_path: Path) -> None:
        if self.bridge_dir.is_symlink() or self.bridge_dir.resolve() != self.pinned_bridge_root:
            return
        request_id = safe_bridge_id(request_path.stem)
        responses_dir = self.bridge_dir / "responses"
        if responses_dir.is_symlink():
            self._write_symlink_response_error(request_path, responses_dir, request_id)
            return
        try:
            if request_path.is_symlink():
                raise ValueError("bridge request must not be a symlink")
            self._assert_responses_dir_safe(responses_dir)
            data = self._read_request_object(request_path)
            request_id = safe_bridge_id(data.get("id"), fallback=request_path.stem)
            if request_id != str(data.get("id") or "").strip():
                raise ValueError("bridge request id is not safe")
            if str(data.get("token") or "") != self.token:
                raise ValueError("bridge request token mismatch")
            tool = str(data.get("tool") or "")
            kwargs_raw = data.get("kwargs")
            kwargs: dict[str, Any] = dict(kwargs_raw) if isinstance(kwargs_raw, dict) else {}
            result, summary = self._call_parent_tool(tool, kwargs)
            payload = {
                "ok": bool(isinstance(result, dict) and result.get("ok", True)),
                "id": request_id,
                "tool": tool,
                "result": result,
                "summary": summary,
            }
        except Exception as exc:
            payload = {
                "ok": False,
                "id": request_id,
                "tool": "",
                "result": {"ok": False, "error": f"{type(exc).__name__}: {exc}"},
                "summary": f"{type(exc).__name__}: {exc}",
            }
        self._write_response(request_path, responses_dir, request_id, payload)

    def _write_symlink_response_error(
        self,
        request_path: Path,
        responses_dir: Path,
        request_id: str,
    ) -> None:
        try:
            responses_dir.unlink()
            responses_dir.mkdir(parents=True, exist_ok=True)
            responses_dir.chmod(0o700)
        except OSError:
            return
        payload = {
            "ok": False,
            "id": request_id,
            "tool": "",
            "result": {"ok": False, "error": "ValueError: bridge responses must not be a symlink"},
            "summary": "ValueError: bridge responses must not be a symlink",
        }
        write_json_atomic(responses_dir / f"{request_id}.json", payload)
        try:
            request_path.unlink()
        except OSError:
            pass

    def _assert_responses_dir_safe(self, responses_dir: Path) -> None:
        if responses_dir.is_symlink():
            raise ValueError("bridge responses must not be a symlink")
        if responses_dir.exists() and not responses_dir.is_dir():
            raise ValueError("bridge responses must be a directory")
        response_root = responses_dir.resolve()
        bridge_root = self.bridge_dir.resolve()
        if response_root != bridge_root:
            response_root.relative_to(bridge_root)

    def _read_request_object(self, request_path: Path) -> dict[str, Any]:
        data: Any = None
        for attempt in range(3):
            try:
                data = json.loads(request_path.read_text(encoding="utf-8", errors="replace"))
                break
            except json.JSONDecodeError:
                if attempt == 2:
                    raise
                time.sleep(0.02)
        if not isinstance(data, dict):
            raise ValueError("bridge request must be an object")
        return data

    def _write_response(
        self,
        request_path: Path,
        responses_dir: Path,
        request_id: str,
        payload: dict[str, Any],
    ) -> None:
        responses_dir.mkdir(parents=True, exist_ok=True)
        try:
            responses_dir.chmod(0o700)
        except OSError:
            pass
        response_path = responses_dir / f"{request_id}.json"
        try:
            response_root = responses_dir.resolve()
            if response_root != self.pinned_bridge_root:
                response_root.relative_to(self.pinned_bridge_root)
            resolved_response = response_path.resolve()
            if response_root not in resolved_response.parents:
                response_path = responses_dir / "invalid.json"
        except Exception:
            return
        write_json_atomic(response_path, payload)
        try:
            request_path.unlink()
        except OSError:
            pass

    def _call_parent_tool(self, tool: str, kwargs: dict[str, Any]) -> tuple[dict[str, Any], str]:
        if tool == "dispatch_workflow":
            return _call_core_tool_bridge(
                callback_name="_dispatch_workflow_callback",
                unavailable="parent dispatch_workflow bridge unavailable",
                kwargs=kwargs,
            )
        if tool == "read_pipeline_state":
            return _call_core_tool_bridge(
                callback_name="_read_pipeline_state_callback",
                unavailable="parent read_pipeline_state bridge unavailable",
                kwargs=kwargs,
            )
        if tool == "wait_job":
            from src.orchestrator import tools as orch_tools

            result, summary = orch_tools.wait_job(str(kwargs.get("job_id") or ""))
            return result, summary
        return {"ok": False, "error": f"unknown bridge tool {tool!r}"}, "unknown bridge tool"


def _call_core_tool_bridge(
    *,
    callback_name: str,
    unavailable: str,
    kwargs: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    try:
        core_tools = importlib.import_module("core.tools")
        bridge = getattr(core_tools, callback_name, None)
    except Exception:
        bridge = None
    if not callable(bridge):
        return {"ok": False, "error": unavailable}, "bridge unavailable"
    result = bridge(**kwargs)
    if not isinstance(result, dict):
        return {"ok": False, "raw": str(result)}, str(result)
    return result, json.dumps(result, ensure_ascii=False, sort_keys=True)
