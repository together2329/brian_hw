import os
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import pytest

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from core.atlas_db import AtlasDB
from core.atlas_multiuser import _MultiUserBridge
from core.session_process_manager import SessionProcessManager


DUMMY_WORKER_TEMPLATE = """import sys
import time
sys.path.insert(0, "__PROJECT_ROOT__")
from core.atlas_db import AtlasDB

session_id = sys.argv[sys.argv.index("--session-id") + 1]
db_path = None
if "--db-path" in sys.argv:
    db_path = sys.argv[sys.argv.index("--db-path") + 1]

db = AtlasDB(db_path)
db.init_db()
db.enqueue_message(session_id, "out", "system", {"text": "worker_started"})

last_activity = time.time()
while time.time() - last_activity < 30:
    msg = db.dequeue_message(session_id, "in", timeout=1.0)
    if msg:
        last_activity = time.time()
        payload = msg.get("payload", {})
        text = payload.get("text", "")
        db.enqueue_message(session_id, "out", "content", {"text": f"echo:{session_id}:{text}"})
        if msg.get("msg_type") == "stop":
            break
    time.sleep(0.05)

db.enqueue_message(session_id, "out", "system", {"text": "worker_exited"})
"""


def _make_dummy_worker_file(project_root: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".py", prefix="dummy_worker_")
    content = DUMMY_WORKER_TEMPLATE.replace("__PROJECT_ROOT__", project_root)
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def _temp_db() -> str:
    fd, path = tempfile.mkstemp(suffix=".db", prefix="test_atlas_")
    os.close(fd)
    return path


class DummyProcessManager(SessionProcessManager):
    def __init__(self, db_path=None, dummy_script_path=None):
        super().__init__(db_path=db_path)
        self._dummy_script_path = dummy_script_path

    def spawn(self, session_id, db_path=None):
        with self._lock:
            if session_id in self._processes:
                if self.is_alive(session_id):
                    return True
                self._processes.pop(session_id, None)

        cmd = [
            sys.executable,
            self._dummy_script_path,
            "--session-id",
            session_id,
        ]
        effective_db = db_path or self.db_path
        if effective_db:
            cmd.extend(["--db-path", effective_db])

        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        with self._lock:
            self._processes[session_id] = {
                "proc": proc,
                "started_at": time.time(),
            }
        return True

    def spawn_result(self, session_id, db_path=None, policy=None, *, replacing=None, reserve=False):
        # The bridge now admits workers via spawn_result (the Task-4 source of
        # truth); this double overrides the dummy spawn(), so spawn_result must
        # delegate to it (otherwise the inherited real spawn_result would Popen a
        # real core.session_worker and bypass the dummy script).
        from core.session_process_manager import (
            SPAWN_STATUS_CAPACITY_WAIT,
            SPAWN_STATUS_READY,
            SPAWN_STATUS_STARTED,
            SpawnResult,
        )

        owner = self._owner_for_session(session_id)
        if self.is_alive(session_id):
            with self._lock:
                self._reserved_sessions.discard(session_id)
            return SpawnResult(
                ok=True, status=SPAWN_STATUS_READY, session_id=session_id,
                owner=owner, pid=self.get_pid(session_id),
            )
        with self._lock:
            has_reservation = session_id in self._reserved_sessions
            active_count = self._admission_count_locked(ignore_session_id=session_id)
        if (
            policy is not None
            and not has_reservation
            and not reserve
            and policy.cap_exceeded(active_count)
        ):
            return SpawnResult(
                ok=False,
                status=SPAWN_STATUS_CAPACITY_WAIT,
                reason="max_active",
                session_id=session_id,
                owner=owner,
                active_count=active_count,
                max_active=getattr(policy, "max_active", 0),
            )
        ok = bool(self.spawn(session_id, db_path=db_path))
        with self._lock:
            self._reserved_sessions.discard(session_id)
        return SpawnResult(
            ok=ok, status=SPAWN_STATUS_STARTED if ok else "capacity_wait",
            session_id=session_id, owner=owner, pid=self.get_pid(session_id),
            active_count=active_count + 1 if ok else active_count,
            max_active=getattr(policy, "max_active", 0),
        )


@pytest.fixture(scope="module")
def dummy_worker_script():
    path = _make_dummy_worker_file(PROJECT_ROOT)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


def test_session_process_manager_spawns_worker_from_project_root(monkeypatch, tmp_path):
    db_path = tmp_path / "atlas-custom.db"
    popen_calls = []

    class FakeProc:
        pid = 12345

        def poll(self):
            return None

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        return FakeProc()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    monkeypatch.delenv("PYTHONPATH", raising=False)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)

    manager = SessionProcessManager()
    assert manager.spawn("alice/spi_core/rtl-gen")

    assert len(popen_calls) == 1
    cmd, kwargs = popen_calls[0]
    assert cmd[:3] == [sys.executable, "-m", "core.session_worker"]
    assert cmd[cmd.index("--db-path") + 1] == str(db_path.resolve())
    assert kwargs["cwd"] == str(tmp_path.resolve())
    env = kwargs["env"]
    assert env["ATLAS_DB_PATH"] == str(db_path.resolve())
    assert env["ATLAS_TRACE_DB_PATH"] == str(db_path.resolve())
    assert env["ATLAS_PROJECT_ROOT"] == str(tmp_path.resolve())
    assert env["ATLAS_SOURCE_ROOT"] == str(Path(PROJECT_ROOT).resolve())
    assert env["COMMON_AI_AGENT_HOME"] == str(Path(PROJECT_ROOT).resolve())
    assert env["ATLAS_ACTIVE_SESSION"] == "alice/spi_core/rtl-gen"
    assert env["ATLAS_DEFAULT_SESSION_ID"] == "alice"
    assert env["ATLAS_ACTIVE_IP"] == "spi_core"
    assert env["ATLAS_DEFAULT_WORKFLOW"] == "rtl-gen"
    assert env["ACTIVE_WORKSPACE"] == "rtl-gen"
    pythonpath = env["PYTHONPATH"].split(os.pathsep)
    assert str(Path(PROJECT_ROOT).resolve()) in pythonpath
    assert str((Path(PROJECT_ROOT) / "src").resolve()) in pythonpath


def test_session_process_manager_uses_base_python_when_sys_executable_is_py_launcher(monkeypatch):
    monkeypatch.setattr(os, "name", "nt", raising=False)
    monkeypatch.setattr(sys, "executable", r"C:\Windows\py.exe")
    monkeypatch.setattr(sys, "_base_executable", r"C:\Python312\python.exe", raising=False)

    assert SessionProcessManager._worker_python_executable() == r"C:\Python312\python.exe"


def test_send_input_bounds_session_queue_busy_timeout(monkeypatch):
    manager = SessionProcessManager(db_path=":memory:")
    enqueue_calls = []

    class FakeDB:
        def enqueue_message(self, *args, **kwargs):
            enqueue_calls.append((args, kwargs))
            return "queued-1"

        def close(self):
            pass

    monkeypatch.setattr(manager, "is_alive", lambda session_id: True)
    monkeypatch.setattr(manager, "_get_db", lambda: FakeDB())

    msg_id = manager.send_input("alice/spi_core/rtl-gen", "prompt", {"text": "hi"})

    assert msg_id == "queued-1"
    assert enqueue_calls
    assert 0 < enqueue_calls[0][1]["busy_timeout_ms"] <= 4500


def test_spawn_prunes_orphan_same_session_worker(monkeypatch, tmp_path):
    db_path = tmp_path / "atlas-custom.db"
    session_id = "alice/spi_core/ssot-gen"
    killed = []
    popen_calls = []
    terminated = set()

    class FakeRunResult:
        stdout = (
            f"111 {sys.executable} -m core.session_worker "
            f"--session-id {session_id} --db-path {db_path.resolve()}\n"
            f"222 {sys.executable} -m core.session_worker "
            f"--session-id alice/other/ssot-gen --db-path {db_path.resolve()}\n"
            f"333 {sys.executable} -m core.session_worker "
            f"--session-id {session_id} --db-path {tmp_path / 'other.db'}\n"
        )

    class FakeProc:
        pid = 444

        def poll(self):
            return None

    def fake_run(cmd, **kwargs):
        assert cmd == ["ps", "-axo", "pid=,command="]
        return FakeRunResult()

    def fake_kill(pid, sig):
        if sig == 0:
            if pid in terminated:
                raise ProcessLookupError
            return
        killed.append((pid, sig))
        terminated.add(pid)

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        return FakeProc()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setattr(subprocess, "run", fake_run)
    monkeypatch.setattr(subprocess, "Popen", fake_popen)
    monkeypatch.setattr(os, "kill", fake_kill)

    manager = SessionProcessManager()
    assert manager.spawn(session_id)

    assert killed == [(111, signal.SIGTERM)]
    assert len(popen_calls) == 1
    assert popen_calls[0][0][popen_calls[0][0].index("--session-id") + 1] == session_id


def test_process_bridge_seeds_output_cursor_before_fresh_spawn():
    class FakeManager:
        def __init__(self):
            self.spawned = []
            self.sent = []

        def is_alive(self, session_id):
            return False

        def latest_output_id(self, session_id):
            assert session_id == "admin/spi_core/tb-gen"
            return "old-output-row"

        def spawn(self, session_id):
            self.spawned.append(session_id)
            return True

        def list_active(self):
            return []

        def send_input(self, session_id, msg_type, payload=None):
            self.sent.append((session_id, msg_type, payload))
            return "new-input-row"

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/tb-gen", "hello")

    assert delivered is True
    assert bridge._process_output_cursors["admin/spi_core/tb-gen"] == "old-output-row"
    assert fake.spawned == ["admin/spi_core/tb-gen"]
    assert fake.sent == [("admin/spi_core/tb-gen", "prompt", {"text": "hello"})]


def test_process_bridge_autostart_seeds_output_cursor():
    class FakeManager:
        def __init__(self):
            self.spawned = []

        def is_alive(self, session_id):
            return False

        def latest_output_id(self, session_id):
            assert session_id == "admin/default/default"
            return "old-default-output-row"

        def spawn(self, session_id):
            self.spawned.append(session_id)
            return True

        def list_active(self):
            return []

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake
    bridge.activate_session("admin/default/default")

    bridge.ensure_agent_alive()

    assert bridge._process_output_cursors["admin/default/default"] == "old-default-output-row"
    assert fake.spawned == ["admin/default/default"]


def test_process_bridge_warm_activation_spawns_worker_without_prompt():
    class FakeManager:
        def __init__(self):
            self.live = set()
            self.spawned = []
            self.sent = []

        def is_alive(self, session_id):
            return session_id in self.live

        def latest_output_id(self, session_id):
            assert session_id == "admin/spi_core/ssot-gen"
            return "old-warm-output-row"

        def spawn(self, session_id):
            self.spawned.append(session_id)
            self.live.add(session_id)
            return True

        def list_active(self):
            return sorted(self.live)

        def get_pid(self, session_id):
            return 4321 if session_id in self.live else 0

        def send_input(self, session_id, msg_type, payload=None):
            self.sent.append((session_id, msg_type, payload))
            return "unexpected-input-row"

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    bridge.activate_session("admin/spi_core/ssot-gen", warm=True)

    session = bridge.get_session("admin/spi_core/ssot-gen")
    assert bridge._process_output_cursors["admin/spi_core/ssot-gen"] == "old-warm-output-row"
    assert fake.spawned == ["admin/spi_core/ssot-gen"]
    assert fake.sent == []
    assert session.agent_alive is True
    assert session.agent_running is False

    events = []
    while True:
        try:
            events.append(session._outbox.get_nowait())
        except Exception:
            break
    assert any(
        event.get("type") == "agent_state"
        and event.get("alive") is True
        and event.get("running") is False
        for event in events
    )


def test_process_bridge_reports_worker_death_after_prompt_before_output_poll():
    class FakeManager:
        def __init__(self):
            self.live = False
            self.spawned = []
            self.cleaned = False

        def is_alive(self, session_id):
            return self.live

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            self.live = True
            return True

        def send_input(self, session_id, msg_type, payload=None):
            self.live = False
            return "queued-input-row"

        def cleanup_zombies(self):
            if self.spawned and not self.live and not self.cleaned:
                self.cleaned = True
                return [self.spawned[-1]]
            return []

        def list_active(self):
            return [self.spawned[-1]] if self.live and self.spawned else []

        def poll_output(self, session_id, since_id=None):
            return []

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "hi")
    assert delivered is True
    session = bridge.get_session("admin/spi_core/default")
    assert session.agent_running is True

    bridge._poll_process_outputs()

    assert session.agent_running is False
    assert session.agent_alive is False
    events = []
    while True:
        try:
            events.append(session._outbox.get_nowait())
        except Exception:
            break
    assert any(
        event.get("type") == "agent_state"
        and event.get("running") is False
        and event.get("alive") is False
        for event in events
    )
    assert any(event.get("type") == "worker_exited" for event in events)
    assert any(event.get("type") == "done" for event in events)


def test_process_bridge_reports_prompt_delivery_failure():
    class FakeManager:
        def __init__(self):
            self.spawned = []

        def is_alive(self, session_id):
            return False

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.spawned.append(session_id)
            return True

        def list_active(self):
            return []

        def send_input(self, session_id, msg_type, payload=None):
            return None

        def cleanup_zombies(self):
            return list(self.spawned)

    bridge = _MultiUserBridge(single_user=False, use_processes=True)
    fake = FakeManager()
    bridge._process_manager = fake

    delivered = bridge.submit_prompt_for_session("admin/spi_core/default", "hi")

    assert delivered is False
    session = bridge.get_session("admin/spi_core/default")
    assert session.agent_running is False
    assert session.agent_alive is False
    events = []
    while True:
        try:
            events.append(session._outbox.get_nowait())
        except Exception:
            break
    assert any(event.get("type") == "worker_exited" for event in events)
    assert any(
        event.get("type") == "error"
        and "input was not delivered" in event.get("message", "")
        for event in events
    )


def test_spawn_multiple_sessions(dummy_worker_script):
    db_path = _temp_db()
    manager = DummyProcessManager(db_path=db_path, dummy_script_path=dummy_worker_script)
    try:
        for i in range(3):
            manager.spawn(f"sess-{i}")

        time.sleep(0.3)

        pids = []
        for i in range(3):
            sid = f"sess-{i}"
            assert manager.is_alive(sid), f"Session {sid} should be alive"
            pid = manager.get_pid(sid)
            assert pid is not None
            pids.append(pid)

        assert len(set(pids)) == 3, f"Expected 3 unique PIDs, got {pids}"
    finally:
        manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_send_input_isolated(dummy_worker_script):
    db_path = _temp_db()
    manager = DummyProcessManager(db_path=db_path, dummy_script_path=dummy_worker_script)
    try:
        sessions = ["sess-a", "sess-b", "sess-c"]
        for sid in sessions:
            manager.spawn(sid)

        time.sleep(0.3)

        for sid in sessions:
            manager.send_input(sid, "prompt", {"text": f"hello-{sid}"})

        time.sleep(0.3)

        for sid in sessions:
            msgs = manager.poll_output(sid)
            content_msgs = [m for m in msgs if m.get("msg_type") == "content"]
            assert len(content_msgs) == 1, (
                f"Expected 1 content msg for {sid}, got {len(content_msgs)}"
            )
            payload = content_msgs[0].get("payload", {})
            expected = f"hello-{sid}"
            assert expected in str(payload.get("text", "")), (
                f"Wrong text for {sid}: {payload}"
            )
    finally:
        manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_poll_output_isolated(dummy_worker_script):
    db_path = _temp_db()
    manager = DummyProcessManager(db_path=db_path, dummy_script_path=dummy_worker_script)
    try:
        sessions = ["sess-x", "sess-y", "sess-z"]
        for sid in sessions:
            manager.spawn(sid)

        time.sleep(0.3)

        for sid in sessions:
            manager.send_input(sid, "prompt", {"text": f"data-{sid}"})

        time.sleep(0.3)

        for sid in sessions:
            msgs = manager.poll_output(sid)
            texts = [
                str(m.get("payload", {}).get("text", ""))
                for m in msgs
                if m.get("msg_type") == "content"
            ]
            for t in texts:
                assert sid in t, f"Output for {sid} contains wrong data: {t}"

            other_sessions = [s for s in sessions if s != sid]
            for t in texts:
                for other in other_sessions:
                    assert other not in t, (
                        f"Output for {sid} leaked data from {other}: {t}"
                    )
    finally:
        manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_multiuser_bridge_process_mode(dummy_worker_script):
    db_path = _temp_db()
    bridge = _MultiUserBridge(use_processes=True)
    bridge._process_manager = DummyProcessManager(
        db_path=db_path, dummy_script_path=dummy_worker_script
    )

    try:
        bridge.activate_session("sess-1")
        bridge.submit_prompt("prompt-1")

        bridge.activate_session("sess-2")
        bridge.submit_prompt("prompt-2")

        time.sleep(0.5)

        bridge._poll_process_outputs()

        sess1 = bridge.get_session("sess-1")
        sess2 = bridge.get_session("sess-2")

        out1 = []
        while True:
            try:
                out1.append(sess1._outbox.get_nowait())
            except Exception:
                break

        out2 = []
        while True:
            try:
                out2.append(sess2._outbox.get_nowait())
            except Exception:
                break

        texts1 = [e.get("text", "") for e in out1]
        texts2 = [e.get("text", "") for e in out2]

        assert any("prompt-1" in t for t in texts1), (
            f"sess-1 should have prompt-1 echo: {texts1}"
        )
        assert any("prompt-2" in t for t in texts2), (
            f"sess-2 should have prompt-2 echo: {texts2}"
        )

        for t in texts1:
            assert "prompt-2" not in t, f"sess-1 leaked prompt-2: {t}"
        for t in texts2:
            assert "prompt-1" not in t, f"sess-2 leaked prompt-1: {t}"
    finally:
        if bridge._process_manager:
            bridge._process_manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_multiuser_bridge_process_mode_routes_explicit_sessions(dummy_worker_script):
    db_path = _temp_db()
    bridge = _MultiUserBridge(use_processes=True)
    bridge._process_manager = DummyProcessManager(
        db_path=db_path, dummy_script_path=dummy_worker_script
    )

    try:
        bridge.submit_prompt_for_session("user-a", "prompt-a")
        bridge.submit_prompt_for_session("user-b", "prompt-b")

        time.sleep(0.5)

        assert bridge._process_manager.is_alive("user-a")
        assert bridge._process_manager.is_alive("user-b")
        assert set(bridge._process_manager.list_active()) >= {"user-a", "user-b"}

        bridge._poll_process_outputs()

        sess_a = bridge.get_session("user-a")
        sess_b = bridge.get_session("user-b")

        events_a = []
        while True:
            try:
                events_a.append(sess_a._outbox.get_nowait())
            except Exception:
                break

        events_b = []
        while True:
            try:
                events_b.append(sess_b._outbox.get_nowait())
            except Exception:
                break

        texts_a = [str(event.get("text") or "") for event in events_a]
        texts_b = [str(event.get("text") or "") for event in events_b]

        assert any("prompt-a" in text for text in texts_a), texts_a
        assert any("prompt-b" in text for text in texts_b), texts_b
        assert all("prompt-b" not in text for text in texts_a), texts_a
        assert all("prompt-a" not in text for text in texts_b), texts_b
    finally:
        if bridge._process_manager:
            bridge._process_manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_single_worker_per_owner_kills_previous_owner_worker(monkeypatch, dummy_worker_script):
    db_path = _temp_db()
    monkeypatch.setenv("ATLAS_SESSION_WORKER_POLICY", "single-active-owner")
    bridge = _MultiUserBridge(use_processes=True, single_worker_per_owner=True)
    bridge._process_manager = DummyProcessManager(
        db_path=db_path, dummy_script_path=dummy_worker_script
    )

    try:
        bridge.submit_prompt_for_session("alice/ip_a/rtl-gen", "prompt-a")
        bridge.submit_prompt_for_session("bob/ip_b/rtl-gen", "prompt-b")
        time.sleep(0.3)

        assert bridge._process_manager.is_alive("alice/ip_a/rtl-gen")
        assert bridge._process_manager.is_alive("bob/ip_b/rtl-gen")

        bridge.submit_prompt_for_session("alice/ip_a/tb-gen", "prompt-c")
        time.sleep(0.3)

        assert not bridge._process_manager.is_alive("alice/ip_a/rtl-gen")
        assert bridge._process_manager.is_alive("alice/ip_a/tb-gen")
        assert bridge._process_manager.is_alive("bob/ip_b/rtl-gen")
        assert bridge.get_session("alice/ip_a/rtl-gen").agent_alive is False
        assert bridge.get_session("alice/ip_a/rtl-gen").agent_running is False
    finally:
        if bridge._process_manager:
            bridge._process_manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_kill_and_cleanup(dummy_worker_script):
    db_path = _temp_db()
    manager = DummyProcessManager(db_path=db_path, dummy_script_path=dummy_worker_script)
    try:
        manager.spawn("sess-kill")
        time.sleep(0.3)
        assert manager.is_alive("sess-kill")

        manager.kill("sess-kill")
        time.sleep(0.2)
        assert not manager.is_alive("sess-kill")

        manager.spawn("sess-kill")
        time.sleep(0.3)
        assert manager.is_alive("sess-kill")

        manager.kill("sess-kill")
        time.sleep(0.2)

        cleaned = manager.cleanup_zombies()
        assert "sess-kill" in cleaned or not manager.is_alive("sess-kill")
    finally:
        manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_bridge_exit_session_kills_only_target_worker(dummy_worker_script):
    db_path = _temp_db()
    bridge = _MultiUserBridge(use_processes=True)
    bridge._process_manager = DummyProcessManager(
        db_path=db_path, dummy_script_path=dummy_worker_script
    )

    try:
        bridge.submit_prompt_for_session("user-a", "prompt-a")
        bridge.submit_prompt_for_session("user-b", "prompt-b")
        time.sleep(0.3)

        assert bridge._process_manager.is_alive("user-a")
        assert bridge._process_manager.is_alive("user-b")

        bridge.exit_session("user-a")
        time.sleep(0.2)

        assert not bridge._process_manager.is_alive("user-a")
        assert bridge._process_manager.is_alive("user-b")
        assert bridge.get_session("user-a").agent_alive is False
    finally:
        if bridge._process_manager:
            bridge._process_manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_stop_all(dummy_worker_script):
    db_path = _temp_db()
    manager = DummyProcessManager(db_path=db_path, dummy_script_path=dummy_worker_script)
    try:
        for i in range(3):
            manager.spawn(f"sess-stop-{i}")

        time.sleep(0.3)

        for i in range(3):
            assert manager.is_alive(f"sess-stop-{i}")

        manager.stop_all()
        time.sleep(0.2)

        for i in range(3):
            assert not manager.is_alive(f"sess-stop-{i}")
    finally:
        manager.stop_all()
        try:
            os.unlink(db_path)
        except OSError:
            pass


def test_worker_env_is_derived_from_session_key(tmp_path: Path, monkeypatch):
    db_path = str(tmp_path / "atlas.db")
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    manager = SessionProcessManager(db_path=db_path)

    env = manager.build_worker_env("alice/dma/rtl-gen")

    assert env["ATLAS_ACTIVE_SESSION"] == "alice/dma/rtl-gen"
    assert env["ATLAS_DEFAULT_SESSION_ID"] == "alice"
    assert env["ATLAS_ACTIVE_IP"] == "dma"
    assert env["ATLAS_DEFAULT_WORKFLOW"] == "rtl-gen"
    assert env["ACTIVE_WORKSPACE"] == "rtl-gen"
    assert env["ATLAS_TRACE_ENABLE"] == "1"
    assert env["ATLAS_TRACE_DB_PATH"] == db_path
    assert env["ATLAS_PROJECT_ROOT"] == str(tmp_path)


def test_session_worker_bootstraps_session_and_workspace_before_chat_loop(
    tmp_path: Path,
    monkeypatch,
):
    from core import session_worker

    calls = []

    class FakeAgent:
        def _setup_session(self, session_id):
            calls.append(("session", session_id))

        def _setup_workspace(self, workflow):
            calls.append(("workspace", workflow))

        def chat_loop(self):
            calls.append((
                "chat_loop",
                os.environ.get("ATLAS_ACTIVE_SESSION"),
                os.environ.get("ACTIVE_WORKSPACE"),
            ))

    fake_agent = FakeAgent()
    real_import = session_worker.importlib.import_module

    def fake_import(name, *args, **kwargs):
        if name == "main":
            return fake_agent
        return real_import(name, *args, **kwargs)

    for key in (
        "ATLAS_ACTIVE_SESSION",
        "ATLAS_DEFAULT_SESSION_ID",
        "ATLAS_ACTIVE_IP",
        "ATLAS_DEFAULT_WORKFLOW",
        "ACTIVE_WORKSPACE",
        "ATLAS_SESSION_APPLIED",
    ):
        monkeypatch.setenv(key, "")
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(session_worker, "_agent", None)
    monkeypatch.setattr(session_worker.importlib, "import_module", fake_import)
    monkeypatch.setattr(session_worker, "_install_signal_handlers", lambda: None)

    rc = session_worker.run_worker(
        "alice/spi_core/orchestrator",
        str(tmp_path / "atlas.db"),
    )

    assert rc == 0
    assert calls[:3] == [
        ("session", "alice/spi_core/orchestrator"),
        ("workspace", "orchestrator"),
        ("chat_loop", "alice/spi_core/orchestrator", "orchestrator"),
    ]
    assert os.environ["ATLAS_SESSION_APPLIED"] == "alice/spi_core/orchestrator"
