from pathlib import Path

import pytest

from core.atlas_db import AtlasDB


def _seed_context_rows(db: AtlasDB) -> tuple[dict, dict, dict, dict]:
    user = db.create_user("alice", "Alice")
    session = db.create_session(user["id"], "DMA RTL", project_id="dma")
    workspace = db.upsert_workspace(
        "soc-workspace",
        owner_user_id=user["id"],
        local_path="/repo/soc",
    )
    ip = db.upsert_ip_block(workspace["id"], "dma", ip_type="controller")
    return user, session, workspace, ip


def test_session_context_is_explicit_and_reusable(tmp_path: Path) -> None:
    from core.atlas_context import SessionContext

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user, session, workspace, ip = _seed_context_rows(db)

    ctx = SessionContext(
        user_id=user["id"],
        username=user["username"],
        session_id=session["id"],
        owner="alice",
        workspace_id=workspace["id"],
        workspace_name=workspace["name"],
        ip_id=ip["id"],
        ip_name=ip["ip_name"],
        workflow="rtl-gen",
        project_root=tmp_path,
    )

    assert ctx.session_key == "alice/dma/rtl-gen"
    assert ctx.session_dir == tmp_path / ".session" / "alice" / "dma" / "rtl-gen"
    assert ctx.trace_fields() == {
        "session_id": session["id"],
        "workspace_id": workspace["id"],
        "ip_id": ip["id"],
        "workflow": "rtl-gen",
        "run_id": "",
        "stage_id": "",
        "todo_id": "",
        "actor_user_id": user["id"],
        "correlation_id": ctx.correlation_id,
    }

    derived = SessionContext.from_session_key(
        "alice/dma/rtl-gen",
        user_id=user["id"],
        session_id=session["id"],
        project_root=tmp_path,
    )
    assert derived.owner == "alice"
    assert derived.ip_name == "dma"
    assert derived.workflow == "rtl-gen"


def test_trace_recorder_writes_event_ledger_and_projections(tmp_path: Path) -> None:
    from core.atlas_context import SessionContext
    from core.atlas_trace import TraceRecorder

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user, session, workspace, ip = _seed_context_rows(db)
        ctx = SessionContext(
            user_id=user["id"],
            username=user["username"],
            session_id=session["id"],
            owner="alice",
            workspace_id=workspace["id"],
            workspace_name=workspace["name"],
            ip_id=ip["id"],
            ip_name=ip["ip_name"],
            workflow="rtl-gen",
            project_root=tmp_path,
            correlation_id="corr-dma",
        )
        recorder = TraceRecorder(db, ctx)

        run = recorder.start_run(mode="pipeline", trigger="ui", input_summary="/ssot-rtl dma")
        todo = recorder.upsert_todo(
            title="Implement descriptor decoder",
            detail="Decode descriptor fields from SSOT.",
            criteria="RTL and tests cover legal and illegal descriptors.",
            notes=["seed note"],
            idempotency_key="todo-1-upsert",
        )
        recorder.record_todo_event(
            todo["id"],
            "in_progress",
            reason="started decoder",
            idempotency_key="todo-1-start",
        )
        recorder.record_todo_event(
            todo["id"],
            "in_progress",
            reason="duplicate ignored",
            idempotency_key="todo-1-start",
        )
        recorder.record_todo_note(
            todo["id"],
            "found endian rule in SSOT",
            idempotency_key="todo-1-note-1",
        )
        recorder.record_todo_event(
            todo["id"],
            "rejected",
            reason="missing illegal descriptor trap",
            idempotency_key="todo-1-reject-1",
        )
        call = recorder.record_llm_call(
            todo_id=todo["id"],
            model="gpt-5.3-codex",
            provider="openai",
            tokens_input=1000,
            tokens_output=200,
            tokens_reasoning=50,
            cost_usd=0.7,
            idempotency_key="llm-1",
        )
        artifact = recorder.register_artifact(
            todo_id=todo["id"],
            kind="rtl",
            path="dma/rtl/dma_desc_decode.sv",
            sha256="deadbeef",
            idempotency_key="artifact-1",
        )
        recorder.record_command(
            "verilator --lint-only dma/list/dma.f",
            exit_code=0,
            stdout_tail="lint clean",
            todo_id=todo["id"],
            idempotency_key="cmd-1",
        )
        recorder.record_ask_user(
            flow_id="flow-1",
            question="Approve trap policy?",
            status="opened",
            todo_id=todo["id"],
            idempotency_key="ask-1",
        )

        events = db.list_trace_events(correlation_id="corr-dma")
        todos = db.list_workflow_todos(run_id=run["id"])
        calls = db.list_llm_calls(run_id=run["id"])
        artifacts = db.list_artifacts(run_id=run["id"])

    assert [event["event_type"] for event in events] == [
        "workflow_run.started",
        "todo.upserted",
        "todo.in_progress",
        "todo.note",
        "todo.rejected",
        "llm_call.completed",
        "artifact.registered",
        "command.completed",
        "ask_user.opened",
    ]
    assert len([event for event in events if event["idempotency_key"] == "todo-1-start"]) == 1
    assert todos[0]["status"] == "rejected"
    assert todos[0]["notes"] == ["seed note", "found endian rule in SSOT"]
    assert calls[0]["id"] == call["id"]
    assert artifacts[0]["id"] == artifact["id"]


def test_trace_recorder_from_env_mirrors_todo_tool_events(tmp_path: Path, monkeypatch) -> None:
    from core.atlas_trace import record_todo_tool_event_from_env
    from lib.todo_tracker import TodoItem

    db_path = tmp_path / "atlas.db"
    monkeypatch.setenv("ATLAS_TRACE_ENABLE", "1")
    monkeypatch.setenv("ATLAS_TRACE_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "alice/dma/rtl-gen")
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "dma")
    monkeypatch.setenv("ATLAS_DEFAULT_WORKFLOW", "rtl-gen")

    item = TodoItem(
        content="Implement DMA top",
        active_form="Implementing DMA top",
        detail="Create dma/rtl/dma.sv from SSOT.",
        criteria="Filelist includes dma.sv and lint passes.",
        notes=["created initial module"],
    )

    assert record_todo_tool_event_from_env(1, item, "in_progress", reason="started")
    assert record_todo_tool_event_from_env(1, item, "completed", reason="wrote RTL")
    assert record_todo_tool_event_from_env(1, item, "approved", reason="lint and file audit passed")
    assert record_todo_tool_event_from_env(1, item, "note", note_text="reviewed filelist")

    with AtlasDB(str(db_path)) as db:
        todos = db.list_workflow_todos()
        events = db.list_trace_events()

    assert len(todos) == 1
    assert todos[0]["title"] == "Implement DMA top"
    assert todos[0]["status"] == "approved"
    assert todos[0]["notes"] == ["created initial module", "reviewed filelist"]
    assert [event["event_type"] for event in events if event["event_type"].startswith("todo.")] == [
        "todo.upserted",
        "todo.in_progress",
        "todo.completed",
        "todo.approved",
        "todo.note",
    ]


def test_permission_policy_enforces_ranked_ip_access(tmp_path: Path) -> None:
    from core.atlas_permissions import PermissionDenied, PermissionPolicy

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        owner = db.create_user("owner", "Owner")
        reviewer = db.create_user("reviewer", "Reviewer")
        workspace = db.upsert_workspace("owner-ws", owner_user_id=owner["id"])
        ip = db.upsert_ip_block(workspace["id"], "dma")
        policy = PermissionPolicy(db)

        assert policy.can_view_ip(owner["id"], ip["id"]) is True
        assert policy.can_import_ip(reviewer["id"], ip["id"]) is False
        with pytest.raises(PermissionDenied):
            policy.require_ip_access(reviewer["id"], ip["id"], "view")

        policy.grant_ip_access(
            ip["id"],
            reviewer["id"],
            "import",
            granted_by_user_id=owner["id"],
        )

        assert policy.can_view_ip(reviewer["id"], ip["id"]) is True
        assert policy.can_import_ip(reviewer["id"], ip["id"]) is True
        assert policy.can_write_ip(reviewer["id"], ip["id"]) is False
        assert policy.require_ip_access(reviewer["id"], ip["id"], "import")["ip_name"] == "dma"
