from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_workspace_renders_editable_todo_tab() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    # Tab chip next to the Git tab + click wiring to the todo main tab
    assert "setMainTab('todo')" in workspace
    assert "mainTab === 'todo'" in workspace
    # Open/total count badge on the chip
    assert "_openTodos}/{_allTodos.length" in workspace

    # Editable pane is rendered in the center column
    assert "<TodoEditorPane />" in workspace
    assert "const TodoEditorPane = () =>" in workspace
    assert "const TodoEditorRow = (" in workspace

    # Per-todo editable fields: state select, content, detail, criteria
    assert "TODO_EDITOR_STATES" in workspace
    assert "'pending', 'in_progress', 'completed', 'approved', 'rejected'" in workspace

    # Controls: add form, per-row remove, clear all
    assert "+ Add todo" in workspace
    assert ">Remove<" in workspace
    assert ">Clear all<" in workspace
    assert ">Save<" in workspace


def test_workspace_and_data_wire_todo_crud_endpoints() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    data = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text()

    # data.jsx exposes the CRUD helpers used by the editor pane
    assert "addTodo:" in data
    assert "updateTodo:" in data
    assert "removeTodo:" in data
    assert "clearTodos:" in data

    # The three new endpoints + existing clear are referenced from data.jsx
    assert "/api/todos/add" in data
    assert "/api/todos/update" in data
    assert "/api/todos/remove" in data
    assert "/api/todos/clear" in data
    assert "async function todoJsonRequest" in data
    assert "throw new Error(message)" in data
    assert "refreshTodosAfterMutation(session, payload)" in data

    # Editor pane calls into those helpers
    assert "api.addTodo(" in workspace
    assert "api.updateTodo(" in workspace
    assert "api.removeTodo(" in workspace
    assert "api.clearTodos(" in workspace


def test_workspace_uses_one_todo_view_for_tab_and_sidebar() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "const _allTodos = Array.isArray(window.TODOS) ? window.TODOS : [];" in workspace
    assert "<TodoEditorPane />" in workspace
    assert "<TodoPanel />" in workspace
    assert "todoPanelOverride" not in workspace
    assert "todosOverride" not in workspace
    assert "workerLocalTodosFromAtlasFeed" not in workspace
    assert "usingOverride" not in workspace


def test_atlas_ui_exposes_todo_crud_endpoints() -> None:
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    assert '@app.post("/api/todos/add")' in atlas_ui
    assert '@app.post("/api/todos/update")' in atlas_ui
    assert '@app.post("/api/todos/remove")' in atlas_ui
    # Source of truth is the local session todo.json, read-modify-write via TodoTracker
    assert "_sync_live_tracker_from_session" in atlas_ui
    assert "TodoTracker.load(session_todo)" in atlas_ui
