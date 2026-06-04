from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

from src.orchestrator.runtime_types import SubmitOutcome
from src.orchestrator.supervisor_wake import (
    append_user_message_wake,
    supervisor_control_dir,
)
from src.orchestrator.supervisor_watch import watch_supervisor_job


ProcessFactory = Callable[..., Any]


def _resolve_ip_workflow_root(project_root: Path, source_root: Path, ip_name: str = "") -> Path:
    resolver = importlib.import_module("core.atlas_context").resolve_ip_workflow_root
    return resolver(project_root, source_root, ip_name)


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
        self._db.append_orchestrator_step(
            run_id,
            tool_name="user_reply",
            decision={"chat_message_id": chat_message_id},
            user_reply=message_text,
            verdict="user_input",
        )
        append_user_message_wake(
            supervisor_control_dir(self._project_root, run_id) / "wake.jsonl",
            message=message_text,
            chat_message_id=chat_message_id,
        )
        return SubmitOutcome(run_id=run_id, status="appended")

    def _spawn_supervisor(self, **data: str) -> None:
        run_id = data["run_id"]
        paths = self._paths(run_id)
        paths["control"].mkdir(parents=True, exist_ok=True)
        request = self._request_payload(paths=paths, **data)
        paths["request"].write_text(
            json.dumps(request, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
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
        log_fh = paths["log"].open("ab")
        try:
            proc = self._process_factory(
                cmd,
                cwd=str(self._project_root),
                env=self._env(ip_name=str(data.get("ip_name") or "")),
                stdout=log_fh,
                stderr=subprocess.STDOUT,
            )
        finally:
            log_fh.close()
        process_key = f"ipc-orch-{run_id}"
        job_id = f"orch-{run_id}"
        job = self._job_metadata(job_id, process_key, paths, proc, data)
        self._register_job(job_id, job)
        self._register_process(process_key, proc)
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
        }

    def _request_payload(self, *, paths: dict[str, Path], **data: str) -> dict[str, Any]:
        run_id = data["run_id"]
        return {
            "schema_version": 1,
            "kind": "orchestrator-supervisor",
            "run_id": run_id,
            "resume": False,
            "project_root": str(self._project_root),
            "source_root": str(self._source_root),
            "db_path": str(getattr(self._db, "db_path", "") or getattr(self._db, "path", "")),
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
        }

    def _env(self, ip_name: str = "") -> dict[str, str]:
        env = os.environ.copy()
        env["ATLAS_PROJECT_ROOT"] = str(self._project_root)
        env["ATLAS_SOURCE_ROOT"] = str(self._source_root)
        env["ATLAS_WORKFLOW_ROOT"] = str(
            _resolve_ip_workflow_root(self._project_root, self._source_root, ip_name)
        )
        env["ATLAS_EXEC_MODE"] = "orchestrator"
        env["ATLAS_ORCHESTRATOR_MODE"] = "1"
        env["ATLAS_WORKER_TRANSPORT"] = "ipc"
        env["ATLAS_SINGLE_MAIN_LOOP"] = "0"
        env["PYTHONPATH"] = f"{self._source_root}{os.pathsep}{env.get('PYTHONPATH', '')}".rstrip(os.pathsep)
        return env

    def _job_metadata(
        self,
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
            "project_root": str(self._project_root),
            "db_user_id": data["user_id"],
            "db_ip_id": data["ip_id"],
            "ip": data["ip_name"],
            "orchestrator_run_id": data["run_id"],
            "worker_pid": getattr(proc, "pid", ""),
            "worker_request_path": self._rel(paths["request"]),
            "worker_response_path": self._rel(paths["response"]),
            "worker_log_path": self._rel(paths["log"]),
        }

    def _rel(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self._project_root).as_posix()
        except Exception:
            return str(path)
