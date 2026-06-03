from __future__ import annotations

import importlib
import os
import threading
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Protocol

from src.orchestrator.runtime_types import SubmitOutcome


class OrchestratorRuntime(Protocol):
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
        ...

    def notify_job_complete(self, job_id: str, status: str = "") -> int:
        ...

    def shutdown(self, wait: bool = False) -> None:
        ...


_IPC_LOCK = threading.Lock()
_IPC_RUNTIMES: dict[tuple[str, str], OrchestratorRuntime] = {}


def orchestrator_transport(env: Optional[Mapping[str, str]] = None) -> str:
    values = env or os.environ
    raw = str(values.get("ATLAS_ORCHESTRATOR_TRANSPORT") or "").strip().lower()
    raw = raw.replace("_", "-")
    if raw in {"thread", "threads", "legacy", "legacy-thread"}:
        return "thread"
    if raw in {"ipc", "process", "subprocess", "portless"}:
        return "ipc"
    exec_mode = str(values.get("ATLAS_EXEC_MODE") or "").strip().lower()
    if exec_mode == "orchestrator":
        return "ipc"
    return "thread"


def get_orchestrator_runtime(
    db_path: str,
    *,
    project_root: Path | str | None = None,
    source_root: Path | str | None = None,
    process_factory: Optional[Callable[..., Any]] = None,
    register_job: Optional[Callable[[str, dict[str, Any]], None]] = None,
    register_process: Optional[Callable[[str, Any], None]] = None,
    update_job: Optional[Callable[[str, dict[str, Any]], None]] = None,
    unregister_process: Optional[Callable[[str], None]] = None,
    start_watcher: bool = True,
) -> OrchestratorRuntime:
    if orchestrator_transport() == "thread":
        from src.orchestrator.runner import get_runner

        return get_runner(db_path)

    root = Path(project_root or os.environ.get("ATLAS_PROJECT_ROOT") or ".").resolve()
    key = (str(Path(db_path).resolve()), str(root))
    with _IPC_LOCK:
        runtime = _IPC_RUNTIMES.get(key)
        if runtime is None:
            from src.orchestrator.supervisor_runtime import OrchestratorSupervisorRuntime

            AtlasDB = importlib.import_module("core.atlas_db").AtlasDB
            runtime = OrchestratorSupervisorRuntime(
                AtlasDB(db_path),
                project_root=root,
                source_root=Path(source_root).resolve() if source_root else None,
                process_factory=process_factory,
                register_job=register_job,
                register_process=register_process,
                update_job=update_job,
                unregister_process=unregister_process,
                start_watcher=start_watcher,
            )
            _IPC_RUNTIMES[key] = runtime
        return runtime


def shutdown_ipc_runtimes(wait: bool = False) -> None:
    with _IPC_LOCK:
        runtimes = list(_IPC_RUNTIMES.values())
        _IPC_RUNTIMES.clear()
    for runtime in runtimes:
        runtime.shutdown(wait=wait)
