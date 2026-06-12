from __future__ import annotations

import importlib.util
import json
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


def test_apb_illegal_access_policy_is_not_reasked_when_ssot_defines_response():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "gpio_policy", "type": "gpio"},
        "io_list": {
            "interfaces": [
                {
                    "name": "apb_slave",
                    "type": "apb",
                    "ports": [
                        {"name": "paddr", "direction": "input", "width": "ADDR_WIDTH"},
                        {"name": "psel", "direction": "input", "width": 1},
                        {"name": "penable", "direction": "input", "width": 1},
                        {"name": "pwrite", "direction": "input", "width": 1},
                        {"name": "prdata", "direction": "output", "width": 32},
                        {"name": "pready", "direction": "output", "width": 1},
                        {"name": "pslverr", "direction": "output", "width": 1},
                    ],
                }
            ]
        },
        "registers": {
            "register_list": [
                {
                    "name": "DATA_IN",
                    "offset": 4,
                    "access": "ro",
                    "write_semantics": "writes ignored",
                }
            ]
        },
        "error_handling": {
            "error_sources": [{"id": "ILLEGAL_ADDR", "condition": "APB ACCESS to unmapped address"}],
            "propagation": ["Illegal address forces pslverr and prdata=0 for reads."],
        },
        "rtl_contract": {
            "protocol_contracts": [
                {
                    "interface": "apb_slave",
                    "rule": "No slave backpressure; pready asserted during ACCESS for legal and illegal accesses",
                },
                {
                    "interface": "apb_slave",
                    "rule": "Illegal address: pslverr=1 in ACCESS; read returns prdata=0; no state updates",
                },
            ]
        },
        "function_model": {
            "transactions": [
                {
                    "id": "FM_ILLEGAL_ACCESS",
                    "output_rules": [
                        {"name": "pslverr_o", "port": "pslverr", "expr": "1", "width": 1},
                        {"name": "prdata_o", "port": "prdata", "expr": "0", "width": 32},
                    ],
                    "state_updates": [],
                }
            ]
        },
    }

    question_ids = {q["id"] for q in rtl_gen._rtl_contract_questions(doc, "gpio_policy")}

    assert "APB_ILLEGAL_ACCESS_POLICY" not in question_ids


def test_apb_illegal_access_policy_accepts_structured_rtl_contract_response():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "gpio_policy", "type": "gpio"},
        "io_list": {
            "interfaces": [
                {
                    "name": "apb_slave",
                    "type": "apb",
                    "ports": [
                        {"name": "paddr", "direction": "input", "width": "ADDR_WIDTH"},
                        {"name": "psel", "direction": "input", "width": 1},
                        {"name": "penable", "direction": "input", "width": 1},
                        {"name": "pwrite", "direction": "input", "width": 1},
                        {"name": "prdata", "direction": "output", "width": 32},
                        {"name": "pready", "direction": "output", "width": 1},
                        {"name": "pslverr", "direction": "output", "width": 1},
                    ],
                }
            ]
        },
        "error_handling": {
            "error_sources": [{"id": "ILLEGAL_ADDR", "condition": "illegal access to unsupported address"}]
        },
        "rtl_contract": {
            "apb_illegal_access_policy": {
                "response": {"pready": 1, "pslverr": 1, "prdata": 0},
                "state_update": "none",
            }
        },
    }

    question_ids = {q["id"] for q in rtl_gen._rtl_contract_questions(doc, "gpio_policy")}

    assert "APB_ILLEGAL_ACCESS_POLICY" not in question_ids


def test_apb_illegal_access_policy_still_blocks_when_response_is_missing():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "gpio_policy", "type": "gpio"},
        "io_list": {
            "interfaces": [
                {
                    "name": "apb_slave",
                    "type": "apb",
                    "ports": [
                        {"name": "paddr", "direction": "input", "width": 12},
                        {"name": "psel", "direction": "input", "width": 1},
                        {"name": "penable", "direction": "input", "width": 1},
                        {"name": "pwrite", "direction": "input", "width": 1},
                    ],
                }
            ]
        },
        "error_handling": {
            "error_sources": [{"id": "ILLEGAL_ADDR", "condition": "illegal access to unsupported address"}]
        },
    }

    question_ids = {q["id"] for q in rtl_gen._rtl_contract_questions(doc, "gpio_policy")}

    assert "APB_ILLEGAL_ACCESS_POLICY" in question_ids


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


def test_generic_rule_contract_allows_inout_observable_output_rule():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "gpio_probe"},
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
            "interfaces": [
                {
                    "name": "gpio",
                    "ports": [{"name": "gpio_pins", "direction": "inout", "width": 32}],
                }
            ],
        },
        "function_model": {
            "transactions": [
                {
                    "id": "FM_GPIO_DRIVE",
                    "outputs": ["gpio_pins drive mask"],
                    "output_rules": [{"name": "gpio_pins", "port": "gpio_pins", "expr": "1", "width": 32}],
                }
            ]
        },
        "cycle_model": {"handshake_rules": []},
        "rtl_contract": {"clock": "clk", "reset": "rst_n", "sample_condition": "1"},
    }
    ports = rtl_gen._io_ports(doc)

    contract, questions = rtl_gen._generic_rule_contract(doc, "gpio_probe", ports)

    assert not [q for q in questions if q["id"].startswith("RTL_OUTPUT_MAP_GPIO_PINS")]
    assert any(item["port"] == "gpio_pins" for item in contract["outputs"])


def test_generic_rule_contract_lowers_reduction_or_and_bit_select_helpers():
    rtl_gen = _load_rtl_gen()
    assert rtl_gen._expr_names("reduction_or(edge_event)") == {"edge_event"}
    doc = {
        "top_module": {"name": "gpio_irq"},
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
            "interfaces": [
                {
                    "name": "apb",
                    "ports": [
                        {"name": "pwdata", "direction": "input", "width": 32},
                        {"name": "pstrb", "direction": "input", "width": 4},
                        {"name": "irq", "direction": "output", "width": 1},
                    ],
                }
            ],
        },
        "function_model": {
            "state_variables": [
                {"name": "dir_reg", "width": 32, "reset": 0},
                {"name": "int_status_reg", "width": 32, "reset": 0},
                {"name": "int_en_reg", "width": 32, "reset": 0},
            ],
            "derived_signals": [
                {"name": "edge_event", "width": 32, "expr": "int_status_reg & int_en_reg"}
            ],
            "transactions": [
                {
                    "id": "FM_IRQ",
                    "output_rules": [
                        {
                            "name": "irq",
                            "port": "irq",
                            "expr": "reduction_or((int_status_reg | edge_event) & int_en_reg)",
                            "width": 1,
                        }
                    ],
                    "state_updates": [
                        {
                            "name": "dir_reg",
                            "expr": "((dir_reg & (4294967295 ^ (255 if pstrb[0] else 0))) | (pwdata & (255 if pstrb[0] else 0)))",
                            "width": 32,
                        }
                    ],
                }
            ],
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "sample_condition": "1",
            "input_map": {"pwdata": "pwdata", "pstrb": "pstrb"},
            "output_map": {"irq": "irq"},
        },
    }
    ports = rtl_gen._io_ports(doc)

    contract, questions = rtl_gen._generic_rule_contract(doc, "gpio_irq", ports)

    question_ids = {q["id"] for q in questions}
    assert "RTL_INPUT_MAP_REDUCTION_OR" not in question_ids
    assert "RTL_EXPR_IRQ" not in question_ids
    assert "RTL_STATE_EXPR_DIR_REG" not in question_ids
    assert "(|" in contract["outputs"][0]["expr"]
    assert "pstrb[0]" in contract["state_updates"][0]["expr"]


def test_generic_rule_contract_resolves_derived_signals_out_of_order():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "gpio_read_mux"},
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
            "interfaces": [
                {
                    "name": "apb",
                    "ports": [
                        {"name": "paddr", "direction": "input", "width": 12},
                        {"name": "prdata", "direction": "output", "width": 32},
                    ],
                }
            ],
        },
        "function_model": {
            "state_variables": [{"name": "data_out_reg", "width": 32, "reset": 0}],
            "derived_signals": [
                {
                    "name": "read_mux",
                    "width": 32,
                    "expr": "(data_out_reg if addr == 4 else 0)",
                },
                {"name": "addr", "width": 12, "expr": "paddr"},
            ],
            "transactions": [
                {
                    "id": "FM_APB_READ",
                    "output_rules": [
                        {
                            "name": "fm_apb_read_prdata",
                            "port": "prdata",
                            "expr": "read_mux",
                            "width": 32,
                        }
                    ],
                }
            ],
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "sample_condition": "1",
            "output_map": {"fm_apb_read_prdata": "prdata"},
        },
    }
    ports = rtl_gen._io_ports(doc)

    contract, questions = rtl_gen._generic_rule_contract(doc, "gpio_read_mux", ports)

    question_ids = {q["id"] for q in questions}
    assert "RTL_INPUT_MAP_READ_MUX" not in question_ids
    assert "RTL_DERIVED_EXPR_READ_MUX" not in question_ids
    assert "RTL_EXPR_FM_APB_READ_PRDATA" not in question_ids
    assert contract["outputs"][0]["port"] == "prdata"
    assert "paddr" in contract["outputs"][0]["expr"]


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


def test_generic_rule_contract_allows_state_backed_output_self_reference():
    rtl_gen = _load_rtl_gen()
    doc = {
        "top_module": {"name": "counter_probe"},
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clk", "direction": "input", "width": 1}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input", "width": 1}]}],
            "interfaces": [
                {
                    "name": "native",
                    "ports": [
                        {"name": "valid", "direction": "input", "width": 1},
                        {"name": "data_in", "direction": "input", "width": 8},
                        {"name": "result", "direction": "output", "width": 9},
                        {"name": "accepted_count", "direction": "output", "width": 8},
                    ],
                }
            ],
        },
        "function_model": {
            "state_variables": [{"name": "accepted_count", "width": 8, "reset": 0}],
            "transactions": [
                {
                    "id": "FM_PRIMARY",
                    "output_rules": [{"name": "result", "port": "result", "expr": "data_in << 1", "width": 9}],
                    "state_updates": [{"name": "accepted_count", "expr": "accepted_count + 1", "width": 8}],
                }
            ],
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "sample_condition": "valid",
            "input_map": {"data_in": "data_in", "valid": "valid"},
            "output_map": {"result": "result", "accepted_count": "accepted_count"},
            "output_rules": [
                {"name": "result", "port": "result", "expr": "data_in << 1", "width": 9},
                {"name": "accepted_count", "port": "accepted_count", "expr": "accepted_count", "width": 8},
            ],
        },
    }
    ports = rtl_gen._io_ports(doc)

    contract, questions = rtl_gen._generic_rule_contract(doc, "counter_probe", ports)

    question_ids = {q["id"] for q in questions}
    assert "RTL_OUTPUT_DEP_ACCEPTED_COUNT" not in question_ids
    assert "RTL_OBSERVABLE_STATE_RULES" not in question_ids
    assert any(item["port"] == "accepted_count" for item in contract["outputs"])


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


def test_manifest_submodule_keyed_refs_imply_source_sections():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_fifo.sv",
            "rtl/simple_cpu_irq.sv",
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu_fifo",
            "file": "rtl/simple_cpu_fifo.sv",
            "ownership": "manifest",
            "implements": "top_module",
            "dataflow_refs": ["rx_fifo"],
        },
        {
            "name": "simple_cpu_irq",
            "file": "rtl/simple_cpu_irq.sv",
            "ownership": "manifest",
            "implements": "top_module",
            "register_refs": ["IRQ_STATUS"],
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


def test_wiring_only_module_can_use_global_integration_connections():
    rtl_gen = _load_rtl_gen()
    doc = _doc_with_structured_primary()
    doc["filelist"] = {
        "rtl": [
            "rtl/simple_cpu_datapath.sv",
            "rtl/simple_cpu_top_int.sv",
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
            "name": "simple_cpu_top_int",
            "file": "rtl/simple_cpu_top_int.sv",
            "ownership": "manifest",
            "wiring_only": True,
            "implements": ["integration.connections", "io_list.interfaces"],
            "source_sections": ["integration", "io_list"],
        },
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "description": "top",
        },
    ]
    doc["integration"] = {
        "connections": [
            {
                "from_module": "simple_cpu_datapath",
                "from_port": "busy_o",
                "to_module": "simple_cpu_top_int",
                "to_port": "busy_i",
                "signal": "busy",
            }
        ]
    }

    questions = rtl_gen._rtl_contract_questions(doc, "simple_cpu")

    assert not [q for q in questions if q["id"] == "RTL_MODULE_CONTRACTS"]


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


def test_ssot_behavior_ownership_allows_top_when_top_owns_behavior():
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
            "rtl/simple_cpu.sv",
        ]
    }
    doc["sub_modules"] = [
        {
            "name": "simple_cpu",
            "file": "rtl/simple_cpu.sv",
            "ownership": "manifest",
            "implements": ["function_model", "decomposition.units"],
            "source_sections": ["function_model", "decomposition"],
            "function_model_refs": ["function_model.transactions"],
            "decomposition_refs": ["decomposition.units"],
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


def test_starter_mode_requires_llm_authored_rtl_from_minimal_output_rules(tmp_path: Path):
    rtl_gen = _load_rtl_gen()
    ip = "tiny_starter_and"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_starter_and
io_list:
  interfaces:
    - name: pins
      type: raw
      ports:
        - {name: a_i, direction: input, width: 1}
        - {name: b_i, direction: input, width: 1}
        - {name: y_o, direction: output, width: 1}
function_model:
  description: y_o is asserted when both inputs are asserted.
  output_rules:
    - {name: y_o, expr: a_i and b_i}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    try:
        rtl_gen.generate(ip, tmp_path, mode="starter")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Starter RTL handoff should stop before RTL authoring")

    contract_doc = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    gates = json.loads((ip_dir / "rtl" / "rtl_preview_gates.json").read_text(encoding="utf-8"))

    assert contract_doc["type"] == "starter_llm_rtl_authoring_contract"
    assert (ip_dir / "rtl" / "starter_llm_rtl_handoff.json").is_file()
    assert not (ip_dir / "rtl" / f"{ip}.sv").exists()
    assert (ip_dir / "rtl" / "rtl_blocked.json").is_file()
    assert gates["status"] == "handoff"
    assert gates["mode"] == "starter"
    assert any(item["id"] == "STARTER_CYCLE_MODEL_DEFERRED" for item in gates["soft_gates"])
    assert any(item["id"] == "STARTER_LLM_RTL_AUTHORING_REQUIRED" for item in gates["soft_gates"])


def test_starter_mode_accepts_existing_common_agent_rtl_provenance(tmp_path: Path):
    rtl_gen = _load_rtl_gen()
    ip = "tiny_starter_done"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_starter_done
  file: rtl/tiny_starter_done.sv
io_list:
  interfaces:
    - name: pins
      type: raw
      ports:
        - {name: a_i, direction: input, width: 1}
        - {name: b_i, direction: input, width: 1}
        - {name: y_o, direction: output, width: 1}
function_model:
  description: y_o is asserted when both inputs are asserted.
  output_rules:
    - {name: y_o, expr: a_i and b_i}
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "module tiny_starter_done(input logic a_i, input logic b_i, output logic y_o); "
        "assign y_o = a_i & b_i; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    todo_path = ip_dir / "rtl" / "rtl_todo_plan.json"
    todo_path.write_text(
        json.dumps({"schema_version": 1, "type": "rtl_todo_plan", "tasks": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "headless_common_engine",
                "todo_plan_sha256": rtl_gen._stable_json_sha256(todo_path),
                "rtl_files": [f"rtl/{ip}.sv"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    rtl_gen.generate(ip, tmp_path, mode="starter")

    gates = json.loads((ip_dir / "rtl" / "rtl_preview_gates.json").read_text(encoding="utf-8"))
    assert gates["status"] == "pass"
    assert not (ip_dir / "rtl" / "rtl_blocked.json").exists()
    hard_gate = [item for item in gates["hard_gates"] if item["id"] == "STARTER_LLM_RTL_AUTHORING_REQUIRED"]
    assert hard_gate and hard_gate[0]["status"] == "pass"


def test_signoff_preflight_preserves_generic_rtl_contract_for_tb(tmp_path: Path):
    rtl_gen = _load_rtl_gen()
    ip = "tiny_signoff_and"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_signoff_and
  file: rtl/tiny_signoff_and.sv
io_list:
  clock_domains:
    - ports:
        - {name: clk, direction: input, width: 1}
  resets:
    - ports:
        - {name: rst_n, direction: input, width: 1}
  interfaces:
    - name: pins
      ports:
        - {name: a_i, direction: input, width: 1}
        - {name: b_i, direction: input, width: 1}
        - {name: y_o, direction: output, width: 1}
rtl_contract:
  clock: clk
  reset: rst_n
  reset_active: low
  sample_condition: "1"
function_model:
  transactions:
    - id: FM_PRIMARY
      output_rules:
        - {name: y_o, port: y_o, expr: "a_i and b_i", width: 1}
custom:
  optional_behavior_policy:
    resolution: No optional behavior exists for this minimal combinational IP.
    rule: Optional behavior is disabled.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "module tiny_signoff_and(input logic clk, input logic rst_n, input logic a_i, input logic b_i, output logic y_o); assign y_o = a_i & b_i; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text("{}", encoding="utf-8")
    todo_hash = rtl_gen._stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "atlas_ui",
                "todo_plan_sha256": todo_hash,
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        ),
        encoding="utf-8",
    )

    rtl_gen.generate(ip, tmp_path, mode="signoff")

    contract_doc = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    assert contract_doc["type"] == "generic_ssot_rule_rtl_contract"
    assert contract_doc["top"] == ip
    assert contract_doc["contract"]["outputs"][0]["port"] == "y_o"


def test_signoff_preflight_accepts_clockless_resetless_combinational_contract(tmp_path: Path):
    rtl_gen = _load_rtl_gen()
    ip = "tiny_clockless_xor"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_clockless_xor
  file: rtl/tiny_clockless_xor.sv
  type: combinational_logic
io_list:
  interfaces:
    - name: pins
      ports:
        - {name: a, direction: input, width: 1}
        - {name: b, direction: input, width: 1}
        - {name: y, direction: output, width: 1}
rtl_contract:
  type: combinational_scalar_contract
  transaction: xor
  clock: none
  reset: none
  reset_active: none
  sample_condition: continuous_comb_evaluation
  input_map: {a: a, b: b}
  output_map: {xor_y: y}
  output_rules:
    - {name: xor_y, port: y, expr: "a ^ b", width: 1}
function_model:
  transactions:
    - id: xor
      output_rules:
        - {name: xor_y, port: y, expr: "a ^ b", width: 1}
cycle_model:
  cycle_model_waiver: true
  combinational_eval:
    clock: none
    reset: none
    latency_cycles: 0
    ready_valid: false
custom:
  optional_behavior_policy:
    resolution: No optional behavior exists for this minimal combinational IP.
    rule: Optional behavior is disabled.
""".strip()
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        "module tiny_clockless_xor(input logic a, input logic b, output logic y); assign y = a ^ b; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text("{}", encoding="utf-8")
    todo_hash = rtl_gen._stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "atlas_ui",
                "todo_plan_sha256": todo_hash,
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        ),
        encoding="utf-8",
    )

    rtl_gen.generate(ip, tmp_path, mode="signoff")

    assert not (ip_dir / "rtl" / "rtl_blocked.json").exists()
    contract_doc = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    contract = contract_doc["contract"]
    assert contract_doc["type"] == "generic_ssot_rule_rtl_contract"
    assert contract["clock"] == "none"
    assert contract["reset"] == "none"
    assert contract["reset_active"] == "none"
    assert contract["no_clock"] is True
    assert contract["no_reset"] is True
    assert contract["sample_condition"] == "1'b1"
    assert contract["outputs"][0]["port"] == "y"
