import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(PROJECT_ROOT), str(PROJECT_ROOT / "src")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def test_external_db_query_is_not_exposed_by_default(monkeypatch):
    from core import tools

    monkeypatch.delenv("ATLAS_ENABLE_EXTERNAL_DB_QUERY_TOOL", raising=False)
    exposed = tools.filtered_available_tools()
    assert "external_db_query" not in exposed

    monkeypatch.setenv("ATLAS_ENABLE_EXTERNAL_DB_QUERY_TOOL", "1")
    exposed = tools.filtered_available_tools()
    assert "external_db_query" in exposed


def test_wiki_query_tool_is_not_exposed_by_default(monkeypatch):
    from core import tools

    monkeypatch.delenv("ATLAS_ENABLE_WIKI_QUERY_TOOL", raising=False)
    exposed = tools.filtered_available_tools()
    assert "wiki_query" not in exposed

    monkeypatch.setenv("ATLAS_ENABLE_WIKI_QUERY_TOOL", "1")
    exposed = tools.filtered_available_tools()
    assert "wiki_query" in exposed


def test_external_db_wiki_aliases_are_disabled_by_default(monkeypatch):
    from core import tools

    monkeypatch.delenv("ATLAS_ENABLE_EXTERNAL_DB_QUERY_TOOL", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_QUERY", raising=False)
    monkeypatch.delenv("ATLAS_EXTERNAL_DB_WIKI", raising=False)
    monkeypatch.delenv("ATLAS_RTL_DB_WIKI", raising=False)

    result = tools.wiki_query(ip="external-db", topic="uart")

    assert "external DB lookup is disabled by default" in result
    assert "ATLAS_ENABLE_EXTERNAL_DB_QUERY_TOOL=1" in result


def test_prompt_tool_table_hides_wiki_query_by_default(monkeypatch):
    import src.config as config
    import src.llm_client as llm_client

    monkeypatch.setenv("PLAN_MODE", "false")
    monkeypatch.setenv("ENABLE_NATIVE_TOOL_CALLS", "false")
    monkeypatch.setattr(llm_client, "is_responses_api_model", lambda: False, raising=False)
    monkeypatch.setattr(config, "ENABLE_WIKI_QUERY_TOOL", False, raising=False)
    monkeypatch.setattr(config, "ENABLE_EXTERNAL_DB_QUERY_TOOL", False, raising=False)

    normal_prompt = config.build_base_system_prompt(plan_mode=False, todo_active=False)
    assert "- wiki_query(" not in normal_prompt
    assert "- external_db_query(" not in normal_prompt

    monkeypatch.setattr(config, "ENABLE_WIKI_QUERY_TOOL", True, raising=False)
    opt_in_prompt = config.build_base_system_prompt(plan_mode=False, todo_active=False)
    assert "- wiki_query(" in opt_in_prompt


def test_ask_user_is_not_exposed_by_default(monkeypatch):
    from core import tools

    monkeypatch.delenv("ATLAS_ENABLE_ASK_USER_TOOL", raising=False)
    exposed = tools.filtered_available_tools()
    assert "ask_user" not in exposed
    assert "disabled by default" in tools.ask_user(question="pick one")

    monkeypatch.setenv("ATLAS_ENABLE_ASK_USER_TOOL", "1")
    exposed = tools.filtered_available_tools()
    assert "ask_user" in exposed


def test_todo_creation_tools_are_plan_mode_only(monkeypatch, tmp_path):
    from core import tools
    import src.config as config

    monkeypatch.setattr(config, "TODO_ERROR_FILE", str(tmp_path / "todo_error.json"), raising=False)
    monkeypatch.setenv("PLAN_MODE", "false")

    normal_tools = tools.filtered_available_tools()
    assert "todo_write" not in normal_tools
    assert "todo_add" not in normal_tools
    assert "todo_update" in normal_tools

    assert "disabled outside plan mode" in tools.todo_write(
        todos=[{"content": "plan", "detail": "detail", "criteria": "criteria"}]
    )
    assert "disabled outside plan mode" in tools.todo_add(
        content="plan",
        detail="detail",
        criteria="criteria",
    )

    monkeypatch.setenv("PLAN_MODE", "true")
    plan_tools = tools.filtered_available_tools()
    assert "todo_write" in plan_tools
    assert "todo_add" in plan_tools


def test_prompt_tool_table_matches_minimal_surface_policy(monkeypatch):
    import src.config as config

    monkeypatch.setenv("PLAN_MODE", "false")
    monkeypatch.setattr(config, "UNLOCK_NORMAL_MODE_TOOLS", True, raising=False)
    monkeypatch.setattr(config, "DISABLE_TODO_TOOLS", False, raising=False)
    monkeypatch.setattr(config, "ENABLE_EXTERNAL_DB_QUERY_TOOL", False, raising=False)
    monkeypatch.setattr(config, "ENABLE_WIKI_QUERY_TOOL", False, raising=False)
    monkeypatch.setattr(config, "ENABLE_ASK_USER_TOOL", False, raising=False)
    monkeypatch.setattr(
        config,
        "NORMAL_MODE_BLOCKED_TOOLS",
        frozenset({"todo_write", "todo_add", "todo_remove"}),
        raising=False,
    )

    normal_prompt = config.build_base_system_prompt(plan_mode=False, todo_active=True)
    assert "todo_write" not in normal_prompt
    assert "todo_add" not in normal_prompt
    assert "- wiki_query(" not in normal_prompt
    assert "- external_db_query(" not in normal_prompt
    assert "- ask_user(" not in normal_prompt
    assert "only advance existing tasks with `todo_update`" in normal_prompt

    plan_prompt = config.build_base_system_prompt(plan_mode=True, todo_active=False)
    assert "ALLOWED TODO TOOLS" in plan_prompt
    assert "todo_write(todos=[...])" in plan_prompt
    assert "todo_add(content" in plan_prompt
