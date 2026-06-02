import json
import importlib
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _register(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def _receive_until_types(ws: Any, *wanted: str, max_frames: int = 12) -> List[Dict[str, Any]]:
    frames: List[Dict[str, Any]] = []
    remaining = set(wanted)
    for _ in range(max_frames):
        frame = ws.receive_json()
        frames.append(frame)
        remaining.discard(str(frame.get("type") or ""))
        if not remaining:
            return frames
    return frames


def _session_queue_rows(db_path: Path) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT session_id, direction, msg_type, payload, processed_at "
            "FROM session_queue ORDER BY created_at ASC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(row) for row in rows]


class _DurableFakeProcessManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.live: Set[str] = set()
        self.spawned: List[str] = []
        self.sent: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []

    def is_alive(self, session_id: str) -> bool:
        return session_id in self.live

    def list_active(self) -> list[str]:
        return sorted(self.live)

    def latest_output_id(self, session_id: str) -> None:
        return None

    def spawn(self, session_id: str) -> bool:
        self.spawned.append(session_id)
        self.live.add(session_id)
        return True

    def send_input(
        self,
        session_id: str,
        msg_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if session_id not in self.live:
            return None
        self.sent.append((session_id, msg_type, payload))
        atlas_db = importlib.import_module("core.atlas_db")

        return atlas_db.AtlasDB(str(self.db_path)).enqueue_message(
            session_id,
            "in",
            msg_type,
            payload or {},
        )

    def cleanup_zombies(self) -> list[str]:
        return []


class _DeadFakeProcessManager:
    def __init__(self) -> None:
        self.spawned: List[str] = []
        self.sent: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []

    def is_alive(self, session_id: str) -> bool:
        return False

    def list_active(self) -> list[str]:
        return []

    def latest_output_id(self, session_id: str) -> None:
        return None

    def spawn(self, session_id: str) -> bool:
        self.spawned.append(session_id)
        return True

    def send_input(
        self,
        session_id: str,
        msg_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.sent.append((session_id, msg_type, payload))
        return None

    def cleanup_zombies(self) -> list[str]:
        return list(self.spawned)


def _create_isolated_app(tmp_path: Path, monkeypatch: Any, *, use_processes: bool):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1" if use_processes else "0")
    monkeypatch.setenv("ATLAS_STRICT_SESSION_ROUTING", "0")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    return atlas_ui.create_app()


def test_process_mode_ws_prompt_ack_matches_durable_session_queue(tmp_path, monkeypatch):
    db_path = tmp_path / "atlas.db"
    app = _create_isolated_app(tmp_path, monkeypatch, use_processes=True)
    manager = _DurableFakeProcessManager(db_path)
    app.state.bridge._process_manager = manager
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_deep/rtl-gen"
    text = f"deep runtime ws db input {time.time_ns()}"
    msg_id = "deep-ok-1"
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "text": text,
            "msg_id": msg_id,
            "session": session_id,
            "ip": "ip_deep",
            "workflow": "rtl-gen",
        })
        frames = _receive_until_types(ws, "agent_received", "agent_accepted")

    assert any(
        frame.get("type") == "agent_received" and frame.get("msg_id") == msg_id
        for frame in frames
    )
    accepted = [
        frame for frame in frames
        if frame.get("type") == "agent_accepted" and frame.get("msg_id") == msg_id
    ][-1]
    assert accepted["ok"] is True
    assert accepted["queued"] is True

    rows = _session_queue_rows(db_path)
    assert len(rows) == 1
    row = rows[0]
    assert row["session_id"] == session_id
    assert row["direction"] == "in"
    assert row["msg_type"] == "prompt"
    assert row["processed_at"] is None
    assert json.loads(row["payload"]) == {"text": text}
    assert manager.spawned == [session_id]
    assert manager.sent == [(session_id, "prompt", {"text": text})]


def test_process_mode_dead_worker_drop_is_not_acknowledged_as_received(tmp_path, monkeypatch):
    db_path = tmp_path / "atlas.db"
    app = _create_isolated_app(tmp_path, monkeypatch, use_processes=True)
    app.state.bridge._process_manager = _DeadFakeProcessManager()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_deep/rtl-gen"
    text = f"deep runtime dropped input {time.time_ns()}"
    msg_id = "deep-drop-1"
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "text": text,
            "msg_id": msg_id,
            "session": session_id,
            "ip": "ip_deep",
            "workflow": "rtl-gen",
        })
        frames = _receive_until_types(ws, "agent_accepted")

    assert not any(
        frame.get("type") == "agent_received" and frame.get("msg_id") == msg_id
        for frame in frames
    )
    accepted = [
        frame for frame in frames
        if frame.get("type") == "agent_accepted" and frame.get("msg_id") == msg_id
    ][-1]
    assert accepted["ok"] is False
    assert accepted["queued"] is False
    assert "input was not delivered" in accepted["error"]
    assert all(text not in (row["payload"] or "") for row in _session_queue_rows(db_path))


def test_in_process_ws_prompt_is_in_memory_not_db_session_queue(tmp_path, monkeypatch):
    db_path = tmp_path / "atlas.db"
    app = _create_isolated_app(tmp_path, monkeypatch, use_processes=False)
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_mem/rtl-gen"
    text = f"deep runtime inproc input {time.time_ns()}"
    msg_id = "deep-inproc-1"
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "text": text,
            "msg_id": msg_id,
            "session": session_id,
            "ip": "ip_mem",
            "workflow": "rtl-gen",
        })
        frames = _receive_until_types(ws, "agent_received", "agent_accepted")

    accepted = [
        frame for frame in frames
        if frame.get("type") == "agent_accepted" and frame.get("msg_id") == msg_id
    ][-1]
    assert accepted["ok"] is True
    assert accepted["queued"] is True

    session = app.state.bridge.get_session(session_id)
    assert session._inbox.get_nowait() == text
    assert _session_queue_rows(db_path) == []
