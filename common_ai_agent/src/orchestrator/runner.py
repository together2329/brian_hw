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
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set, Tuple

from src.orchestrator.loop import OrchestratorContext, RunOutcome
from src.orchestrator.runtime_types import SubmitOutcome


_MAX_WORKERS = 4


@dataclass
class Waker:
    """Per-run interrupt + timer source.

    The loop calls ``wait()`` after the LLM has issued ``yield_run``; the
    runner sets the event when a watched job finishes, a user message
    arrives, or the optional timer fires. ``reason`` records which path
    woke the run so the LLM sees it on the next iteration.
    """

    run_id: str
    user_id: str
    ip_id: str
    job_ids: Set[str] = field(default_factory=set)
    user_message: bool = True
    after_seconds: Optional[float] = None
    event: threading.Event = field(default_factory=threading.Event)
    reason: str = ""

    def wake(self, reason: str) -> None:
        if not self.event.is_set():
            self.reason = reason
            self.event.set()

    def wait(self) -> str:
        timeout = self.after_seconds if self.after_seconds and self.after_seconds > 0 else None
        woken = self.event.wait(timeout=timeout)
        if not woken:
            self.reason = self.reason or "timer"
        return self.reason or "unknown"


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
        self._wakers: Dict[str, Waker] = {}
        self._loop_factory = loop_factory or _build_loop

    def shutdown(self, wait: bool = False) -> None:
        self._executor.shutdown(wait=wait)

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
                    waker = self._wakers.get(run_id)
                    if waker is not None and waker.user_message:
                        waker.wake("user_message")
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
                self._db.update_orchestrator_run(run_id, status="running")
                future = self._executor.submit(
                    self._run_loop,
                    run_id=run_id,
                    user_id=user_id,
                    ip_id=ip_id,
                    ip_name=ip_name,
                    workspace_id=workspace_id or str(existing.get("workspace_id") or ""),
                    session_id=session_id,
                    initial_user_message=message_text,
                )
                self._active[key] = (run_id, future)
                return SubmitOutcome(run_id=run_id, status="resumed")

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
            run_id = run["id"]
            future = self._executor.submit(
                self._run_loop,
                run_id=run_id,
                user_id=user_id,
                ip_id=ip_id,
                ip_name=ip_name,
                workspace_id=workspace_id,
                session_id=session_id,
                initial_user_message=message_text,
            )
            self._active[key] = (run_id, future)
            return SubmitOutcome(run_id=run_id, status="started")

    # ------------------------------------------------------------------
    # Waker registry (interrupt-style wake on job complete / user msg)
    # ------------------------------------------------------------------

    def register_waker(
        self,
        run_id: str,
        user_id: str,
        ip_id: str,
        job_ids: Optional[Set[str]] = None,
        user_message: bool = True,
        after_seconds: Optional[float] = None,
    ) -> Waker:
        waker = Waker(
            run_id=run_id,
            user_id=user_id,
            ip_id=ip_id,
            job_ids=set(job_ids or ()),
            user_message=user_message,
            after_seconds=after_seconds,
        )
        with self._lock:
            self._wakers[run_id] = waker
        return waker

    def unregister_waker(self, run_id: str) -> None:
        with self._lock:
            self._wakers.pop(run_id, None)

    def notify_job_complete(self, job_id: str, status: str = "") -> int:
        """Wake any waker watching this job_id. Returns count notified."""
        notified = 0
        with self._lock:
            wakers = list(self._wakers.values())
        for w in wakers:
            if job_id in w.job_ids:
                w.wake(f"job_complete:{job_id}:{status}".rstrip(":"))
                notified += 1
        return notified

    def _run_loop(
        self,
        *,
        run_id: str,
        user_id: str,
        ip_id: str,
        ip_name: str,
        workspace_id: str,
        session_id: str,
        initial_user_message: str,
    ) -> RunOutcome:
        ctx = OrchestratorContext(
            run_id=run_id,
            user_id=user_id,
            ip_id=ip_id,
            ip_name=ip_name,
            workspace_id=workspace_id,
            session_id=session_id,
            runner=self,
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


def _build_loop(db, ctx, initial_user_message: str):
    """Production factory — instantiates the react_loop-backed orchestrator.

    Compression / TodoTracker sync / per-IP context injection / streaming
    UI / ESC interrupt are all inherited from
    ``core/react_loop.py::run_react_agent_impl`` via
    ``OrchestratorReactLoop``. The Phase-3 ``OrchestratorLoop`` scaffold
    that this factory previously instantiated has been deleted; parity
    contracts are asserted by ``tests/test_orchestrator_react_loop_parity.py``.
    """
    from src.orchestrator.react_bridge import OrchestratorReactLoop

    return OrchestratorReactLoop(db, ctx, initial_user_message=initial_user_message)


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


def notify_job_complete(job_id: str, status: str = "") -> int:
    """Module-level interrupt hook.

    Called from the job-completion path (``_advance_pipeline_from`` in
    ``src/atlas_api_jobs.py``) so the orchestrator loop can sleep on a Waker
    and resume the moment a watched worker finishes — interrupt-style — rather
    than burning LLM iterations polling.
    """
    runner = _RUNNER
    if runner is None:
        return 0
    try:
        return runner.notify_job_complete(job_id, status)
    except Exception:
        return 0
