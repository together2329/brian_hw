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
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter


class SessionProcessManager:
    """Manages subprocess lifecycle for Atlas session worker processes.

    Each session gets its own ``python -m core.session_worker`` subprocess.
    Input/output is routed through the SQLite queue in :class:`AtlasDB`.

    DB-path resolution goes through an :class:`AtlasDBRouter` (Wave 1 / Unit A).
    In ``ATLAS_RUNTIME_DB_MODE=central`` (default) the router returns the control
    path everywhere, so behavior is byte-identical to the historical single-DB
    layout. In ``=session`` mode the router shards each session onto its own
    runtime ``.db`` file; ``send_input`` / ``poll_output`` / ``latest_output_id``
    then all open the SAME runtime DB for a given session (the SAME-DB invariant).
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        project_root: Optional[str | Path] = None,
        router: Optional[AtlasDBRouter] = None,
    ) -> None:
        """Initialize the process manager.

        Args:
            db_path: Path to the Atlas *control* SQLite database. Defaults to
                ``~/.common_ai_agent/atlas.db``. When provided, it pins the
                router's control path so a per-call/per-instance db override
                stays authoritative (e.g. ``:memory:`` or a temp file in tests).
            project_root: Artifact root served by Atlas. Defaults to
                ``ATLAS_PROJECT_ROOT`` or the current working directory.
            router: Optional :class:`AtlasDBRouter`. Defaults to one whose
                control path is pinned to ``db_path`` when given (so existing
                callers that pass an explicit db keep working in central mode).
        """
        self.db_path = db_path
        self._source_root = Path(__file__).resolve().parents[1]
        raw_project_root = (
            project_root
            or os.environ.get("ATLAS_PROJECT_ROOT")
            or Path.cwd()
        )
        self._project_root = Path(os.path.expanduser(str(raw_project_root))).resolve()
        self._processes: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        # Router is the single DB-path resolution point. Pin the control path to
        # an explicit db_path so a constructor override (tests, :memory:) wins
        # over env in central mode without re-implementing AtlasDB's own default.
        self._router = router or AtlasDBRouter(control_path=db_path)
        # Hot-path connection reuse (plan §2.6 / R2). send_input/poll_output/
        # latest_output_id used to do ``db = AtlasDB(...); finally: db.close()``;
        # close() pops the thread-local cached connection so the very next poll
        # re-opens + re-runs busy_timeout + the WAL retry loop. At 100 sessions
        # that is 100 reconnect cycles per broadcaster pass on one thread. We
        # instead hold a long-lived AtlasDB handle per (thread, resolved path)
        # so AtlasDB's ``_TLS`` connection survives between polls. The handle is
        # only ever touched by its owning thread (AtlasDB._TLS is thread-local),
        # so the cache is keyed by thread id + path.
        self._db_handles: Dict[tuple, AtlasDB] = {}
        self._db_handles_lock = threading.RLock()
        # Non-silent recovery audit trail (plan §2.12 / R5/R13): each entry is
        # {"session_id", "event", "at"} for a runtime-DB recreate/error. Guarded
        # by _db_handles_lock (same lifecycle as the handle cache).
        self._runtime_recovery_events: List[Dict[str, Any]] = []
        # Cheap fleet-health counter (plan §2.12 / R25): how many times the hot
        # enqueue path hit a 'database is locked' and retried. Surfaced via
        # ``locked_retry_count()`` so ``runtime_rollup.fleet_health`` can report
        # it. Guarded by its own tiny lock so the hot path stays uncontended.
        self._locked_retry_count = 0
        self._metrics_lock = threading.Lock()

    @staticmethod
    def _env_enabled(name: str, default: bool = True) -> bool:
        raw = os.environ.get(name)
        if raw is None or not raw.strip():
            return default
        return raw.strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _path_basename(path: str) -> str:
        return str(path or "").replace("\\", "/").rsplit("/", 1)[-1].lower()

    @classmethod
    def _worker_python_executable(cls) -> str:
        executable = str(getattr(sys, "executable", "") or "").strip()
        if os.name == "nt" and cls._path_basename(executable) == "py.exe":
            base_executable = str(getattr(sys, "_base_executable", "") or "").strip()
            if base_executable and cls._path_basename(base_executable) != "py.exe":
                return base_executable
            for candidate in ("python.exe", "python3.exe", "python"):
                resolved = shutil.which(candidate)
                if resolved and cls._path_basename(resolved) != "py.exe":
                    return resolved
        return executable or "python"

    def _resolve_db_path(self, db_path: Optional[str] = None) -> str:
        """Return the concrete CONTROL DB path shared by UI and worker processes.

        This is the control path (== today's single DB). Per-session runtime
        paths are resolved through :meth:`_resolve_runtime_db_path`. An explicit
        ``db_path`` argument still wins (per-call override), then the manager's
        ``self.db_path``, then the router's control resolution (which honors
        ``ATLAS_CONTROL_DB_PATH`` / ``ATLAS_DB_PATH`` / the home default).
        """
        raw = (
            db_path
            or self.db_path
            or self._router.control_db_path()
        )
        return str(Path(os.path.expanduser(raw)).resolve())

    def _resolve_runtime_db_path(
        self,
        session_id: str,
        db_path: Optional[str] = None,
        create: bool = True,
    ) -> str:
        """Return the runtime DB path for *session_id* via the router.

        - central mode -> the control path (== ``_resolve_db_path``), so the
          ``--db-path`` channel and env stay byte-identical to today.
        - session mode -> the per-session runtime ``.db`` file. When an explicit
          ``db_path`` override is passed AND we are in central mode, the override
          wins (preserves per-call control overrides used by tests).
        """
        if self._router.mode() == "central":
            return self._resolve_db_path(db_path)
        return str(
            Path(os.path.expanduser(self._router.runtime_db_path(session_id, create=create))).resolve()
        )

    def _get_db(self) -> AtlasDB:
        """Return an initialized AtlasDB instance on the control path."""
        db = AtlasDB(self._resolve_db_path())
        db.init_db()
        return db

    def _get_runtime_db(self, session_id: str, db_path: Optional[str] = None) -> AtlasDB:
        """Return a long-lived AtlasDB handle for *session_id*'s runtime DB.

        Hot-path connection reuse (plan §2.6 / R2): we cache one AtlasDB per
        (thread, resolved path) and NEVER call ``close()`` on the hot poll /
        enqueue path, so AtlasDB's thread-local sqlite connection survives
        between polls instead of being re-opened (busy_timeout + WAL retry) on
        every call. The cache is keyed by thread id because AtlasDB's ``_TLS``
        connection cache is thread-local — a handle reused from another thread
        would build its own connection on first touch anyway, but keying by
        thread keeps each handle's lifetime aligned with the connection it owns.

        In central mode a cache miss is built through ``_get_db()`` so the
        historical hook (tests monkeypatch ``_get_db``) keeps working; in session
        mode we open the routed runtime file directly with the runtime schema.

        Recovery contract (plan §2.12 / Task 4(c), R5/R13). In session mode, on a
        cache MISS we run the open through ``_open_runtime_db_with_recovery``:

        * MISSING file -> ``AtlasDB(...).init_db()`` recreates an initialized
          runtime DB; we record a non-silent ``runtime_db_recreated`` signal
          (never a silent empty result).
        * CORRUPT file -> quarantine the file (rename to ``*.corrupt-<ts>``),
          flip the manifest ``status='error'`` on the control DB, and RE-RAISE so
          the failure surfaces. We do NOT hide corruption behind empty results.
        """
        resolved = self._resolve_runtime_db_path(session_id, db_path=db_path)
        key = (threading.get_ident(), resolved)
        with self._db_handles_lock:
            db = self._db_handles.get(key)
            if db is None:
                if self._router.mode() == "central":
                    db = self._get_db()
                else:
                    db = self._open_runtime_db_with_recovery(session_id, resolved)
                self._db_handles[key] = db
            return db

    def _record_runtime_recovery(self, session_id: str, event: str) -> None:
        """Append a non-silent recovery event (plan §2.12 / R5/R13).

        ``event`` is e.g. ``'runtime_db_recreated'`` or ``'runtime_db_error'``.
        The list is the manager's observable audit trail (read by tests / the
        Task 9 fleet metrics). It is intentionally NOT swallowed — a missing or
        corrupt runtime DB must never be hidden behind empty results.
        """
        with self._db_handles_lock:
            self._runtime_recovery_events.append(
                {"session_id": session_id, "event": event, "at": time.time()}
            )

    def runtime_recovery_events(self) -> List[Dict[str, Any]]:
        """Return a copy of the recorded runtime-DB recovery events."""
        with self._db_handles_lock:
            return list(self._runtime_recovery_events)

    def locked_retry_count(self) -> int:
        """Return the cumulative 'database is locked' enqueue retry count (R25).

        Read by ``core.runtime_rollup.fleet_health`` for the fleet metrics JSON.
        """
        with self._metrics_lock:
            return self._locked_retry_count

    def _open_runtime_db_with_recovery(self, session_id: str, resolved: str) -> AtlasDB:
        """Open a per-session runtime DB, applying the recovery contract."""
        path = Path(resolved)
        existed_before = path.exists()
        try:
            db = AtlasDB(resolved, schema_set="runtime")
            db.init_db()
        except sqlite3.DatabaseError as exc:
            # Corrupt/unreadable runtime file: quarantine + manifest status=error
            # + surface. Never hide corruption behind empty results.
            self._quarantine_corrupt_runtime_db(session_id, resolved)
            self._record_runtime_recovery(session_id, "runtime_db_error")
            raise RuntimeError(
                f"runtime DB for session {session_id!r} is corrupt and was "
                f"quarantined: {exc}"
            ) from exc
        if not existed_before:
            # Missing file was just recreated + initialized. Emit a non-silent
            # signal (plan §2.12 / Task 4(c)). On a genuine first-spawn this also
            # fires; that is acceptable — the manifest distinguishes lifecycle.
            self._record_runtime_recovery(session_id, "runtime_db_recreated")
        return db

    def _quarantine_corrupt_runtime_db(self, session_id: str, resolved: str) -> None:
        """Rename a corrupt runtime file aside and flag the manifest as error."""
        path = Path(resolved)
        ts = int(time.time() * 1000)
        for suffix in ("", "-wal", "-shm"):
            src = Path(str(path) + suffix)
            if src.exists():
                try:
                    src.rename(Path(f"{src}.corrupt-{ts}"))
                except Exception:
                    pass
        try:
            control = self._get_db()
            control.update_session_runtime_db_status(session_id, "error")
        except Exception:
            pass

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

        control_db = self._resolve_db_path(db_path)
        # In central mode runtime == control (behavior-identical); in session
        # mode the worker's queue, llm_calls and trace_events all land in the
        # per-session runtime DB. The worker binds its queue from --db-path; the
        # env vars below redirect its secondary AtlasDB opens to the SAME file.
        runtime_db = self._resolve_runtime_db_path(session_id, db_path=db_path)
        env["ATLAS_ACTIVE_SESSION"] = session_key
        env["ATLAS_DEFAULT_SESSION_ID"] = owner
        env["ATLAS_MEMORY_USER"] = owner
        env["ATLAS_ACTIVE_IP"] = ip_name
        env["ATLAS_DEFAULT_WORKFLOW"] = workflow
        env["ACTIVE_WORKSPACE"] = workflow
        env["ATLAS_TRACE_ENABLE"] = "1"
        env["ATLAS_CONTROL_DB_PATH"] = control_db
        env["ATLAS_RUNTIME_DB_PATH"] = runtime_db
        env["ATLAS_DB_PATH"] = runtime_db
        env["ATLAS_TRACE_DB_PATH"] = runtime_db
        env["ATLAS_SOURCE_ROOT"] = str(self._source_root)
        env.setdefault("COMMON_AI_AGENT_HOME", str(self._source_root))
        env["ATLAS_PROJECT_ROOT"] = str(self._project_root)
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

    @staticmethod
    def _arg_value(args: List[str], name: str) -> str:
        for i, arg in enumerate(args):
            if arg == name and i + 1 < len(args):
                return args[i + 1]
            prefix = f"{name}="
            if arg.startswith(prefix):
                return arg[len(prefix):]
        return ""

    @staticmethod
    def _is_session_worker_args(args: List[str]) -> bool:
        for i, arg in enumerate(args[:-1]):
            if arg == "-m" and args[i + 1] == "core.session_worker":
                return True
        return False

    @staticmethod
    def _same_resolved_path(left: str, right: str) -> bool:
        try:
            return Path(os.path.expanduser(left)).resolve() == Path(os.path.expanduser(right)).resolve()
        except Exception:
            return str(left or "") == str(right or "")

    @staticmethod
    def _pid_exists(pid: int) -> bool:
        try:
            os.kill(pid, 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True
        except OSError:
            return False

    def _external_worker_pids(self, session_id: str, db_path: str) -> List[int]:
        if not self._env_enabled("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", True):
            return []
        try:
            result = subprocess.run(
                ["ps", "-axo", "pid=,command="],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
        except Exception:
            return []

        current_pid = os.getpid()
        matches: List[int] = []
        for raw_line in (result.stdout or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                pid_text, command = line.split(None, 1)
                pid = int(pid_text)
            except ValueError:
                continue
            if pid == current_pid:
                continue
            try:
                args = shlex.split(command)
            except ValueError:
                continue
            if not self._is_session_worker_args(args):
                continue
            if self._arg_value(args, "--session-id") != session_id:
                continue
            worker_db = self._arg_value(args, "--db-path")
            if worker_db and not self._same_resolved_path(worker_db, db_path):
                continue
            matches.append(pid)
        return matches

    def _terminate_external_session_workers(self, session_id: str, db_path: str) -> None:
        """Stop untracked same-session workers left behind by an old UI server.

        Detached workers share the SQLite input queue. If an orphan survives a
        backend restart, it can consume prompts that the new backend never
        polls, making the user resend input until the tracked worker wins.
        """
        pids = self._external_worker_pids(session_id, db_path)
        if not pids:
            return
        for pid in pids:
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            except Exception:
                continue

        deadline = time.time() + 3.0
        while time.time() < deadline:
            if all(not self._pid_exists(pid) for pid in pids):
                return
            time.sleep(0.05)

        for pid in pids:
            if not self._pid_exists(pid):
                continue
            try:
                os.kill(pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except Exception:
                pass

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

            # The worker binds its queue DB from --db-path. In session mode that
            # MUST be the per-session runtime file so the worker's queue (and,
            # via env, its llm_calls/trace_events) co-locate with what
            # send_input/poll_output open here. In central mode this resolves to
            # the control path == today's behavior. Orphan pruning matches on
            # this same --db-path, so it must use the runtime path too.
            runtime_db = self._resolve_runtime_db_path(session_id, db_path=db_path)
            self._terminate_external_session_workers(session_id, runtime_db)

            cmd = [
                self._worker_python_executable(),
                "-m",
                "core.session_worker",
                "--session-id",
                session_id,
            ]
            cmd.extend(["--db-path", runtime_db])

            proc = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env=self.build_worker_env(session_id, db_path=db_path),
                cwd=str(self._project_root),
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
            if entry is not None:
                proc = entry["proc"]
                if proc.poll() is None:
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
        # Evict any cached runtime DB handle for this session (R2): a killed
        # session's long-lived connection must not be reused by a later spawn
        # that may delete/recreate the runtime file (stale-inode reuse). Done
        # outside self._lock — _evict_db_handles takes _db_handles_lock.
        self._evict_db_handles(session_id)
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

        # Route to the session's runtime DB (control DB in central mode) and
        # reuse the long-lived handle — do NOT close() on this hot enqueue path
        # (plan §2.6 / R2). SAME-DB invariant: this opens the SAME file that
        # poll_output / latest_output_id open for the session.
        db = self._get_runtime_db(session_id)
        enqueue_budget_ms = 4500.0
        started_at = time.monotonic()
        msg_id = None
        for _ in range(3):
            remaining_ms = enqueue_budget_ms - ((time.monotonic() - started_at) * 1000.0)
            if remaining_ms <= 0:
                break
            try:
                msg_id = db.enqueue_message(
                    session_id,
                    "in",
                    msg_type,
                    payload,
                    busy_timeout_ms=int(remaining_ms),
                )
                break
            except sqlite3.OperationalError as exc:
                if "database is locked" not in str(exc).lower():
                    raise
                with self._metrics_lock:
                    self._locked_retry_count += 1
                if enqueue_budget_ms - ((time.monotonic() - started_at) * 1000.0) <= 0:
                    break
                time.sleep(0.02)
        blocked_ms = (time.monotonic() - started_at) * 1000.0
        if blocked_ms > 500.0:
            print(
                f"[prompt-latency] enqueue session={session_id} "
                f"type={msg_type} blocked={blocked_ms:.0f}ms",
                flush=True,
            )
        return msg_id

    def poll_output(
        self,
        session_id: str,
        since_id: Optional[str] = None,
        limit: int = 100,
        on_absent_cursor: str = "empty",
    ) -> List[Dict[str, Any]]:
        """Fetch undelivered output messages from the session worker.

        Args:
            session_id: The Atlas session identifier.
            since_id: Optional message id to fetch messages after.
            limit: Maximum number of messages to return.
            on_absent_cursor: ``'empty'`` (default, historical 0-rows) or
                ``'raise'`` to surface :class:`core.atlas_db.QueueCursorNotFound`
                when ``since_id`` is absent from the (possibly recreated/swapped)
                runtime DB. The atlas_multiuser poll path passes ``'raise'`` so a
                swapped runtime DB triggers an atomic cursor re-seed instead of a
                silent permanent stall (plan §2.4 / R5).

        Returns:
            List of output message dicts.
        """
        # Reuse the long-lived runtime handle; no close() on this hot poll path
        # (plan §2.6 / R2). SAME-DB invariant with send_input / latest_output_id.
        db = self._get_runtime_db(session_id)
        return db.poll_messages(
            session_id, "out", since_id, limit, on_absent_cursor=on_absent_cursor
        )

    def reseed_output_cursor(self, session_id: str) -> Optional[str]:
        """Re-seed the output cursor for *session_id* after a runtime-DB swap.

        Returns the newest already-delivered out-row id (resume point that does
        not re-deliver), or ``None`` when nothing has been delivered yet (resume
        from the top is then correct — no client has seen the buffered output).
        Reuses the long-lived runtime handle (R2); SAME-DB invariant. See
        :meth:`core.atlas_db.AtlasDB.reseed_output_cursor` (plan §2.4 / R5).
        """
        db = self._get_runtime_db(session_id)
        return db.reseed_output_cursor(session_id, "out")

    def latest_output_id(self, session_id: str) -> Optional[str]:
        """Return the newest output queue id for *session_id*, if any.

        Orders by the strict total order ``(created_at DESC, rowid DESC)`` to
        match Unit A's monotonic-rowid queue ordering (plan §2.3 / R1): plain
        ``created_at DESC`` could return either of two rows sharing a wall-clock
        timestamp, so the seed cursor could skip the genuinely-last row.
        """
        # Reuse the long-lived runtime handle (R2); SAME-DB invariant.
        db = self._get_runtime_db(session_id)
        row = db._fetchone(
            """
            SELECT id FROM session_queue
            WHERE session_id = ? AND direction = 'out'
            ORDER BY created_at DESC, rowid DESC
            LIMIT 1
            """,
            (session_id,),
        )
        return str(row["id"]) if row is not None else None

    def stop_all(self) -> None:
        """Kill all tracked worker processes and release cached DB handles."""
        with self._lock:
            session_ids = list(self._processes.keys())
        for session_id in session_ids:
            self.kill(session_id)
        self._close_db_handles()

    def recover_after_restart(self) -> List[Any]:
        """Build the restart-recovery plan for every manifest session (R13).

        Thin entrypoint the UI calls once on startup. Delegates to
        :func:`core.runtime_rollup.recover_all_sessions`, passing ``self`` so the
        orphan-PID reconcile (matching ``--session-id`` AND ``--db-path``) can run
        against this manager's runtime paths. Returns the list of RecoveryPlan
        objects (each carries the oldest-undelivered resume cursor so the
        broadcaster replays buffered output without re-delivering, plus any pruned
        orphan worker PIDs). The ``_jobs``-loss policy is documented on
        ``runtime_rollup.JOBS_LOSS_POLICY``.
        """
        from core.runtime_rollup import recover_all_sessions

        return recover_all_sessions(router=self._router, process_manager=self)

    def _close_db_handles(self) -> None:
        """Close every cached long-lived AtlasDB handle (releases sqlite conns).

        Called on shutdown. Mid-flight reuse keeps the thread-local connection
        alive (R2); this is the explicit release path so the pooled handles do
        not outlive the manager.
        """
        with self._db_handles_lock:
            handles = list(self._db_handles.values())
            self._db_handles.clear()
        for db in handles:
            try:
                db.close()
            except Exception:
                pass

    def _evict_db_handles(self, session_id: str) -> None:
        """Close + drop cached runtime DB handles for one session (all threads).

        Called from ``kill()`` (and, later, the Task 9 session-delete path) so a
        killed/deleted session's pooled connection is never reused after the
        underlying runtime file may have been removed or recreated. Without this
        the (thread, path) cache would hand back a connection to a stale/unlinked
        inode. Bounded-growth fix for the hot-path handle cache.
        """
        try:
            resolved = self._resolve_runtime_db_path(session_id, create=False)
        except Exception:
            resolved = None
        if not resolved:
            return
        with self._db_handles_lock:
            keys = [k for k in self._db_handles if k[1] == resolved]
            handles = [self._db_handles.pop(k) for k in keys]
        for db in handles:
            try:
                db.close()
            except Exception:
                pass

    # -- Context manager support -------------------------------------------

    def __enter__(self) -> SessionProcessManager:
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.stop_all()
