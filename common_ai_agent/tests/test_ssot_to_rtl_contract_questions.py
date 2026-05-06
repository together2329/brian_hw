from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_rtl_gen():
    root = Path(__file__).resolve().parents[1]
    path = root / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
    spec = importlib.util.spec_from_file_location("ssot_to_rtl_contract", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _doc_with_structured_primary() -> dict:
    return {
        "top_module": {"name": "simple_cpu", "type": "cpu"},
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
            "interfaces": [
                {
                    "name": "debug_status",
                    "type": "custom",
                    "ports": [{"name": "busy", "direction": "output", "width": 1}],
                }
            ],
        },
        "function_model": {
            "transactions": [
                {
                    "id": "FM_PRIMARY",
                    "outputs": ["busy follows accepted work"],
                    "output_rules": [{"name": "busy", "expr": "valid", "width": 1, "port": "busy"}],
                    "state_updates": [{"state": "accepted_count", "expr": "accepted_count + valid"}],
                }
            ]
        },
        "cycle_model": {"handshake_rules": [{"signal": "valid_ready", "rule": "valid && ready"}]},
        "error_handling": {
            "error_sources": [
                {
                    "id": "ERR_TRAP",
                    "architectural_effect": "error status and optional interrupt follow approved policy",
                }
            ]
        },
        "integration": {},
    }


def test_unresolved_optional_text_still_blocks_rtl_contract():
    rtl_gen = _load_rtl_gen()
    questions = rtl_gen._rtl_contract_questions(_doc_with_structured_primary(), "simple_cpu")

    assert [q["id"] for q in questions] == ["OPTIONAL_BEHAVIOR_POLICY"]


def test_resolved_optional_policy_does_not_reblock_on_policy_text():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["custom"] = {
        "optional_behavior_policy": {
            "resolution": "ENABLE_IRQ controls interrupt behavior; reset default ENABLE_IRQ=1.",
            "rule": "Optional behavior is resolved into explicit parameter policy.",
        }
    }

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    assert not [q for q in questions if q["id"] == "OPTIONAL_BEHAVIOR_POLICY"]


def test_generic_rule_rtl_does_not_redeclare_output_state_names():
    rtl_gen = _load_rtl_gen()
    ports = [
        {"name": "clk", "direction": "input", "width": 1},
        {"name": "rst_n", "direction": "input", "width": 1},
        {"name": "busy", "direction": "output", "width": 1},
    ]
    contract = {
        "clock": "clk",
        "reset": "rst_n",
        "reset_active": "low",
        "sample_condition": "1",
        "outputs": [],
        "state_vars": {"busy": {"width": 32, "reset": 0}, "state_0": {"width": 32, "reset": 0}},
        "state_updates": [{"name": "busy", "expr": "1"}],
        "special_outputs": {},
    }

    rtl = rtl_gen._generic_rule_rtl("demo", ports, contract)

    assert "output reg busy" in rtl
    assert "reg [31:0] busy;" not in rtl
    assert "reg [31:0] state_0;" not in rtl
    assert "busy <= 1'b1;" in rtl


def test_generic_rule_rtl_drives_apb_ready_in_single_module_path():
    rtl_gen = _load_rtl_gen()
    ports = [
        {"name": "aclk", "direction": "input", "width": 1},
        {"name": "aresetn", "direction": "input", "width": 1},
        {"name": "paddr", "direction": "input", "width": 16},
        {"name": "psel", "direction": "input", "width": 1},
        {"name": "penable", "direction": "input", "width": 1},
        {"name": "pwrite", "direction": "input", "width": 1},
        {"name": "pwdata", "direction": "input", "width": 32},
        {"name": "prdata", "direction": "output", "width": 32},
        {"name": "pready", "direction": "output", "width": 1},
        {"name": "pslverr", "direction": "output", "width": 1},
    ]
    contract = {
        "clock": "aclk",
        "reset": "aresetn",
        "reset_active": "low",
        "sample_condition": "(psel & penable)",
        "outputs": [],
        "state_vars": {},
        "state_updates": [],
        "special_outputs": {},
    }

    rtl = rtl_gen._generic_rule_rtl("apb_demo", ports, contract)
    active_block = rtl.split("        if (!(!aresetn)) begin", 1)[1].split("        end", 1)[0]

    assert "pready = (psel & penable);" in active_block
    assert "pslverr = 1'b0;" in active_block
    assert "prdata = 32'd0;" in active_block
    assert "pready = 1'b0;" not in active_block


def test_generic_rule_contract_defaults_custom_control_to_data_path():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["io_list"]["interfaces"] = [
        {
            "name": "custom_control",
            "type": "custom",
            "ports": [
                {"name": "cfg_valid", "direction": "input", "width": 1},
                {"name": "cfg_data", "direction": "input", "width": 32},
                {"name": "status_data", "direction": "output", "width": 32},
            ],
        }
    ]
    doc["function_model"]["transactions"][0]["output_rules"] = [
        {"id": "primary_observable_outputs", "outputs": ["status"]}
    ]
    doc["function_model"]["transactions"][0]["state_updates"] = [
        {"id": "write_only_state", "updates": ["internal"]}
    ]
    doc["rtl_contract"] = {
        "clock": "clk",
        "reset": "rst_n",
        "reset_active": "low",
        "output_map": {"output_0": "status_data"},
    }
    ports = rtl_gen._io_ports(doc)

    contract, questions = rtl_gen._generic_rule_contract(doc, "demo", ports)

    assert questions == []
    assert contract["sample_condition"] == "cfg_valid"
    assert contract["outputs"][0]["expr"] == "32'(cfg_data)"
    assert contract["state_updates"] == []


def test_manifest_submodules_need_module_contracts_before_rtl_gen():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_fetch.sv",
            "rtl/simple_cpu_decode.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_fetch",
            "file": "rtl/simple_cpu_fetch.sv",
            "ownership": "manifest",
            "description": "fetch unit",
        },
        {
            "name": "simple_cpu_decode",
            "file": "rtl/simple_cpu_decode.sv",
            "ownership": "manifest",
            "description": "decode unit",
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top wrapper",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    module_questions = [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]
    assert len(module_questions) == 1
    assert "simple_cpu_fetch:rtl/simple_cpu_fetch.sv" in module_questions[0]["evidence"]
    assert "simple_cpu_decode:rtl/simple_cpu_decode.sv" in module_questions[0]["evidence"]
    assert module_questions[0]["missing_modules"] == [
        {"name": "simple_cpu_fetch", "file": "rtl/simple_cpu_fetch.sv"},
        {"name": "simple_cpu_decode", "file": "rtl/simple_cpu_decode.sv"},
    ]
    assert "source_sections" in module_questions[0]["required_fields"]
    assert module_questions[0]["answer_schema"]["root_key"] == "module_contracts"
    assert "function_model.transactions.FM_PRIMARY" in module_questions[0]["available_refs"]["function_model_refs"]
    assert "function_model.transactions.FM_PRIMARY.output_rules.busy" in module_questions[0]["available_refs"]["function_model_refs"]
    assert "cycle_model.handshake_rules.valid_ready" in module_questions[0]["available_refs"]["cycle_model_refs"]


def test_manifest_submodule_contract_refs_allow_multi_file_rtl_gen():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_datapath.sv",
            "rtl/simple_cpu_wrapper.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_datapath",
            "file": "rtl/simple_cpu_datapath.sv",
            "ownership": "manifest",
            "implements": ["function_model.transactions.FM_PRIMARY.output_rules"],
            "source_sections": ["features", "function_model", "cycle_model"],
            "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
        },
        {
            "name": "simple_cpu_wrapper",
            "file": "rtl/simple_cpu_wrapper.sv",
            "ownership": "manifest",
            "wiring_only": True,
            "ports": ["clk", "rst_n", "busy"],
            "connections": {"clk": "clk", "rst_n": "rst_n", "busy": "busy"},
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    assert not [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]
    assert not [q for q in questions if q["id"] == "RTL_MANIFEST_FILELIST_SYNC"]


def test_ssot_behavior_ownership_blocks_orphan_function_refs():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_ctrl.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_ctrl",
            "file": "rtl/simple_cpu_ctrl.sv",
            "ownership": "manifest",
            "implements": ["cycle_model.handshake_rules"],
            "source_sections": ["cycle_model"],
            "cycle_model_refs": ["cycle_model.handshake_rules.valid_ready"],
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    assert not [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]
    ownership = [q for q in questions if q["id"] == "SSOT_BEHAVIOR_OWNERSHIP"]
    assert len(ownership) == 1
    assert "function_model.transactions.FM_PRIMARY" in ownership[0]["orphan_refs"]
    assert "function_model.transactions.FM_PRIMARY.output_rules.busy" in ownership[0]["orphan_refs"]
    assert ownership[0]["answer_schema"]["root_key"] == "module_contracts"


def test_ssot_behavior_ownership_blocks_orphan_decomposition_refs():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["decomposition"] = {
        "units": [
            {"id": "decode", "kind": "control"},
            {"id": "execute", "kind": "datapath"},
        ]
    }
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_decode.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_decode",
            "file": "rtl/simple_cpu_decode.sv",
            "ownership": "manifest",
            "implements": ["function_model.transactions", "decomposition.units.decode"],
            "source_sections": ["function_model", "decomposition"],
            "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
            "decomposition_refs": ["decomposition.units.decode"],
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    ownership = [q for q in questions if q["id"] == "SSOT_BEHAVIOR_OWNERSHIP"]
    assert len(ownership) == 1
    assert ownership[0]["orphan_refs"] == ["decomposition.units.execute"]
    assert "decomposition.units.execute" in ownership[0]["available_refs"]["decomposition_refs"]


def test_ssot_behavior_ownership_allows_parent_refs_to_cover_children():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["decomposition"] = {
        "units": [
            {"id": "decode", "kind": "control"},
            {"id": "execute", "kind": "datapath"},
        ]
    }
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_core.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_core",
            "file": "rtl/simple_cpu_core.sv",
            "ownership": "manifest",
            "implements": ["function_model", "decomposition.units"],
            "source_sections": ["function_model", "decomposition"],
            "function_model_refs": ["function_model.transactions"],
            "decomposition_refs": ["decomposition.units"],
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    assert not [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]
    assert not [q for q in questions if q["id"] == "SSOT_BEHAVIOR_OWNERSHIP"]


def test_manifest_submodule_contract_requires_behavior_refs_not_just_prose():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_datapath.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_datapath",
            "file": "rtl/simple_cpu_datapath.sv",
            "ownership": "manifest",
            "implements": ["datapath"],
            "source_sections": ["features", "function_model"],
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    module_questions = [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]
    assert len(module_questions) == 1
    assert module_questions[0]["missing_modules"] == [
        {"name": "simple_cpu_datapath", "file": "rtl/simple_cpu_datapath.sv"}
    ]
