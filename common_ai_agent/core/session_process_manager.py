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
import uuid
import signal
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter, RuntimeDBError
from core.atlas_context import AtlasContext
from core.session_worker_policy import SessionWorkerPolicy

# Legal SpawnResult.status values (Wave-3 H10 — enumerated, each has a producer).
SPAWN_STATUS_READY = "ready"          # target already had a live tracked process
SPAWN_STATUS_STARTED = "started"      # a new subprocess was Popen'd
SPAWN_STATUS_CAPACITY_WAIT = "capacity_wait"  # net-new spawn refused by the cap
SPAWN_STATUS_FAILED = "failed"        # net-new spawn raised (Popen/env) — a real failure, NOT backpressure (H10)

# Legal ProcessEntry.state values (Wave-3 H10). Every frontend state has a
# backend producer here or is dropped: 'starting' (set at Popen, before liveness
# is observable), 'ready' (alive worker), 'stopping' (set at the START of
# terminate_session), 'failed' (Popen/handoff error). 'switching'/'capacity_wait'/
# 'evicted' are owner-slot/bridge-level states surfaced via SpawnResult.status and
# the bridge events, NOT stored on the manager entry.
ENTRY_STATE_STARTING = "starting"
ENTRY_STATE_READY = "ready"
ENTRY_STATE_STOPPING = "stopping"
ENTRY_STATE_FAILED = "failed"


class ProcessEntry(dict):
    """Typed-but-dict-compatible per-session worker entry.

    A ``dict`` subclass on purpose: existing tests inject RAW dicts
    (``{"proc": ..., "started_at": ...}``) straight into ``manager._processes``
    and ``DummyProcessManager.spawn`` re-implements spawn writing that same
    2-key dict. Internal code reads ``entry["proc"]`` / ``entry["started_at"]`` by
    subscript, so the entry MUST stay subscriptable and tolerate missing new
    keys. Attribute access mirrors the dict keys for readability; every NEW
    field is read elsewhere via ``entry.get(...)`` with a default so a foreign
    plain dict keeps working.

    Fields (Task 4): ``proc``, ``session_id``, ``owner``, ``started_at``,
    ``last_active_at``, ``last_input_at``, ``last_output_at``, ``worker_epoch``
    (None until Task 5 lands), ``state`` (see ENTRY_STATE_*).
    """

    _FIELDS = (
        "proc",
        "session_id",
        "owner",
        "started_at",
        "last_active_at",
        "last_input_at",
        "last_output_at",
        "worker_epoch",
        "state",
    )

    def __init__(
        self,
        proc: Any,
        *,
        session_id: str = "",
        owner: str = "",
        started_at: Optional[float] = None,
        state: str = ENTRY_STATE_STARTING,
        worker_epoch: Optional[str] = None,
    ) -> None:
        now = time.time() if started_at is None else started_at
        super().__init__(
            proc=proc,
            session_id=session_id,
            owner=owner,
            started_at=now,
            last_active_at=now,
            last_input_at=None,
            last_output_at=None,
            worker_epoch=worker_epoch,
            state=state,
        )

    def __getattr__(self, name: str) -> Any:
        if name in self._FIELDS:
            return self.get(name)
        raise AttributeError(name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._FIELDS:
            self[name] = value
        else:
            super().__setattr__(name, value)


@dataclass
class SpawnResult:
    """Structured admission result for an interactive session-worker spawn.

    ``status`` is one of SPAWN_STATUS_READY / _STARTED / _CAPACITY_WAIT (H10).
    ``ok`` is True for ready/started and False for capacity_wait. ``active_count``
    / ``max_active`` snapshot the cap accounting at decision time so the bridge
    and ``/api/session/worker/status`` can render capacity without re-querying.
    """

    ok: bool
    status: str
    reason: str = ""
    session_id: str = ""
    owner: str = ""
    pid: Optional[int] = None
    active_count: int = 0
    max_active: int = 0


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
        self._reserved_sessions: set[str] = set()
        self._lock = threading.RLock()
        # Router is the single DB-path resolution point. Pin the control path to
        # an explicit db_path so a constructor override (tests, :memory:) wins
        # over env in central mode without re-implementing AtlasDB's own default.
        self._router = router or AtlasDBRouter(control_path=db_path)
        self._runtime_path_cache: Dict[Tuple[str, str, str, str], str] = {}
        self._db_handles: Dict[Tuple[int, str], AtlasDB] = {}
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
        cache_key = (
            session_id,
            str(db_path or ""),
            str(Path(os.path.expanduser(self._router.control_db_path())).resolve()),
            str(Path(os.path.expanduser(self._router.runtime_root())).resolve()),
        )
        with self._db_handles_lock:
            cached = self._runtime_path_cache.get(cache_key)
            if cached is not None:
                return cached
        resolved = str(
            Path(os.path.expanduser(self._router.runtime_db_path(session_id, create=create))).resolve()
        )
        with self._db_handles_lock:
            self._runtime_path_cache[cache_key] = resolved
        return resolved

    def _get_db(self) -> AtlasDB:
        """Return an initialized AtlasDB instance on the control path."""
        db = AtlasDB(self._resolve_db_path())
        db.init_db()
        return db

    def _get_runtime_db(self, session_id: str, db_path: Optional[str] = None, create: bool = True) -> AtlasDB:
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
        resolved = self._resolve_runtime_db_path(session_id, db_path=db_path, create=create)
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
        worker_epoch: Optional[str] = None,
    ) -> Dict[str, str]:
        """Build deterministic worker environment from ``owner/ip/workflow``."""
        env = os.environ.copy()
        session_key = str(session_id or "").strip().strip("/") or "default"
        parts = [part for part in session_key.split("/") if part]
        context: AtlasContext | None = None
        if len(parts) >= 3:
            try:
                context = AtlasContext.from_session_key(
                    session_key,
                    atlas_root=env.get("ATLAS_ROOT") or str(self._project_root),
                )
            except Exception:
                context = None
        if context is not None:
            owner, ip_name, workflow = context.user_name, context.ip_name, context.workflow
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
        if context is not None:
            env.update(context.export_env())
        env["ATLAS_TRACE_ENABLE"] = "1"
        env["ATLAS_CONTROL_DB_PATH"] = control_db
        env["ATLAS_RUNTIME_DB_PATH"] = runtime_db
        env["ATLAS_DB_PATH"] = runtime_db
        env["ATLAS_TRACE_DB_PATH"] = runtime_db
        env["ATLAS_SOURCE_ROOT"] = str(self._source_root)
        env.setdefault("COMMON_AI_AGENT_HOME", str(self._source_root))
        env.setdefault("ATLAS_PROJECT_ROOT", str(self._project_root))
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
        # Task 5: stamp this spawn's epoch so the worker can fence stale inbound
        # rows and ignore epoch-mismatched prompt/interrupt/answer/stop msgs.
        if worker_epoch:
            env["ATLAS_SESSION_WORKER_EPOCH"] = str(worker_epoch)
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

        Compatibility wrapper (Task 4 / plan "Result Objects"): the admission
        source of truth is :meth:`spawn_result`; ``spawn`` stays a ``bool`` for
        old tests/callers and is simply ``spawn_result(...).ok``. It is called
        with no policy so the cap is OFF here (unbounded, byte-identical to the
        historical spawn); only the structured ``spawn_result`` path enforces the
        cap.
        """
        return self.spawn_result(session_id, db_path=db_path).ok

    def spawn_result(
        self,
        session_id: str,
        db_path: Optional[str] = None,
        policy: Optional[SessionWorkerPolicy] = None,
        *,
        replacing: Optional[str] = None,
        reserve: bool = False,
    ) -> SpawnResult:
        """Admission-checked spawn for *session_id*; the source of truth (H9).

        Ordering is binding (Wave-3 H9): the ``is_alive`` short-circuit
        (``status=ready``) and dead-entry cleanup happen BEFORE the cap is
        evaluated, and the cap is checked ONLY on the branch that will actually
        ``Popen`` a net-new process.

        ``replacing``/``reserve`` (Wave-3 H2/H3): a same-owner-slot REPLACEMENT
        (workflow/IP switch) is slot-preserving and MUST NOT be cap-refused.
        ``terminate_and_reserve_slot`` creates the authoritative manager-side
        reservation before killing the previous worker, so the freed slot cannot
        be stolen by a concurrent net-new owner before this method spawns the
        replacement. ``reserve=True`` remains a compatibility hint; the manager
        reservation is the source of truth for cap accounting.

        ``policy`` defaults to an empty :class:`SessionWorkerPolicy` (cap OFF) so
        the legacy ``spawn`` wrapper stays unbounded.
        """
        policy = policy or SessionWorkerPolicy()
        owner = self._owner_for_session(session_id)
        with self._lock:
            has_reservation = session_id in self._reserved_sessions
            # (1) is_alive short-circuit — ready, consumes no new slot (H9).
            existing = self._processes.get(session_id)
            if existing is not None:
                if self.is_alive(session_id):
                    existing["state"] = ENTRY_STATE_READY
                    self._reserved_sessions.discard(session_id)
                    return SpawnResult(
                        ok=True,
                        status=SPAWN_STATUS_READY,
                        reason="already_alive",
                        session_id=session_id,
                        owner=owner,
                        pid=self._entry_pid(existing),
                        active_count=self._active_count_locked(),
                        max_active=policy.max_active,
                    )
                # Dead entry — clean it up before the cap is evaluated (H9).
                self._processes.pop(session_id, None)

            active_count = self._admission_count_locked(ignore_session_id=session_id)
            if not has_reservation and not reserve and policy.cap_exceeded(active_count):
                return SpawnResult(
                    ok=False,
                    status=SPAWN_STATUS_CAPACITY_WAIT,
                    reason="max_active",
                    session_id=session_id,
                    owner=owner,
                    pid=None,
                    active_count=active_count,
                    max_active=policy.max_active,
                )

            # (3) Popen the net-new (or reserved-replacement) worker. The worker
            #     binds its queue DB from --db-path; in session mode that MUST be
            #     the per-session runtime file (central -> control path, byte-
            #     identical). Orphan pruning matches the same --db-path.
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
            # Task 5: mint a fresh epoch for THIS spawn, stamp it into the child
            # env, and record it on the entry so send_input() tags every inbound
            # payload with it; a stale input carrying an OLD epoch (queued against
            # a previous process for this canonical session) is then ignored.
            worker_epoch = uuid.uuid4().hex
            try:
                worker_env = self.build_worker_env(
                    session_id, db_path=db_path, worker_epoch=worker_epoch
                )
                worker_cwd = Path(
                    worker_env.get("ATLAS_IP_ROOT")
                    or worker_env.get("ATLAS_PROJECT_ROOT")
                    or str(self._project_root)
                ).expanduser().resolve()
                worker_cwd.mkdir(parents=True, exist_ok=True)
                proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    env=worker_env,
                    cwd=str(worker_cwd),
                    # Detach from parent TTY so signals/shells don't propagate.
                    start_new_session=True,
                )
            except Exception as exc:  # Popen/env build failure -> failed, no slot held.
                self._reserved_sessions.discard(session_id)
                return SpawnResult(
                    ok=False,
                    status=SPAWN_STATUS_FAILED,
                    reason=f"spawn_failed:{exc}",
                    session_id=session_id,
                    owner=owner,
                    pid=None,
                    active_count=active_count,
                    max_active=policy.max_active,
                )
            self._processes[session_id] = ProcessEntry(
                proc,
                session_id=session_id,
                owner=owner,
                state=ENTRY_STATE_STARTING,
                worker_epoch=worker_epoch,
            )
            self._reserved_sessions.discard(session_id)
            return SpawnResult(
                ok=True,
                status=SPAWN_STATUS_STARTED,
                reason="replacing:" + replacing if replacing else ("reserved" if has_reservation else "net_new"),
                session_id=session_id,
                owner=owner,
                pid=self._entry_pid(self._processes[session_id]),
                active_count=active_count + 1,
                max_active=policy.max_active,
            )

    def terminate_and_reserve_slot(
        self,
        session_id: str,
        new_session_id: str,
        reason: str = "switch",
        stop_timeout_sec: float = 0.0,
        kill_grace_sec: float = 5.0,
        *,
        graceful: bool = True,
        has_running_prompt: bool = False,
        worker_epoch: Optional[str] = None,
    ) -> bool:
        with self._lock:
            self._reserved_sessions.add(new_session_id)
        try:
            ok = self.terminate_session(
                session_id,
                reason=reason,
                stop_timeout_sec=stop_timeout_sec,
                kill_grace_sec=kill_grace_sec,
                graceful=graceful,
                has_running_prompt=has_running_prompt,
                worker_epoch=worker_epoch,
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

    def kill(self, session_id: str) -> bool:
        """Hard-terminate the worker process for *session_id* (or no-op).

        Backwards-compatible wrapper (Task 4): delegates to
        :meth:`terminate_session` with ``graceful=False`` and the historical
        hard-stop grace (5s SIGTERM wait, 2s SIGKILL wait), so old callers keep
        the exact SIGTERM->wait->SIGKILL behavior and the runtime-DB handle
        eviction contract. Returns ``True`` even when the session is untracked.
        """
        return self.terminate_session(
            session_id,
            reason="kill",
            stop_timeout_sec=0.0,
            kill_grace_sec=5.0,
            graceful=False,
        )

    def terminate_session(
        self,
        session_id: str,
        reason: str = "terminate",
        stop_timeout_sec: float = 0.0,
        kill_grace_sec: float = 5.0,
        *,
        graceful: bool = True,
        has_running_prompt: bool = False,
        worker_epoch: Optional[str] = None,
    ) -> bool:
        """Stop a tracked worker, then evict its DB handles and entry.

        Ordering (Task 4 + Wave-3 H4): set ``state='stopping'`` at the START
        (H10 producer), then

        1. GRACEFUL STOP, busy-worker ONLY (H4): if ``graceful`` AND the worker
           has a running prompt, enqueue a ``stop`` and wait up to
           ``stop_timeout_sec`` for the PROCESS to exit. A warm-IDLE worker does
           NOT exit on a queued ``stop`` (stop only interrupts a running turn),
           so when ``has_running_prompt`` is False (or ``graceful`` is False) we
           SKIP the stop-ack wait entirely and go straight to terminate/kill.
           The authoritative manager-side ack is ``proc.poll() is not None``
           (process exit); the bridge separately observes ``worker_stopped`` /
           ``worker_exited`` out-rows.
        2. ``proc.terminate()`` (SIGTERM) and wait up to ``kill_grace_sec``.
        3. ``proc.kill()`` (SIGKILL) if still alive.
        4. Evict cached runtime DB handles (existing R2 contract).
        5. Remove the process entry.

        CRITICAL (plan "Locking And Switch Semantics"): ``self._lock`` is NEVER
        held while sleeping. Every wait runs OUTSIDE the lock so an unrelated
        owner slot keeps making progress while this one drains. The lock is only
        taken for the short critical sections (read the entry / mark state / pop).

        Returns ``True`` even when the session is untracked (no-op), preserving
        the historical ``kill`` contract.
        """
        # -- short critical section: locate + mark stopping (H10). Do NOT pop
        #    yet; popping now would let a concurrent net-new spawn reuse the
        #    slot before this process is actually dead.
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                # Untracked: still honor the handle-eviction contract + no-op.
                self._reserved_sessions.discard(session_id)
                self._evict_db_handles(session_id)
                return True
            entry["state"] = ENTRY_STATE_STOPPING
            proc = entry.get("proc")
            epoch = worker_epoch if worker_epoch is not None else entry.get("worker_epoch")

        # -- (1) graceful stop, busy-worker only (H4) — OUTSIDE the lock.
        if graceful and has_running_prompt and stop_timeout_sec > 0:
            payload: Dict[str, Any] = {"reason": reason}
            if epoch is not None:
                # Task 5 hook: tag the stop with the worker epoch when one exists;
                # do NOT require epoch support before that task lands.
                payload["worker_epoch"] = epoch
            try:
                self.send_input(session_id, "stop", payload)
            except Exception:
                pass
            self._wait_for_exit(proc, stop_timeout_sec)

        # -- (2)/(3) SIGTERM grace then SIGKILL — OUTSIDE the lock.
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
                self._wait_for_exit(proc, kill_grace_sec)
            except Exception:
                pass
            if proc.poll() is None:
                try:
                    proc.kill()
                    self._wait_for_exit(proc, 2.0)
                except Exception:
                    pass

        # -- final liveness verdict (Wave-3 P1 fix): a process that survived
        #    SIGKILL (uninterruptible / unkillable) MUST NOT be reported as
        #    terminated. Popping its entry would hide a live worker behind
        #    is_alive()=False and let a caller start a sibling; instead keep it
        #    tracked and return False so _prepare_owner_slot_for_session yields
        #    `termination_failed` and refuses to spawn. Only a confirmed-dead (or
        #    never-running) process frees the slot.
        if proc is not None and proc.poll() is None:
            return False
        # -- (5) remove the entry under the lock (idempotent if a race popped it).
        with self._lock:
            self._processes.pop(session_id, None)
            self._reserved_sessions.discard(session_id)
        # -- (4) evict cached runtime DB handles (R2) — outside self._lock,
        #    _evict_db_handles takes _db_handles_lock. Unchanged contract.
        self._evict_db_handles(session_id)
        return True

    @staticmethod
    def _wait_for_exit(proc: Any, timeout_sec: float) -> bool:
        """Wait up to *timeout_sec* for *proc* to exit. Never holds the manager
        lock (callers invoke this outside ``self._lock``). Returns True if the
        process is no longer running."""
        if proc is None:
            return True
        if timeout_sec <= 0:
            return proc.poll() is not None
        try:
            proc.wait(timeout=timeout_sec)
            return True
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            # Process may have already exited between checks.
            return proc.poll() is not None

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

    # -- Task 4 metadata / status helpers ----------------------------------

    @staticmethod
    def _entry_pid(entry: Any) -> Optional[int]:
        """Best-effort PID from an entry that may be a foreign plain dict."""
        proc = entry.get("proc") if isinstance(entry, dict) else None
        try:
            return int(proc.pid) if proc is not None and proc.pid is not None else None
        except Exception:
            return None

    def _owner_for_session(self, session_id: str) -> str:
        """Owner slot for v2 is ``user/session``; legacy keeps first segment.

        Matches the bridge's owner-slot convention without importing it. Kept
        dependency-free and defensive so cap/metadata accounting never raises.
        """
        parts = [part for part in str(session_id or "").strip().strip("/").split("/") if part]
        if len(parts) >= 4:
            return "/".join(parts[:2])
        return parts[0] if parts else ""

    def _active_count_locked(self) -> int:
        """Count live tracked processes. MUST be called holding ``self._lock``.

        This is the cap denominator (H2/H3 — counts owner slots == live
        entries). It does not mutate ``_processes`` (unlike ``list_active``); the
        net-new branch of ``spawn_result`` has already popped the dead entry it
        cares about, and a stale-dead sibling is conservatively still counted
        until the reaper/poll path clears it — never under-counting the cap.
        """
        count = 0
        for entry in self._processes.values():
            proc = entry.get("proc") if isinstance(entry, dict) else None
            try:
                if proc is not None and proc.poll() is None:
                    count += 1
            except Exception:
                continue
        return count

    def _admission_count_locked(self, *, ignore_session_id: str = "") -> int:
        count = self._active_count_locked()
        for reserved_session_id in self._reserved_sessions:
            if reserved_session_id == ignore_session_id:
                continue
            entry = self._processes.get(reserved_session_id)
            proc = entry.get("proc") if isinstance(entry, dict) else None
            try:
                if proc is not None and proc.poll() is None:
                    continue
            except Exception:
                pass
            count += 1
        return count

    def active_count(self) -> int:
        """Public live-worker count for the status endpoint / cap reporting."""
        with self._lock:
            return self._active_count_locked()

    def _touch_entry_activity(self, session_id: str, *, msg_type: str = "") -> None:
        """Stamp last_active_at/last_input_at on an entry (best-effort)."""
        now = time.time()
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                return
            entry["last_active_at"] = now
            entry["last_input_at"] = now
            # A delivered prompt means the worker is no longer warm-idle; promote
            # a 'starting'/'ready' entry to 'ready' (never override 'stopping').
            if entry.get("state") != ENTRY_STATE_STOPPING:
                entry["state"] = ENTRY_STATE_READY

    def note_output_activity(self, session_id: str) -> None:
        """Stamp last_output_at/last_active_at (called by the bridge poll path).

        Optional hook so the idle-TTL reaper (Task 7) measures idle age from the
        last OUTPUT too, not only the last input. Safe no-op for untracked ids.
        """
        now = time.time()
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                return
            entry["last_output_at"] = now
            entry["last_active_at"] = now

    def idle_age_sec(self, session_id: str, now: Optional[float] = None) -> Optional[float]:
        """Seconds since the entry's last activity, or None if untracked.

        Idle age = now - max(last_active_at, last_input_at, last_output_at,
        started_at). Used by the Task-7 reaper and the status endpoint.
        """
        ref = time.time() if now is None else now
        with self._lock:
            entry = self._processes.get(session_id)
            if entry is None:
                return None
            stamps = [
                entry.get("last_active_at"),
                entry.get("last_input_at"),
                entry.get("last_output_at"),
                entry.get("started_at"),
            ]
            last = max((s for s in stamps if s is not None), default=ref)
        return max(0.0, ref - float(last))

    def list_active_metadata(self, now: Optional[float] = None) -> List[Dict[str, Any]]:
        """Return per-session metadata dicts for the worker-status endpoint.

        One dict per ALIVE tracked worker (dead entries are skipped, matching
        ``list_active``). ``running`` is the manager's best-effort view
        (``state == ready and a prompt was the last input`` is NOT tracked here),
        so it is reported as ``None`` — the bridge merges the authoritative
        ``_SessionBridge.agent_running``. Fields: ``owner``, ``session_id``,
        ``alive``, ``running``, ``pid``, ``state``, ``idle_age_sec``,
        ``last_active_at``, ``last_input_at``, ``last_output_at``,
        ``started_at``, ``worker_epoch`` (H10 — every status field has a
        producer here).
        """
        ref = time.time() if now is None else now
        out: List[Dict[str, Any]] = []
        with self._lock:
            for session_id, entry in self._processes.items():
                proc = entry.get("proc") if isinstance(entry, dict) else None
                try:
                    alive = proc is not None and proc.poll() is None
                except Exception:
                    alive = False
                if not alive:
                    continue
                stamps = [
                    entry.get("last_active_at"),
                    entry.get("last_input_at"),
                    entry.get("last_output_at"),
                    entry.get("started_at"),
                ]
                last = max((s for s in stamps if s is not None), default=ref)
                out.append(
                    {
                        "owner": entry.get("owner") or self._owner_for_session(session_id),
                        "session_id": session_id,
                        "alive": True,
                        "running": None,
                        "pid": self._entry_pid(entry),
                        "state": entry.get("state") or ENTRY_STATE_READY,
                        "idle_age_sec": max(0.0, ref - float(last)),
                        "last_active_at": entry.get("last_active_at"),
                        "last_input_at": entry.get("last_input_at"),
                        "last_output_at": entry.get("last_output_at"),
                        "started_at": entry.get("started_at"),
                        "worker_epoch": entry.get("worker_epoch"),
                    }
                )
        return out

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
            # Task 5: read the live entry's epoch under the SAME lock that guards
            # the process table. Wave-3 (line 270): tagging is UNCONDITIONAL.
            entry = self._processes.get(session_id)
            worker_epoch = entry.get("worker_epoch") if entry else None

        # Task 5: stamp the current epoch into prompt/interrupt/answer/stop
        # payloads UNCONDITIONALLY so the worker can drop a stale message that
        # targets a previous process. Copy first - never mutate the caller's
        # dict, never overwrite a caller-supplied epoch.
        if worker_epoch and msg_type in {"prompt", "interrupt", "answer", "stop"}:
            payload = dict(payload or {})
            payload.setdefault("worker_epoch", worker_epoch)

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
        # Activity bookkeeping for idle-TTL/status (Task 4 metadata). Best-effort,
        # defensive: a foreign plain-dict entry simply has these keys added. Touch
        # only on a real enqueue, and treat a 'prompt' as the worker going busy so
        # idle-age does not reap a session that was just handed work.
        if msg_id is not None:
            self._touch_entry_activity(session_id, msg_type=msg_type)
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
        # READ path: resolve with create=False so a cold-cache first poll never
        # upserts session_runtime_dbs / moves updated_at (review #1). A session
        # with no runtime DB yet (no manifest) has nothing to poll -> [].
        try:
            db = self._get_runtime_db(session_id, create=False)
        except RuntimeDBError:
            return []
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
        # READ path: create=False so a cold first call never upserts the
        # manifest / moves updated_at (review #1); no runtime DB yet -> None.
        try:
            db = self._get_runtime_db(session_id, create=False)
        except RuntimeDBError:
            return None
        return db.reseed_output_cursor(session_id, "out")

    def latest_output_id(self, session_id: str) -> Optional[str]:
        """Return the newest output queue id for *session_id*, if any.

        Orders by the strict total order ``(created_at DESC, rowid DESC)`` to
        match Unit A's monotonic-rowid queue ordering (plan §2.3 / R1): plain
        ``created_at DESC`` could return either of two rows sharing a wall-clock
        timestamp, so the seed cursor could skip the genuinely-last row.
        """
        # Reuse the long-lived runtime handle (R2); SAME-DB invariant. READ path:
        # create=False so a cold first call never upserts the manifest (review #1).
        try:
            db = self._get_runtime_db(session_id, create=False)
        except RuntimeDBError:
            return None
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
            self._reserved_sessions.clear()
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
            self._runtime_path_cache.clear()
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
            path_keys = [k for k, value in self._runtime_path_cache.items() if value == resolved]
            for key in path_keys:
                self._runtime_path_cache.pop(key, None)
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
