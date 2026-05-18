"""Background runner for the orchestrator loop.

Owns the ``(user_id, ip_id) -> Future`` single-flight registry so the HTTP
route at ``/api/pipeline/orchestrator/chat`` can return immediately while the
LLM loop runs in a thread.

Concurrent chats for the same ``(user_id, ip_id)`` do NOT spawn a parallel
run; instead a step row with ``user_reply`` is appended to the active run
and a condition variable wakes the loop (used when the run is paused on
``ask_user``).
"""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from src.orchestrator.loop import OrchestratorContext, OrchestratorLoop, RunOutcome


_MAX_WORKERS = 4


@dataclass
class SubmitOutcome:
    run_id: str
    status: str  # "started" | "appended" | "resumed"


class OrchestratorRunner:
    """Manages a thread pool + single-flight (user_id, ip_id) -> run mapping."""

    def __init__(
        self,
        db: Any,
        max_workers: int = _MAX_WORKERS,
        loop_factory=None,
    ) -> None:
        self._db = db
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="orchestrator"
        )
        self._active: Dict[Tuple[str, str], Tuple[str, Future]] = {}
        self._loop_factory = loop_factory or _build_loop

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)

    def submit_or_attach(
        self,
        *,
        user_id: str,
        ip_id: str,
        ip_name: str,
        session_id: str = "",
        chat_message_id: str = "",
        message_text: str = "",
        model: str = "",
        reasoning_effort: str = "",
    ) -> SubmitOutcome:
        key = (user_id, ip_id)
        with self._lock:
            entry = self._active.get(key)
            if entry is not None:
                run_id, future = entry
                if not future.done():
                    self._db.append_orchestrator_step(
                        run_id,
                        tool_name="user_reply",
                        decision={"chat_message_id": chat_message_id},
                        user_reply=message_text,
                        verdict="user_input",
                    )
                    return SubmitOutcome(run_id=run_id, status="appended")
                # Future already done — fall through and start a fresh run.
                self._active.pop(key, None)

            existing = self._db.find_active_run_for(user_id=user_id, ip_id=ip_id)
            if existing is not None:
                # An active row exists but no in-process future (process restart).
                run_id = existing["id"]
                self._db.append_orchestrator_step(
                    run_id,
                    tool_name="user_reply",
                    decision={"chat_message_id": chat_message_id},
                    user_reply=message_text,
                    verdict="user_input",
                )
                future = self._executor.submit(
                    self._run_loop,
                    run_id=run_id,
                    user_id=user_id,
                    ip_id=ip_id,
                    ip_name=ip_name,
                    session_id=session_id,
                    initial_user_message="",
                )
                self._active[key] = (run_id, future)
                return SubmitOutcome(run_id=run_id, status="resumed")

            run = self._db.create_orchestrator_run(
                user_id=user_id,
                ip_id=ip_id,
                session_id=session_id,
                chat_message_id=chat_message_id,
                model=model,
                reasoning_effort=reasoning_effort,
                status="running",
            )
            run_id = run["id"]
            future = self._executor.submit(
                self._run_loop,
                run_id=run_id,
                user_id=user_id,
                ip_id=ip_id,
                ip_name=ip_name,
                session_id=session_id,
                initial_user_message=message_text,
            )
            self._active[key] = (run_id, future)
            return SubmitOutcome(run_id=run_id, status="started")

    def _run_loop(
        self,
        *,
        run_id: str,
        user_id: str,
        ip_id: str,
        ip_name: str,
        session_id: str,
        initial_user_message: str,
    ) -> RunOutcome:
        ctx = OrchestratorContext(
            run_id=run_id,
            user_id=user_id,
            ip_id=ip_id,
            ip_name=ip_name,
            session_id=session_id,
        )
        loop = self._loop_factory(self._db, ctx, initial_user_message)
        try:
            return loop.run()
        finally:
            with self._lock:
                entry = self._active.get((user_id, ip_id))
                if entry is not None and entry[0] == run_id:
                    self._active.pop((user_id, ip_id), None)

    # Test hook: drain to completion deterministically.
    def wait_for(self, user_id: str, ip_id: str, timeout: Optional[float] = None):
        with self._lock:
            entry = self._active.get((user_id, ip_id))
        if entry is None:
            return None
        return entry[1].result(timeout=timeout)


def _build_loop(db, ctx, initial_user_message: str) -> OrchestratorLoop:
    return OrchestratorLoop(db, ctx, initial_user_message=initial_user_message)


# Module-level singleton — the FastAPI route shares one runner across requests.
_RUNNER_LOCK = threading.Lock()
_RUNNER: Optional[OrchestratorRunner] = None
_RUNNER_DB_PATH: Optional[str] = None


def get_runner(db_path: str) -> OrchestratorRunner:
    """Return the process-wide runner, initialising it on first call.

    Subsequent calls with a different ``db_path`` keep the original runner —
    the DB path is locked at first use to keep the loop's persistent
    ``AtlasDB`` handle stable.
    """
    global _RUNNER, _RUNNER_DB_PATH
    with _RUNNER_LOCK:
        if _RUNNER is None:
            from core.atlas_db import AtlasDB

            _RUNNER_DB_PATH = db_path
            _RUNNER = OrchestratorRunner(AtlasDB(db_path))
        return _RUNNER


def set_runner_for_test(runner: Optional[OrchestratorRunner]) -> None:
    """Test seam: swap the singleton (pass None to clear)."""
    global _RUNNER, _RUNNER_DB_PATH
    with _RUNNER_LOCK:
        _RUNNER = runner
        _RUNNER_DB_PATH = None
