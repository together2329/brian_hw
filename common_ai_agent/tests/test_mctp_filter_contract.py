from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
COCOTB_DIR = REPO / "mctp_assembler_scratch" / "tb" / "cocotb"
RUNTIME_DIR = REPO / "workflow" / "tb-gen" / "runtime"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_filter_vdm_contract_accepts_valid_vdm_ack() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    sys.path.insert(0, str(RUNTIME_DIR))
    scoreboard = _load_module(COCOTB_DIR / "scoreboard.py", "mctp_scoreboard_filter_contract")

    goal_id = "EQ_TRANSACTION_FM_FILTER_VDM"
    scenario_id = "SC_002_EQ_TRANSACTION_FM_FILTER_VDM"
    stimulus = {
        "kind": "Validate PCIe VDM envelope for MCTP transport",
        "scenario_id": scenario_id,
    }
    observed = {
        "debug_vdm_valid": 1,
        "debug_drop_pulse": 0,
        "m_axi_bvalid": 1,
        "m_axi_bresp": 0,
    }

    assert scoreboard._mctp_contract_verdict(goal_id, scenario_id, stimulus, observed)


def test_filter_vdm_contract_rejects_drop_or_malformed_observations() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    sys.path.insert(0, str(RUNTIME_DIR))
    scoreboard = _load_module(COCOTB_DIR / "scoreboard.py", "mctp_scoreboard_filter_contract_reject")

    goal_id = "EQ_TRANSACTION_FM_FILTER_VDM"
    scenario_id = "SC_002_EQ_TRANSACTION_FM_FILTER_VDM"
    stimulus = {
        "kind": "Validate PCIe VDM envelope for MCTP transport",
        "scenario_id": scenario_id,
    }

    malformed = {
        "debug_vdm_valid": 0,
        "debug_drop_pulse": 1,
        "m_axi_bvalid": 1,
        "m_axi_bresp": 0,
    }
    drop_only = {
        "debug_vdm_valid": 1,
        "debug_drop_pulse": 1,
        "m_axi_bvalid": 0,
        "m_axi_bresp": 0,
    }

    assert not scoreboard._mctp_contract_verdict(goal_id, scenario_id, stimulus, malformed)
    assert not scoreboard._mctp_contract_verdict(goal_id, scenario_id, stimulus, drop_only)


def test_filter_vdm_stimulus_normalizes_supported_vdm_to_drop_none() -> None:
    sys.path.insert(0, str(COCOTB_DIR))
    stimulus_mod = _load_module(COCOTB_DIR / "mctp_contract_stimulus.py", "mctp_filter_stimulus_contract")
    goal = {
        "goal_id": "EQ_TRANSACTION_FM_FILTER_VDM",
        "kind": "transaction",
        "stimulus_contract": {
            "transaction_type": "Validate PCIe VDM envelope for MCTP transport",
            "required_fields": ["kind", "vdm_supported", "packet_drop_reason"],
            "constraints": ["tlp_valid"],
        },
    }

    stimulus = stimulus_mod.normalize_mctp_stimulus(
        goal,
        {
            "kind": "Validate PCIe VDM envelope for MCTP transport",
            "vdm_supported": 1,
            "packet_drop_reason": 2,
        },
    )

    assert stimulus["packet_drop_reason"] == 0
    assert int(stimulus["m_axi_wstrb"]) != 0
