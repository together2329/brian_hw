import json
import os
from pathlib import Path

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator import tools as orch_tools


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


class TestReadPipelineState:
    def test_returns_bridge_unavailable_when_not_registered(self, monkeypatch):
        monkeypatch.setattr(orch_tools, "_read_pipeline_state_bridge", lambda: None)
        result, summary = orch_tools.read_pipeline_state(ip="ipA")
        assert result["ok"] is False
        assert "bridge" in result["error"]

    def test_invokes_registered_bridge(self, monkeypatch):
        captured = {}

        def fake_bridge(*, ip, scope, include_jobs):
            captured["ip"] = ip
            captured["include_jobs"] = include_jobs
            return {"ok": True, "passed": ["ssot"], "failed": [], "running": []}

        monkeypatch.setattr(orch_tools, "_read_pipeline_state_bridge", lambda: fake_bridge)
        result, summary = orch_tools.read_pipeline_state(ip="ipA", include_jobs=False)
        assert captured == {"ip": "ipA", "include_jobs": False}
        assert result["passed"] == ["ssot"]
        assert "ssot" in summary


class TestDispatchWorkflow:
    def test_injects_provenance_into_payload(self, monkeypatch):
        seen = {}

        def fake_bridge(**kwargs):
            seen.update(kwargs)
            return {"ok": True, "pipeline_run_id": "pr1", "jobs": [{"job_id": "j1"}]}

        monkeypatch.setattr(orch_tools, "_dispatch_workflow_bridge", lambda: fake_bridge)
        result, summary = orch_tools.dispatch_workflow(
            workflow="rtl-gen",
            ip="ipA",
            orchestrator_run_id="run-xyz",
            reason="testing",
            payload={"scope": ["mod1"]},
        )
        assert result["ok"] is True
        assert seen["workflow"] == "rtl-gen"
        assert seen["payload"]["orchestrator_run_id"] == "run-xyz"
        assert seen["payload"]["trigger_source"] == "orchestrator_chat"
        assert seen["payload"]["scope"] == ["mod1"]
        assert "j1" in summary


class TestWaitJob:
    def test_uses_top_level_jobs_module_when_server_loaded_that_way(self, monkeypatch):
        import sys
        import threading
        import types

        live_module = types.ModuleType("atlas_api_jobs")
        live_module._jobs = {
            "live": {"job_id": "live", "status": "running", "workflow": "ssot-gen"}
        }
        live_module._jobs_lock = threading.Lock()

        stale_module = types.ModuleType("src.atlas_api_jobs")
        stale_module._jobs = {}
        stale_module._jobs_lock = threading.Lock()

        monkeypatch.setitem(sys.modules, "atlas_api_jobs", live_module)
        monkeypatch.setitem(sys.modules, "src.atlas_api_jobs", stale_module)

        result, summary = orch_tools.wait_job("live")

        assert result["ok"] is True
        assert result["job"]["workflow"] == "ssot-gen"
        assert "live" in summary

    def test_snapshots_job_state(self, monkeypatch):
        import threading

        fake_jobs = {"j1": {"job_id": "j1", "status": "running", "workflow": "rtl-gen"}}
        fake_lock = threading.Lock()
        monkeypatch.setattr(
            orch_tools, "_jobs_registry", lambda: (fake_jobs, fake_lock)
        )
        result, summary = orch_tools.wait_job("j1")
        assert result["ok"] is True
        assert result["job"]["status"] == "running"
        # snapshot is a copy, not the same dict
        fake_jobs["j1"]["status"] = "completed"
        assert result["job"]["status"] == "running"

    def test_missing_job(self, monkeypatch):
        import threading

        monkeypatch.setattr(orch_tools, "_jobs_registry", lambda: ({}, threading.Lock()))
        result, _ = orch_tools.wait_job("ghost")
        assert result["ok"] is False
        assert "ghost" in result["error"]


class TestReadArtifact:
    def test_reads_existing_json(self, tmp_path):
        ip = "ipA"
        (tmp_path / ip / "rtl").mkdir(parents=True)
        compile_path = tmp_path / ip / "rtl" / "rtl_compile.json"
        compile_path.write_text(json.dumps({"ok": False, "errors": 3}))
        result, summary = orch_tools.read_artifact(
            ip=ip, stage="rtl", project_root=tmp_path
        )
        rtl_compile_entry = next(
            a for a in result["artifacts"] if a["rel"].endswith("rtl_compile.json")
        )
        assert rtl_compile_entry["exists"]
        assert rtl_compile_entry["data"]["errors"] == 3
        assert "rtl/rtl_compile.json" in summary

    def test_reads_rtl_blocker_json(self, tmp_path):
        ip = "ipA"
        (tmp_path / ip / "rtl").mkdir(parents=True)
        blocked_path = tmp_path / ip / "rtl" / "rtl_blocked.json"
        blocked_path.write_text(
            json.dumps(
                {
                    "reason": "SSOT-derived dynamic RTL TODO gate is blocked",
                    "questions": [{"id": "RTL_DYNAMIC_TODO_OWNERSHIP"}],
                }
            ),
            encoding="utf-8",
        )
        result, summary = orch_tools.read_artifact(
            ip=ip, stage="rtl", project_root=tmp_path
        )
        rtl_blocker_entry = next(
            a for a in result["artifacts"] if a["rel"].endswith("rtl_blocked.json")
        )
        assert rtl_blocker_entry["exists"]
        assert rtl_blocker_entry["data"]["questions"][0]["id"] == "RTL_DYNAMIC_TODO_OWNERSHIP"
        assert "rtl/rtl_blocked.json" in summary

    def test_rtl_summary_includes_stage_log_gate_preview(self, tmp_path):
        ip = "ipA"
        log_path = tmp_path / ip / "logs" / "stage_engine" / "ssot-rtl.json"
        log_path.parent.mkdir(parents=True)
        log_path.write_text(
            json.dumps(
                {
                    "headline": "[RTL RESULT] FAIL - LLM-authored RTL needs rtl-gen repair",
                    "status": "fail",
                    "metadata": {
                        "rtl_todo_plan": {
                            "gate": {
                                "status": "fail",
                                "open_required_todos": 4,
                                "static_missing": 1,
                            }
                        }
                    },
                }
            ),
            encoding="utf-8",
        )

        result, summary = orch_tools.read_artifact(
            ip=ip, stage="rtl", project_root=tmp_path
        )

        log_entry = next(
            a for a in result["artifacts"] if a["rel"].endswith("ssot-rtl.json")
        )
        assert log_entry["exists"]
        assert "open_required_todos" in summary
        assert "rtl_todo_gate" in summary

    def test_reports_missing_files(self, tmp_path):
        result, summary = orch_tools.read_artifact(
            ip="ipA", stage="sim", project_root=tmp_path
        )
        for art in result["artifacts"]:
            assert art["exists"] is False
        assert "missing" in summary

    def test_reads_safe_relative_artifact_path(self, tmp_path):
        ip = "ipA"
        blocked = tmp_path / ip / "tb" / "cocotb" / "tb_blocked.json"
        blocked.parent.mkdir(parents=True)
        blocked.write_text(json.dumps({"reason": "missing rtl contract"}), encoding="utf-8")

        result, summary = orch_tools.read_artifact(
            ip=ip, stage="tb/cocotb/tb_blocked.json", project_root=tmp_path
        )

        assert result["artifacts"][0]["exists"] is True
        assert result["artifacts"][0]["data"]["reason"] == "missing rtl contract"
        assert "tb/cocotb/tb_blocked.json" in summary

    def test_summary_includes_json_status_and_classification_preview(self, tmp_path):
        ip = "ipA"
        classify = tmp_path / ip / "sim" / "mismatch_classification.json"
        classify.parent.mkdir(parents=True)
        classify.write_text(
            json.dumps(
                {
                    "type": "mismatch_classification",
                    "status": "action_required",
                    "classifications": [
                        {
                            "classification": "stale_oracle",
                            "owner": "fl-model-gen",
                            "reason": "verify/equivalence_goals.json older than current SSOT",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

        result, summary = orch_tools.read_artifact(
            ip=ip, stage="sim/mismatch_classification.json", project_root=tmp_path
        )

        assert result["artifacts"][0]["data"]["status"] == "action_required"
        assert "stale_oracle" in summary
        assert "fl-model-gen" in summary

    def test_reads_sim_debug_underscore_alias(self, tmp_path):
        ip = "ipA"
        classify = tmp_path / ip / "sim" / "mismatch_classification.json"
        classify.parent.mkdir(parents=True)
        classify.write_text(
            json.dumps(
                {
                    "type": "mismatch_classification",
                    "status": "action_required",
                    "classifications": [{"classification": "rtl_bug", "owner": "rtl-gen"}],
                }
            ),
            encoding="utf-8",
        )

        result, summary = orch_tools.read_artifact(
            ip=ip, stage="sim_debug", project_root=tmp_path
        )

        assert any(a["rel"] == "sim/mismatch_classification.json" for a in result["artifacts"])
        assert "rtl_bug" in summary

    def test_summary_marks_stale_sim_debug_artifact(self, tmp_path):
        ip = "ipA"
        sim_dir = tmp_path / ip / "sim"
        sim_dir.mkdir(parents=True)
        compare = sim_dir / "fl_rtl_compare.json"
        scoreboard = sim_dir / "scoreboard_events.jsonl"
        compare.write_text(
            json.dumps({"type": "fl_rtl_compare", "status": "stale"}),
            encoding="utf-8",
        )
        scoreboard.write_text('{"goal_id":"EQ1"}\n', encoding="utf-8")
        os.utime(compare, (1000, 1000))
        os.utime(scoreboard, (2000, 2000))

        result, summary = orch_tools.read_artifact(
            ip=ip, stage="sim/fl_rtl_compare.json", project_root=tmp_path
        )

        entry = result["artifacts"][0]
        assert entry["freshness_status"] == "stale_artifact"
        assert entry["stale_against"][0]["rel"] == "sim/scoreboard_events.jsonl"
        assert "stale_artifact" in summary


class TestClassifyFailureTool:
    def test_wraps_pure_function(self):
        result, summary = orch_tools.classify_failure_tool(stage="lint")
        assert result["owner"] == "lint_violation"
        assert "lint_violation" in summary


class TestAskUser:
    def test_records_event_and_pauses_run(self, db):
        run = db.create_orchestrator_run(user_id="u1", ip_id="ip1", session_id="s1")
        result, summary = orch_tools.ask_user(
            db=db,
            run_id=run["id"],
            ip_id="ip1",
            user_id="u1",
            session_id="s1",
            question="Choose FIFO depth: 8 or 16?",
            context={"stage": "ssot-gen"},
        )
        assert result["state"] == "paused"
        refreshed = db.get_orchestrator_run(run["id"])
        assert refreshed["status"] == "paused"
        events = db.list_trace_events(correlation_id=run["id"])
        ask_events = [e for e in events if e["event_type"] == "orchestrator_ask_user"]
        assert ask_events, "expected at least one orchestrator_ask_user event"
        assert ask_events[0]["payload"]["question"].startswith("Choose FIFO")


class TestWriteHandoff:
    def test_writes_pending_record(self, tmp_path):
        result, summary = orch_tools.write_handoff(
            ip="ipA",
            workflow="rtl-gen",
            payload={"scope": ["mod1"], "note": "test"},
            reason="no worker bound",
            user_id="u1",
            session_id="s1",
            pipeline_run_id="pr1",
            orchestrator_run_id="orch-1234abcd",
            project_root=tmp_path,
        )
        assert result["ok"] is True
        out = Path(result["path"])
        assert out.exists()
        record = json.loads(out.read_text())
        assert record["to_workflow"] == "rtl-gen"
        assert record["scope"]["user_id"] == "u1"
        assert record["payload"]["scope"] == ["mod1"]
        assert record["orchestrator_run_id"] == "orch-1234abcd"


class TestMarkDownstreamStale:
    def test_walks_pipeline_dependency_graph(self, db, monkeypatch):
        fake_deps = {
            "ssot": (),
            "rtl": ("ssot",),
            "lint": ("rtl",),
            "sim": ("rtl",),
            "coverage": ("sim",),
        }
        monkeypatch.setattr(orch_tools, "_pipeline_stage_deps", lambda: fake_deps)
        result, summary = orch_tools.mark_downstream_stale(
            db=db, ip_id="ip1", from_stage="rtl", run_id="run1", session_id="s1"
        )
        assert result["ok"] is True
        assert set(result["stale"]) == {"lint", "sim", "coverage"}
        events = db.list_trace_events(correlation_id="run1")
        stale_stages = {
            e["stage_id"] for e in events if e["event_type"] == "stage_stale"
        }
        assert stale_stages == {"lint", "sim", "coverage"}

    def test_unavailable_graph(self, db, monkeypatch):
        monkeypatch.setattr(orch_tools, "_pipeline_stage_deps", lambda: {})
        result, _ = orch_tools.mark_downstream_stale(
            db=db, ip_id="ip1", from_stage="rtl"
        )
        assert result["ok"] is False
