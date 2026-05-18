"""Deep tests for Phase 5 evidence gate hardening.

Currently focused on the SYN stage gate (newly added). The STA/PnR/PSTA
gates already exist and are exercised by other suites; this file adds a
direct unit test for the new `_synthesis_artifact_failure` helper plus an
integration test that `_job_artifact_failure` routes SYN failures correctly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.atlas_api_jobs import (
    _job_artifact_failure,
    _synthesis_artifact_failure,
)


@pytest.fixture
def ip_dir(tmp_path):
    d = tmp_path / "ipA"
    (d / "syn" / "out").mkdir(parents=True)
    return d


class TestSynthesisArtifactFailure:
    """Direct tests for the helper."""

    def test_passes_when_netlist_and_clean_reports(self, ip_dir):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "area.json").write_text(
            json.dumps({"total_cells": 100, "total_area_um2": 1234, "errors": 0,
                        "status": "pass"})
        )
        assert _synthesis_artifact_failure(ip_dir) == ""

    def test_fails_when_netlist_missing(self, ip_dir):
        # syn/out/ exists but has no .v file → must fail.
        (ip_dir / "syn" / "out" / "area.json").write_text(
            json.dumps({"errors": 0, "status": "pass"})
        )
        reason = _synthesis_artifact_failure(ip_dir)
        assert "mapped netlist missing" in reason

    def test_fails_on_synth_errors_report(self, ip_dir):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "synth_errors.json").write_text(
            json.dumps({"errors": 3})
        )
        reason = _synthesis_artifact_failure(ip_dir)
        assert "errors=3" in reason

    def test_fails_on_area_json_error_count(self, ip_dir):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "area.json").write_text(
            json.dumps({"error_count": 5, "total_cells": 100})
        )
        reason = _synthesis_artifact_failure(ip_dir)
        assert "errors=5" in reason

    def test_fails_on_non_pass_status(self, ip_dir):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "synth_summary.json").write_text(
            json.dumps({"errors": 0, "status": "failed"})
        )
        reason = _synthesis_artifact_failure(ip_dir)
        assert "status=failed" in reason

    def test_treats_pass_aliases_as_pass(self, ip_dir):
        # "ok", "completed", "success" must all be accepted.
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        for alias in ("pass", "ok", "completed", "success"):
            (ip_dir / "syn" / "out" / "synth_summary.json").write_text(
                json.dumps({"errors": 0, "status": alias})
            )
            assert _synthesis_artifact_failure(ip_dir) == "", f"alias {alias!r} not accepted"

    def test_unparseable_report_is_failure(self, ip_dir):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "area.json").write_text("{not json")
        reason = _synthesis_artifact_failure(ip_dir)
        assert "unparseable" in reason

    def test_no_syn_dir_returns_empty(self, tmp_path):
        # If syn/out/ doesn't even exist, the failure helper is a no-op —
        # the recovery layer is responsible for the "ran but produced
        # nothing" case.
        ip = tmp_path / "ipB"
        ip.mkdir()
        assert _synthesis_artifact_failure(ip) == ""


class TestJobArtifactFailureRoutesSyn:
    """Confirm `_job_artifact_failure` invokes the new SYN gate."""

    def test_syn_job_routes_to_synthesis_check(self, ip_dir, tmp_path):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        # Inject a failing report.
        (ip_dir / "syn" / "out" / "synth_errors.json").write_text(
            json.dumps({"errors": 7})
        )
        job = {"ip": "ipA", "stage_id": "syn", "workflow": "syn"}
        failed, reason = _job_artifact_failure(job, tmp_path)
        assert failed is True
        assert "errors=7" in reason

    def test_passing_syn_job_does_not_fail(self, ip_dir, tmp_path):
        (ip_dir / "syn" / "out" / "synth.v").write_text("module ipA(); endmodule\n")
        (ip_dir / "syn" / "out" / "area.json").write_text(
            json.dumps({"errors": 0, "status": "pass"})
        )
        job = {"ip": "ipA", "stage_id": "syn", "workflow": "syn"}
        failed, reason = _job_artifact_failure(job, tmp_path)
        assert failed is False
        assert reason == ""

    def test_other_stages_still_route_correctly(self, ip_dir, tmp_path):
        # Adding SYN must not break the existing LINT branch.
        (ip_dir / "lint").mkdir(parents=True, exist_ok=True)
        (ip_dir / "lint" / "dut_lint.json").write_text(
            json.dumps({"errors": 2})
        )
        job = {"ip": "ipA", "stage_id": "lint", "workflow": "lint"}
        failed, reason = _job_artifact_failure(job, tmp_path)
        assert failed is True
        assert "errors=2" in reason
