"""Regression tests for derive_rtl_todos.py fixes landed 2026-05-14.

Two bugs were caught by the uart_lite end-to-end trial:

1. ``_audit_rtl_placeholder_free`` rejected the literal phrase
   ``not implemented`` even when it appeared inside a SystemVerilog comment
   that legitimately documented a deliberate SSOT-driven omission. The fix
   moves ``not\\s+implemented`` and ``implement\\s+later`` to a code-only
   regex (run after stripping ``//`` comments). The hard tokens
   (TODO/TBD/FIXME/HACK/PLACEHOLDER/STUB/DUMMY) remain blocked everywhere.

2. ``_owner_for`` used to ``break`` after the first ``refs`` match per
   module, so a generic owner_ref (``fsm``) could shadow a more specific
   one (``fsm.rx_fsm``) in another module and cause RX FSM tasks to be
   mapped to the TX FSM file. The fix collects every matching owner_ref
   per module and globally picks the most specific one.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any


def _load_derive():
    root = Path(__file__).resolve().parents[1]
    path = root / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
    spec = importlib.util.spec_from_file_location("derive_rtl_todos_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _two_fsm_modules() -> list[dict[str, Any]]:
    """Mimic the uart_lite topology where two FSM submodules share the
    ``fsm`` source_section but each owns its own subsection."""
    return [
        {
            "name": "uart_lite_tx_fsm",
            "file": "rtl/uart_lite_tx_fsm.sv",
            "refs": ["cycle_model", "cycle_model.pipeline.tx_stages", "fsm", "fsm.tx_fsm"],
        },
        {
            "name": "uart_lite_rx_fsm",
            "file": "rtl/uart_lite_rx_fsm.sv",
            "refs": ["cycle_model", "cycle_model.pipeline.rx_stages", "fsm", "fsm.rx_fsm"],
        },
    ]


def _write_contract_demo_ssot(tmp_path: Path, ip: str) -> Path:
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        f"""
top_module:
  name: {ip}_top
io_list:
  clock_domains:
    - name: clk
      direction: input
      width: 1
  resets:
    - name: rst_n
      direction: input
      width: 1
  interfaces:
    - name: ctrl
      ports:
        - name: cmd_valid
          direction: input
          width: 1
        - name: cmd_ready
          direction: output
          width: 1
        - name: rsp_rdata
          direction: output
          width: 32
sub_modules:
  - name: {ip}_core
    file: rtl/{ip}_core.sv
    refs:
      - function_model.transactions.READ
      - cycle_model.handshake_rules.ctrl
function_model:
  transactions:
    - id: READ
      name: read_cmd
      behavioral_contract_refs: [BC_READ]
      inputs: [cmd_valid]
      outputs:
        - name: rsp_rdata
      output_rules:
        - name: rsp_rdata
          port: rsp_rdata
          expr: count_q
      state_updates:
        - name: count_q
          expr: count_q + 1
cycle_model:
  handshake_rules:
    - name: ctrl
      signal: cmd_valid
      condition: cmd_valid && cmd_ready
traceability:
  locked_truth_projection:
    behavioral_contracts: [BC_READ]
""",
        encoding="utf-8",
    )
    (ip_dir / "req" / "obligations.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "obligations": [
                    {
                        "obligation_id": "OBL_READ",
                        "requirement_refs": ["REQ_READ"],
                        "statement": "Implement the read command behavior.",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return ip_dir


def _write_behavioral_contract(ip_dir: Path, *, rtl_stage: bool = True) -> None:
    stage_contracts = [
        {"stage": "rtl-gen", "observable": "cmd_valid cmd_ready rsp_rdata count_q", "pass_condition": "accepted read drives rsp_rdata from count_q"}
    ] if rtl_stage else [{"stage": "sim", "validator": "scoreboard"}]
    (ip_dir / "req" / "behavioral_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip_dir.name,
                "contracts": [
                    {
                        "id": "BC_READ",
                        "obligations": ["OBL_READ"],
                        "inputs": ["cmd_valid", "cmd_ready"],
                        "outputs": ["rsp_rdata"],
                        "decision_table": [
                            {
                                "when": "cmd_valid == 1 and cmd_ready == 1",
                                "then": {"rsp_rdata": "count_q"},
                            }
                        ],
                        "stage_contracts": stage_contracts,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_owner_for_picks_specific_ref_over_generic_one():
    derive = _load_derive()
    modules = _two_fsm_modules()

    rx_state = derive._owner_for("fsm.rx_fsm.states.state_0", modules, "uart_lite")
    assert rx_state["module"] == "uart_lite_rx_fsm"
    assert rx_state["file"] == "rtl/uart_lite_rx_fsm.sv"
    assert rx_state["matched_ref"] == "fsm.rx_fsm"

    tx_trans = derive._owner_for("fsm.tx_fsm.transitions.transition_0", modules, "uart_lite")
    assert tx_trans["module"] == "uart_lite_tx_fsm"
    assert tx_trans["matched_ref"] == "fsm.tx_fsm"


def test_owner_for_breaks_tie_via_name_token_overlap():
    """When two modules share the same most-specific owner_ref (e.g.
    ``cycle_model.pipeline`` listed on both ``uart_lite_tx`` and
    ``uart_lite_rx``), the resolver must use the ref's leaf tokens
    (``RX_IDLE`` / ``TX_DATA``) to pick the side-specific owner."""
    derive = _load_derive()
    modules = [
        {
            "name": "uart_lite_tx",
            "file": "rtl/uart_lite_tx.sv",
            "refs": ["cycle_model", "cycle_model.pipeline"],
        },
        {
            "name": "uart_lite_rx",
            "file": "rtl/uart_lite_rx.sv",
            "refs": ["cycle_model", "cycle_model.pipeline"],
        },
    ]
    rx_pipe = derive._owner_for("cycle_model.pipeline.RX_IDLE", modules, "uart_lite")
    assert rx_pipe["module"] == "uart_lite_rx"
    tx_pipe = derive._owner_for("cycle_model.pipeline.TX_DATA", modules, "uart_lite")
    assert tx_pipe["module"] == "uart_lite_tx"


def test_handshake_rule_owner_defaults_to_top_module():
    derive = _load_derive()
    modules = [
        {
            "name": "counter_reg",
            "file": "rtl/counter_reg.sv",
            "refs": ["cycle_model", "function_model"],
        },
        {
            "name": "counter_top",
            "file": "rtl/counter_top.sv",
            "refs": ["top_module", "io_list", "integration"],
        },
    ]

    owner = derive._owner_for("cycle_model.handshake_rules.req_valid_req_ready", modules, "counter_top")

    assert owner["module"] == "counter_top"
    assert owner["matched_ref"] == "top_level_handshake_rule"


def test_direct_name_owner_match_falls_back_when_refs_missing():
    derive = _load_derive()
    modules = [
        {"name": "ip_rx_fsm", "file": "rtl/ip_rx_fsm.sv"},
        {"name": "ip_tx_fsm", "file": "rtl/ip_tx_fsm.sv"},
        {"name": "ip_top", "file": "rtl/ip_top.sv"},
    ]
    result = derive._direct_name_owner_match("fsm.rx_fsm.states.state_0", modules)
    assert result is not None
    assert result["module"] == "ip_rx_fsm"
    assert result["matched_ref"].startswith("name_token:")


def test_direct_name_owner_match_returns_none_when_ambiguous():
    derive = _load_derive()
    modules = [
        {"name": "rx_fsm_alpha", "file": "rtl/rx_fsm_alpha.sv"},
        {"name": "rx_fsm_beta", "file": "rtl/rx_fsm_beta.sv"},
    ]
    # Two modules contain "rx_fsm" — ambiguous, fallback must abstain.
    assert derive._direct_name_owner_match("fsm.rx_fsm.states.state_0", modules) is None


def test_direct_name_owner_match_ignores_short_tokens():
    derive = _load_derive()
    modules = [
        {"name": "ip_tx_path", "file": "rtl/ip_tx_path.sv"},
        {"name": "ip_rx_path", "file": "rtl/ip_rx_path.sv"},
    ]
    # ``tx`` is 2 chars long — too noisy to act on. The fallback must abstain
    # rather than guess.
    assert derive._direct_name_owner_match("path.tx.stage_0", modules) is None


def test_generic_ssot_prose_does_not_become_static_rtl_terms():
    derive = _load_derive()

    assert (
        derive._evidence_terms(
            "dataflow.source",
            "dataflow.source.source_0",
            "declared io_list request/control interfaces",
        )
        == []
    )
    assert (
        derive._evidence_terms(
            "function_model.output",
            "function_model.transactions.FM1.outputs.output_0",
            "Architectural output matches feature definition",
        )
        == []
    )
    assert (
        derive._evidence_terms(
            "function_model.invariant",
            "function_model.invariants.invariant_3",
            "Data movement and ordering follow the dataflow section without bypassing declared buffers or counters.",
        )
        == []
    )
    assert (
        derive._evidence_terms(
            "function_model.output",
            "function_model.transactions.FM1.outputs.error",
            "Auto-injected placeholder rule for observable state error (repair_ssot_schema rule_expr_completeness pass; TB scoreboard expr)",
        )
        == []
    )
    assert (
        derive._evidence_terms(
            "function_model.state_update",
            "function_model.transactions.FM2.state_updates.fm2_observed",
            {
                "name": "fm2_observed",
                "expr": "1",
                "description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectural state/output equations before signoff.",
            },
        )
        == []
    )
    assert (
        derive._evidence_terms(
            "function_model.output",
            "function_model.transactions.FM2.outputs.output_0",
            {
                "id": "FM2",
                "name": "feature_2",
                "signal": ["Architectural output matches feature definition"],
                "state": ["fm2_observed"],
            },
        )
        == []
    )


def test_function_output_leaf_evidence_does_not_inherit_sibling_terms():
    derive = _load_derive()
    tx = {
        "id": "FM3",
        "name": "increment",
        "outputs": [{"name": "count", "expr": "count"}],
        "output_rules": [{"name": "rsp_data", "port": "rsp_data", "expr": "count"}],
        "state_updates": [{"name": "tc", "expr": "tc"}],
    }

    value = derive._function_leaf_evidence_value(tx, "outputs", {"name": "count", "expr": "count"})
    terms = derive._evidence_terms(
        "function_model.output",
        "function_model.transactions.FM3.outputs.count",
        value,
    )

    assert "count" in terms
    assert "rsp_data" not in terms
    assert "tc" not in terms


def test_function_model_static_evidence_can_fall_back_to_live_dut_scope(tmp_path: Path):
    derive = _load_derive()
    ip_dir = tmp_path / "demo_ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "counter_reg.sv").write_text(
        "module counter_reg(input logic clk, output logic [7:0] count);\n"
        "  always_ff @(posedge clk) count <= count + 1'b1;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (rtl_dir / "tc_comparator.sv").write_text(
        "module tc_comparator(input logic [7:0] count, output logic tc);\n"
        "  assign tc = (count == 8'hff);\n"
        "endmodule\n",
        encoding="utf-8",
    )
    plan = {
        "tasks": [
            {
                "id": "RTL-0001",
                "required": True,
                "category": "function_model.state_variable",
                "source_ref": "function_model.state_variables.tc",
                "owner_file": "rtl/counter_reg.sv",
                "evidence_terms": ["tc"],
                "requires_static_rtl_evidence": True,
            }
        ]
    }

    derive._audit_static_evidence(ip_dir, plan)

    task = plan["tasks"][0]
    assert task["static_evidence"]["status"] == "pass"
    assert task["static_evidence"]["fallback_scope"] == "all_sources_without_owner"
    assert plan["static_rtl_evidence"]["missing"] == 0


def test_function_model_static_evidence_needs_one_live_trace_token():
    derive = _load_derive()

    assert derive._required_static_match_count(
        "function_model.output",
        ["MAX", "tc"],
    ) == 1


def test_workflow_todo_evidence_ignores_synthetic_todo_ids():
    derive = _load_derive()

    terms = derive._evidence_terms(
        "workflow_todo.rtl_gen",
        "workflow_todos.rtl-gen[8]",
        {
            "id": "RTL_FM_TX_FM2",
            "source_refs": ["function_model.transactions.FM2"],
            "owner_module": "counter_reg",
            "owner_file": "rtl/counter_reg.sv",
        },
    )

    assert "FM2" not in terms
    assert "RTL_FM_TX_FM2" not in terms
    assert {"counter_reg", "reg"} <= set(terms)


def test_repair_generated_fm_markers_are_not_authoring_work(tmp_path: Path):
    derive = _load_derive()
    tasks: list[dict[str, Any]] = []
    repair_marker = {
        "name": "fm2_observed",
        "expr": "1",
        "description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectural state/output equations before signoff.",
    }
    owner = {"module": "counter_reg", "file": "rtl/counter_reg.sv", "matched_ref": "function_model"}

    derive._task(
        tasks,
        category="function_model.state_update",
        source_ref="function_model.transactions.FM2.state_updates.fm2_observed",
        title="Implement state update for FM2: fm2_observed",
        detail="Repair-generated marker from SSOT schema repair.",
        criteria=["RTL owner logic is identifiable"],
        owner=owner,
        value=repair_marker,
    )
    derive._task(
        tasks,
        category="function_model.output_rule",
        source_ref="function_model.transactions.FM1.output_rules.count",
        title="Implement output rule for FM1: count",
        detail="Real output rule.",
        criteria=["count is driven"],
        owner=owner,
        value={"name": "count", "expr": "count_q"},
    )
    derive._task(
        tasks,
        category="workflow_todo.rtl_gen",
        source_ref="workflow_todos.rtl-gen[8]",
        title="Implement transaction marker FM2",
        detail="Repair marker workflow TODO from SSOT schema repair.",
        criteria=["Do not create marker-only RTL"],
        owner=owner,
        value={
            "id": "RTL_FM_TX_FM2",
            "content": "Implement state update `fm2_observed` from FunctionalModel expression",
            "detail": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectural state/output equations before signoff.",
            "owner_module": "counter_reg",
            "owner_file": "rtl/counter_reg.sv",
        },
    )

    plan = {"schema_version": 1, "ip": "counter", "top": "counter", "tasks": tasks, "gate": {"status": "fail"}}
    derive._update_todo_completion(plan, tmp_path, audit_rtl=True)

    assert tasks[0]["required"] is False
    assert "repair_generated_fm_marker" in tasks[0]["policy_tags"]
    assert tasks[0]["todo_completion"]["status"] == "pass"
    assert tasks[1]["required"] is True
    assert tasks[2]["required"] is False
    assert tasks[2]["todo_completion"]["status"] == "pass"

    authoring_plan = derive._write_authoring_packets(tmp_path, plan, todo_plan_sha256="unit-test")
    packet_tasks = []
    for packet in authoring_plan["packets"]:
        packet_json = tmp_path / packet["json"]
        packet_tasks.extend(derive._safe_read_json(packet_json)["tasks"])

    assert packet_tasks
    assert all("fm2_observed" not in str(task.get("source_ref", "")) for task in packet_tasks)
    assert all("RTL_FM_TX_FM2" not in str(task.get("workflow_todo", "")) for task in packet_tasks)
    assert any(task.get("source_ref") == "function_model.transactions.FM1.output_rules.count" for task in packet_tasks)


def test_placeholder_audit_accepts_not_implemented_in_comment(tmp_path: Path):
    derive = _load_derive()
    ip_dir = tmp_path / "ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    list_dir = ip_dir / "list"
    list_dir.mkdir()
    sv_file = rtl_dir / "ip_rx.sv"
    sv_file.write_text(
        "module ip_rx (input logic clk, output logic break_detected);\n"
        "    assign break_detected = 1'b0;  // RX break detect: not implemented per SSOT\n"
        "endmodule\n"
    )
    (list_dir / "ip.f").write_text("rtl/ip_rx.sv\n")

    report = derive._audit_rtl_placeholder_free(ip_dir)
    assert report["status"] == "pass", report["issues"]


def test_placeholder_audit_rejects_not_implemented_outside_line_comment(tmp_path: Path):
    """The soft pattern ``not\\s+implemented`` must still fire when the phrase
    appears outside a ``//`` line comment — for example, in a ``$display``
    string. The fix permits the phrase only inside line comments, where it
    legitimately documents an SSOT-driven omission."""
    derive = _load_derive()
    ip_dir = tmp_path / "ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    list_dir = ip_dir / "list"
    list_dir.mkdir()
    sv_file = rtl_dir / "ip_rx.sv"
    sv_file.write_text(
        "module ip_rx (input logic clk);\n"
        '    always @(posedge clk) $display("not implemented");\n'
        "endmodule\n"
    )
    (list_dir / "ip.f").write_text("rtl/ip_rx.sv\n")

    report = derive._audit_rtl_placeholder_free(ip_dir)
    assert report["status"] == "fail"
    assert any("not implemented" in str(issue.get("token", "")).lower() for issue in report["issues"])


def test_placeholder_audit_still_rejects_todo_in_comment(tmp_path: Path):
    derive = _load_derive()
    ip_dir = tmp_path / "ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    list_dir = ip_dir / "list"
    list_dir.mkdir()
    sv_file = rtl_dir / "ip_rx.sv"
    sv_file.write_text(
        "module ip_rx (input logic clk, output logic done);\n"
        "    assign done = 1'b1;  // TODO: connect to real source\n"
        "endmodule\n"
    )
    (list_dir / "ip.f").write_text("rtl/ip_rx.sv\n")

    report = derive._audit_rtl_placeholder_free(ip_dir)
    assert report["status"] == "fail"
    assert any("TODO" in str(issue.get("token", "")) for issue in report["issues"])


def test_locked_behavioral_contract_without_rtl_stage_blocks_rtl_gate(tmp_path: Path):
    derive = _load_derive()
    ip = "contract_demo"
    ip_dir = _write_contract_demo_ssot(tmp_path, ip)
    _write_behavioral_contract(ip_dir, rtl_stage=False)

    plan = derive.derive_plan(tmp_path, ip, audit_rtl=False)

    blocker_ids = {item["id"] for item in plan["blockers"]}
    assert "LOCKED_TRUTH_CONTRACT_NO_RTL_STAGE_BC_READ" in blocker_ids
    contract_tasks = [task for task in plan["tasks"] if task.get("category") == "contract.behavioral.rtl"]
    assert len(contract_tasks) == 1
    assert contract_tasks[0]["contract_ref"] == "BC_READ"
    assert contract_tasks[0]["contract_stage_contracts"] == []


def test_locked_behavioral_contract_closes_with_live_rtl_evidence(tmp_path: Path):
    derive = _load_derive()
    ip = "contract_demo"
    ip_dir = _write_contract_demo_ssot(tmp_path, ip)
    _write_behavioral_contract(ip_dir, rtl_stage=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}_core.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_core.sv").write_text(
        f"""module {ip}_core(
  input logic clk,
  input logic rst_n,
  input logic cmd_valid,
  output logic cmd_ready,
  output logic [31:0] rsp_rdata
);
  logic [31:0] count_q;
  assign cmd_ready = 1'b1;
  assign rsp_rdata = cmd_valid ? count_q : 32'd0;
endmodule
""",
        encoding="utf-8",
    )

    plan = derive.derive_plan(tmp_path, ip, audit_rtl=True)

    contract_tasks = [task for task in plan["tasks"] if task.get("category") == "contract.behavioral.rtl"]
    assert len(contract_tasks) == 1
    task = contract_tasks[0]
    assert task["contract_ref"] == "BC_READ"
    assert task["contract_projection_refs"]
    assert {"cmd_valid", "cmd_ready", "rsp_rdata"} <= set(task["evidence_terms"])
    assert task["static_evidence"]["status"] == "pass"
    contract_evidence = plan["contract_implementation_evidence"]
    assert contract_evidence["status"] == "pass", contract_evidence["issues"]
    contract_gate = next(
        task
        for task in plan["tasks"]
        if (task.get("gate_todo") or {}).get("kind") == "locked_truth_contract_implementation"
    )
    assert contract_gate["todo_completion"]["status"] == "pass"


def test_production_direct_rtl_policy_bypasses_fl_cl_artifact_gates_with_contract_evidence(tmp_path: Path):
    derive = _load_derive()
    ip = "contract_demo"
    ip_dir = _write_contract_demo_ssot(tmp_path, ip)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        ssot_path.read_text(encoding="utf-8")
        + "\nquality_gates:\n"
        + "  rtl_gen:\n"
        + "    profile: production\n"
        + "    direct_rtl_allowed:\n"
        + "      approved: true\n"
        + "      reason: locked contracts gate RTL directly for this run\n",
        encoding="utf-8",
    )
    _write_behavioral_contract(ip_dir, rtl_stage=True)
    (ip_dir / "req" / "design_spec_trace.json").write_text(
        json.dumps({"schema_version": 1, "type": "design_spec_trace_check", "ip": ip, "status": "pass"})
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}_core.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_core.sv").write_text(
        f"""module {ip}_core(
  input logic clk,
  input logic rst_n,
  input logic cmd_valid,
  output logic cmd_ready,
  output logic [31:0] rsp_rdata
);
  logic [31:0] count_q;
  assign cmd_ready = 1'b1;
  assign rsp_rdata = cmd_valid ? count_q : 32'd0;
endmodule
""",
        encoding="utf-8",
    )

    plan = derive.derive_plan(tmp_path, ip, audit_rtl=True)

    assert plan["summary"]["direct_rtl_allowed"] is True
    gate_by_kind = {
        (task.get("gate_todo") or {}).get("kind"): task
        for task in plan["tasks"]
        if task.get("category") == "rtl_gate.rtl_gen"
    }
    for kind in ("golden_authority_artifacts", "cycle_model_artifacts", "fl_rtl_goal_audit"):
        completion = gate_by_kind[kind]["todo_completion"]
        assert completion["status"] == "pass", completion
        assert "Direct RTL contract authority is approved" in completion["reason"]


def test_structural_contracts_are_direct_top_io_gate_inputs(tmp_path: Path):
    derive = _load_derive()
    ip = "contract_demo"
    ip_dir = _write_contract_demo_ssot(tmp_path, ip)
    (ip_dir / "req" / "structural_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "C_STRUCT_IO",
                        "obligations": ["OBL_READ"],
                        "signals": [
                            {"name": "clk", "dir": "input", "width": 1},
                            {"name": "rst_n", "dir": "input", "width": 1},
                            {"name": "cmd_valid", "dir": "input", "width": 1},
                            {"name": "rsp_rdata", "dir": "output", "width": 32},
                        ],
                        "clock_domains": [{"id": "main", "clock_signal": "clk"}],
                        "reset_domains": [{"id": "rst", "reset_signal": "rst_n", "clock_domain": "main"}],
                        "interfaces": [{"id": "ctrl", "signals": ["cmd_valid", "rsp_rdata"], "clock_domain": "main"}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}_top.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_top.sv").write_text(
        f"""module {ip}_top(
  input logic clk,
  input logic rst_n,
  input logic cmd_valid
);
endmodule
""",
        encoding="utf-8",
    )

    plan = derive.derive_plan(tmp_path, ip, audit_rtl=True)

    assert plan["locked_truth_top_io_contracts"]
    issues = plan["top_io_contract_evidence"]["issues"]
    assert any(
        issue.get("source_ref") == "req.structural_contracts.C_STRUCT_IO.signals.rsp_rdata"
        and issue.get("issue") == "SSOT top IO port is missing from RTL top declaration"
        for issue in issues
    )
