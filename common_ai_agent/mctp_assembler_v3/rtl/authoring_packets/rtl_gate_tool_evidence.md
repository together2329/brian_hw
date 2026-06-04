# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 7
- Required tasks: 7

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, function_model, function_model.transactions, integration, integration.connections, io_list, io_list.interfaces, top_module
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])
  - mctp_assembler_v3_cdc_sync.evt_fatal_internal_error_a <= 1'b0 (integration.connections[7])
- SSOT top IO contracts: 51

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: RTL authoring provenance proves common_ai_agent rtl-gen ownership.
- Criteria:
  - rtl/rtl_authoring_provenance.json exists
  - provenance agent is common_ai_agent
  - provenance workflow is rtl-gen
  - provenance surface is atlas_ui, textual_ui, or headless_common_engine
  - provenance todo_plan_sha256 matches the current rtl_todo_plan.json
  - provenance rtl_files lists every SSOT manifest RTL file
  - provenance rtl_files covers the current DUT filelist sources
  - Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: DUT-only lint artifact passed with zero errors, warnings, and suppression violations.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: Every required non-closure TODO has pass status.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure

### RTL-0024: Gate: production RTL has protocol assertion generation and clean simulation evidence

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.protocol_assertion_evidence
- Detail: PL330-level RTL needs protocol-checker style evidence for interface, ordering, valid/ready, reset, and backpressure rules. The assertion source comes from SSOT cycle_model; the pass condition comes from real simulation evidence.
SSOT ref: quality_gates.rtl_gen.protocol_assertion_evidence.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: Protocol assertions were generated and simulation reported zero assertion failures.
- Criteria:
  - verify/protocol_assertions.sva exists
  - verify/protocol_assertions.summary.json has assertions_total > 0
  - sim/assertion_failures.jsonl exists after simulation
  - assertion_failures.jsonl is newer than or equal to every listed DUT RTL source
  - assertion_failures.jsonl has zero non-empty failure records
  - Assertion rules trace to SSOT cycle_model/interface contracts
  - Traceability keeps source_ref quality_gates.rtl_gen.protocol_assertion_evidence
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.protocol_assertion_evidence

### RTL-0025: Gate: production RTL passes FL-vs-RTL goal audit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.fl_rtl_goal_audit
- Detail: Passing compile/lint is not enough. The final RTL must be proven against FunctionalModel-derived equivalence goals using real RTL-observed evidence.
SSOT ref: quality_gates.rtl_gen.fl_rtl_goal_audit.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: FL-vs-RTL goal audit passed and compare covers every required unblocked equivalence goal.
- Criteria:
  - sim/fl_rtl_goal_audit.json exists
  - fl_rtl_goal_audit.json is newer than or equal to every listed DUT RTL source
  - fl_rtl_goal_audit status is pass
  - failed_checks is zero
  - blockers list is empty
  - sim/fl_rtl_compare.json exists and is newer than or equal to every listed DUT RTL source
  - Every required unblocked verify/equivalence_goals.json goal is checked and passed by fl_rtl_compare
  - Traceability keeps source_ref quality_gates.rtl_gen.fl_rtl_goal_audit
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.fl_rtl_goal_audit

### RTL-0026: Gate: production RTL closes SSOT functional coverage goals

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.coverage_closure
- Detail: Coverage must be measured from passing RTL-observed scoreboard evidence. Raw FL-only coverage or weakened coverage goals cannot close this gate.
SSOT ref: quality_gates.rtl_gen.coverage_closure.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_module.
- Current reason: SSOT functional coverage closure passed with RTL-observed evidence.
- Criteria:
  - cov/coverage.json exists
  - coverage.json is newer than or equal to every listed DUT RTL source
  - coverage status is pass
  - functional coverage pct meets target
  - coverage.json source is ssot_coverage_summary
  - functional hit equals total with pct >= 100 for planned bins
  - rtl_observed.status is pass with passing scoreboard events and coverage refs
  - rtl_observed missing_bins and invalid_rows are empty
  - coverage limitations are empty or explicitly waived in SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.coverage_closure
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.coverage_closure
