from pathlib import Path

from core.atlas_admin_usage import build_admin_usage_payload
from core.atlas_db import AtlasDB


def _table_names(db: AtlasDB) -> set[str]:
    rows = db._fetchall("SELECT name FROM sqlite_master WHERE type='table'")
    return {row["name"] for row in rows}


def test_observability_schema_is_additive(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        tables = _table_names(db)

    assert {
        "workspaces",
        "ip_blocks",
        "workflow_runs",
        "workflow_stages",
        "workflow_events",
        "workflow_todos",
        "todo_events",
        "llm_calls",
        "artifacts",
        "ip_permissions",
    }.issubset(tables)


def test_workflow_trace_round_trip(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("alice", "Alice")
        session = db.create_session(user["id"], "DMA Pipeline", project_id="dma")
        workspace = db.upsert_workspace(
            owner_user_id=user["id"],
            name="soc-a",
            local_path="/repo/soc-a",
            git_remote="https://example.invalid/soc-a.git",
            git_branch="main",
            head_commit="abc123",
            dirty_state="clean",
        )
        ip = db.upsert_ip_block(
            workspace["id"],
            "dma",
            ip_type="controller",
            ssot_path="dma/yaml/dma.ssot.yaml",
        )
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            mode="pipeline",
            model_profile="gpt-5.3-codex",
            reasoning_effort="medium",
            trigger="ui_button",
            input_summary="/ssot-rtl dma",
        )
        stage = db.start_workflow_stage(run["id"], "derive-rtl-todos", attempt=1)
        event = db.record_workflow_event(
            run["id"],
            "command",
            {"command": "derive_rtl_todos.py dma", "exit_code": 0},
            stage_id=stage["id"],
        )
        todo = db.upsert_workflow_todo(
            run["id"],
            title="Implement top-level ports",
            detail="Expose SSOT-defined DMA top ports.",
            criteria="RTL top module contains all io_list ports.",
            owner_file="dma/rtl/dma.sv",
            owner_module="dma",
            source_refs=["io_list", "top_module"],
        )
        db.record_todo_event(
            todo["id"],
            "approved",
            reason="Static audit found all top-level ports.",
            evidence={"audit": "pass"},
        )
        artifact = db.register_artifact(
            run_id=run["id"],
            stage_id=stage["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            kind="rtl",
            path="dma/rtl/dma.sv",
            sha256="deadbeef",
            git_commit="abc123",
        )
        db.finish_workflow_stage(stage["id"], "passed")
        finished = db.finish_workflow_run(run["id"], "passed")

        fetched_run = db.get_workflow_run(run["id"])
        fetched_todos = db.list_workflow_todos(run["id"])
        fetched_artifacts = db.list_artifacts(run_id=run["id"])
        fetched_events = db.list_workflow_events(run_id=run["id"])

    assert finished["status"] == "passed"
    assert fetched_run["workflow"] == "rtl-gen"
    assert fetched_run["workspace_name"] == "soc-a"
    assert fetched_run["ip_name"] == "dma"
    assert fetched_todos[0]["source_refs"] == ["io_list", "top_module"]
    assert fetched_todos[0]["evidence"]["audit"] == "pass"
    assert fetched_artifacts[0]["id"] == artifact["id"]
    assert fetched_artifacts[0]["path"] == "dma/rtl/dma.sv"
    assert fetched_events[0]["id"] == event["id"]
    assert fetched_events[0]["payload"]["exit_code"] == 0


def test_message_cost_dual_writes_to_llm_calls(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("bob", "Bob")
        session = db.create_session(user["id"], "RTL Review", project_id="timer")
        msg = db.save_message(
            session["id"],
            "assistant",
            agent="rtl-gen",
            model_id="gpt-5.3-codex",
            provider_id="openai",
            cost=0.42,
            tokens_input=1200,
            tokens_output=300,
            tokens_reasoning=80,
            workflow="rtl-gen",
        )
        db.save_message(session["id"], "user")

        calls = db.list_llm_calls(session_id=session["id"])
        messages = db.get_messages(session["id"])

    assert len(messages) == 2
    assert len(calls) == 1
    assert calls[0]["message_id"] == msg["id"]
    assert calls[0]["workflow"] == "rtl-gen"
    assert calls[0]["model"] == "gpt-5.3-codex"
    assert calls[0]["provider"] == "openai"
    assert calls[0]["cost_usd"] == 0.42
    assert calls[0]["tokens_input"] == 1200
    assert calls[0]["tokens_output"] == 300
    assert calls[0]["tokens_reasoning"] == 80


def test_admin_usage_prefers_llm_calls_for_cost_context(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("carol", "Carol")
        session = db.create_session(user["id"], "DMA Run", project_id="legacy-project")
        workspace = db.upsert_workspace(
            owner_user_id=user["id"],
            name="soc-workspace",
            local_path="/repo/soc",
        )
        ip = db.upsert_ip_block(workspace["id"], "dma", ip_type="controller")
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
        )
        db.record_llm_call(
            session_id=session["id"],
            run_id=run["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            model="gpt-5.3-codex",
            provider="openai",
            tokens_input=4000,
            tokens_output=900,
            tokens_reasoning=100,
            cost_usd=2.5,
        )

        usage = build_admin_usage_payload(db)

    assert usage["users"][0]["username"] == "carol"
    assert usage["users"][0]["message_count"] == 1
    assert usage["users"][0]["total_cost_usd"] == 2.5
    assert usage["users"][0]["models"][0]["model_id"] == "gpt-5.3-codex"
    assert usage["cost_by_context"][0]["ip"] == "dma"
    assert usage["cost_by_context"][0]["workspace"] == "soc-workspace"
    assert usage["cost_by_context"][0]["workflow"] == "rtl-gen"
    assert usage["cost_by_date"][0]["cost"] == 2.5


def test_admin_usage_falls_back_to_messages_when_no_llm_calls_exist(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("dave", "Dave")
        session = db.create_session(user["id"], "Legacy Cost", project_id="timer")
        db.import_message(
            "legacy-msg",
            session["id"],
            "assistant",
            model_id="legacy-model",
            cost=0.75,
            tokens_input=100,
            tokens_output=50,
        )

        usage = build_admin_usage_payload(db)

    assert usage["users"][0]["username"] == "dave"
    assert usage["users"][0]["total_cost_usd"] == 0.75
    assert usage["users"][0]["models"][0]["model_id"] == "legacy-model"
    assert usage["cost_by_context"][0]["ip"] == "timer"


def test_admin_usage_reports_todo_flow_and_llm_usage(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("erin", "Erin")
        session = db.create_session(user["id"], "DMA RTL", project_id="dma")
        workspace = db.upsert_workspace(user["id"], "soc-workspace", local_path="/repo/soc")
        ip = db.upsert_ip_block(workspace["id"], "dma", ip_type="controller")
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
        )
        todo = db.upsert_workflow_todo(
            run["id"],
            title="Implement DMA descriptor decoder",
            detail="Decode descriptor fields from SSOT register map.",
            criteria="Descriptor decode RTL and tests cover legal and illegal descriptors.",
            notes=["found descriptor endian rule in SSOT", "lint clean after mask fix"],
            status="pending",
        )
        db.record_todo_event(todo["id"], "in_progress", reason="started descriptor decoder")
        db.record_todo_event(todo["id"], "rejected", reason="missing illegal descriptor trap")
        db.record_todo_event(todo["id"], "rejected", reason="trap path did not clear busy")
        db.record_todo_event(todo["id"], "approved", reason="read RTL and ran descriptor tests")
        db.record_llm_call(
            session_id=session["id"],
            run_id=run["id"],
            todo_id=todo["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            model="gpt-5.3-codex",
            provider="openai",
            tokens_input=1000,
            tokens_output=250,
            tokens_reasoning=75,
            cost_usd=0.9,
            latency_ms=1200,
        )
        db.record_llm_call(
            session_id=session["id"],
            run_id=run["id"],
            todo_id=todo["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            model="gpt-5.3-codex",
            provider="openai",
            tokens_input=800,
            tokens_output=150,
            tokens_reasoning=25,
            cost_usd=0.6,
            latency_ms=900,
        )

        usage = build_admin_usage_payload(db)

    assert len(usage["todo_usage"]) == 1
    item = usage["todo_usage"][0]
    assert item["content"] == "Implement DMA descriptor decoder"
    assert item["detail"] == "Decode descriptor fields from SSOT register map."
    assert item["criteria"] == "Descriptor decode RTL and tests cover legal and illegal descriptors."
    assert item["notes"] == ["found descriptor endian rule in SSOT", "lint clean after mask fix"]
    assert item["status"] == "approved"
    assert item["rejected_count"] == 2
    assert item["approved_count"] == 1
    assert item["last_rejected_reason"] == "trap path did not clear busy"
    assert item["last_event_type"] == "approved"
    assert item["last_event_reason"] == "read RTL and ran descriptor tests"
    assert item["llm_calls"] == 2
    assert item["tokens_input"] == 1800
    assert item["tokens_output"] == 400
    assert item["tokens_reasoning"] == 100
    assert item["tokens"] == 2200
    assert item["cost"] == 1.5
    assert item["ip"] == "dma"
    assert item["workspace"] == "soc-workspace"
    assert item["workflow"] == "rtl-gen"

    flow = usage["todo_flow"]
    assert [event["event_type"] for event in flow] == [
        "in_progress",
        "rejected",
        "rejected",
        "approved",
    ]
    assert flow[-1]["content"] == "Implement DMA descriptor decoder"


def test_ip_permissions_allow_view_and_import_by_user(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        owner = db.create_user("owner", "Owner")
        reviewer = db.create_user("reviewer", "Reviewer")
        workspace = db.upsert_workspace(owner["id"], "owner-ws", local_path="/repo/owner")
        ip = db.upsert_ip_block(workspace["id"], "dma", ip_type="controller")

        assert db.can_user_access_ip(ip["id"], owner["id"], "admin") is True
        assert db.can_user_access_ip(ip["id"], reviewer["id"], "view") is False

        grant = db.grant_ip_permission(
            ip["id"],
            reviewer["id"],
            "import",
            granted_by_user_id=owner["id"],
        )
        accessible = db.list_accessible_ip_blocks(reviewer["id"], permission="view")

    assert grant["permission"] == "import"
    assert grant["grantee_user_id"] == reviewer["id"]
    assert accessible[0]["ip_name"] == "dma"
    assert accessible[0]["permission"] == "import"
