from __future__ import annotations

import os
from pathlib import Path

from .contract_reflection_helpers import map_field, read_json
from .sim_freshness_helpers import append_text, make_reflected_ip, run_contract_check, run_stamp


def test_contract_check_with_sim_freshness_rejects_forged_sim_stage_restamp_with_touched_evidence(tmp_path: Path) -> None:
    ip_dir = make_reflected_ip(tmp_path)
    stamp = run_stamp(tmp_path)
    assert stamp.returncode == 0, stamp.stdout
    append_text(ip_dir / "rtl" / "contract_ip.sv")
    changed_mtime = (ip_dir / "rtl" / "contract_ip.sv").stat().st_mtime_ns
    for offset, rel in enumerate(("sim/scoreboard_events.jsonl", "sim/contract_ip.vcd"), 1):
        artifact = ip_dir / rel
        next_mtime = changed_mtime + offset * 1_000_000
        os.utime(artifact, ns=(next_mtime, next_mtime))

    restamp = run_stamp(tmp_path, source="sim_stage")
    result = run_contract_check(tmp_path)

    assert restamp.returncode == 1
    assert "sim stage run marker older than input: sim/sim_stage_run.json" in restamp.stdout
    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    assert route["owner_workflow"] == "sim-debug"
    assert "sim stage run marker older than input: sim/sim_stage_run.json" in str(route["reason"])
