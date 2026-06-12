import json
import importlib
import sys
import types
from pathlib import Path

import config
from core import tools
from lib.todo_tracker import TodoTracker


def _write_tracker(path: Path, content: str) -> TodoTracker:
    tracker = TodoTracker(persist_path=path)
    tracker.add_todos([{"content": content, "status": "pending"}])
    return tracker


def test_tool_todo_tracker_follows_current_config_path(monkeypatch, tmp_path):
    old_path = tmp_path / "old" / "todo.json"
    new_path = tmp_path / "new" / "todo.json"
    old_tracker = _write_tracker(old_path, "old todo")
    _write_tracker(new_path, "new todo")
    fake_main = types.SimpleNamespace(todo_tracker=old_tracker)

    monkeypatch.setitem(sys.modules, "main", fake_main)
    monkeypatch.setitem(sys.modules, "src.main", fake_main)
    monkeypatch.setattr(config, "TODO_FILE", str(new_path), raising=False)

    tracker = tools._get_todo_tracker()

    assert Path(tracker._persist_path) == new_path
    assert tracker.todos[0].content == "new todo"
    assert fake_main.todo_tracker is tracker


def test_scoped_todo_runtime_makes_todo_update_use_session_file(monkeypatch, tmp_path):
    old_path = tmp_path / "old" / "todo.json"
    session_path = tmp_path / ".session" / "brian" / "new_axi" / "default" / "todo.json"
    old_tracker = _write_tracker(old_path, "old todo")
    session_tracker = _write_tracker(session_path, "session todo")
    fake_main = types.SimpleNamespace(todo_tracker=old_tracker)

    monkeypatch.setitem(sys.modules, "main", fake_main)
    monkeypatch.setitem(sys.modules, "src.main", fake_main)
    monkeypatch.setattr(config, "TODO_FILE", str(old_path), raising=False)

    with tools.scoped_todo_runtime(session_tracker, session_path):
        result = tools.todo_update(index=1, status="in_progress")

    assert "Task 1 in progress" in result
    assert json.loads(session_path.read_text(encoding="utf-8"))["todos"][0]["status"] == "in_progress"
    assert json.loads(old_path.read_text(encoding="utf-8"))["todos"][0]["status"] == "pending"


def test_worker_tool_dispatch_binds_todo_runtime():
    source = Path("core/agent_server.py").read_text(encoding="utf-8")

    assert "scoped_todo_runtime" in source
    assert 'session_overrides.get("TODO_FILE")' in source


def test_interactive_tool_dispatch_binds_todo_runtime():
    source = Path("src/main.py").read_text(encoding="utf-8")

    assert "def execute_tool(" in source
    assert "with tools.scoped_todo_runtime(" in source
    assert 'getattr(config, "TODO_FILE", None)' in source


def test_main_todo_reload_helper_rebinds_stale_global(monkeypatch, tmp_path):
    main_mod = importlib.import_module("src.main")
    stale_path = tmp_path / "old" / "todo.json"
    session_path = tmp_path / ".session" / "brian" / "default" / "ip" / "default" / "todo.json"
    stale_tracker = _write_tracker(stale_path, "stale todo")
    session_tracker = _write_tracker(session_path, "fresh session todo")
    session_tracker.mark_in_progress(0)

    monkeypatch.setattr(main_mod.config, "ENABLE_TODO_TRACKING", True, raising=False)
    monkeypatch.setattr(main_mod.config, "TODO_FILE", str(session_path), raising=False)
    monkeypatch.setattr(main_mod, "todo_tracker", stale_tracker, raising=False)

    fresh = main_mod._reload_todo_tracker_from_config()

    assert fresh is main_mod.todo_tracker
    assert Path(fresh._persist_path) == session_path
    assert fresh.todos[0].content == "fresh session todo"
    assert fresh.todos[0].status == "in_progress"


def test_chat_loop_reloads_todo_after_input_before_dispatch():
    source = Path("src/main.py").read_text(encoding="utf-8")

    input_idx = source.index("user_input = _input_fn(")
    reload_idx = source.index("# Refresh TODO after input returns.")
    bang_idx = source.index('if user_input.startswith("!"):')
    slash_idx = source.index("# Handle slash commands", bang_idx)
    llm_idx = source.index("_process_chat_turn(user_input, _loop_state, _loop_deps)")

    assert input_idx < reload_idx < bang_idx < slash_idx < llm_idx
    reload_block = source[reload_idx:bang_idx]
    assert "todo_tracker_main = _reload_todo_tracker_from_config()" in reload_block
