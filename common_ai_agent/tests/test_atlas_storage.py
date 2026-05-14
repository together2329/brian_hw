from pathlib import Path

from core.atlas_db import AtlasDB
from core.atlas_storage import SQLiteStorage, create_atlas_storage


def test_storage_factory_defaults_to_existing_atlasdb_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("ATLAS_STORAGE_BACKEND", raising=False)

    with create_atlas_storage(tmp_path / "atlas.db") as storage:
        user = storage.create_user("default_user", "Default User")
        session = storage.create_session(user["id"], "Default Path")

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        assert db.get_session(session["id"])["title"] == "Default Path"


def test_storage_factory_keeps_legacy_backend_option(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_STORAGE_BACKEND", "legacy")

    storage = create_atlas_storage(tmp_path / "atlas.db")
    try:
        assert isinstance(storage, SQLiteStorage)
    finally:
        storage.close()


def test_storage_factory_rejects_unimplemented_backend(tmp_path: Path) -> None:
    try:
        create_atlas_storage(tmp_path / "atlas.db", backend="supabase")
    except NotImplementedError as exc:
        assert "not implemented yet" in str(exc)
    else:
        raise AssertionError("supabase backend must stay opt-in and blocked until implemented")


def test_sqlite_storage_round_trips_existing_session_contract(tmp_path: Path) -> None:
    db_path = tmp_path / "atlas.db"

    with SQLiteStorage(db_path) as storage:
        user = storage.create_user("alice", "Alice")
        session = storage.create_session(user["id"], "GPIO Bringup", project_id="gpio")
        message = storage.append_message(
            session["id"],
            "assistant",
            agent="rtl-gen",
            model_id="gpt-5.3-codex",
            provider_id="openai",
            cost=0.25,
            tokens_input=1000,
            tokens_output=200,
            tokens_reasoning=50,
        )
        part = storage.append_part(
            message["id"],
            session["id"],
            "tool",
            tool_name="run_command",
            tool_status="completed",
            tool_input={"command": "pytest tests/test_atlas_db.py"},
            tool_output="passed",
        )

        state = storage.get_session_state(session["id"])

    assert state["session"]["title"] == "GPIO Bringup"
    assert state["messages"][0]["id"] == message["id"]
    assert state["messages"][0]["parts"][0]["id"] == part["id"]
    assert state["messages"][0]["parts"][0]["tool_input"]["command"].startswith("pytest")

    with AtlasDB(str(db_path)) as db:
        assert db.get_session(session["id"])["project_id"] == "gpio"
        assert db.get_messages(session["id"])[0]["cost"] == 0.25


def test_sqlite_storage_preserves_queue_contract(tmp_path: Path) -> None:
    with SQLiteStorage(tmp_path / "atlas.db") as storage:
        msg_id = storage.enqueue_message(
            "session-a",
            direction="in",
            msg_type="user",
            payload={"text": "/ssot-rtl gpio"},
        )

        queued = storage.poll_messages("session-a", "in")
        assert [row["id"] for row in queued] == [msg_id]
        assert queued[0]["payload"] == {"text": "/ssot-rtl gpio"}

        received = storage.dequeue_message("session-a", "in", timeout=0.01)
        assert received["id"] == msg_id
        assert received["processed_at"] is not None

        storage.acknowledge_message(msg_id)
        assert storage.poll_messages("session-a", "in") == []


def test_sqlite_storage_admin_usage_matches_existing_payload_shape(tmp_path: Path) -> None:
    with SQLiteStorage(tmp_path / "atlas.db") as storage:
        user = storage.create_user("admin", "Admin", role="admin")
        session = storage.create_session(user["id"], "Timer Run", project_id="timer")
        storage.append_message(
            session["id"],
            "assistant",
            model_id="gpt-5.3-codex",
            cost=1.5,
            tokens_input=3000,
            tokens_output=700,
            tokens_reasoning=100,
        )

        usage = storage.get_admin_usage()

    assert usage["users"][0]["username"] == "admin"
    assert usage["users"][0]["total_cost_usd"] == 1.5
    assert usage["cost_by_context"][0]["ip"] == "timer"
    assert usage["cost_by_date"][0]["calls"] == 1
