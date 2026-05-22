from pathlib import Path

from core.atlas_admin_chat import answer_admin_question
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
        "trace_events",
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


def test_admin_usage_reports_memory_rules_and_user_inputs(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("input_user", "Input User")
        session = db.create_session(user["id"], "Input Session", project_id="axi")
        msg = db.save_message(session["id"], "user")
        db.save_part(msg["id"], session["id"], "text", text="build the AXI block")
        db.add_user_memory_rule(user["id"], "Always use strict SSOT")

        usage = build_admin_usage_payload(db)

    assert usage["memory_rules"][0]["username"] == "input_user"
    assert usage["memory_rules"][0]["rule"] == "Always use strict SSOT"
    assert usage["input_history"][0]["username"] == "input_user"
    assert usage["input_history"][0]["content"] == "build the AXI block"


def test_admin_chat_answers_memory_and_input_questions_from_db(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("chat_user", "Chat User")
        session = db.create_session(user["id"], "Chat Session", project_id="timer")
        msg = db.save_message(session["id"], "user")
        db.save_part(msg["id"], session["id"], "text", text="check timer usage")
        db.add_user_memory_rule(user["id"], "Use timer-specific reset rules")

        answer = answer_admin_question(db, "show memory and user input history")

    assert "Memory rules: 1 total" in answer["answer"]
    assert "User input history: 1 recent" in answer["answer"]
    section_titles = [section["title"] for section in answer["sections"]]
    assert "Memory Rules" in section_titles
    assert "Latest User Inputs" in section_titles


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
        workspace = db.upsert_workspace(
            "soc-workspace",
            owner_user_id=user["id"],
            local_path="/repo/soc",
        )
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
        trace = db.record_trace_event(
            "todo.approved",
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            run_id=run["id"],
            todo_id=todo["id"],
            actor_user_id=user["id"],
            correlation_id="corr-dma",
            idempotency_key="todo-approved-trace",
            payload={"reason": "read RTL and ran descriptor tests"},
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
        db.save_message(session["id"], "user")
        tool_msg = db.save_message(session["id"], "assistant", agent="rtl-gen")
        db.save_part(
            tool_msg["id"],
            session["id"],
            "tool_result",
            tool_name="run_command",
            tool_status="ok",
            tool_output="lint clean\n",
            start_time=10.0,
            end_time=12.0,
        )
        db.save_part(
            tool_msg["id"],
            session["id"],
            "tool_result",
            tool_name="read_file",
            tool_status="error",
            tool_output="x" * 400,
            tool_error="file missing",
        )
        db.record_trace_event(
            "ask_user.answered",
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            actor_user_id=user["id"],
            payload={"flow_id": "qa-1", "answer": "approved"},
        )
        db.record_trace_event(
            "chat_message",
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            actor_user_id=user["id"],
            payload={"content": "please keep descriptor trap visible"},
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

    assert len(usage["trace_events"]) == 3
    event = next(row for row in usage["trace_events"] if row["event_type"] == "todo.approved")
    assert event["event_id"] == trace["id"]
    assert event["event_type"] == "todo.approved"
    assert event["ip"] == "dma"
    assert event["workspace"] == "soc-workspace"
    assert event["workflow"] == "rtl-gen"
    assert event["todo_id"] == todo["id"]
    assert event["username"] == "erin"
    assert event["correlation_id"] == "corr-dma"
    assert event["payload"]["reason"] == "read RTL and ran descriptor tests"

    tools = {row["tool_name"]: row for row in usage["tool_usage"]}
    assert tools["run_command"]["calls"] == 1
    assert tools["run_command"]["failed_calls"] == 0
    assert tools["run_command"]["observation_chars"] == len("lint clean\n")
    assert tools["run_command"]["observation_tokens_est"] == 3
    assert tools["run_command"]["avg_latency_ms"] == 2000
    assert tools["run_command"]["ip"] == "dma"
    assert tools["run_command"]["workspace"] == "soc-workspace"
    assert tools["run_command"]["workflow"] == "rtl-gen"
    assert tools["read_file"]["failed_calls"] == 1
    assert tools["read_file"]["observation_tokens_est"] == 100

    assert len(usage["interventions"]) == 1
    intervention = usage["interventions"][0]
    assert intervention["username"] == "erin"
    assert intervention["ip"] == "dma"
    assert intervention["workspace"] == "soc-workspace"
    assert intervention["workflow"] == "rtl-gen"
    assert intervention["intervention_count"] == 3
    assert intervention["user_messages"] == 1
    assert intervention["chat_messages"] == 1
    assert intervention["ask_user_answers"] == 1


def test_ip_permissions_allow_view_and_import_by_user(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        owner = db.create_user("owner", "Owner")
        reviewer = db.create_user("reviewer", "Reviewer")
        workspace = db.upsert_workspace(
            "owner-ws",
            owner_user_id=owner["id"],
            local_path="/repo/owner",
        )
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


def test_rtl_versions_anchor_lint_and_sim_run_history(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("owner", "Owner")
        session = db.create_session(user["id"], "GPIO pipeline", project_id="gpio")
        workspace = db.upsert_workspace(
            "soc",
            owner_user_id=user["id"],
            local_path="/repo/soc",
            git_branch="main",
            head_commit="abc123",
        )
        ip = db.upsert_ip_block(workspace["id"], "gpio", ip_type="peripheral")
        rtl_run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            mode="pipeline",
        )
        rtl_stage = db.start_workflow_stage(rtl_run["id"], "rtl-gen")
        version = db.register_rtl_version(
            ip_id=ip["id"],
            workspace_id=workspace["id"],
            source_run_id=rtl_run["id"],
            source_stage_id=rtl_stage["id"],
            version="rtl-v001",
            label="first generated RTL",
            rtl_root="gpio/rtl",
            filelist_path="gpio/list/gpio.f",
            top_module="gpio",
            artifact_manifest=[
                {"path": "gpio/rtl/gpio.sv", "sha256": "top"},
                {"path": "gpio/rtl/gpio_regs.sv", "sha256": "regs"},
            ],
            sha256_tree="tree-v1",
            git_commit="abc123",
            git_tag="atlas/gpio/rtl-v001",
        )
        lint_run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="lint",
            mode="pipeline",
            rtl_version_id=version["id"],
        )
        sim_run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="sim",
            mode="pipeline",
            rtl_version_id=version["id"],
        )
        lint_stage = db.start_workflow_stage(lint_run["id"], "dut-lint", rtl_version_id=version["id"])
        artifact = db.register_artifact(
            run_id=lint_run["id"],
            stage_id=lint_stage["id"],
            ip_id=ip["id"],
            workflow="lint",
            kind="lint_report",
            path="gpio/lint/dut_lint.json",
            sha256="lint-json",
            rtl_version_id=version["id"],
        )
        db.finish_workflow_run(lint_run["id"], "failed", error_summary="width mismatch")
        db.finish_workflow_run(sim_run["id"], "blocked", error_summary="lint failed first")

        history = db.list_rtl_run_history(ip_id=ip["id"])
        versions = db.list_rtl_versions(ip_id=ip["id"])
        fetched_artifact = db.list_artifacts(run_id=lint_run["id"])[0]
        fetched_run = db.get_workflow_run(lint_run["id"])
        fetched_stage = db.get_workflow_stage(lint_stage["id"])

    assert versions[0]["version"] == "rtl-v001"
    assert versions[0]["artifact_version_id"]
    assert versions[0]["artifact_manifest"][0]["path"] == "gpio/rtl/gpio.sv"
    assert fetched_run["rtl_version"] == "rtl-v001"
    assert fetched_run["rtl_sha256_tree"] == "tree-v1"
    assert fetched_run["rtl_git_tag"] == "atlas/gpio/rtl-v001"
    assert fetched_stage["rtl_version_id"] == version["id"]
    assert fetched_artifact["id"] == artifact["id"]
    assert fetched_artifact["rtl_version_id"] == version["id"]
    assert [row["workflow"] for row in history] == ["sim", "lint"]
    assert {row["status"] for row in history} == {"failed", "blocked"}
    assert all(row["rtl_version"] == "rtl-v001" for row in history)
    assert all(row["rtl_sha256_tree"] == "tree-v1" for row in history)
    assert all(row["rtl_git_tag"] == "atlas/gpio/rtl-v001" for row in history)


def test_artifact_version_graph_tracks_ssot_rtl_tb_and_sim_inputs(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("owner", "Owner")
        session = db.create_session(user["id"], "GPIO pipeline", project_id="gpio")
        workspace = db.upsert_workspace("soc", owner_user_id=user["id"], local_path="/repo/soc")
        ip = db.upsert_ip_block(workspace["id"], "gpio", ip_type="peripheral")
        ssot = db.register_artifact_version(
            ip_id=ip["id"],
            workspace_id=workspace["id"],
            artifact_type="ssot",
            version="ssot-v001",
            root_path="gpio/yaml",
            primary_path="gpio/yaml/gpio.ssot.yaml",
            manifest=[{"path": "gpio/yaml/gpio.ssot.yaml", "sha256": "ssot"}],
            sha256_tree="ssot-tree",
            git_commit="abc123",
            git_tag="atlas/gpio/ssot-v001",
        )
        rtl = db.register_rtl_version(
            ip_id=ip["id"],
            workspace_id=workspace["id"],
            version="rtl-v001",
            rtl_root="gpio/rtl",
            filelist_path="gpio/list/gpio.f",
            top_module="gpio",
            artifact_manifest=[{"path": "gpio/rtl/gpio.sv", "sha256": "rtl"}],
            sha256_tree="rtl-tree",
        )
        tb = db.register_artifact_version(
            ip_id=ip["id"],
            workspace_id=workspace["id"],
            artifact_type="tb",
            version="tb-v001",
            root_path="gpio/tb",
            primary_path="gpio/tb/run_tests.py",
            manifest=[{"path": "gpio/tb/run_tests.py", "sha256": "tb"}],
            sha256_tree="tb-tree",
        )
        db.link_artifact_versions(ssot["id"], rtl["artifact_version_id"], "generated_from")
        db.link_artifact_versions(ssot["id"], tb["id"], "generated_from")
        db.link_artifact_versions(rtl["artifact_version_id"], tb["id"], "verified_against")
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="sim",
            mode="pipeline",
            rtl_version_id=rtl["id"],
        )
        db.attach_run_artifact_version(run["id"], ssot["id"], role="input")
        db.attach_run_artifact_version(run["id"], rtl["artifact_version_id"], role="input")
        db.attach_run_artifact_version(run["id"], tb["id"], role="input")

        sets = db.list_run_artifact_version_sets(workflows=["sim"])
        edges = db.list_artifact_version_edges(child_version_id=tb["id"])

    assert sets[0]["workflow"] == "sim"
    assert sets[0]["artifact_versions"]["ssot"][0]["version"] == "ssot-v001"
    assert sets[0]["artifact_versions"]["rtl"][0]["version"] == "rtl-v001"
    assert sets[0]["artifact_versions"]["tb"][0]["version"] == "tb-v001"
    assert {edge["parent_type"] for edge in edges} == {"ssot", "rtl"}
    assert {edge["relation"] for edge in edges} == {"generated_from", "verified_against"}


def test_admin_usage_reports_rtl_version_run_history(tmp_path: Path) -> None:
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.create_user("owner", "Owner")
        session = db.create_session(user["id"], "GPIO pipeline", project_id="gpio")
        workspace = db.upsert_workspace("soc", owner_user_id=user["id"], local_path="/repo/soc")
        ip = db.upsert_ip_block(workspace["id"], "gpio", ip_type="peripheral")
        rtl_run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="rtl-gen",
            mode="pipeline",
        )
        version = db.register_rtl_version(
            ip_id=ip["id"],
            workspace_id=workspace["id"],
            source_run_id=rtl_run["id"],
            version="rtl-v002",
            label="after irq repair",
            rtl_root="gpio/rtl",
            filelist_path="gpio/list/gpio.f",
            top_module="gpio",
            artifact_manifest=[{"path": "gpio/rtl/gpio.sv", "sha256": "top-v2"}],
            sha256_tree="tree-v2",
            git_commit="def456",
            git_tag="atlas/gpio/rtl-v002",
        )
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="sim",
            mode="pipeline",
            rtl_version_id=version["id"],
        )
        db.attach_run_artifact_version(run["id"], version["artifact_version_id"], role="input")
        db.record_llm_call(
            session_id=session["id"],
            run_id=run["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="sim",
            model="gpt-5.3-codex",
            tokens_input=100,
            tokens_output=40,
            cost_usd=0.12,
        )
        db.finish_workflow_run(run["id"], "passed")

        payload = build_admin_usage_payload(db)

    history = payload["rtl_run_history"]
    assert len(history) == 1
    row = history[0]
    assert row["ip"] == "gpio"
    assert row["workspace"] == "soc"
    assert row["workflow"] == "sim"
    assert row["rtl_version"] == "rtl-v002"
    assert row["rtl_git_tag"] == "atlas/gpio/rtl-v002"
    assert row["rtl_sha256_tree"] == "tree-v2"
    assert row["llm_calls"] == 1
    assert row["tokens"] == 140
    assert row["cost"] == 0.12
    assert payload["artifact_versions"][0]["artifact_type"] == "rtl"
    assert payload["artifact_versions"][0]["version"] == "rtl-v002"
    assert payload["run_artifact_sets"][0]["workflow"] == "sim"
    assert payload["run_artifact_sets"][0]["artifact_versions"]["rtl"][0]["version"] == "rtl-v002"


# ---------------------------------------------------------------------------
# Orchestrator chat (stored on trace_events; no separate chat_messages table)
# ---------------------------------------------------------------------------


def _bootstrap_two_ips(tmp_path: Path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    owner = db.create_user("owner", "Owner")
    ws = db.upsert_workspace("ws", owner_user_id=owner["id"], local_path="/repo")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    return db, owner, ip_uart, ip_dma


def _content_set(rows):
    out = set()
    for r in rows:
        payload = r.get("payload") or {}
        c = payload.get("content") if isinstance(payload, dict) else None
        if c:
            out.add(c)
    return out


def test_chat_message_per_ip_and_global_rooms_isolated(tmp_path: Path) -> None:
    db, owner, ip_uart, ip_dma = _bootstrap_two_ips(tmp_path)
    db.record_chat_message(ip_uart["id"], owner["id"], "uart hello", "Owner")
    db.record_chat_message(None, owner["id"], "global hello", "Owner")
    db.record_chat_message(ip_dma["id"], owner["id"], "dma hello", "Owner")

    assert _content_set(db.list_chat_messages(ip_uart["id"])) == {"uart hello"}
    assert _content_set(db.list_chat_messages(ip_dma["id"])) == {"dma hello"}
    assert _content_set(db.list_chat_messages(None)) == {"global hello"}


def test_chat_unconsumed_advances_per_session(tmp_path: Path) -> None:
    db, owner, ip_uart, _ = _bootstrap_two_ips(tmp_path)
    m1 = db.record_chat_message(ip_uart["id"], owner["id"], "one")
    m2 = db.record_chat_message(ip_uart["id"], owner["id"], "two")

    sid = "owner/uart_lite/rtl-gen"
    unread = db.list_chat_unconsumed_for(sid, ip_uart["id"])
    assert [m["id"] for m in unread] == [m1["id"], m2["id"]]

    db.record_chat_consumed(m1["id"], sid, ip_uart["id"])
    unread2 = db.list_chat_unconsumed_for(sid, ip_uart["id"])
    assert [m["id"] for m in unread2] == [m2["id"]]

    # Different session — has not consumed anything yet, sees both.
    unread_other = db.list_chat_unconsumed_for("other/uart/rtl-gen", ip_uart["id"])
    assert {m["id"] for m in unread_other} == {m1["id"], m2["id"]}


def test_chat_unconsumed_global_room_ignores_ip_rows(tmp_path: Path) -> None:
    db, owner, ip_uart, _ = _bootstrap_two_ips(tmp_path)
    db.record_chat_message(ip_uart["id"], owner["id"], "uart only")
    g = db.record_chat_message(None, owner["id"], "for everyone")
    unread = db.list_chat_unconsumed_for("owner/_global", None)
    assert [m["id"] for m in unread] == [g["id"]]


def test_latest_chat_consumed_id_returns_watermark(tmp_path: Path) -> None:
    db, owner, ip_uart, _ = _bootstrap_two_ips(tmp_path)
    m = db.record_chat_message(ip_uart["id"], owner["id"], "ping")
    sid = "s1"
    assert db.latest_chat_consumed_id(sid, ip_uart["id"]) is None
    db.record_chat_consumed(m["id"], sid, ip_uart["id"])
    assert db.latest_chat_consumed_id(sid, ip_uart["id"]) == m["id"]


def test_summarize_ip_room_context_shape(tmp_path: Path) -> None:
    db, owner, ip_uart, _ = _bootstrap_two_ips(tmp_path)
    run = db.start_workflow_run(
        workspace_id=ip_uart["workspace_id"],
        ip_id=ip_uart["id"],
        workflow="rtl-gen",
        mode="pipeline",
        model_profile="deepseek",
        status="running",
    )
    db.upsert_workflow_todo(run["id"], title="impl x", status="in_progress")
    db.upsert_workflow_todo(run["id"], title="lock policy", status="blocked")

    ctx = db.summarize_ip_room_context(ip_uart["id"])
    assert ctx is not None
    assert ctx["ip"]["name"] == "uart_lite"
    assert ctx["workflow"]["latest_run"]["workflow"] == "rtl-gen"
    counts = ctx["todos"]["counts"]
    assert counts["in_progress"] == 1
    assert counts["blocked"] == 1
    titles = {b["title"] for b in ctx["todos"]["top_blockers"]}
    assert "lock policy" in titles


def test_summarize_global_room_context_lists_all_ips(tmp_path: Path) -> None:
    db, _owner, _ip_uart, _ip_dma = _bootstrap_two_ips(tmp_path)
    ctx = db.summarize_global_room_context()
    names = {row["name"] for row in ctx["ips"]}
    assert names == {"uart_lite", "dma"}


def test_get_ip_block_by_name_resolves_room_to_id(tmp_path: Path) -> None:
    db, _owner, ip_uart, ip_dma = _bootstrap_two_ips(tmp_path)
    assert db.get_ip_block_by_name("uart_lite")["id"] == ip_uart["id"]
    assert db.get_ip_block_by_name("dma")["id"] == ip_dma["id"]
    assert db.get_ip_block_by_name("nonexistent") is None
