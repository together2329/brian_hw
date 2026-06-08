from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_workspace_renders_editable_todo_tab() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    # Tab chip next to the Git tab + click wiring to the todo main tab
    assert "setMainTab('todo')" in workspace
    assert "mainTab === 'todo'" in workspace
    # Approved/total count badge on the chip
    assert "_approvedTodos}/{_allTodos.length" in workspace

    # Editable pane is rendered in the center column
    assert "<TodoEditorPane />" in workspace
    assert "const TodoEditorPane = () =>" in workspace
    assert "const TodoEditorRow = (" in workspace

    # Per-todo editable fields: state select, content, detail, criteria
    assert "TODO_EDITOR_STATES" in workspace
    assert "'pending', 'in_progress', 'completed', 'approved', 'rejected'" in workspace

    # Controls: add form, per-row remove, clear all
    assert "+ Add todo" in workspace
    assert "Detail is required to add a todo." in workspace
    assert "Criteria is required to add a todo." in workspace
    assert 'placeholder="detail (required)"' in workspace
    assert 'placeholder="criteria — one per line (required)"' in workspace
    assert "Approved Reason" in workspace
    assert "Reject Reason" in workspace
    assert "To Do Note" in workspace
    assert "approved_reason: approvedReason" in workspace
    assert "rejection_reason: rejectionReason" in workspace
    assert 'placeholder="approved reason (required)"' in workspace
    assert 'placeholder="reject reason (required)"' in workspace
    assert "const reasonMissing =" in workspace
    assert "const canAddTodo =" in workspace
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

    add_start = atlas_ui.index('@app.post("/api/todos/add")')
    update_start = atlas_ui.index('@app.post("/api/todos/update")')
    add_endpoint = atlas_ui[add_start:update_start]
    update_endpoint = atlas_ui[update_start:atlas_ui.index('@app.post("/api/todos/remove")')]
    assert '"detail is required"' in add_endpoint
    assert '"criteria is required"' in add_endpoint
    assert "_sync_live_tracker_from_session(session_todo)" not in add_endpoint
    assert 'todo.approved_reason = str(body.get("approved_reason"))' in update_endpoint
    assert 'todo.rejection_reason = str(body.get("rejection_reason"))' in update_endpoint
    assert '"approved_reason is required"' in update_endpoint
    assert '"rejection_reason is required"' in update_endpoint


def test_todos_update_endpoint_gates_status_changes_in_plan_mode() -> None:
    """The /api/todos/update endpoint must refuse UI status transitions while
    plan mode is active — mirroring the core/tools.py:todo_update gate — so the
    frontend cannot bypass plan approval the way the agent tool is blocked.
    Content/detail/criteria/priority edits stay allowed."""
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    update_start = atlas_ui.index('@app.post("/api/todos/update")')
    update_endpoint = atlas_ui[update_start:atlas_ui.index('@app.post("/api/todos/remove")')]

    # Status changes go through the same transition engine as core/tools.py so
    # plan mode, completion evidence, approval order, and rejection gates stay
    # aligned across Textual/agent and Atlas web surfaces.
    assert "apply_todo_status_transition" in update_endpoint
    assert 'plan_mode=os.environ.get("PLAN_MODE") == "true"' in update_endpoint
    assert "status_code=transition.http_status or 409" in update_endpoint


def test_web_slash_todo_uses_active_session_todo_file() -> None:
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    assert "active_slash_session = normalize_session_name" in atlas_ui
    assert 'session_dir = PROJECT_ROOT / ".session" / active_slash_session' in atlas_ui
    assert '"TODO_FILE": str(session_dir / "todo.json")' in atlas_ui
    assert '"TODO_ERROR_FILE": str(session_dir / "todo_error.json")' in atlas_ui
    assert 'slash_tt.TODO_FILE = session_dir / "todo.json"' in atlas_ui
