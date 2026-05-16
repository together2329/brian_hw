from __future__ import annotations

import importlib.util
from pathlib import Path


def _load_module(relative: str, name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_bridge():
    return _load_module("workflow/ssot-gen/scripts/approved_to_ssot.py", "approved_to_ssot_bridge")


def test_cpu_intent_wins_over_instruction_data_memory_text():
    bridge = _load_bridge()
    state = {
        "kind": "simple 32-bit CPU core",
        "decisions": {
            "purpose": (
                "A minimal CPU core that fetches instructions from instruction "
                "memory and accesses external data memory."
            ),
            "memory_map": (
                "Instruction and data memories are external native "
                "request/response interfaces."
            ),
        },
    }

    assert bridge._infer_ip_type("simple_cpu", state) == "cpu"


def test_memory_intent_still_classifies_as_memory_without_cpu_terms():
    bridge = _load_bridge()
    state = {
        "kind": "sram controller",
        "decisions": {
            "purpose": "A local SRAM memory controller with native request response.",
            "memory_map": "Local RAM window with CSR status.",
        },
    }

    assert bridge._infer_ip_type("local_sram", state) == "memory"


def test_isa_instruction_execute_intent_wins_over_memory_terms():
    bridge = _load_bridge()
    state = {
        "kind": "ARMv6-M Cortex-M0 decoded Thumb instruction execute block",
        "decisions": {
            "purpose": (
                "Decoded Thumb instruction execute/control block computes ALU, "
                "branch pc_next, register write enable, and load/store memory request intent."
            ),
            "memory_map": "No local RAM; instruction and data memory are external.",
        },
    }

    assert bridge._infer_ip_type("arm_m0_thumb_exec", state) == "cpu"


def test_bus_bridge_intent_wins_over_arm_cpu_mentions():
    bridge = _load_bridge()
    state = {
        "kind": "ARM M0 I3C system bus bridge",
        "decisions": {
            "purpose": (
                "Transaction-level ARM M0 system bus bridge/fabric that connects "
                "the CPU memory-intent interface to an I3C-capable gateway and "
                "routes non-I3C accesses to memory."
            ),
            "bus_interface": "Native CPU memory request sink plus I3C gateway and memory target source.",
        },
    }

    assert bridge._infer_ip_type("arm_m0_i3c_bus", state) == "bus"


def test_quad_spi_controller_is_peripheral_even_with_negated_cpu_text():
    bridge = _load_bridge()
    state = {
        "kind": "Quad SPI controller supporting DDR transfers",
        "decisions": {
            "purpose": "Quad SPI flash controller/peripheral with DDR launch/sample support; not a CPU or processor.",
            "bus_interface": "Native valid/ready transaction sink with qspi dq rise/fall observables.",
        },
    }

    assert bridge._infer_ip_type("quad_spi_ddr_ctrl", state) == "peripheral"


def test_qspi_ddr_signal_widths_use_dq_and_boolean_widths():
    bridge = _load_bridge()
    params = [{"name": "DATA_WIDTH", "default": 32}, {"name": "DQ_WIDTH", "default": 4}]

    assert bridge._signal_width("dq_i_rise", params) == 4
    assert bridge._signal_width("dq_o_fall", params) == 4
    assert bridge._signal_width("quad_mode_active", params) == 1
    assert bridge._signal_width("launch_fall", params) == 1
    assert bridge._signal_width("cs_n", params) == 1


def test_approved_bridge_writes_audit_clean_requirements(tmp_path):
    bridge = _load_bridge()
    state = {
        "kind": "SMBus transaction block",
        "decisions": {
            "purpose": (
                "Accept valid native transactions, compute PEC, and avoid any "
                "TODO/TBD/stub/mock/placeholder language in final artifacts. "
                "The accepted_count state increments for each sampled transaction."
            ),
            "bus_interface": "Native valid/ready request with addr, command, data_in, pec_in, result, packet_ok, and result_valid.",
            "test_expectation": "Cover pass, fail, backpressure, reset, and accepted_count state transitions.",
        },
    }
    doc = bridge._doc("smbus", state)

    req = bridge._write_requirements(tmp_path, "smbus", state, doc)
    text = req.read_text(encoding="utf-8")

    assert req.stat().st_size >= 1000
    for marker in ("TBD", "TODO", "FIXME", "PLACEHOLDER", "stub", "mock"):
        assert marker.lower() not in text.lower()


def test_dma330_doc_starts_with_rtl_gen_gate_and_deferred_connections():
    bridge = _load_bridge()
    state = {
        "kind": "DMA controller",
        "decisions": {
            "purpose": "DMA330-like controller with manifest control, datapath, and status modules.",
            "submodule_structure": (
                "submodules: engine schedules transfers; axi_frontend handles bus commands; "
                "status tracks completion. Top wrapper only wires these units."
            ),
        },
    }

    doc = bridge._doc("dma330", state)

    assert doc["quality_gates"]["rtl_gen"]["profile"] == "production"
    assert doc["quality_gates"]["rtl_gen"]["pass"]
    assert doc["integration"]["connections"] == []
    assert doc["integration"]["connection_contract_status"].startswith("missing machine-readable")
    scale_todo = next(item for item in doc["workflow_todos"]["rtl-gen"] if item["id"] == "RTL_TARGET_SCALE_POLICY")
    assert scale_todo["answer_schema"]["root_key"] == "target_scale or target_scale_waiver"
    assert "source_files_min" in scale_todo["answer_schema"]["target_scale_fields"]
    assert "lines_min" in scale_todo["answer_schema"]["target_scale_fields"]
    assert scale_todo["example_answer"]["target_scale"]["depth_score_min"] == 120
    todo = next(item for item in doc["workflow_todos"]["rtl-gen"] if item["id"] == "RTL_RESOLVE_CONNECTION_CONTRACTS")
    assert "integration.connections" in todo["source_refs"]
    assert "module/port/signal" in todo["criteria"][0]
    assert todo["answer_schema"]["root_key"] == "connection_contracts"
    assert todo["answer_schema"]["item_required_fields"] == ["module", "port", "signal"]
    assert todo["example_answer"]["connection_contracts"][0]["module"] == "dma330_engine"


def test_goal_audit_placeholder_detection_ignores_negated_quality_text(tmp_path):
    audit = _load_module(
        "workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py",
        "audit_fl_rtl_equivalence_goal",
    )
    artifact = tmp_path / "artifact.md"

    artifact.write_text(
        "pass: all sections validate with no unresolved TBDs\n"
        "rtl: all expected files are non-placeholder and lint clean\n",
        encoding="utf-8",
    )
    assert not audit._text_has_placeholder(artifact)

    artifact.write_text("TODO: fill in the missing behavior\n", encoding="utf-8")
    assert audit._text_has_placeholder(artifact)


def test_submodule_structure_extracts_names_separately_from_responsibilities():
    bridge = _load_bridge()
    state = {
        "decisions": {
            "submodule_structure": (
                "submodules: transaction_control samples valid transactions and drives ready/result_valid; "
                "pec_checker computes expected PEC and packet_ok; "
                "response_datapath computes result from addr command data_in; "
                "count_state maintains accepted_count. Top wrapper smbus only wires these units together."
            )
        }
    }

    rows = bridge._sub_modules("smbus", state)
    names = [row["name"] for row in rows]

    assert names == [
        "smbus_transaction_control",
        "smbus_pec_checker",
        "smbus_response_datapath",
        "smbus_count_state",
        "smbus",
    ]
    assert rows[0]["description"] == "samples valid transactions and drives ready/result_valid"


def test_single_top_conceptual_decomposition_does_not_create_manifest_submodules():
    bridge = _load_bridge()
    state = {
        "decisions": {
            "submodule_structure": (
                "Single generated top module for v1. Functional decomposition should list "
                "decode_control, alu_execute, branch_control as conceptual units only; "
                "no separate RTL submodule files and no child SSOT."
            )
        }
    }

    rows = bridge._sub_modules("arm_m0_thumb_exec", state)

    assert rows
    assert {row["ownership"] for row in rows} == {"conceptual"}
    assert all(not row.get("file") for row in rows)
    assert all(row.get("rtl_emit") is False for row in rows)


def test_rtl_ignores_conceptual_submodules_for_manifest_generation():
    rtl = _load_module("workflow/rtl-gen/scripts/ssot_to_rtl.py", "ssot_to_rtl_manifest")
    doc = {
        "sub_modules": [
            {"name": "demo_decode_control", "ownership": "conceptual", "rtl_emit": False},
            {"name": "demo_core", "file": "rtl/demo_core.sv", "ownership": "manifest"},
        ]
    }

    assert [item["name"] for item in rtl._manifest_submodules(doc)] == ["demo_core"]


def test_rtl_single_top_conceptual_units_do_not_require_module_ownership_gate():
    rtl = _load_module("workflow/rtl-gen/scripts/ssot_to_rtl.py", "ssot_to_rtl_ownership")
    doc = {
        "sub_modules": [
            {"name": "demo_decode_control", "ownership": "conceptual", "rtl_emit": False},
        ],
        "function_model": {
            "transactions": [
                {"id": "FM_PRIMARY", "output_rules": [{"name": "result", "expr": "data_in"}]},
            ]
        },
    }

    assert rtl._ssot_behavior_ownership_questions(doc, "demo") == []


def test_rtl_manifest_requires_explicit_module_contracts_instead_of_name_heuristics():
    rtl = _load_module("workflow/rtl-gen/scripts/ssot_to_rtl.py", "ssot_to_rtl_bridge")
    submods = [
        {"name": "smbus_transaction_control", "file": "rtl/smbus_transaction_control.sv", "description": "samples valid transactions and drives ready/result_valid"},
        {"name": "smbus_pec_checker", "file": "rtl/smbus_pec_checker.sv", "description": "computes expected PEC and packet_ok"},
        {"name": "smbus_response_datapath", "file": "rtl/smbus_response_datapath.sv", "description": "computes result from addr command data_in"},
        {"name": "smbus_count_state", "file": "rtl/smbus_count_state.sv", "description": "maintains accepted_count"},
    ]
    doc = {
        "top_module": "smbus",
        "filelist": {"rtl": [sm["file"] for sm in submods]},
        "sub_modules": submods,
        "function_model": {
            "transactions": [
                {
                    "id": "primary",
                    "output_rules": [
                        {
                            "name": "packet_ok",
                            "port": "packet_ok",
                            "expr": "pec_in == ((data_in ^ command ^ addr) & 255)",
                        },
                        {"name": "result", "port": "result", "expr": "(data_in ^ command ^ addr) & 255"},
                        {"name": "result_valid", "port": "result_valid", "expr": "1"},
                    ],
                }
            ]
        },
    }

    questions = rtl._module_contract_questions(doc, "smbus")

    assert [q["id"] for q in questions] == ["RTL_MODULE_CONTRACTS"]
    missing = {item["name"] for item in questions[0]["missing_modules"]}
    assert missing == {sm["name"] for sm in submods}
    assert "function_model_refs" in questions[0]["required_fields"]


def test_machine_rule_predicates_infer_one_bit_widths_before_address_widths():
    bridge = _load_bridge()
    params = [
        {"name": "ADDR_WIDTH", "default": 7},
        {"name": "DYN_ADDR_WIDTH", "default": 7},
        {"name": "RESP_WIDTH", "default": 2},
        {"name": "DATA_WIDTH", "default": 32},
    ]

    assert bridge._signal_width("dyn_addr", params) == 7
    assert bridge._signal_width("dyn_addr_valid", params) == 1
    assert bridge._signal_width("frame_valid", params) == 1
    assert bridge._signal_width("parity_error", params) == 1
    assert bridge._signal_width("illegal_ccc", params) == 1
    assert bridge._signal_width("accept", params) == 1
    assert bridge._signal_width("cpu_we", params) == 1
    assert bridge._signal_width("mem_write", params) == 1
    assert bridge._signal_width("irq", params) == 1
    assert bridge._signal_width("i3c_irq", params) == 1
    assert bridge._signal_width("hotjoin_req", params) == 1
    assert bridge._signal_width("resp_code", params) == 2


def test_machine_rules_are_deduped_and_validated_per_marker():
    bridge = _load_bridge()
    params = [{"name": "DATA_WIDTH", "default": 32}, {"name": "COUNT_WIDTH", "default": 16}]
    decisions = {
        "purpose": (
            "machine_rules: sample_condition=instr_valid; "
            "output alu_result=(src_a + src_b) * add_req; "
            "state accepted_count=accepted_count+1"
        ),
        "test_expectation": (
            "Repeat the same approved executable ledger for traceability. "
            "machine_rules: sample_condition=instr_valid; "
            "output alu_result=(src_a + src_b) * add_req; "
            "state accepted_count=accepted_count+1"
        ),
    }

    machine = bridge._machine_rules(decisions, params)

    assert machine["sample_condition"] == "instr_valid"
    assert [rule["name"] for rule in machine["output_rules"]] == ["alu_result"]
    assert [rule["name"] for rule in machine["state_updates"]] == ["accepted_count"]


def test_valid_ready_sample_condition_uses_accept_phase_in_ssot_contract():
    bridge = _load_bridge()
    state = {
        "kind": "valid-ready datapath",
        "decisions": {
            "purpose": (
                "machine_rules: sample_condition=valid; "
                "output result=data_in; "
                "state accepted_count=accepted_count+1"
            ),
            "bus_interface": "Native valid/ready request sink with data_in, result, and accepted_count.",
            "test_expectation": "Only accepted valid && ready transfers may update outputs or state.",
        },
    }

    doc = bridge._doc("vr_block", state)
    primary = next(tx for tx in doc["function_model"]["transactions"] if tx["id"] == "FM_PRIMARY")

    assert primary["sample_condition"] == "(valid) and ready"
    assert doc["rtl_contract"]["sample_condition"] == "(valid) and ready"


def test_machine_rule_ternary_keywords_do_not_become_ports():
    bridge = _load_bridge()
    state = {
        "kind": "decoded instruction execute block",
        "decisions": {
            "purpose": (
                "machine_rules: sample_condition=instr_valid; "
                "output pc_next=(pc + imm) if branch_req else (pc + 2); "
                "state accepted_count=accepted_count+1"
            ),
            "bus_interface": "Native valid/ready decoded instruction transaction interface.",
        },
    }

    doc = bridge._doc("thumb_exec", state)
    ports = {
        port["name"]
        for intf in doc["io_list"]["interfaces"]
        for port in intf.get("ports", [])
    }
    input_map = set(doc["rtl_contract"]["input_map"])

    assert "if" not in ports
    assert "else" not in ports
    assert "if" not in input_map
    assert "else" not in input_map


def test_explicit_machine_rule_interface_does_not_emit_unused_default_payload_ports():
    bridge = _load_bridge()
    params = [{"name": "DATA_WIDTH", "default": 32}, {"name": "COUNT_WIDTH", "default": 16}]
    ports = bridge._valid_ready_ports(
        32,
        16,
        params,
        extra_inputs=["frame_valid", "broadcast"],
        extra_outputs=["accept", "ccc_hit"],
    )
    by_name = {port["name"]: port for port in ports}

    assert "valid" not in by_name
    assert "data_in" not in by_name
    assert "result" not in by_name
    assert "result_valid" not in by_name
    assert by_name["frame_valid"]["width"] == 1
    assert by_name["broadcast"]["width"] == 1
    assert by_name["accept"]["width"] == 1


def test_rtl_boolean_lowering_casts_wide_terms_before_logical_ops():
    rtl = _load_module("workflow/rtl-gen/scripts/ssot_to_rtl.py", "ssot_to_rtl_bool")
    env = {
        "parity_error": "32'(parity_error)",
        "hdr_unsupported": "32'(hdr_unsupported)",
        "illegal_ccc": "32'(illegal_ccc)",
    }
    widths = {name: 32 for name in env}

    expr = rtl._ast_to_rtl_width(
        rtl._parse_rule_expr("parity_error or hdr_unsupported or illegal_ccc"),
        env,
        widths,
        1,
    )

    assert "!= 0" in expr
    assert "|| 32'(" not in expr


def test_rtl_output_rule_dependencies_use_same_cycle_expression():
    rtl = _load_module("workflow/rtl-gen/scripts/ssot_to_rtl.py", "ssot_to_rtl_output_deps")
    ports = [
        {"name": "clk", "direction": "input", "width": 1},
        {"name": "rst_n", "direction": "input", "width": 1},
        {"name": "cpu_req", "direction": "input", "width": 1},
        {"name": "cpu_addr", "direction": "input", "width": 32},
        {"name": "i3c_ready", "direction": "input", "width": 1},
        {"name": "mem_ready", "direction": "input", "width": 1},
        {"name": "i3c_hit", "direction": "output", "width": 1},
        {"name": "i3c_cmd_valid", "direction": "output", "width": 1},
        {"name": "mem_valid", "direction": "output", "width": 1},
        {"name": "cpu_ready", "direction": "output", "width": 1},
    ]
    doc = {
        "parameters": [
            {"name": "I3C_BASE", "default": 0x40010000},
            {"name": "I3C_WINDOW_BYTES", "default": 0x1000},
        ],
        "function_model": {
            "transactions": [
                {
                    "id": "bus_route",
                    "output_rules": [
                        {
                            "name": "i3c_hit",
                            "port": "i3c_hit",
                            "expr": "cpu_addr >= I3C_BASE and cpu_addr < I3C_BASE + I3C_WINDOW_BYTES",
                        },
                        {"name": "i3c_cmd_valid", "port": "i3c_cmd_valid", "expr": "cpu_req and i3c_hit"},
                        {"name": "mem_valid", "port": "mem_valid", "expr": "cpu_req and not i3c_hit"},
                        {
                            "name": "cpu_ready",
                            "port": "cpu_ready",
                            "expr": "(i3c_ready and i3c_hit) or (mem_ready and not i3c_hit)",
                        },
                    ],
                }
            ]
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "sample_condition": "cpu_req",
        },
    }

    contract, questions = rtl._generic_rule_contract(doc, "arm_m0_i3c_bus", ports)
    assert questions == []
    by_port = {item["port"]: item["expr"] for item in contract["outputs"]}

    assert "i3c_hit" not in by_port["i3c_cmd_valid"]
    assert "i3c_hit" not in by_port["cpu_ready"]
    assert "cpu_addr" in by_port["i3c_cmd_valid"]
    assert "cpu_addr" in by_port["cpu_ready"]


def test_cocotb_template_normalizes_stimulus_to_port_width_before_scoreboard():
    tb = _load_module("workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py", "tb_gen_widths")

    assert tb._param_defaults({"parameters": [{"name": "I3C_BASE", "default": "0x40010000"}]}) == {
        "I3C_BASE": 0x40010000
    }
    assert "def _stimulus_value_for_field" in tb.TEST_PY
    assert "def _named_windows" in tb.TEST_PY
    assert "def _register_offset_for_goal" in tb.TEST_PY
    assert "def _address_value_for_goal" in tb.TEST_PY
    assert "def _outside_selected_window" in tb.TEST_PY
    assert 'replace("_", " ").replace("-", " ")' in tb.TEST_PY
    assert 'route.startswith(("mem", "memory"))' in tb.TEST_PY
    assert '"mux from memory"' in tb.TEST_PY
    assert 'low == "ddr_enable"' in tb.TEST_PY
    assert '"ddr disabled"' in tb.TEST_PY
    assert 'low == "illegal_mode"' in tb.TEST_PY
    assert 'low == "unsupported_width"' in tb.TEST_PY
    assert "stimulus[field] = _stimulus_value_for_field(manifest, field, idx, goal)" in tb.TEST_PY
    assert "stimulus.setdefault(field, _stimulus_value_for_field(manifest, field, idx, goal))" in tb.TEST_PY
    assert '"ready is high after reset" in identity' in tb.TEST_PY
    assert '"backpressure" in identity or "backpressure" in goal_text' in tb.TEST_PY
    assert 'for port in manifest.get("sample_inputs") or []:' in tb.TEST_PY
    assert "stimulus[str(port)] = value" in tb.TEST_PY
    assert '"broadcast"' in tb.TEST_PY
    assert '"accept"' in tb.TEST_PY
