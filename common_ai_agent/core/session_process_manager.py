"""Process lifecycle manager for per-session Atlas agent worker processes.

Spawns, monitors, and kills subprocesses running :mod:`core.session_worker`.
Workers communicate via the SQLite session queue managed by
:class:`core.atlas_db.AtlasDB`, not through stdio pipes.

Typical usage::

    manager = SessionProcessManager()
    manager.spawn("sess_abc123")
    msg_id = manager.send_input("sess_abc123", "prompt", {"text": "hello"})
    outputs = manager.poll_output("sess_abc123")
    manager.kill("sess_abc123")

Or as a context manager::

    with SessionProcessManager() as manager:
        manager.spawn("sess_abc123")
        ...
    # stop_all() is called automatically on exit.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.atlas_db import AtlasDB


class SessionProcessManager:
    """Manages subprocess lifecycle for Atlas session worker processes.

    Each session gets its own ``python -m core.session_worker`` subprocess.
    Input/output is routed through the SQLite queue in :class:`AtlasDB`.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the process manager.

        Args:
            db_path: Path to the Atlas SQLite database. Defaults to
                ``~/.common_ai_agent/atlas.db``.
        """
        self.db_path = db_path
        self._source_root = Path(__file__).resolve().parents[1]
        self._processes: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _resolve_db_path(self, db_path: Optional[str] = None) -> str:
        """Return the concrete DB path shared by UI and worker processes."""
        raw = (
            db_path
            or self.db_path
            or os.environ.get("ATLAS_DB_PATH")
            or str(Path.home() / ".common_ai_agent" / "atlas.db")
        )
        return str(Path(os.path.expanduser(raw)).resolve())

    def _get_db(self) -> AtlasDB:
        """Return an initialized AtlasDB instance."""
        db = AtlasDB(self._resolve_db_path())
        db.init_db()
        return db

    def build_worker_env(
        self,
        session_id: str,
        db_path: Optional[str] = None,
    ) -> Dict[str, str]:
        """Build deterministic worker environment from ``owner/ip/workflow``."""
        env = os.environ.copy()
        session_key = str(session_id or "").strip().strip("/") or "default"
        parts = [part for part in session_key.split("/") if part]
        if len(parts) >= 3:
            owner, ip_name, workflow = parts[0], parts[1], parts[2]
        elif len(parts) == 2:
            owner = env.get("ATLAS_DEFAULT_SESSION_ID") or parts[0]
            ip_name, workflow = parts[0], parts[1]
        elif len(parts) == 1:
            owner = env.get("ATLAS_DEFAULT_SESSION_ID") or parts[0]
            ip_name = env.get("ATLAS_ACTIVE_IP") or "default"
            workflow = env.get("ATLAS_DEFAULT_WORKFLOW") or "default"
        else:
            owner = env.get("ATLAS_DEFAULT_SESSION_ID") or "default"
            ip_name = env.get("ATLAS_ACTIVE_IP") or "default"
            workflow = env.get("ATLAS_DEFAULT_WORKFLOW") or "default"

        effective_db = self._resolve_db_path(db_path)
        env["ATLAS_ACTIVE_SESSION"] = session_key
        env["ATLAS_DEFAULT_SESSION_ID"] = owner
        env["ATLAS_ACTIVE_IP"] = ip_name
        env["ATLAS_DEFAULT_WORKFLOW"] = workflow
        env["ACTIVE_WORKSPACE"] = workflow
        env["ATLAS_TRACE_ENABLE"] = "1"
        env["ATLAS_DB_PATH"] = effective_db
        env["ATLAS_TRACE_DB_PATH"] = effective_db
        env.setdefault("ATLAS_SOURCE_ROOT", str(self._source_root))
        env.setdefault("ATLAS_PROJECT_ROOT", str(Path.cwd()))
        python_paths = [str(self._source_root), str(self._source_root / "src")]
        existing_pythonpath = env.get("PYTHONPATH", "")
        if existing_pythonpath:
            python_paths.append(existing_pythonpath)
        env["PYTHONPATH"] = os.pathsep.join(python_paths)
        # Windows defaults to the active ANSI code page for redirected text
        # I/O unless UTF-8 mode is forced before Python starts. Worker output
        # is DB/file backed, so every child should agree on UTF-8 regardless
        # of the launching console locale.
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8:replace")
        return env

    def spawn(self, session_id: str, db_path: Optional[str] = None) -> bool:
        """Start a worker process for *session_id* if not already running.

        Args:
            session_id: The Atlas session identifier.
            db_path: Optional override for the SQLite database path.

        Returns:
            ``True`` if the worker is running (spawned or already alive).
        """
        with self._lock:
            if session_id in self._processes:
                if self.is_alive(session_id):
                    return True
                # Dead entry — clean it up before respawning.
                self._processes.pop(session_id, None)

            cmd = [
                sys.executable,
                "-m",
                "core.session_worker",
                "--session-id",
                session_id,
            ]
            effective_db = self._resolve_db_path(db_path)
            cmd.extend(["--db-path", effective_db])

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self.build_worker_env(session_id, db_path=effective_db),
                cwd=str(self._source_root),
                # Detach from parent TTY so signals/shells don't propagate.
                start_new_session=True,
            )
            self._processes[session_id] = {
                "proc": proc,
                "started_at": time.time(),
            }
            return True

    def kill(self, session_id: str) -> bool:
        """Terminate the worker process for *session_id* gracefully.

        Sends SIGTERM, waits up to 5 seconds, then sends SIGKILL if still alive.

        Args:
            session_id: The Atlas session identifier.

        Returns:
            ``True`` if the process was killed (or was not tracked).
        """
        with self._lock:
            entry = self._processes.pop(session_id, None)
            if entry is None:
                return True

            proc = entry["proc"]
            if proc.poll() is not None:
                return True

            try:
                proc.terminate()
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                    proc.wait(timeout=2)
                except Exception:
                    pass
            except Exception:
                # Process may have exited between poll and terminate.
                pass
            return True

    def is_alive(self, session_id: str) -> bool:
        """Check whether the worker process for *session_id* is still running.

        Args:
            session_id: The Atlas session identifier.

        Returns:
            ``True`` if the process is alive.
        """
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                return False
            return entry["proc"].poll() is None

    def list_active(self) -> List[str]:
        """Return a list of session IDs with active (running) worker processes.

        Automatically cleans up dead entries while scanning.
        """
        with self._lock:
            active: List[str] = []
            dead: List[str] = []
            for session_id, entry in self._processes.items():
                if entry["proc"].poll() is None:
                    active.append(session_id)
                else:
                    dead.append(session_id)
            for session_id in dead:
                self._processes.pop(session_id, None)
            return active

    def cleanup_zombies(self) -> List[str]:
        """Remove dead processes from internal tracking.

        Returns:
            List of session IDs that were cleaned up.
        """
        with self._lock:
            dead: List[str] = []
            for session_id, entry in list(self._processes.items()):
                if entry["proc"].poll() is not None:
                    dead.append(session_id)
                    self._processes.pop(session_id, None)
            return dead

    def get_pid(self, session_id: str) -> Optional[int]:
        """Return the PID of the worker process for *session_id*, or ``None``.

        Args:
            session_id: The Atlas session identifier.
        """
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                return None
            pid = entry["proc"].pid
            # pid may be None before the process fully starts.
            return pid

    def send_input(
        self,
        session_id: str,
        msg_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """Enqueue an input message for the session worker.

        Args:
            session_id: The Atlas session identifier.
            msg_type: Message type (e.g. ``"prompt"``, ``"stop"``).
            payload: Optional JSON-serializable payload dict.

        Returns:
            The message id if the session has an active process, else ``None``.
        """
        with self._lock:
            if not self.is_alive(session_id):
                return None

        db = self._get_db()
        try:
            msg_id = db.enqueue_message(session_id, "in", msg_type, payload)
            return msg_id
        finally:
            db.close()

    def poll_output(
        self,
        session_id: str,
        since_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch undelivered output messages from the session worker.

        Args:
            session_id: The Atlas session identifier.
            since_id: Optional message id to fetch messages after.
            limit: Maximum number of messages to return.

        Returns:
            List of output message dicts.
        """
        db = self._get_db()
        try:
            return db.poll_messages(session_id, "out", since_id, limit)
        finally:
            db.close()

    def latest_output_id(self, session_id: str) -> Optional[str]:
        """Return the newest output queue id for *session_id*, if any."""
        db = self._get_db()
        try:
            row = db._fetchone(
                """
                SELECT id FROM session_queue
                WHERE session_id = ? AND direction = 'out'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (session_id,),
            )
            return str(row["id"]) if row is not None else None
        finally:
            db.close()

    def stop_all(self) -> None:
        """Kill all tracked worker processes."""
        with self._lock:
            session_ids = list(self._processes.keys())
        for session_id in session_ids:
            self.kill(session_id)

    # -- Context manager support -------------------------------------------

    def __enter__(self) -> SessionProcessManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop_all()
