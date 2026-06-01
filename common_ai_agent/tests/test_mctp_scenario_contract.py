from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCENARIO_PATH = REPO / "mctp_assembler_scratch" / "tc" / "mctp_assembler_scratch_scenarios.py"
COCOTB_DIR = REPO / "mctp_assembler_scratch" / "tb" / "cocotb"
RUNTIME_DIR = REPO / "workflow" / "tb-gen" / "runtime"
COCOTB_RUNNER = COCOTB_DIR / "test_mctp_assembler_scratch.py"
TB_GEN = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_scenario_contract_distinguishes_single_multi_interleave() -> None:
    scenarios = _load_module(SCENARIO_PATH, "mctp_scenarios_contract")

    goals = {goal["goal_id"]: goal for goal in scenarios.scenario_goals()}
    assert "EQ_SCENARIO_SC_SINGLE_PACKET_32B" in goals
    assert "EQ_SCENARIO_SC_MULTI_FRAGMENT_3PKT_SHORT_LAST" in goals
    assert "EQ_SCENARIO_SC_INTERLEAVE_TWO_Q_COMPLETE" in goals
    assert "EQ_SCENARIO_SC_READBACK_AFTER_MULTI_ASSEMBLE" in goals

    multi = goals["EQ_SCENARIO_SC_MULTI_FRAGMENT_3PKT_SHORT_LAST"]["stimulus_contract"]
    assert multi["scenario_payload_bytes"] == 76
    assert multi["scenario_packet_count"] == 3
    assert multi["scenario_source_eid"] == 0x22
    assert multi["scenario_message_tag"] == 5
    timeline = multi["machine_spec"]["timeline"]
    writes = [step["assign"] for step in timeline if "assign" in step and step["assign"].get("m_axi_wvalid") == 1]
    assert len(writes) >= 2
    assert all(write["m_axi_wstrb"] != 0 for write in writes)


def test_contract_stimulus_uses_scenario_fields_for_encoded_packet() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    stimulus_mod = _load_module(COCOTB_DIR / "mctp_contract_stimulus.py", "mctp_contract_stimulus_under_test")
    goal = {
        "goal_id": "EQ_SCENARIO_SC_SINGLE_PACKET_32B",
        "kind": "scenario",
        "scenario": "SC_SINGLE_PACKET_32B",
        "stimulus_contract": {
            "transaction_type": "FM_COMPLETE_MESSAGE",
            "scenario_payload_bytes": 32,
            "scenario_source_eid": 0x55,
            "scenario_destination_eid": 0xA0,
            "scenario_tag_owner": 1,
            "scenario_message_tag": 3,
            "scenario_packet_seq": 2,
            "scenario_payload_word": 0x112233445566778899AABBCC,
        },
    }

    stimulus = stimulus_mod.normalize_mctp_stimulus(goal, {"kind": "FM_COMPLETE_MESSAGE", "scenario_id": "SC_SINGLE_PACKET_32B"})

    assert stimulus["payload_len"] == 32
    assert stimulus["payload_byte_strobe"] == 0xFFFFFFFF
    assert stimulus["source_eid"] == 0x55
    assert stimulus["destination_eid"] == 0xA0
    assert stimulus["tag_owner"] == 1
    assert stimulus["message_tag"] == 3
    word = int(stimulus["m_axi_wdata"])
    assert ((word >> 136) & 0xFF) == 0x55
    assert ((word >> 144) & 0x7) == 3
    assert ((word >> 147) & 0x1) == 1
    assert ((word >> 148) & 0x3) == 2


def test_scoreboard_rejects_weak_multi_observation() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    sys.path.insert(0, str(RUNTIME_DIR))
    scoreboard = _load_module(COCOTB_DIR / "scoreboard.py", "mctp_scoreboard_under_test")
    stimulus = {
        "kind": "FM_ASSEMBLE_FRAGMENT",
        "scenario_id": "SC_MULTI_FRAGMENT_3PKT_SHORT_LAST",
        "source_eid": 0x22,
        "tag_owner": 1,
        "message_tag": 5,
        "scenario_payload_bytes": 76,
        "scenario_packet_count": 3,
    }
    weak = {
        "axi_bvalid": 1,
        "axi_bresp": 0,
        "debug_vdm_valid": 1,
        "sram_wr_valid": 1,
        "sram_wr_strb": 0xFFFF,
        "ctx_state": 3,
        "ctx_valid": 1,
        "descriptor_count": 1,
        "payload_byte_count": 16,
        "debug_context_key": 0,
    }
    strong = {
        **weak,
        "payload_byte_count": 76,
        "debug_context_key": (0x22 << 10) | (1 << 9) | 5,
    }
    strong_done_state = {
        **weak,
        "payload_byte_count": 12,
        "ctx_payload_byte_count": 76,
        "debug_context_key": (0x22 << 10) | (1 << 9) | 5,
        "descriptor_count": 0,
        "ctx_state": 3,
    }

    assert not scoreboard._mctp_contract_verdict("EQ_SCENARIO_SC_MULTI_FRAGMENT_3PKT_SHORT_LAST", "SC_X", stimulus, weak)
    assert scoreboard._mctp_contract_verdict("EQ_SCENARIO_SC_MULTI_FRAGMENT_3PKT_SHORT_LAST", "SC_X", stimulus, strong)
    assert scoreboard._mctp_contract_verdict("EQ_SCENARIO_SC_MULTI_FRAGMENT_3PKT_SHORT_LAST", "SC_X", stimulus, strong_done_state)


def test_cocotb_runner_applies_preconditions_before_machine_timeline() -> None:
    source = COCOTB_RUNNER.read_text(encoding="utf-8")
    precondition_pos = source.index("await _apply_goal_preconditions(dut, manifest, goal, stimulus)")
    clear_pos = source.index("_clear_sample_inputs(dut, manifest)", precondition_pos)
    machine_spec_pos = source.index("await _apply_machine_spec(dut, manifest, machine_spec)")

    assert precondition_pos < clear_pos < machine_spec_pos


def test_tb_generator_aliases_payload_byte_count_state_to_rtl_counter() -> None:
    generator = _load_module(TB_GEN, "tb_generator_under_test")

    aliases = generator._state_observable_aliases(["ctx_payload_byte_count"], ["ctx_payload_count"])

    assert aliases == {"ctx_payload_byte_count": ["ctx_payload_count"]}


def test_cocotb_runner_idles_axi_valid_last_and_strobe_low() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    runner = _load_module(COCOTB_RUNNER, "mctp_runner_idle_under_test")
    manifest = {
        "input_map": {
            "m_axi_awvalid": "m_axi_awvalid",
            "m_axi_wvalid": "m_axi_wvalid",
            "m_axi_wlast": "m_axi_wlast",
            "m_axi_wstrb": "m_axi_wstrb",
            "m_axi_bready": "m_axi_bready",
        },
        "input_ports": ["m_axi_awvalid", "m_axi_wvalid", "m_axi_wlast", "m_axi_wstrb", "m_axi_bready"],
        "port_widths": {
            "m_axi_awvalid": 1,
            "m_axi_wvalid": 1,
            "m_axi_wlast": 1,
            "m_axi_wstrb": 32,
            "m_axi_bready": 1,
        },
    }

    assert runner._idle_input_value(manifest, "m_axi_awvalid") == 0
    assert runner._idle_input_value(manifest, "m_axi_wvalid") == 0
    assert runner._idle_input_value(manifest, "m_axi_wlast") == 0
    assert runner._idle_input_value(manifest, "m_axi_wstrb") == 0
    assert runner._idle_input_value(manifest, "m_axi_bready") == 1


def test_cocotb_runner_clears_single_shot_inputs_without_sample_inputs_gate() -> None:
    source = COCOTB_RUNNER.read_text(encoding="utf-8")
    first_cycle = source.index("if _cycle_idx == 0:")
    clear_pos = source.index("_clear_single_shot_inputs(dut, manifest)", first_cycle)

    assert 'and (manifest.get("sample_inputs") or [])' not in source
    assert 'if bool(stimulus.get("_sample_active", True)):' not in source[first_cycle:clear_pos]
    assert "def _clear_single_shot_inputs" in source
