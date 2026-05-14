import os
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


@pytest.fixture(scope="module")
def dummy_worker_script():
    path = _make_dummy_worker_file(PROJECT_ROOT)
    yield path
    try:
        os.unlink(path)
    except OSError:
        pass


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
    assert env["ATLAS_TRACE_ENABLE"] == "1"
    assert env["ATLAS_TRACE_DB_PATH"] == db_path
    assert env["ATLAS_PROJECT_ROOT"] == str(tmp_path)
