"""Reusable deterministic SessionProcessManager double (Wave-3 H11).

A drop-in for :class:`core.session_process_manager.SessionProcessManager` that
keeps ALL state in memory and launches NO subprocesses, so 100-owner capacity /
owner-slot logic runs instantly and deterministically. It implements:

* the surface the bridge (``core.atlas_multiuser._MultiUserBridge``) calls today:
  ``is_alive``, ``latest_output_id``, ``spawn``, ``send_input``, ``get_pid``,
  ``cleanup_zombies``, ``list_active``, ``poll_output``, ``kill``, ``stop_all``;
* the Task-4 admission/lifecycle contract: ``spawn_result`` (capacity source of
  truth), ``terminate_session`` (graceful->kill), ``list_active_metadata``.

The clock is injectable so idle-age / TTL logic is testable without sleeping.
``spawn`` stays a thin ``spawn_result(...).ok`` wrapper, mirroring the real
manager's bool/SpawnResult split (plan 'Result Objects').
"""

from __future__ import annotations

import itertools
import threading
from typing import Any, Callable, Dict, List, Optional, Set


class ManualClock:
    """A monotonic clock the test advances by hand (no real time passes)."""

    def __init__(self, start: float = 1_000.0) -> None:
        self._now = float(start)
        self._lock = threading.Lock()

    def __call__(self) -> float:
        with self._lock:
            return self._now

    def advance(self, seconds: float) -> float:
        with self._lock:
            self._now += float(seconds)
            return self._now


def _owner_of(session_id: str) -> str:
    parts = [p for p in str(session_id or "").strip("/").split("/") if p]
    return parts[0] if parts else "default"


class FakeProcessManager:
    """In-memory, subprocess-free SessionProcessManager double.

    Args:
        clock: zero-arg callable returning a monotonic float; defaults to a
            :class:`ManualClock` the test can ``advance(...)``.
        fail_terminate_for: session_ids whose ``terminate_session`` reports
            ``False`` (drives the Task-3 ``termination_failed`` branch).
        busy_sessions: session_ids treated as having a running prompt so
            ``terminate_session`` exercises the stop-ack budget instead of the
            idle straight-to-kill path (Wave-3 H4).
    """

    def __init__(
        self,
        clock: Optional[Callable[[], float]] = None,
        *,
        fail_terminate_for: Optional[Set[str]] = None,
        busy_sessions: Optional[Set[str]] = None,
    ) -> None:
        self._clock = clock or ManualClock()
        self._fail_terminate = set(fail_terminate_for or set())
        self._busy = set(busy_sessions or set())
        self._procs: Dict[str, Dict[str, Any]] = {}
        self._reserved_sessions: Set[str] = set()
        self._lock = threading.RLock()
        self._pid_seq = itertools.count(10_000)
        # Observable call logs for assertions.
        self.spawned: List[str] = []
        self.killed: List[str] = []
        self.terminated: List[tuple[str, str]] = []  # (session_id, reason)
        self.sent: List[tuple[str, str, Optional[Dict[str, Any]]]] = []

    # -- internal helpers --------------------------------------------------

    def _alive_ids(self) -> List[str]:
        return [sid for sid, e in self._procs.items() if e.get("alive")]

    def _admission_count(self, ignore_session_id: str = "") -> int:
        count = len(self._alive_ids())
        for session_id in self._reserved_sessions:
            if session_id == ignore_session_id:
                continue
            entry = self._procs.get(session_id)
            if entry is not None and entry.get("alive"):
                continue
            count += 1
        return count

    def _mark_running(self, session_id: str, running: bool) -> None:
        with self._lock:
            e = self._procs.get(session_id)
            if e is not None:
                e["running"] = running

    def set_busy(self, session_id: str, busy: bool = True) -> None:
        """Test hook: toggle whether a worker has a running turn (H4)."""
        with self._lock:
            if busy:
                self._busy.add(session_id)
            else:
                self._busy.discard(session_id)
            e = self._procs.get(session_id)
            if e is not None:
                e["running"] = busy

    # -- current bridge surface -------------------------------------------

    def is_alive(self, session_id: str) -> bool:
        with self._lock:
            e = self._procs.get(session_id)
            return bool(e and e.get("alive"))

    def latest_output_id(self, session_id: str) -> Optional[str]:
        return None

    def get_pid(self, session_id: str) -> Optional[int]:
        with self._lock:
            e = self._procs.get(session_id)
            return e.get("pid") if e else None

    def list_active(self) -> List[str]:
        with self._lock:
            return sorted(self._alive_ids())

    def cleanup_zombies(self) -> List[str]:
        with self._lock:
            dead = [sid for sid, e in self._procs.items() if not e.get("alive")]
            for sid in dead:
                self._procs.pop(sid, None)
            return dead

    def poll_output(self, session_id: str, since_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return []

    def send_input(
        self,
        session_id: str,
        msg_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        with self._lock:
            e = self._procs.get(session_id)
            if not (e and e.get("alive")):
                return None
            e["last_input_at"] = self._clock()
            if msg_type == "prompt":
                e["running"] = True
                self._busy.add(session_id)
            elif msg_type == "stop":
                e["running"] = False
                self._busy.discard(session_id)
            self.sent.append((session_id, msg_type, payload))
            return f"fake-msg-{len(self.sent)}"

    def spawn(self, session_id: str, db_path: Optional[str] = None) -> bool:
        # Mirror the real bool/SpawnResult split: bool wrapper over spawn_result.
        return bool(self.spawn_result(session_id, db_path=db_path).ok)

    def kill(self, session_id: str) -> bool:
        with self._lock:
            self._procs.pop(session_id, None)
            self._busy.discard(session_id)
        self.killed.append(session_id)
        return True

    def stop_all(self) -> None:
        with self._lock:
            ids = list(self._procs.keys())
            self._procs.clear()
            self._reserved_sessions.clear()
            self._busy.clear()
        self.killed.extend(ids)

    # -- Task-4 admission / lifecycle contract ----------------------------

    def spawn_result(
        self,
        session_id: str,
        db_path: Optional[str] = None,
        policy: Any = None,
        *,
        replacing: Optional[str] = None,
        reserve: bool = False,
    ):
        """Admission source of truth. Cap is net-new only (H2/H3/H9).

        Order (H9): is_alive short-circuit (status='ready') + dead cleanup
        BEFORE the cap check; the cap is evaluated only on the branch that will
        actually create a new entry. ``reserve=True`` (a same-owner-slot
        replacement) skips the cap entirely so a switch is never cap-refused.
        """
        try:
            from core.session_process_manager import SpawnResult  # Task 4 owns it
        except Exception as exc:  # pragma: no cover - explicit dependency signal
            raise ImportError(
                "FakeProcessManager.spawn_result needs SpawnResult from "
                "core.session_process_manager (Task 4). Build Task 4 first."
            ) from exc
        owner = _owner_of(session_id)
        with self._lock:
            has_reservation = session_id in self._reserved_sessions
            e = self._procs.get(session_id)
            if e is not None and e.get("alive"):
                self._reserved_sessions.discard(session_id)
                return SpawnResult(
                    ok=True, status="ready", reason="", session_id=session_id,
                    owner=owner, pid=e["pid"], active_count=len(self._alive_ids()),
                    max_active=getattr(policy, "max_active", 0),
                )
            if e is not None:
                self._procs.pop(session_id, None)  # dead entry cleanup
            active_count = self._admission_count(ignore_session_id=session_id)
            if (
                not has_reservation
                and not reserve
                and policy is not None
                and policy.cap_exceeded(active_count)
            ):
                return SpawnResult(
                    ok=False, status="capacity_wait", reason="max_active",
                    session_id=session_id, owner=owner, pid=None,
                    active_count=active_count,
                    max_active=getattr(policy, "max_active", 0),
                )
            pid = next(self._pid_seq)
            now = self._clock()
            self._procs[session_id] = {
                "pid": pid, "owner": owner, "alive": True, "running": False,
                "started_at": now, "last_input_at": now, "last_output_at": now,
                "state": "ready",
            }
            self._reserved_sessions.discard(session_id)
            self.spawned.append(session_id)
            return SpawnResult(
                ok=True, status="started", reason="", session_id=session_id,
                owner=owner, pid=pid, active_count=len(self._alive_ids()),
                max_active=getattr(policy, "max_active", 0),
            )

    def terminate_and_reserve_slot(
        self,
        session_id: str,
        new_session_id: str,
        reason: str = "",
        stop_timeout_sec: float = 0.0,
        kill_grace_sec: float = 0.0,
        **kwargs: Any,
    ) -> bool:
        with self._lock:
            self._reserved_sessions.add(new_session_id)
        try:
            ok = self.terminate_session(
                session_id,
                reason=reason,
                stop_timeout_sec=stop_timeout_sec,
                kill_grace_sec=kill_grace_sec,
                **kwargs,
            )
        except Exception:
            with self._lock:
                self._reserved_sessions.discard(new_session_id)
            return False
        if ok:
            return True
        with self._lock:
            self._reserved_sessions.discard(new_session_id)
        return False

    def release_reserved_slot(self, session_id: str) -> None:
        with self._lock:
            self._reserved_sessions.discard(session_id)

    def terminate_session(
        self,
        session_id: str,
        reason: str = "",
        stop_timeout_sec: float = 0.0,
        kill_grace_sec: float = 0.0,
        **kwargs: Any,
    ) -> bool:
        """Graceful stop (busy only, H4) -> terminate -> kill, all in-memory.

        Returns False for sessions in ``fail_terminate_for`` so the bridge's
        Task-3 ``termination_failed`` branch can be exercised. The double does
        not sleep; ``stop_timeout_sec``/``kill_grace_sec`` are recorded only.
        ``**kwargs`` tolerates the real manager's keyword-only extras
        (graceful/has_running_prompt/worker_epoch) so the bridge call signature
        is interchangeable.
        """
        if session_id in self._fail_terminate:
            self.terminated.append((session_id, reason))
            return False
        with self._lock:
            self._procs.pop(session_id, None)
            self._reserved_sessions.discard(session_id)
            self._busy.discard(session_id)
        self.terminated.append((session_id, reason))
        return True

    def list_active_metadata(self, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Owner/session/state rows for the Task-7 status endpoint."""
        ref = self._clock() if now is None else now
        with self._lock:
            rows: List[Dict[str, Any]] = []
            for sid, e in self._procs.items():
                if not e.get("alive"):
                    continue
                rows.append({
                    "session_id": sid,
                    "owner": e["owner"],
                    "pid": e["pid"],
                    "state": e.get("state", "ready"),
                    "alive": True,
                    "running": bool(e.get("running")),
                    "idle_age_sec": max(0.0, ref - float(e.get("last_input_at", ref))),
                })
            return rows
