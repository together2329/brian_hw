from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[1]
SCENARIO_PATH = REPO / "mctp_assembler_scratch" / "tc" / "mctp_assembler_scratch_scenarios.py"
COCOTB_DIR = REPO / "mctp_assembler_scratch" / "tb" / "cocotb"
SSOT_PATH = REPO / "mctp_assembler_scratch" / "yaml" / "mctp_assembler_scratch.ssot.yaml"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _scenario_goals() -> dict[str, dict[str, Any]]:
    scenarios = _load_module(SCENARIO_PATH, "mctp_ad_scenarios")
    return {goal["goal_id"]: goal for goal in scenarios.scenario_goals()}


def test_ad_scenarios_include_precondition_machine_spec_timeline() -> None:
    goals = _scenario_goals()
    duplicate = goals["EQ_SCENARIO_AD_DUPLICATE_SOM"]
    overflow = goals["EQ_SCENARIO_AD_SRAM_OVERFLOW"]

    assert "no_sram_write" in duplicate["expected_contract"]["state_updates"]
    assert "no_sram_write" in overflow["expected_contract"]["state_updates"]

    duplicate_machine = duplicate["stimulus_contract"]["machine_spec"]
    duplicate_timeline = duplicate_machine["timeline"]
    duplicate_writes = [
        step["assign"]
        for step in duplicate_timeline
        if isinstance(step, dict) and isinstance(step.get("assign"), dict) and int(step["assign"].get("m_axi_wvalid", 0)) == 1
    ]
    assert duplicate_writes
    assert int(duplicate_writes[0]["m_axi_wstrb"]) != 0
    encoded = int(duplicate_writes[0]["m_axi_wdata"])
    assert (encoded >> 151) & 0x1 == 1
    assert (encoded >> 150) & 0x1 == 0

    overflow_machine = overflow["stimulus_contract"]["machine_spec"]
    overflow_timeline = overflow_machine["timeline"]
    csr_offsets = [
        int(step["csr_write"]["offset"])
        for step in overflow_timeline
        if isinstance(step, dict) and isinstance(step.get("csr_write"), dict) and "offset" in step["csr_write"]
    ]
    assert 0x0030 in csr_offsets
    assert 0x0034 in csr_offsets


def test_ad_scenarios_normalize_to_valid_packet_drive() -> None:
    goals = _scenario_goals()
    sys.path.insert(0, str(COCOTB_DIR))
    stimulus_mod = _load_module(COCOTB_DIR / "mctp_contract_stimulus.py", "mctp_contract_stimulus_ad")

    for goal_id in ("EQ_SCENARIO_AD_DUPLICATE_SOM", "EQ_SCENARIO_AD_SRAM_OVERFLOW"):
        goal = goals[goal_id]
        stimulus = stimulus_mod.normalize_mctp_stimulus(
            goal,
            {
                "kind": goal["stimulus_contract"]["transaction_type"],
                "scenario_id": goal["scenario"],
            },
        )
        assert int(stimulus["m_axi_awvalid"]) == 1
        assert int(stimulus["m_axi_wvalid"]) == 1
        assert int(stimulus["m_axi_wstrb"]) != 0
        assert int(stimulus["payload_byte_strobe"]) != 0
        assert "no_sram_write" in goal["expected_contract"]["state_updates"]


def test_ssot_ad_scenarios_carry_executable_machine_specs() -> None:
    doc = yaml.safe_load(SSOT_PATH.read_text(encoding="utf-8"))
    scenarios = {
        scenario["id"]: scenario
        for scenario in doc["test_requirements"]["scenarios"]
        if scenario["id"] in {"AD_DUPLICATE_SOM", "AD_SRAM_OVERFLOW"}
    }

    duplicate = scenarios["AD_DUPLICATE_SOM"]["stimulus_machine_spec"]
    assert duplicate["metadata"]["scenario_force_valid_packet"] == 1
    assert duplicate["metadata"]["scenario_som"] == 1
    assert duplicate["metadata"]["scenario_eom"] == 0
    duplicate_write = next(step["assign"] for step in duplicate["timeline"] if "assign" in step and step["assign"].get("m_axi_wvalid"))
    assert int(duplicate_write["m_axi_wstrb"]) != 0

    overflow = scenarios["AD_SRAM_OVERFLOW"]["stimulus_machine_spec"]
    assert overflow["metadata"]["scenario_force_valid_packet"] == 1
    csr_writes = [step["csr_write"] for step in overflow["timeline"] if "csr_write" in step]
    assert {"offset": 48, "data": 0} in csr_writes
    assert {"offset": 52, "data": 16} in csr_writes
