from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Optional

from src.orchestrator.ipc_tool_bridge import write_json_atomic
from src.orchestrator.ipc_tool_bridge_server import (
    prepare_tool_bridge_dir,
    start_tool_bridge,
)
from src.orchestrator.runtime_types import SubmitOutcome
from src.orchestrator.supervisor_manifest import (
    supervisor_job_metadata,
    supervisor_process_env,
    supervisor_request_payload,
)
from src.orchestrator.supervisor_wake import (
    append_user_message_wake,
    supervisor_control_dir,
)
from src.orchestrator.supervisor_watch import watch_supervisor_job


ProcessFactory = Callable[..., Any]


def _prepare_supervisor_paths(paths: dict[str, Path], project_root: Path) -> None:
    root = project_root.resolve()
    control = paths["control"]
    for directory in (root / ".session", root / ".session" / "orchestrators-ipc", control):
        if directory.is_symlink():
            raise ValueError(f"supervisor IPC path must not be a symlink: {directory}")
        directory.mkdir(parents=True, exist_ok=True)
        resolved = directory.resolve()
        if resolved != root and root not in resolved.parents:
            raise ValueError(f"supervisor IPC path escapes project root: {directory}")
        try:
            directory.chmod(0o700)
        except OSError:
            pass
    control_root = control.resolve()
    for name in ("request", "response", "wake", "cancel", "log", "bridge"):
        path = paths[name]
        if path.is_symlink():
            raise ValueError(f"supervisor IPC file must not be a symlink: {path}")
        if path.parent.resolve() != control_root:
            raise ValueError(f"supervisor IPC file escapes control directory: {path}")


def _open_supervisor_log(path: Path) -> Any:
    flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    return os.fdopen(fd, "ab")


class OrchestratorSupervisorRuntime:
    def __init__(
        self,
        db: Any,
        *,
        project_root: Path | str,
        source_root: Path | str | None = None,
        process_factory: Optional[ProcessFactory] = None,
        register_job: Optional[Callable[[str, dict[str, Any]], None]] = None,
        register_process: Optional[Callable[[str, Any], None]] = None,
        update_job: Optional[Callable[[str, dict[str, Any]], None]] = None,
        unregister_process: Optional[Callable[[str], None]] = None,
        start_watcher: bool = True,
    ) -> None:
        self._db = db
        self._project_root = Path(project_root).resolve()
        self._source_root = Path(source_root).resolve() if source_root else Path(__file__).resolve().parents[2]
        self._process_factory = process_factory or subprocess.Popen
        self._register_job = register_job or (lambda _job_id, _job: None)
        self._register_process = register_process or (lambda _run_id, _proc: None)
        self._update_job = update_job or (lambda _job_id, _updates: None)
        self._unregister_process = unregister_process or (lambda _run_id: None)
        self._start_watcher = start_watcher
        self._lock = threading.Lock()
        self._active_by_key: dict[tuple[str, str], str] = {}

    def shutdown(self, wait: bool = False) -> None:
        close = getattr(self._db, "close", None)
        if callable(close):
            close()

    def notify_job_complete(self, job_id: str, status: str = "") -> int:
        return 0

    def submit_or_attach(
        self,
        *,
        user_id: str,
        ip_id: str,
        ip_name: str,
        workspace_id: str = "",
        session_id: str = "",
        chat_message_id: str = "",
        message_text: str = "",
        model: str = "",
        reasoning_effort: str = "",
    ) -> SubmitOutcome:
        key = (str(user_id), str(ip_id))
        with self._lock:
            run_id = self._active_by_key.get(key)
            if run_id and self._run_is_active(run_id):
                return self._append_user_reply(run_id, message_text, chat_message_id)

            existing = self._db.find_active_run_for(user_id=user_id, ip_id=ip_id)
            if existing is not None:
                run_id = str(existing["id"])
                self._active_by_key[key] = run_id
                return self._append_user_reply(run_id, message_text, chat_message_id)

            run = self._db.create_orchestrator_run(
                user_id=user_id,
                ip_id=ip_id,
                workspace_id=workspace_id,
                session_id=session_id,
                chat_message_id=chat_message_id,
                model=model,
                reasoning_effort=reasoning_effort,
                status="running",
            )
            run_id = str(run["id"])
            self._active_by_key[key] = run_id
            self._spawn_supervisor(
                run_id=run_id,
                user_id=user_id,
                ip_id=ip_id,
                ip_name=ip_name,
                workspace_id=workspace_id,
                session_id=session_id,
                chat_message_id=chat_message_id,
                message_text=message_text,
                model=model,
                reasoning_effort=reasoning_effort,
            )
            return SubmitOutcome(run_id=run_id, status="started")

    def _run_is_active(self, run_id: str) -> bool:
        run = self._db.get_orchestrator_run(run_id)
        status = str((run or {}).get("status") or "")
        return status in {"running", "paused", "yielded"}

    def _append_user_reply(
        self, run_id: str, message_text: str, chat_message_id: str
    ) -> SubmitOutcome:
        paths = self._paths(run_id)
        _prepare_supervisor_paths(paths, self._project_root)
        self._db.append_orchestrator_step(
            run_id,
            tool_name="user_reply",
            decision={"chat_message_id": chat_message_id},
            user_reply=message_text,
            verdict="user_input",
        )
        append_user_message_wake(
            paths["wake"],
            message=message_text,
            chat_message_id=chat_message_id,
        )
        return SubmitOutcome(run_id=run_id, status="appended")

    def _spawn_supervisor(self, **data: str) -> None:
        run_id = data["run_id"]
        paths = self._paths(run_id)
        _prepare_supervisor_paths(paths, self._project_root)
        request = supervisor_request_payload(
            db=self._db,
            project_root=self._project_root,
            source_root=self._source_root,
            paths=paths,
            data=data,
        )
        prepare_tool_bridge_dir(paths["bridge"])
        write_json_atomic(paths["request"], request)
        cmd = [
            sys.executable,
            "-m",
            "src.atlas_orchestrator_supervisor_ipc",
            "--request",
            str(paths["request"]),
            "--response",
            str(paths["response"]),
            "--run-id",
            run_id,
        ]
        log_fh = _open_supervisor_log(paths["log"])
        try:
            proc = self._process_factory(
                cmd,
                cwd=str(self._project_root),
                env=supervisor_process_env(
                    project_root=self._project_root,
                    source_root=self._source_root,
                    ip_name=str(data.get("ip_name") or ""),
                ),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
            )
        finally:
            log_fh.close()
        process_key = f"ipc-orch-{run_id}"
        job_id = f"orch-{run_id}"
        job = supervisor_job_metadata(
            project_root=self._project_root,
            job_id=job_id,
            process_key=process_key,
            paths=paths,
            proc=proc,
            data=data,
        )
        self._register_job(job_id, job)
        self._register_process(process_key, proc)
        start_tool_bridge(
            run_id=run_id,
            proc=proc,
            bridge_dir=paths["bridge"],
            token=str(request.get("tool_bridge_token") or ""),
        )
        if self._start_watcher:
            threading.Thread(
                target=watch_supervisor_job,
                kwargs={
                    "db": self._db,
                    "job_id": job_id,
                    "process_key": process_key,
                    "run_id": run_id,
                    "response_path": paths["response"],
                    "proc": proc,
                    "update_job": self._update_job,
                    "unregister_process": self._unregister_process,
                },
                name=f"atlas-orchestrator-supervisor-{run_id[:8]}",
                daemon=True,
            ).start()

    def _paths(self, run_id: str) -> dict[str, Path]:
        control = supervisor_control_dir(self._project_root, run_id)
        return {
            "control": control,
            "request": control / "request.json",
            "response": control / "response.json",
            "wake": control / "wake.jsonl",
            "cancel": control / "cancel.json",
            "log": control / "supervisor.log",
            "bridge": control / "tool-bridge",
        }
