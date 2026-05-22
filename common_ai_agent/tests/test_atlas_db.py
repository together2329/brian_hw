import threading
import time
import pytest
import sqlite3
from pathlib import Path

from core.atlas_db import AtlasDB


@pytest.fixture
def db(tmp_path):
    db_path = str(tmp_path / "test_atlas.db")
    atlas = AtlasDB(db_path)
    atlas.init_db()
    yield atlas
    atlas.close()


@pytest.fixture
def memory_db():
    atlas = AtlasDB(":memory:")
    atlas.init_db()
    yield atlas
    atlas.close()


class TestUsers:
    def test_create_user(self, db):
        user = db.create_user("alice", "Alice", password_hash="hash123")
        assert user["username"] == "alice"
        assert user["display_name"] == "Alice"
        assert user["password_hash"] == "hash123"
        assert user["role"] == "user"
        assert isinstance(user["id"], str) and len(user["id"]) == 32
        assert isinstance(user["created_at"], float)

    def test_get_user(self, db):
        created = db.create_user("bob", "Bob")
        fetched = db.get_user(created["id"])
        assert fetched is not None
        assert fetched["username"] == "bob"
        assert fetched["display_name"] == "Bob"

    def test_get_user_missing(self, db):
        assert db.get_user("nonexistent") is None

    def test_get_user_by_username(self, db):
        db.create_user("carol", "Carol")
        fetched = db.get_user_by_username("carol")
        assert fetched is not None
        assert fetched["username"] == "carol"

    def test_user_email_lookup_and_reset_token(self, db):
        user = db.create_user("erin", "Erin", email="Erin@Example.COM")
        assert user["email"] == "erin@example.com"
        assert db.get_user_by_email("ERIN@example.com")["id"] == user["id"]

        with pytest.raises(sqlite3.IntegrityError):
            db.create_user("erin2", "Erin 2", email="erin@example.com")

        db.set_user_password_reset(user["id"], "token-hash", time.time() + 60)
        assert db.get_user_by_password_reset_token_hash("token-hash")["id"] == user["id"]

        db.update_user_password(user["id"], "hash-new")
        refreshed = db.get_user(user["id"])
        assert refreshed["password_hash"] == "hash-new"
        assert refreshed["password_reset_token_hash"] is None


class TestSessions:
    def test_create_session(self, db):
        user = db.create_user("dave", "Dave")
        session = db.create_session(user["id"], "Test Session", project_id="proj-1")
        assert session["title"] == "Test Session"
        assert session["user_id"] == user["id"]
        assert session["project_id"] == "proj-1"
        assert session["status"] == "active"
        assert session["directory"] == str(Path.cwd())
        assert isinstance(session["id"], str) and len(session["id"]) == 32

    def test_get_session(self, db):
        user = db.create_user("eve", "Eve")
        created = db.create_session(user["id"], "Get Me")
        fetched = db.get_session(created["id"])
        assert fetched is not None
        assert fetched["title"] == "Get Me"

    def test_get_session_missing(self, db):
        assert db.get_session("nonexistent") is None

    def test_list_sessions(self, db):
        user = db.create_user("frank", "Frank")
        s1 = db.create_session(user["id"], "Session 1")
        s2 = db.create_session(user["id"], "Session 2")
        time.sleep(0.01)
        s3 = db.create_session(user["id"], "Session 3")
        db.archive_session(s2["id"])

        active = db.list_sessions(user["id"], status="active")
        assert len(active) == 2
        assert active[0]["id"] == s3["id"]

        archived = db.list_sessions(user["id"], status="archived")
        assert len(archived) == 1
        assert archived[0]["id"] == s2["id"]

    def test_update_session(self, db):
        user = db.create_user("grace", "Grace")
        session = db.create_session(user["id"], "Old Title")
        db.update_session(session["id"], title="New Title", project_id="proj-x")
        fetched = db.get_session(session["id"])
        assert fetched["title"] == "New Title"
        assert fetched["project_id"] == "proj-x"
        assert fetched["updated_at"] > session["updated_at"]

    def test_update_session_with_json_summary(self, db):
        user = db.create_user("hank", "Hank")
        session = db.create_session(user["id"], "Summary Test")
        summary = {"key": "value", "items": [1, 2, 3]}
        db.update_session(session["id"], summary=summary)
        fetched = db.get_session(session["id"])
        assert fetched["summary"] == summary

    def test_archive_session(self, db):
        user = db.create_user("ivy", "Ivy")
        session = db.create_session(user["id"], "To Archive")
        db.archive_session(session["id"])
        fetched = db.get_session(session["id"])
        assert fetched["status"] == "archived"
        assert isinstance(fetched["archived_at"], float)

    def test_delete_session(self, db):
        user = db.create_user("jack", "Jack")
        session = db.create_session(user["id"], "To Delete")
        msg = db.save_message(session["id"], "user", agent="test")
        db.save_part(msg["id"], session["id"], "text", text="hello")

        db.delete_session(session["id"])
        assert db.get_session(session["id"]) is None
        assert db.get_messages(session["id"]) == []
        assert db.get_parts(msg["id"]) == []


class TestMessages:
    def test_save_message(self, db):
        user = db.create_user("kate", "Kate")
        session = db.create_session(user["id"], "Msg Test")
        msg = db.save_message(
            session["id"],
            "assistant",
            agent="build",
            model_id="gpt-4",
            provider_id="openai",
            cost=0.05,
            tokens_input=100,
            tokens_output=50,
            tokens_reasoning=10,
        )
        assert msg["role"] == "assistant"
        assert msg["agent"] == "build"
        assert msg["model_id"] == "gpt-4"
        assert msg["cost"] == 0.05
        assert msg["tokens_input"] == 100
        assert msg["tokens_output"] == 50
        assert msg["tokens_reasoning"] == 10
        assert msg["error"] is None

    def test_save_message_with_error(self, db):
        user = db.create_user("leo", "Leo")
        session = db.create_session(user["id"], "Error Test")
        error = {"code": 500, "message": "boom"}
        msg = db.save_message(session["id"], "system", error=error)
        fetched = db.get_messages(session["id"])
        assert len(fetched) == 1
        assert fetched[0]["error"] == error

    def test_get_messages_ordering(self, db):
        user = db.create_user("mia", "Mia")
        session = db.create_session(user["id"], "Order Test")
        m1 = db.save_message(session["id"], "user")
        time.sleep(0.01)
        m2 = db.save_message(session["id"], "assistant")
        time.sleep(0.01)
        m3 = db.save_message(session["id"], "user")

        messages = db.get_messages(session["id"])
        assert [m["id"] for m in messages] == [m1["id"], m2["id"], m3["id"]]


class TestParts:
    def test_save_text_part(self, db):
        user = db.create_user("noah", "Noah")
        session = db.create_session(user["id"], "Part Test")
        msg = db.save_message(session["id"], "assistant")
        part = db.save_part(msg["id"], session["id"], "text", text="Hello world")
        assert part["type"] == "text"
        assert part["text"] == "Hello world"

    def test_save_tool_part(self, db):
        user = db.create_user("olivia", "Olivia")
        session = db.create_session(user["id"], "Tool Test")
        msg = db.save_message(session["id"], "assistant")
        tool_input = {"path": "/tmp/test.txt"}
        part = db.save_part(
            msg["id"],
            session["id"],
            "tool",
            tool_name="read_file",
            call_id="call-1",
            tool_status="completed",
            tool_input=tool_input,
            tool_output="file contents",
            tool_title="Read File",
            start_time=time.time(),
            end_time=time.time(),
        )
        assert part["tool_name"] == "read_file"
        assert part["tool_status"] == "completed"
        assert part["tool_input"] == tool_input

    def test_get_parts_with_json_roundtrip(self, db):
        user = db.create_user("paul", "Paul")
        session = db.create_session(user["id"], "JSON Test")
        msg = db.save_message(session["id"], "assistant")
        patch_files = ["a.py", "b.py"]
        part = db.save_part(
            msg["id"],
            session["id"],
            "patch",
            patch_hash="abc123",
            patch_files=patch_files,
        )
        fetched = db.get_parts(msg["id"])
        assert len(fetched) == 1
        assert fetched[0]["patch_files"] == patch_files
        assert fetched[0]["patch_hash"] == "abc123"

    def test_get_parts_ordering(self, db):
        user = db.create_user("quinn", "Quinn")
        session = db.create_session(user["id"], "Part Order")
        msg = db.save_message(session["id"], "assistant")
        p1 = db.save_part(msg["id"], session["id"], "text", text="first")
        time.sleep(0.01)
        p2 = db.save_part(msg["id"], session["id"], "text", text="second")

        parts = db.get_parts(msg["id"])
        assert [p["id"] for p in parts] == [p1["id"], p2["id"]]


class TestWSConnections:
    def test_create_ws_connection(self, db):
        user = db.create_user("ruby", "Ruby")
        session = db.create_session(user["id"], "WS Test")
        conn = db.create_ws_connection("conn-1", user["id"], session["id"], client_ip="127.0.0.1")
        assert conn["connection_id"] == "conn-1"
        assert conn["user_id"] == user["id"]
        assert conn["client_ip"] == "127.0.0.1"
        assert isinstance(conn["connected_at"], float)

    def test_update_ws_ping(self, db):
        user = db.create_user("sam", "Sam")
        session = db.create_session(user["id"], "Ping Test")
        conn = db.create_ws_connection("conn-2", user["id"], session["id"])
        original_ping = conn["last_ping_at"]
        time.sleep(0.01)
        db.update_ws_ping("conn-2")
        fetched = db.get_ws_connections(user_id=user["id"])
        assert fetched[0]["last_ping_at"] > original_ping

    def test_delete_ws_connection(self, db):
        user = db.create_user("tina", "Tina")
        session = db.create_session(user["id"], "Delete WS")
        db.create_ws_connection("conn-3", user["id"], session["id"])
        db.delete_ws_connection("conn-3")
        assert db.get_ws_connections(user_id=user["id"]) == []


class TestUserMemoryRules:
    def test_user_memory_rules_are_user_scoped(self, db):
        alice = db.create_user("alice_mem", "Alice")
        bob = db.create_user("bob_mem", "Bob")

        db.add_user_memory_rule(alice["id"], "Alice global")
        db.add_user_memory_rule(alice["id"], "Alice RTL", workflow="rtl-gen")
        db.add_user_memory_rule(bob["id"], "Bob global")

        alice_rules = db.list_user_memory_rules(alice["id"], workflow="rtl-gen")
        bob_rules = db.list_user_memory_rules(bob["id"], workflow="rtl-gen")

        assert [row["rule"] for row in alice_rules] == ["Alice global", "Alice RTL"]
        assert [row["rule"] for row in bob_rules] == ["Bob global"]

    def test_user_memory_rule_admin_list_and_clear(self, db):
        user = db.ensure_user_by_username("rule_admin")
        first = db.add_user_memory_rule(user["id"], "Global one")
        second = db.add_user_memory_rule(user["id"], "Workflow one", workflow="ssot-gen")

        listed = db.list_all_user_memory_rules()
        assert {row["id"] for row in listed} >= {first["id"], second["id"]}
        assert any(row["username"] == "rule_admin" for row in listed)

        assert db.delete_user_memory_rule(user["id"], first["id"]) is True
        assert db.clear_user_memory_rules(user["id"], all_scopes=True) == 1
        assert db.list_user_memory_rules(user["id"], include_all_workflows=True) == []


class TestConcurrency:
    def test_concurrent_session_creation(self, db):
        user = db.create_user("concurrent", "Concurrent User")
        errors = []
        created_ids = []
        lock = threading.Lock()

        def worker():
            for i in range(10):
                try:
                    session = db.create_session(user["id"], f"Session {threading.current_thread().name}-{i}")
                    with lock:
                        created_ids.append(session["id"])
                except Exception as e:
                    with lock:
                        errors.append(e)

        threads = [threading.Thread(target=worker, name=f"T{i}") for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []
        assert len(created_ids) == 100
        assert len(set(created_ids)) == 100

        sessions = db.list_sessions(user["id"])
        assert len(sessions) == 100


class TestMemoryDB:
    def test_memory_db_basic(self, memory_db):
        user = memory_db.create_user("mem", "Memory User")
        session = memory_db.create_session(user["id"], "In-Memory")
        assert memory_db.get_session(session["id"])["title"] == "In-Memory"
        assert memory_db.get_user(user["id"])["username"] == "mem"

    def test_memory_db_init_and_crud(self, memory_db):
        user = memory_db.create_user("u1", "User One")
        session = memory_db.create_session(user["id"], "S1")
        msg = memory_db.save_message(session["id"], "user")
        part = memory_db.save_part(msg["id"], session["id"], "text", text="world")
        conn = memory_db.create_ws_connection("c1", user["id"], session["id"])

        assert len(memory_db.list_sessions(user["id"])) == 1
        assert len(memory_db.get_messages(session["id"])) == 1
        assert len(memory_db.get_parts(msg["id"])) == 1
        assert len(memory_db.get_ws_connections()) == 1

        memory_db.delete_session(session["id"])
        assert memory_db.get_session(session["id"]) is None
