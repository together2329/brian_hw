import pytest

from core.atlas_db import AtlasDB


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "test_atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


class TestOrchestratorRuns:
    def test_create_and_get_run(self, db):
        run = db.create_orchestrator_run(
            user_id="user1",
            ip_id="ip1",
            session_id="sess1",
            chat_message_id="msg1",
            pipeline_run_id="pr1",
            model="gpt-5.5",
            reasoning_effort="medium",
        )
        assert isinstance(run["id"], str) and len(run["id"]) == 32
        assert run["user_id"] == "user1"
        assert run["ip_id"] == "ip1"
        assert run["model"] == "gpt-5.5"
        assert run["status"] == "running"
        assert run["final_state"] is None
        assert isinstance(run["started_at"], float)
        assert run["ended_at"] is None

        fetched = db.get_orchestrator_run(run["id"])
        assert fetched["id"] == run["id"]

    def test_find_active_run_for(self, db):
        assert db.find_active_run_for("u1", "ip1") is None
        r1 = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        active = db.find_active_run_for("u1", "ip1")
        assert active["id"] == r1["id"]

        db.update_orchestrator_run(
            r1["id"], status="completed", final_state="ok", ended=True
        )
        assert db.find_active_run_for("u1", "ip1") is None

        r2 = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        assert db.find_active_run_for("u1", "ip1")["id"] == r2["id"]
        assert db.find_active_run_for("u2", "ip1") is None

    def test_paused_runs_count_as_active(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        db.update_orchestrator_run(r["id"], status="paused")
        active = db.find_active_run_for("u1", "ip1")
        assert active["id"] == r["id"]
        assert active["status"] == "paused"

    def test_update_sets_ended_at(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        updated = db.update_orchestrator_run(
            r["id"], status="error", final_state="llm_error", ended=True
        )
        assert updated["status"] == "error"
        assert updated["final_state"] == "llm_error"
        assert isinstance(updated["ended_at"], float)


class TestOrchestratorSteps:
    def test_step_index_auto_increments(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        s0 = db.append_orchestrator_step(r["id"], tool_name="read_pipeline_state")
        s1 = db.append_orchestrator_step(r["id"], tool_name="dispatch_workflow")
        s2 = db.append_orchestrator_step(r["id"], tool_name="wait_job")
        assert s0["step_index"] == 0
        assert s1["step_index"] == 1
        assert s2["step_index"] == 2

    def test_step_json_round_trip(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        observed = {"stage": "rtl", "status": "failed"}
        decision = {"tool": "classify_failure", "args": {"stage": "rtl"}}
        evidence = {"compile_log": "error: missing semicolon"}
        budget = {"rtl": 2, "sim": 1}
        step = db.append_orchestrator_step(
            r["id"],
            tool_name="classify_failure",
            observed_state=observed,
            decision=decision,
            evidence_read=evidence,
            retry_budget_state=budget,
            verdict="repair_routed",
        )
        assert step["observed_state_json"] == observed
        assert step["decision_json"] == decision
        assert step["evidence_read_json"] == evidence
        assert step["retry_budget_state_json"] == budget
        assert step["verdict"] == "repair_routed"

    def test_list_steps_ordered_by_index(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        for i in range(5):
            db.append_orchestrator_step(r["id"], tool_name=f"tool{i}")
        listed = db.list_orchestrator_steps(r["id"])
        assert [s["step_index"] for s in listed] == [0, 1, 2, 3, 4]
        assert [s["tool_name"] for s in listed] == [f"tool{i}" for i in range(5)]

    def test_latest_step(self, db):
        r = db.create_orchestrator_run(user_id="u1", ip_id="ip1")
        assert db.latest_orchestrator_step(r["id"]) is None
        db.append_orchestrator_step(r["id"], tool_name="a")
        last = db.append_orchestrator_step(r["id"], tool_name="b")
        assert db.latest_orchestrator_step(r["id"])["id"] == last["id"]


class TestProvenanceColumns:
    def test_workflow_runs_has_provenance(self, db):
        conn = db._connect()
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(workflow_runs)").fetchall()}
        assert "orchestrator_run_id" in cols
        assert "trigger_source" in cols

    def test_artifacts_has_provenance(self, db):
        conn = db._connect()
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(artifacts)").fetchall()}
        assert "orchestrator_run_id" in cols
        assert "trigger_source" in cols


class TestMigrationIdempotency:
    def test_init_db_twice_is_safe(self, tmp_path):
        path = str(tmp_path / "twice.db")
        a = AtlasDB(path)
        a.init_db()
        a.create_orchestrator_run(user_id="u", ip_id="ip")
        a.close()

        b = AtlasDB(path)
        b.init_db()
        active = b.find_active_run_for("u", "ip")
        assert active is not None
        b.close()
