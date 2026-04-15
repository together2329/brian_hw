"""
Tests for core/job.py — Job model lifecycle, serialization, and factory.

Covers:
  - JobStatus.is_terminal
  - Job lifecycle: start, complete, cancel
  - Job result capture: capture_metrics, set_classification, set_score
  - Job serialization: to_dict, from_dict (old + new format)
  - Job persistence: save, load round-trip
  - Job display: format_summary
  - Factory: job_from_agent_result
"""

import os
import sys
import json
import time
import pytest
from pathlib import Path
from unittest.mock import MagicMock

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.job import Job, JobStatus, job_from_agent_result


# ============================================================
# JobStatus
# ============================================================

class TestJobStatus:
    def test_terminal_states(self):
        assert JobStatus.is_terminal(JobStatus.COMPLETED) is True
        assert JobStatus.is_terminal(JobStatus.ERROR) is True
        assert JobStatus.is_terminal(JobStatus.TIMEOUT) is True
        assert JobStatus.is_terminal(JobStatus.CANCELLED) is True

    def test_non_terminal_states(self):
        assert JobStatus.is_terminal(JobStatus.PENDING) is False
        assert JobStatus.is_terminal(JobStatus.RUNNING) is False

    def test_unknown_status(self):
        assert JobStatus.is_terminal("unknown") is False

    def test_status_values(self):
        assert JobStatus.PENDING == "pending"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.COMPLETED == "completed"
        assert JobStatus.ERROR == "error"
        assert JobStatus.TIMEOUT == "timeout"
        assert JobStatus.CANCELLED == "cancelled"


# ============================================================
# Job Lifecycle
# ============================================================

class TestJobLifecycle:
    def test_default_state(self):
        job = Job()
        assert job.status == JobStatus.PENDING
        assert job.started_at == 0.0
        assert job.finished_at == 0.0
        assert job.execution_time_ms == 0
        assert job.output == ""
        assert job.error is None

    def test_start(self):
        job = Job()
        job.start()
        assert job.status == JobStatus.RUNNING
        assert job.started_at > 0

    def test_complete_success(self):
        job = Job()
        job.start()
        time.sleep(0.01)  # small delay for measurable time
        job.complete(output="done", raw_output="full output")
        assert job.status == JobStatus.COMPLETED
        assert job.output == "done"
        assert job.raw_output == "full output"
        assert job.error is None
        assert job.finished_at > 0
        assert job.execution_time_ms >= 0

    def test_complete_with_error(self):
        job = Job()
        job.start()
        job.complete(output="", raw_output="error log", error="Something failed")
        assert job.status == JobStatus.ERROR
        assert job.error == "Something failed"

    def test_cancel(self):
        job = Job()
        job.start()
        job.cancel(reason="User requested")
        assert job.status == JobStatus.CANCELLED
        assert job.error == "User requested"
        assert job.finished_at > 0

    def test_cancel_default_reason(self):
        job = Job()
        job.start()
        job.cancel()
        assert job.error == ""

    def test_is_terminal(self):
        job = Job()
        assert job.is_terminal() is False  # PENDING

        job.start()
        assert job.is_terminal() is False  # RUNNING

        job.complete(output="ok")
        assert job.is_terminal() is True  # COMPLETED


# ============================================================
# Result Capture
# ============================================================

class TestResultCapture:
    def test_capture_metrics(self):
        job = Job()
        job.capture_metrics({"lint.errors": 3, "lint.warnings": 5})
        assert job.parsed_metrics == {"lint.errors": 3, "lint.warnings": 5}

    def test_capture_metrics_merge(self):
        job = Job(parsed_metrics={"sim.pass": 10})
        job.capture_metrics({"lint.errors": 0})
        assert job.parsed_metrics == {"sim.pass": 10, "lint.errors": 0}

    def test_capture_metrics_overwrite(self):
        job = Job(parsed_metrics={"lint.errors": 3})
        job.capture_metrics({"lint.errors": 0})
        assert job.parsed_metrics["lint.errors"] == 0

    def test_set_classification(self):
        job = Job()
        job.set_classification("tb_bug")
        assert job.classification_label == "tb_bug"

    def test_set_score(self):
        job = Job()
        job.set_score(10.5)
        assert job.loop_score == 10.5

    def test_set_score_default(self):
        job = Job()
        assert job.loop_score == -999.0


# ============================================================
# Serialization: to_dict / from_dict
# ============================================================

class TestJobSerialization:
    def test_to_dict_full(self):
        job = Job(
            job_id="job5",
            agent_name="execute",
            workflow="eda",
            status=JobStatus.COMPLETED,
            iterations=3,
            execution_time_ms=1500,
            output="All tests passed",
            raw_output="Full output here",
            files_examined=["counter.sv", "tb_counter.sv"],
            files_modified=["counter.sv"],
            stage_id="lint",
            iteration_in_stage=2,
            loop_score=15.0,
            classification_label="",
            converge_action="lint-run",
            parsed_metrics={"lint.errors": 0},
        )
        job.tool_calls = [{"tool": "read_file"}]
        job.created_at = 1000.0
        job.started_at = 1001.0
        job.finished_at = 1002.5

        d = job.to_dict()
        assert d["agent_name"] == "execute"
        assert d["status"] == "completed"
        assert d["iterations"] == 3
        assert d["execution_time_ms"] == 1500
        assert d["output_preview"] == "All tests passed"
        assert d["tool_calls"] == 1  # stored as count in to_dict
        assert d["converge"]["job_id"] == "job5"
        assert d["converge"]["stage_id"] == "lint"
        assert d["converge"]["loop_score"] == 15.0
        assert d["converge"]["parsed_metrics"] == {"lint.errors": 0}

    def test_to_dict_empty(self):
        job = Job()
        d = job.to_dict()
        assert d["status"] == "pending"
        assert d["converge"]["job_id"] == ""
        assert d["converge"]["parsed_metrics"] == {}

    def test_to_dict_output_truncated(self):
        job = Job(output="x" * 5000)
        d = job.to_dict()
        assert len(d["output_preview"]) == 2000

    def test_to_dict_files_truncated(self):
        job = Job(files_examined=[f"file_{i}" for i in range(30)])
        d = job.to_dict()
        assert len(d["files_examined"]) == 20

    def test_from_dict_new_format(self):
        data = {
            "agent_name": "execute",
            "status": "completed",
            "iterations": 3,
            "execution_time_ms": 500,
            "output_preview": "Lint clean",
            "raw_output": "full output",
            "tool_calls": [{"tool": "write"}],
            "files_examined": ["counter.sv"],
            "files_modified": [],
            "converge": {
                "job_id": "job5",
                "workflow": "eda",
                "stage_id": "lint",
                "iteration_in_stage": 1,
                "loop_score": 10.0,
                "classification_label": "syntax_error",
                "retry_count": 1,
                "converge_action": "lint-run",
                "parsed_metrics": {"lint.errors": 0},
                "converge_context": {},
            },
            "created_at": 1000.0,
            "started_at": 1001.0,
            "finished_at": 1001.5,
        }
        job = Job.from_dict(data)
        assert job.agent_name == "execute"
        assert job.status == "completed"
        assert job.job_id == "job5"
        assert job.stage_id == "lint"
        assert job.loop_score == 10.0
        assert job.classification_label == "syntax_error"
        assert job.parsed_metrics == {"lint.errors": 0}
        assert job.output == "Lint clean"
        assert job.tool_calls == [{"tool": "write"}]

    def test_from_dict_old_format(self):
        """Old format has no 'converge' key and tool_calls as int."""
        data = {
            "agent_name": "execute",
            "status": "completed",
            "iterations": 5,
            "execution_time_ms": 2000,
            "output_preview": "RTL generated",
            "tool_calls": 3,  # old format: count
            "files_examined": ["spec.md"],
            "files_modified": ["counter.sv"],
        }
        job = Job.from_dict(data)
        assert job.agent_name == "execute"
        assert job.status == "completed"
        assert job.tool_calls == []  # old format count → empty list
        assert job.output == "RTL generated"
        assert job.stage_id == ""  # no converge data
        assert job.loop_score == -999.0

    def test_from_dict_minimal(self):
        job = Job.from_dict({})
        assert job.status == JobStatus.PENDING
        assert job.agent_name == ""

    def test_round_trip(self):
        """to_dict → from_dict should preserve key fields."""
        job = Job(
            job_id="job1",
            agent_name="execute",
            workflow="eda",
            stage_id="spec",
            loop_score=5.0,
            classification_label="",
            parsed_metrics={"errors": 0},
            converge_action="spec-gen",
        )
        job.status = JobStatus.COMPLETED
        job.iterations = 2
        job.execution_time_ms = 300

        d = job.to_dict()
        restored = Job.from_dict(d)

        assert restored.job_id == job.job_id
        assert restored.agent_name == job.agent_name
        assert restored.workflow == job.workflow
        assert restored.status == job.status
        assert restored.stage_id == job.stage_id
        assert restored.loop_score == job.loop_score
        assert restored.parsed_metrics == job.parsed_metrics
        assert restored.converge_action == job.converge_action
        assert restored.iterations == job.iterations
        assert restored.execution_time_ms == job.execution_time_ms


# ============================================================
# Persistence: save / load
# ============================================================

class TestJobPersistence:
    def test_save_and_load(self, tmp_path):
        job = Job(
            job_id="job10",
            agent_name="execute",
            workflow="eda",
            stage_id="sim",
            loop_score=20.0,
            parsed_metrics={"sim.pass": 10, "sim.fail": 0},
        )
        job.status = JobStatus.COMPLETED
        job.iterations = 4
        job.execution_time_ms = 5000
        job.output = "All tests passed"

        job_dir = tmp_path / "jobs" / "job10"
        job.save(job_dir)

        # Verify file exists
        assert (job_dir / "result.json").exists()

        # Load and verify
        loaded = Job.load(job_dir)
        assert loaded is not None
        assert loaded.job_id == "job10"
        assert loaded.stage_id == "sim"
        assert loaded.loop_score == 20.0
        assert loaded.parsed_metrics == {"sim.pass": 10, "sim.fail": 0}
        assert loaded.status == "completed"

    def test_save_creates_directory(self, tmp_path):
        job = Job(job_id="job1")
        job_dir = tmp_path / "deep" / "nested" / "job1"
        job.save(job_dir)
        assert (job_dir / "result.json").exists()

    def test_load_nonexistent(self, tmp_path):
        result = Job.load(tmp_path / "nonexistent")
        assert result is None

    def test_load_corrupted_json(self, tmp_path):
        job_dir = tmp_path / "job_bad"
        job_dir.mkdir()
        (job_dir / "result.json").write_text("{bad json", encoding="utf-8")
        assert Job.load(job_dir) is None

    def test_save_load_round_trip_with_all_fields(self, tmp_path):
        job = Job(
            job_id="job7",
            agent_name="execute",
            workflow="rtl-gen",
            stage_id="rtl",
            iteration_in_stage=3,
            loop_score=-5.0,
            classification_label="syntax_error",
            retry_count=3,
            converge_action="rtl-fix",
            parsed_metrics={"lint.errors": 2},
            converge_context={"previous_score": -15.0},
        )
        job.status = JobStatus.ERROR
        job.error = "Lint failed"
        job.iterations = 8
        job.execution_time_ms = 3000
        job.files_examined = ["counter.sv"]
        job.files_modified = ["counter.sv"]
        job.created_at = 1000.0
        job.started_at = 1001.0
        job.finished_at = 1004.0

        job_dir = tmp_path / "jobs" / "job7"
        job.save(job_dir)
        loaded = Job.load(job_dir)

        assert loaded is not None
        assert loaded.job_id == "job7"
        assert loaded.workflow == "rtl-gen"
        assert loaded.stage_id == "rtl"
        assert loaded.iteration_in_stage == 3
        assert loaded.loop_score == -5.0
        assert loaded.classification_label == "syntax_error"
        assert loaded.retry_count == 3
        assert loaded.converge_action == "rtl-fix"
        assert loaded.parsed_metrics == {"lint.errors": 2}
        assert loaded.converge_context == {"previous_score": -15.0}
        assert loaded.error == "Lint failed"


# ============================================================
# Display: format_summary
# ============================================================

class TestJobDisplay:
    def test_format_summary_completed(self):
        job = Job(job_id="job3", status=JobStatus.COMPLETED, stage_id="lint",
                  execution_time_ms=500, loop_score=10.0)
        summary = job.format_summary()
        assert "[+]" in summary
        assert "job3" in summary
        assert "stage=lint" in summary
        assert "completed" in summary
        assert "500ms" in summary
        assert "score=10.0" in summary

    def test_format_summary_error(self):
        job = Job(job_id="job4", status=JobStatus.ERROR, classification_label="tb_bug")
        summary = job.format_summary()
        assert "[X]" in summary
        assert "cls=tb_bug" in summary

    def test_format_summary_running(self):
        job = Job(job_id="job5", status=JobStatus.RUNNING)
        summary = job.format_summary()
        assert "[...]" in summary

    def test_format_summary_pending(self):
        job = Job(job_id="job6", status=JobStatus.PENDING)
        summary = job.format_summary()
        assert "[-]" in summary

    def test_format_summary_with_metrics(self):
        job = Job(job_id="job7", status=JobStatus.COMPLETED,
                  parsed_metrics={"lint.errors": 0, "sim.pass": 10})
        summary = job.format_summary()
        assert "lint.errors=0" in summary
        assert "sim.pass=10" in summary

    def test_format_summary_no_job_id(self):
        job = Job(status=JobStatus.PENDING)
        summary = job.format_summary()
        assert "?" in summary

    def test_format_summary_with_converge_action(self):
        job = Job(job_id="job8", status=JobStatus.COMPLETED, converge_action="lint-fix")
        summary = job.format_summary()
        assert "lint-fix" in summary

    def test_format_summary_timeout(self):
        job = Job(job_id="job9", status=JobStatus.TIMEOUT)
        summary = job.format_summary()
        assert "[T]" in summary

    def test_format_summary_cancelled(self):
        job = Job(job_id="job10", status=JobStatus.CANCELLED)
        summary = job.format_summary()
        assert "[C]" in summary


# ============================================================
# Factory: job_from_agent_result
# ============================================================

class TestJobFromAgentResult:
    def _make_result(self, **kwargs):
        """Create a mock AgentResult."""
        mock = MagicMock()
        for k, v in kwargs.items():
            setattr(mock, k, v)
        return mock

    def test_basic_creation(self):
        result = self._make_result(
            agent_name="execute",
            status=JobStatus.COMPLETED,
            output="done",
            raw_output="full output",
            error=None,
            iterations=3,
            tool_calls=[{"tool": "read_file"}],
            files_examined=["counter.sv"],
            files_modified=["counter.sv"],
            token_usage={"input": 100, "output": 50},
            execution_time_ms=1500,
        )
        job = job_from_agent_result(
            result,
            job_id="job5",
            stage_id="lint",
            workflow="eda",
            iteration_in_stage=2,
            loop_score=10.0,
            classification_label="",
            converge_action="lint-run",
            parsed_metrics={"lint.errors": 0},
        )
        assert job.job_id == "job5"
        assert job.agent_name == "execute"
        assert job.workflow == "eda"
        assert job.stage_id == "lint"
        assert job.iteration_in_stage == 2
        assert job.retry_count == 2  # same as iteration_in_stage
        assert job.loop_score == 10.0
        assert job.parsed_metrics == {"lint.errors": 0}
        assert job.converge_action == "lint-run"
        assert job.output == "done"
        assert job.iterations == 3
        assert job.files_examined == ["counter.sv"]
        assert job.files_modified == ["counter.sv"]
        assert job.token_usage == {"input": 100, "output": 50}
        assert job.execution_time_ms == 1500
        assert job.created_at > 0
        assert job.finished_at > 0

    def test_minimal_creation(self):
        result = self._make_result()
        job = job_from_agent_result(result)
        assert job.job_id == ""
        assert job.stage_id == ""
        assert job.loop_score == -999.0
        assert job.parsed_metrics == {}

    def test_with_error(self):
        result = self._make_result(
            agent_name="execute",
            error="Sim failed",
            status="error",
        )
        job = job_from_agent_result(result, job_id="job6")
        assert job.error == "Sim failed"

    def test_missing_attrs_use_defaults(self):
        """Object with minimal attrs → getattr defaults kick in where provided."""
        class MinimalResult:
            error = None
        result = MinimalResult()
        job = job_from_agent_result(result, job_id="job7")
        assert job.agent_name == "execute"  # default
        assert job.status == JobStatus.COMPLETED  # default
        assert job.output == ""
        assert job.iterations == 0
        assert job.error is None

    def test_timing_derived(self):
        result = self._make_result(execution_time_ms=2000)
        job = job_from_agent_result(result)
        # started_at should be before finished_at
        assert job.finished_at >= job.started_at


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
