from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from .contract_reflection_helpers import REPO, JsonMap, map_field, read_json, write_json, write_rows
from .sim_freshness_helpers import append_text, make_reflected_ip, mark_evidence_newer_than_inputs, mark_input_newer_than_evidence, run_contract_check, run_stamp


def test_contract_check_with_sim_freshness_passes_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout

    result = run_contract_check(tmp_path)

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] == "pass"
    assert "sim_evidence_freshness" in str(report["runs"])


def test_sim_freshness_stamp_rejects_manual_source_even_with_fresh_artifacts(tmp_path: Path) -> None:
    _ = make_reflected_ip(tmp_path)

    stamp = run_stamp(tmp_path, source="")

    assert stamp.returncode == 1
    assert "sim evidence freshness stamp_source is not sim_stage: manual" in stamp.stdout


def test_contract_check_with_sim_freshness_rejects_changed_rtl_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    _ = (ip_dir / "rtl" / "contract_ip.sv").write_text("// changed after sim evidence\n", encoding="utf-8")

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert report["status"] == "fail"
    assert route["owner_workflow"] == "sim-debug"
    assert "sim evidence input fingerprint mismatch: rtl/contract_ip.sv" in str(route["reason"])


@pytest.mark.parametrize(
    "rel",
    [
        "yaml/contract_ip.ssot.yaml",
        "model/functional_model.py",
        "model/cycle_model.py",
        "tb/cocotb/test_contract_ip.py",
    ],
)
def test_contract_check_with_sim_freshness_rejects_changed_stage_input_after_stamp(tmp_path: Path, rel: str) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / rel)

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert f"sim evidence input fingerprint mismatch: {rel}" in str(route["reason"])


def test_contract_check_with_sim_freshness_rejects_changed_scoreboard_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    scoreboard = ip_dir / "sim" / "scoreboard_events.jsonl"
    _ = scoreboard.write_text(scoreboard.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert "sim evidence artifact fingerprint mismatch: sim/scoreboard_events.jsonl" in str(route["reason"])


def test_contract_check_with_sim_freshness_rejects_changed_evidence_row_artifact_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    obligations = contract.get("obligations")
    assert isinstance(obligations, list)
    obligation = obligations[0]
    assert isinstance(obligation, dict)
    evidence_rows = obligation.get("evidence_rows")
    assert isinstance(evidence_rows, list)
    evidence_row = evidence_rows[0]
    assert isinstance(evidence_row, dict)
    evidence_row["artifact"] = "sim/contract_v2_events.jsonl"
    write_json(ip_dir / "verify" / "evidence_contract.json", contract)
    write_rows(
        ip_dir / "sim" / "contract_v2_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
                "scenario_id": "SC_PAYLOAD",
            }
        ],
    )
    mark_evidence_newer_than_inputs(ip_dir, ("sim/contract_v2_events.jsonl",))
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    write_rows(
        ip_dir / "sim" / "contract_v2_events.jsonl",
        [
            {
                "changed_after_stamp": True,
                "goal_id": "EQ_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
                "scenario_id": "SC_PAYLOAD",
            }
        ],
    )

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert report["status"] == "fail"
    assert route["owner_workflow"] == "sim-debug"
    assert "sim evidence artifact fingerprint mismatch: sim/contract_v2_events.jsonl" in str(route["reason"])


def test_contract_check_with_sim_freshness_rejects_changed_vcd_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "sim" / "contract_ip.vcd")

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert "sim evidence artifact fingerprint mismatch: sim/contract_ip.vcd" in str(route["reason"])


def test_sim_freshness_stamp_rejects_invalid_reflection_path(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    reflection = read_json(ip_dir / "verify" / "contract_reflection.json")
    contract_refs = reflection["contract_refs"]
    assert isinstance(contract_refs, list)
    first_ref = contract_refs[0]
    assert isinstance(first_ref, dict)
    ssot = first_ref["ssot"]
    assert isinstance(ssot, dict)
    ssot["path"] = "../outside.yaml"
    write_json(ip_dir / "verify" / "contract_reflection.json", reflection)

    stamp = run_stamp(tmp_path)

    assert stamp.returncode == 1
    assert "invalid sim evidence path ssot.path: ../outside.yaml" in stamp.stdout


def test_contract_check_with_sim_freshness_rejects_reflection_shrink_after_stamp(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    reflection = read_json(ip_dir / "verify" / "contract_reflection.json")
    contract_refs = reflection["contract_refs"]
    assert isinstance(contract_refs, list)
    first_ref = contract_refs[0]
    assert isinstance(first_ref, dict)
    first_ref.pop("tb", None)
    write_json(ip_dir / "verify" / "contract_reflection.json", reflection)

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    assert "sim evidence metadata fingerprint mismatch: verify/contract_reflection.json" in result.stdout
    assert "stamped sim evidence input fingerprint no longer required: tb/cocotb/test_contract_ip.py" in result.stdout


def test_contract_check_with_sim_freshness_rejects_manual_restamp_after_rtl_change(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    manual = run_stamp(tmp_path, source="")
    assert manual.returncode == 1
    assert "sim evidence artifact older than input" in manual.stdout

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    assert "sim evidence artifact older than input" in result.stdout
    assert "sim evidence freshness stamp_source is not sim_stage: manual" in result.stdout


def test_contract_check_with_sim_freshness_rejects_forged_sim_stage_restamp_after_input_change(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    mark_input_newer_than_evidence(ip_dir, "rtl/contract_ip.sv")

    restamp = run_stamp(tmp_path, source="sim_stage")
    result = run_contract_check(tmp_path)

    assert restamp.returncode == 1
    assert "sim evidence artifact older than input" in restamp.stdout
    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert "sim evidence artifact older than input" in str(route["reason"])


def test_contract_check_with_sim_freshness_rejects_forged_sim_stage_restamp_even_if_artifacts_are_touched_newer(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    mark_evidence_newer_than_inputs(ip_dir, include_provenance=False)

    restamp = run_stamp(tmp_path, source="sim_stage")
    result = run_contract_check(tmp_path)

    assert restamp.returncode == 1
    assert "sim stage run marker older than input: sim/sim_stage_run.json predates rtl/contract_ip.sv" in restamp.stdout
    assert result.returncode == 1
    assert "sim evidence freshness stamp status is not pass: fail" in result.stdout


def test_contract_check_with_sim_freshness_rejects_failed_stamp_even_if_artifacts_touched(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    mark_input_newer_than_evidence(ip_dir, "rtl/contract_ip.sv")
    failed_stamp = run_stamp(tmp_path, source="sim_stage")
    assert failed_stamp.returncode == 1
    mark_evidence_newer_than_inputs(ip_dir, include_provenance=False)

    result = run_contract_check(tmp_path)

    assert result.returncode == 1
    assert "sim evidence freshness stamp status is not pass: fail" in result.stdout
    assert "sim evidence freshness stamp recorded issue: sim evidence artifact older than input" in result.stdout


def test_contract_check_routes_sim_freshness_before_semantic_overlay_failure(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    empty_semantic_source: JsonMap = {"contract_refs": [], "requirements": [], "schema_version": 1, "type": "semantic_contracts"}
    write_json(ip_dir / "verify" / "semantic_contracts.json", empty_semantic_source)

    result = run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert "sim_evidence_freshness" in str(route["reason"])


def test_sim_script_stamps_freshness_after_successful_python_runner(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    runner = ip_dir / "tb" / "cocotb" / "test_runner.py"
    _ = runner.write_text(
        "if __name__ == '__main__':\n"
        "    import os\n"
        "    from pathlib import Path\n"
        "    ip_dir = Path(__file__).resolve().parents[2]\n"
        "    os.utime(ip_dir / 'sim' / 'scoreboard_events.jsonl')\n"
        "    os.utime(ip_dir / 'sim' / 'contract_ip.vcd')\n"
        "    print('TESTS=1 PASS=1 FAIL=0')\n"
        "    print('0 errors, 0 warnings')\n",
        encoding="utf-8",
    )
    env = dict(os.environ)
    env["SIM_TIMEOUT_SEC"] = "20"
    env["BENCHMARK_LOG"] = str(tmp_path / "benchmark.log")

    sim = subprocess.run(
        [sys.executable, str(REPO / "workflow" / "tb-gen" / "scripts" / "sim.py"), str(runner)],
        cwd=REPO,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert sim.returncode == 0, sim.stdout
    freshness = read_json(ip_dir / "sim" / "evidence_freshness.json")
    assert freshness["stamp_source"] == "sim_stage"
    result = run_contract_check(tmp_path)
    assert result.returncode == 0, result.stdout
