from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_resolver():
    root = Path(__file__).resolve().parents[1]
    path = root / "workflow" / "ssot-gen" / "scripts" / "resolve_rtl_blockers.py"
    spec = importlib.util.spec_from_file_location("resolve_rtl_blockers_module", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rtl_contract_blocker_answers_project_into_rtl_contract():
    resolver = _load_resolver()
    doc = {
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clock", "direction": "input"}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input"}]}],
            "interfaces": [
                {"ports": [{"name": "cfg_valid", "direction": "input"}, {"name": "status_data", "direction": "output"}]}
            ],
        }
    }
    blocker = {
        "questions": [
            {"id": "RTL_CLOCK_PORT", "decision_needed": "clock"},
            {"id": "RTL_RESET_PORT", "decision_needed": "reset"},
            {"id": "RTL_OUTPUT_MAP_OUTPUT_0", "decision_needed": "output map"},
        ]
    }
    answers = [
        {"id": "RTL_CLOCK_PORT", "answer": "Use clock as rtl_contract.clock."},
        {"id": "RTL_RESET_PORT", "answer": "Use rst_n as active-low reset."},
        {"id": "RTL_OUTPUT_MAP_OUTPUT_0", "answer": "Map output_0 to status_data."},
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    contract = out["rtl_contract"]

    assert contract["clock"] == "clock"
    assert contract["reset"] == "rst_n"
    assert contract["reset_active"] == "low"
    assert contract["output_map"]["output_0"] == "status_data"


def test_valid_ready_sample_condition_answer_updates_contract_and_fm():
    resolver = _load_resolver()
    doc = {
        "function_model": {
            "transactions": [{"id": "FM_PRIMARY", "name": "primary_behavior"}]
        },
        "rtl_contract": {"sample_condition": "valid"},
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_VALID_READY_SAMPLE_CONDITION",
                "current_sample_condition": "valid",
                "ready_port": "ready",
            }
        ]
    }
    answers = [{"id": "RTL_VALID_READY_SAMPLE_CONDITION", "answer": "Use the recommended valid/ready acceptance."}]

    out = resolver.apply_answers(doc, blocker, answers)

    assert out["rtl_contract"]["sample_condition"] == "(valid) and ready"
    assert out["function_model"]["transactions"][0]["sample_condition"] == "(valid) and ready"
    assert any("sample_condition=(valid) and ready" in row["rule"] for row in out["cycle_model"]["handshake_rules"])


def test_observable_state_rule_answer_projects_machine_rules():
    resolver = _load_resolver()
    doc = {
        "function_model": {
            "transactions": [{"id": "FM_PRIMARY", "name": "primary_behavior"}]
        },
        "rtl_contract": {},
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_OBSERVABLE_STATE_RULES",
                "missing_observable_state": ["busy", "error"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_OBSERVABLE_STATE_RULES",
            "custom": """
observable_state_rules:
  - name: busy
    port: busy
    expr: valid and ready
    width: 1
  - name: error
    port: error
    expr: not packet_ok
    width: 1
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    txn = out["function_model"]["transactions"][0]

    assert {row["name"] for row in txn["output_rules"]} == {"busy", "error"}
    assert out["rtl_contract"]["output_map"]["busy"] == "busy"
    assert out["rtl_contract"]["output_map"]["error"] == "error"
    assert out["custom"]["rtl_observable_state_resolution_history"][-1]["unresolved"] == []


def test_rtl_module_contract_answer_projects_into_submodules():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_fetch",
                "file": "rtl/demo_fetch.sv",
                "ownership": "manifest",
                "description": "fetch block",
            },
            {
                "name": "demo_top",
                "file": "rtl/demo_top.sv",
                "ownership": "manifest",
            },
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_MODULE_CONTRACTS",
                "missing_modules": [{"name": "demo_fetch", "file": "rtl/demo_fetch.sv"}],
                "required_fields": ["implements", "source_sections", "function_model_refs"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_MODULE_CONTRACTS",
            "custom": """
module_contracts:
  - name: demo_fetch
    implements:
      - fetches next instruction address and captures imem response
    source_sections: [features, function_model, cycle_model]
    function_model_refs: [function_model.transactions.FM_PRIMARY.state_updates]
    decomposition_refs: [decomposition.units.fetch]
    cycle_model_refs: [cycle_model.pipeline.S0_ACCEPT]
    feature_refs: [approved_primary_behavior]
    dataflow_refs: [dataflow.sequence]
    ports: [clock, rst_n, imem_addr, imem_valid, imem_ready, imem_rdata]
    connections:
      clock: io_list.clock_domains.primary_clk
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    fetch = out["sub_modules"][0]

    assert fetch["implements"] == ["fetches next instruction address and captures imem response"]
    assert fetch["source_sections"] == ["features", "function_model", "cycle_model"]
    assert fetch["function_model_refs"] == ["function_model.transactions.FM_PRIMARY.state_updates"]
    assert fetch["decomposition_refs"] == ["decomposition.units.fetch"]
    assert fetch["ports"] == ["clock", "rst_n", "imem_addr", "imem_valid", "imem_ready", "imem_rdata"]
    assert fetch["connections"] == {"clock": "io_list.clock_domains.primary_clk"}
    assert fetch["contract_status"] == "approved_by_rtl_blocker_answer"
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["applied"][0]["name"] == "demo_fetch"
    assert history[-1]["unresolved"] == []


def test_ssot_behavior_ownership_answer_projects_module_refs():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_core",
                "file": "rtl/demo_core.sv",
                "ownership": "manifest",
                "implements": ["function_model"],
                "source_sections": ["function_model"],
                "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
            }
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "SSOT_BEHAVIOR_OWNERSHIP",
                "orphan_refs": ["decomposition.units.execute"],
                "candidate_modules": [{"name": "demo_core", "file": "rtl/demo_core.sv"}],
            }
        ]
    }
    answers = [
        {
            "id": "SSOT_BEHAVIOR_OWNERSHIP",
            "custom": """
module_contracts:
  - name: demo_core
    decomposition_refs: [decomposition.units.execute]
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    core = out["sub_modules"][0]

    assert core["decomposition_refs"] == ["decomposition.units.execute"]
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["blocker_id"] == "SSOT_BEHAVIOR_OWNERSHIP"
    assert history[-1]["applied"][0]["fields"] == ["decomposition_refs"]


def test_rtl_module_contract_option_click_does_not_fabricate_contracts():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_decode",
                "file": "rtl/demo_decode.sv",
                "ownership": "manifest",
                "description": "decode block",
            }
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_MODULE_CONTRACTS",
                "missing_modules": [{"name": "demo_decode", "file": "rtl/demo_decode.sv"}],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_MODULE_CONTRACTS",
            "selected": ["recommended"],
            "answer": "Have ssot-gen repair sub_modules into a module contract ledger.",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)

    assert "implements" not in out["sub_modules"][0]
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["applied"] == []
    assert history[-1]["unresolved"] == [
        {"name": "demo_decode", "reason": "no structured contract answer"}
    ]
