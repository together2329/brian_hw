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
