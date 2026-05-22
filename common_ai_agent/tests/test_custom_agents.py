import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_custom_agent_registry_saves_project_local_definition(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    from core.custom_agents import list_custom_agents, load_custom_agent, save_custom_agent

    definition = save_custom_agent(
        name="my_reviewer",
        base_agent="review",
        system_prompt="Focus on regression holes.",
        allowed_tools="read_file, grep_file",
        model="glm",
        reasoning_effort="high",
    )

    path = tmp_path / ".atlas" / "custom_agents" / "my_reviewer.json"
    assert path.is_file()
    assert definition.base_agent == "review"

    loaded = load_custom_agent("my_reviewer")
    assert loaded is not None
    assert loaded.system_prompt == "Focus on regression holes."
    assert loaded.allowed_tools == ["read_file", "grep_file"]
    assert [agent.name for agent in list_custom_agents()] == ["my_reviewer"]


def test_custom_agent_registry_isolates_db_definitions_by_user(monkeypatch, tmp_path):
    monkeypatch.delenv("ATLAS_USER_ID", raising=False)
    monkeypatch.delenv("ATLAS_MEMORY_USER", raising=False)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    from core.atlas_db import AtlasDB
    from core.custom_agents import list_custom_agents, load_custom_agent, save_custom_agent

    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice")
    bob = db.create_user("bob", "Bob")

    alice_agent = save_custom_agent(
        name="risk_audit",
        base_agent="review",
        system_prompt="Alice-only review rules.",
        owner_user_id=alice["id"],
        db=db,
    )
    bob_agent = save_custom_agent(
        name="risk_audit",
        base_agent="explore",
        system_prompt="Bob-only exploration rules.",
        owner_user_id=bob["id"],
        db=db,
    )

    assert alice_agent.owner_user_id == alice["id"]
    assert bob_agent.owner_user_id == bob["id"]
    assert not (tmp_path / ".atlas" / "custom_agents" / "risk_audit.json").exists()

    loaded_for_alice = load_custom_agent("risk_audit", owner_user_id=alice["id"], db=db)
    loaded_for_bob = load_custom_agent("risk_audit", owner_user_id=bob["id"], db=db)

    assert loaded_for_alice is not None
    assert loaded_for_alice.base_agent == "review"
    assert loaded_for_alice.system_prompt == "Alice-only review rules."
    assert loaded_for_bob is not None
    assert loaded_for_bob.base_agent == "explore"
    assert loaded_for_bob.system_prompt == "Bob-only exploration rules."
    assert [agent.owner_user_id for agent in list_custom_agents(owner_user_id=alice["id"], db=db)] == [
        alice["id"]
    ]
    assert [agent.owner_user_id for agent in list_custom_agents(owner_user_id=bob["id"], db=db)] == [
        bob["id"]
    ]


def test_active_db_user_does_not_fall_back_to_shared_legacy_file(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    from core.atlas_db import AtlasDB
    from core.custom_agents import list_custom_agents, load_custom_agent, save_custom_agent

    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice")

    save_custom_agent(
        name="legacy_agent",
        base_agent="review",
        system_prompt="Legacy file prompt.",
        root=tmp_path,
    )

    assert load_custom_agent("legacy_agent", root=tmp_path) is not None
    assert load_custom_agent("legacy_agent", owner_user_id=alice["id"], db=db, root=tmp_path) is None
    assert list_custom_agents(owner_user_id=alice["id"], db=db, root=tmp_path) == []


def test_current_owner_user_id_resolves_memory_user_username(monkeypatch, tmp_path):
    from core.atlas_db import AtlasDB
    from core.custom_agents import current_owner_user_id

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    alice = db.create_user("alice", "Alice")

    monkeypatch.delenv("ATLAS_USER_ID", raising=False)
    monkeypatch.delenv("ATLAS_ACTIVE_USER_ID", raising=False)
    monkeypatch.delenv("ATLAS_OWNER_USER_ID", raising=False)
    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_MEMORY_USER", "alice")

    assert current_owner_user_id() == alice["id"]


def test_current_owner_user_id_does_not_accept_session_id_when_db_is_active(monkeypatch, tmp_path):
    from core.atlas_db import AtlasDB
    from core.custom_agents import current_owner_user_id

    db_path = tmp_path / "atlas.db"
    AtlasDB(str(db_path)).create_user("alice", "Alice")

    monkeypatch.delenv("ATLAS_ACTIVE_USER_ID", raising=False)
    monkeypatch.delenv("ATLAS_OWNER_USER_ID", raising=False)
    monkeypatch.delenv("ATLAS_MEMORY_USER", raising=False)
    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_USER_ID", "alice/random_session_123")

    assert current_owner_user_id() == ""


def test_background_task_runs_saved_custom_agent(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    import config
    from core.agent_runner import AgentResult
    from core.custom_agents import save_custom_agent
    from core.tools import background_task

    monkeypatch.setattr(config, "ENABLE_SUB_AGENTS", True, raising=False)
    monkeypatch.setattr(config, "DEBUG_MODE", False, raising=False)

    save_custom_agent(
        name="risk_audit",
        base_agent="review",
        system_prompt="Find only user-visible regressions.",
        allowed_tools=["read_file", "grep_file"],
        reasoning_effort="high",
    )

    captured = {}

    def fake_run_agent_session(**kwargs):
        captured.update(kwargs)
        return AgentResult(
            output="risk summary",
            status="completed",
            execution_time_ms=12,
            iterations=1,
        )

    monkeypatch.setattr("core.agent_runner.run_agent_session", fake_run_agent_session)

    result = background_task(agent="risk_audit", prompt="review auth changes")

    assert "Foreground Agent Result: risk_audit" in result
    assert captured["agent_name"] == "review"
    assert captured["allowed_tools"] == {"read_file", "grep_file"}
    assert "Custom Agent Instructions" in captured["system_prompt"]
    assert "Find only user-visible regressions." in captured["system_prompt"]


def test_background_task_uses_current_users_db_custom_agent(monkeypatch, tmp_path):
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    import config
    from core.agent_runner import AgentResult
    from core.atlas_db import AtlasDB
    from core.custom_agents import save_custom_agent
    from core.tools import background_task

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    alice = db.create_user("alice", "Alice")
    bob = db.create_user("bob", "Bob")
    save_custom_agent(
        name="risk_audit",
        base_agent="review",
        system_prompt="Alice must not see Bob's prompt.",
        owner_user_id=alice["id"],
        db=db,
    )
    save_custom_agent(
        name="risk_audit",
        base_agent="explore",
        system_prompt="Bob prompt should stay isolated.",
        owner_user_id=bob["id"],
        db=db,
    )

    monkeypatch.setenv("ATLAS_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_USER_ID", alice["id"])
    monkeypatch.setattr(config, "ENABLE_SUB_AGENTS", True, raising=False)
    monkeypatch.setattr(config, "DEBUG_MODE", False, raising=False)

    captured = {}

    def fake_run_agent_session(**kwargs):
        captured.update(kwargs)
        return AgentResult(output="ok", status="completed", execution_time_ms=3, iterations=1)

    monkeypatch.setattr("core.agent_runner.run_agent_session", fake_run_agent_session)

    result = background_task(agent="risk_audit", prompt="review per-user prompt")

    assert "Foreground Agent Result: risk_audit" in result
    assert captured["agent_name"] == "review"
    assert "Alice must not see Bob's prompt." in captured["system_prompt"]
    assert "Bob prompt should stay isolated." not in captured["system_prompt"]


def test_background_task_runs_one_off_custom_prompt(monkeypatch):
    import config
    from core.agent_runner import AgentResult
    from core.tools import background_task

    monkeypatch.setattr(config, "ENABLE_SUB_AGENTS", True, raising=False)
    monkeypatch.setattr(config, "DEBUG_MODE", False, raising=False)

    captured = {}

    def fake_run_agent_session(**kwargs):
        captured.update(kwargs)
        return AgentResult(output="ok", status="completed", execution_time_ms=3, iterations=1)

    monkeypatch.setattr("core.agent_runner.run_agent_session", fake_run_agent_session)

    result = background_task(
        agent="scratch_checker",
        base_agent="review",
        prompt="check this once",
        system_prompt="Use the temporary checker rules.",
        allowed_tools="read_file",
    )

    assert "Foreground Agent Result: scratch_checker" in result
    assert captured["agent_name"] == "review"
    assert captured["allowed_tools"] == {"read_file"}
    assert "Use the temporary checker rules." in captured["system_prompt"]


def test_worker_call_sends_custom_agent_payload():
    from core.agent_client import worker_call

    posted_bodies = []

    def mock_urlopen(req, timeout=10):
        url = req.full_url if hasattr(req, "full_url") else str(req)
        if url.endswith("/run"):
            posted_bodies.append(json.loads(req.data.decode("utf-8")))
            body = json.dumps({"run_id": "r1", "status": "pending"})
        elif "/status/" in url:
            body = json.dumps({"run_id": "r1", "status": "completed"})
        elif "/result/" in url:
            body = json.dumps({
                "run_id": "r1",
                "status": "completed",
                "result": "ok",
                "files_modified": [],
                "files_examined": [],
                "iterations": 1,
            })
        else:
            raise AssertionError(f"Unexpected URL: {url}")
        response = MagicMock()
        response.read.return_value = body.encode()
        response.__enter__ = lambda s: s
        response.__exit__ = MagicMock(return_value=False)
        return response

    with patch("core.agent_client.urllib.request.urlopen", side_effect=mock_urlopen):
        result = worker_call(
            worker="http://localhost:8001",
            task="do work",
            custom_agent="risk_audit",
            system_prompt="Custom prompt text",
            allowed_tools="read_file,grep_file",
            reasoning_effort="high",
            custom_agent_owner_id="user_123",
            timeout=5,
            poll_interval=0.01,
            show_log=False,
        )

    assert result["status"] == "completed"
    body = posted_bodies[0]
    assert body["custom_agent"] == "risk_audit"
    assert body["system_prompt"] == "Custom prompt text"
    assert body["allowed_tools"] == "read_file,grep_file"
    assert body["reasoning_effort"] == "high"
    assert body["custom_agent_owner_id"] == "user_123"
