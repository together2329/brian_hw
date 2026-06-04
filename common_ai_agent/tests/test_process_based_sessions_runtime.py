"""Runtime-mode (ATLAS_RUNTIME_DB_MODE=session) coverage for SessionProcessManager.

Sibling of ``tests/test_process_based_sessions.py`` (Wave 1 / Unit B = Task 3).

Covers:

* spawn command + worker env route to the per-session RUNTIME db while the
  control db is advertised via ``ATLAS_CONTROL_DB_PATH``;
* the SAME-DB invariant — ``send_input`` / ``poll_output`` / ``latest_output_id``
  all open the SAME runtime file for one session, and the CONTROL db never
  receives that session's ``session_queue`` rows;
* hot-path connection reuse (plan §2.6 / R2): the number of NEW sqlite
  connection opens during many sequential ``poll_output`` calls is ~0 in steady
  state (we instrument ``sqlite3.connect``);
* central-mode parity: with the default router (mode=central) the spawn env is
  byte-identical to the historical single-DB behavior.
"""

import os
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter
from core.session_process_manager import SessionProcessManager


SESSION_ID = "alice/spi_core/rtl-gen"


def _runtime_env(monkeypatch, tmp_path):
    """Pin a session-mode router via env: control db + runtime root + mode."""
    control_db = tmp_path / "control.db"
    runtime_root = tmp_path / "runtime"
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", str(control_db))
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", str(runtime_root))
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    return control_db, runtime_root


class FakeProc:
    pid = 12345

    def poll(self):
        return None


def test_runtime_mode_spawn_cmd_and_env_route_to_runtime_db(monkeypatch, tmp_path):
    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    popen_calls = []

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    manager = SessionProcessManager()
    assert manager.spawn(SESSION_ID)

    assert len(popen_calls) == 1
    cmd, kwargs = popen_calls[0]
    assert cmd[:3] == [sys.executable, "-m", "core.session_worker"]

    runtime_path = manager._resolve_runtime_db_path(SESSION_ID, create=False)
    control_path = str(Path(os.path.expanduser(str(control_db))).resolve())

    # --db-path is the per-session RUNTIME file, NOT the control db.
    db_path_arg = cmd[cmd.index("--db-path") + 1]
    assert db_path_arg == runtime_path
    assert db_path_arg != control_path
    # Runtime file lives under the runtime root, sharded by uid[:2], not the
    # human-readable session_id.
    assert str(Path(runtime_root).resolve()) in runtime_path
    assert "alice" not in Path(runtime_path).name

    env = kwargs["env"]
    # Worker's primary + trace + runtime opens all point at the runtime db.
    assert env["ATLAS_DB_PATH"] == runtime_path
    assert env["ATLAS_TRACE_DB_PATH"] == runtime_path
    assert env["ATLAS_RUNTIME_DB_PATH"] == runtime_path
    # Control db is advertised separately for control-only reads.
    assert env["ATLAS_CONTROL_DB_PATH"] == control_path
    assert env["ATLAS_CONTROL_DB_PATH"] != env["ATLAS_DB_PATH"]
    assert env["ATLAS_MEMORY_DB_PATH"] == control_path


def test_v2_workspace_session_worker_starts_in_active_ip_root(monkeypatch, tmp_path):
    control_db, _runtime_root = _runtime_env(monkeypatch, tmp_path)
    atlas_root = tmp_path / "atlas-root"
    session_id = "alice/s1/spi_core/rtl-gen"
    monkeypatch.setenv("ATLAS_ROOT", str(atlas_root))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(atlas_root / "alice" / "s1"))

    popen_calls = []

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        return FakeProc()

    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    manager = SessionProcessManager(project_root=str(atlas_root / "alice" / "s1"))
    assert manager.spawn(session_id)

    assert len(popen_calls) == 1
    _cmd, kwargs = popen_calls[0]
    env = kwargs["env"]
    expected_workspace = atlas_root / "alice" / "s1"
    expected_ip_root = expected_workspace / "spi_core"
    expected_session_dir = expected_workspace / ".session" / "spi_core" / "rtl-gen"
    assert kwargs["cwd"] == str(expected_ip_root.resolve())
    assert env["ATLAS_ROOT"] == str(atlas_root.resolve())
    assert env["ATLAS_WORKSPACE_ROOT"] == str(expected_workspace.resolve())
    assert env["ATLAS_PROJECT_ROOT"] == str(expected_workspace.resolve())
    assert env["ATLAS_IP_ROOT"] == str(expected_ip_root.resolve())
    assert env["ATLAS_SESSION_DIR"] == str(expected_session_dir.resolve())
    assert env["ATLAS_CONTEXT_KEY"] == session_id
    assert env["ATLAS_ACTIVE_SESSION"] == session_id
    assert env["ATLAS_SESSION_WORKER_PARENT_PID"] == str(os.getpid())
    assert env["ATLAS_CONTROL_DB_PATH"] == str(control_db.resolve())


def test_runtime_mode_same_db_invariant_and_control_db_empty(monkeypatch, tmp_path):
    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    manager = SessionProcessManager(project_root=str(tmp_path))

    # Pretend the worker is alive so send_input enqueues.
    monkeypatch.setattr(manager, "is_alive", lambda session_id: True)

    runtime_path = manager._resolve_runtime_db_path(SESSION_ID, create=True)
    control_path = str(Path(os.path.expanduser(str(control_db))).resolve())
    assert runtime_path != control_path

    # send_input writes an inbound row to the runtime db.
    in_id = manager.send_input(SESSION_ID, "prompt", {"text": "hi"})
    assert in_id is not None

    # Simulate a worker emitting output INTO THE SAME runtime db that
    # poll_output / latest_output_id must read from.
    runtime_db = AtlasDB(runtime_path, schema_set="runtime")
    runtime_db.init_db()
    out_id = runtime_db.enqueue_message(SESSION_ID, "out", "content", {"text": "echo"})

    # latest_output_id + poll_output both resolve to the SAME runtime file.
    assert manager.latest_output_id(SESSION_ID) == out_id
    polled = manager.poll_output(SESSION_ID)
    assert [m["id"] for m in polled] == [out_id]

    # The inbound prompt landed in the runtime db (SAME-DB invariant), not control.
    runtime_conn = sqlite3.connect(runtime_path)
    try:
        runtime_in = runtime_conn.execute(
            "SELECT id FROM session_queue WHERE session_id=? AND direction='in'",
            (SESSION_ID,),
        ).fetchall()
    finally:
        runtime_conn.close()
    assert [r[0] for r in runtime_in] == [in_id]

    # The CONTROL db has NO session_queue rows for this session.
    control_conn = sqlite3.connect(control_path)
    try:
        control_rows = control_conn.execute(
            "SELECT COUNT(*) FROM session_queue WHERE session_id=?",
            (SESSION_ID,),
        ).fetchone()
    finally:
        control_conn.close()
    assert control_rows[0] == 0

    manager.stop_all()


def test_runtime_mode_poll_output_steady_state_opens_zero_connections(monkeypatch, tmp_path):
    """R2: hot-path connection reuse — opens-per-poll ~0 in steady state."""
    _runtime_env(monkeypatch, tmp_path)
    manager = SessionProcessManager(project_root=str(tmp_path))

    runtime_path = manager._resolve_runtime_db_path(SESSION_ID, create=True)

    # Instrument sqlite3.connect to count NEW physical opens.
    real_connect = sqlite3.connect
    opens = {"count": 0}
    lock = threading.Lock()

    def counting_connect(*args, **kwargs):
        with lock:
            opens["count"] += 1
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)
    # AtlasDB imported sqlite3 at module scope; patch the name it actually calls.
    import core.atlas_db as atlas_db_mod
    monkeypatch.setattr(atlas_db_mod.sqlite3, "connect", counting_connect)

    # Warm-up: first poll opens (and caches) the runtime connection.
    manager.poll_output(SESSION_ID)
    warmup_opens = opens["count"]
    assert warmup_opens >= 1, "first poll should open at least one connection"

    # Steady state: many sequential polls must NOT re-open the connection.
    opens["count"] = 0
    for _ in range(50):
        manager.poll_output(SESSION_ID)
    assert opens["count"] == 0, (
        f"expected 0 new sqlite opens across 50 steady-state polls, "
        f"got {opens['count']}"
    )

    # send_input / latest_output_id reuse the SAME cached handle too.
    monkeypatch.setattr(manager, "is_alive", lambda session_id: True)
    opens["count"] = 0
    for _ in range(10):
        manager.send_input(SESSION_ID, "prompt", {"text": "x"})
        manager.latest_output_id(SESSION_ID)
        manager.poll_output(SESSION_ID)
    assert opens["count"] == 0, (
        f"expected 0 new sqlite opens across mixed hot-path calls, "
        f"got {opens['count']}"
    )

    # Restore real connect before teardown closes handles.
    monkeypatch.setattr(sqlite3, "connect", real_connect)
    monkeypatch.setattr(atlas_db_mod.sqlite3, "connect", real_connect)
    manager.stop_all()
    _ = runtime_path  # silence unused in case path assert is later removed


def test_central_mode_default_router_env_is_behavior_identical(monkeypatch, tmp_path):
    """Default router -> mode=central -> env identical to the historical layout."""
    db_path = tmp_path / "atlas-custom.db"
    monkeypatch.delenv("ATLAS_RUNTIME_DB_MODE", raising=False)
    monkeypatch.delenv("ATLAS_CONTROL_DB_PATH", raising=False)
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")

    manager = SessionProcessManager()
    assert isinstance(manager._router, AtlasDBRouter)
    assert manager._router.mode() == "central"

    resolved = str(db_path.resolve())
    env = manager.build_worker_env(SESSION_ID)

    # In central mode control == runtime == today's single db path.
    assert env["ATLAS_DB_PATH"] == resolved
    assert env["ATLAS_TRACE_DB_PATH"] == resolved
    assert env["ATLAS_CONTROL_DB_PATH"] == resolved
    assert env["ATLAS_RUNTIME_DB_PATH"] == resolved
    assert env["ATLAS_MEMORY_DB_PATH"] == resolved
    # And the runtime-path resolver returns the control path in central mode.
    assert manager._resolve_runtime_db_path(SESSION_ID) == resolved
