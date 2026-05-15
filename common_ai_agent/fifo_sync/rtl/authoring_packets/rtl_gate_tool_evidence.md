# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: fifo_sync
- Owner file: rtl/fifo_sync.sv
- Task count: 7
- Required tasks: 7

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Tool-evidence blockers:
  - common_ai_agent_authoring: Missing common_ai_agent RTL authoring provenance.
  - dynamic_todo_closure: 37 required non-closure TODO(s) remain open.
  - protocol_assertion_evidence: Missing protocol assertion artifact: verify/protocol_assertions.sva.
  - fl_rtl_goal_audit: FL-vs-RTL goal audit is not clean.
  - coverage_closure: Missing coverage closure artifact: cov/coverage.json.
- Tool-evidence runbook:
  - common_ai_agent_authoring: stages=ssot-rtl; artifact=fifo_sync/rtl/rtl_authoring_provenance.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=fifo_sync/rtl/rtl_todo_plan.json
  - protocol_assertion_evidence: stages=ssot-protocol-assertions, sim; artifact=fifo_sync/verify/protocol_assertions.sva
  - fl_rtl_goal_audit: stages=ssot-fl-model, ssot-equiv-goals, ssot-tb-cocotb, sim, goal-audit; artifact=fifo_sync/sim/fl_rtl_goal_audit.json
  - coverage_closure: stages=sim, coverage; artifact=fifo_sync/cov/coverage.json
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
- SSOT top IO contracts: 20

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: Missing common_ai_agent RTL authoring provenance.
- Criteria:
  - rtl/rtl_authoring_provenance.json exists
  - provenance agent is common_ai_agent
  - provenance workflow is rtl-gen
  - provenance surface is atlas_ui, textual_ui, or headless_common_engine
  - provenance todo_plan_sha256 matches the current rtl_todo_plan.json
  - provenance rtl_files lists every SSOT manifest RTL file
  - provenance rtl_files covers the current DUT filelist sources
  - Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: DUT-only lint artifact passed with zero errors, warnings, and suppression violations.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: 37 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure

### RTL-0024: Gate: production RTL has protocol assertion generation and clean simulation evidence

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.protocol_assertion_evidence
- Detail: PL330-level RTL needs protocol-checker style evidence for interface, ordering, valid/ready, reset, and backpressure rules. The assertion source comes from SSOT cycle_model; the pass condition comes from real simulation evidence.
SSOT ref: quality_gates.rtl_gen.protocol_assertion_evidence.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: Missing protocol assertion artifact: verify/protocol_assertions.sva.
- Criteria:
  - verify/protocol_assertions.sva exists
  - verify/protocol_assertions.summary.json has assertions_total > 0
  - sim/assertion_failures.jsonl exists after simulation
  - assertion_failures.jsonl is newer than or equal to every listed DUT RTL source
  - assertion_failures.jsonl has zero non-empty failure records
  - Assertion rules trace to SSOT cycle_model/interface contracts
  - Traceability keeps source_ref quality_gates.rtl_gen.protocol_assertion_evidence
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.protocol_assertion_evidence

### RTL-0025: Gate: production RTL passes FL-vs-RTL goal audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.fl_rtl_goal_audit
- Detail: Passing compile/lint is not enough. The final RTL must be proven against FunctionalModel-derived equivalence goals using real RTL-observed evidence.
SSOT ref: quality_gates.rtl_gen.fl_rtl_goal_audit.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: FL-vs-RTL goal audit is not clean.
- Criteria:
  - sim/fl_rtl_goal_audit.json exists
  - fl_rtl_goal_audit.json is newer than or equal to every listed DUT RTL source
  - fl_rtl_goal_audit status is pass
  - failed_checks is zero
  - blockers list is empty
  - sim/fl_rtl_compare.json exists and is newer than or equal to every listed DUT RTL source
  - Every required unblocked verify/equivalence_goals.json goal is checked and passed by fl_rtl_compare
  - Traceability keeps source_ref quality_gates.rtl_gen.fl_rtl_goal_audit
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.fl_rtl_goal_audit

### RTL-0026: Gate: production RTL closes SSOT functional coverage goals

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.coverage_closure
- Detail: Coverage must be measured from passing RTL-observed scoreboard evidence. Raw FL-only coverage or weakened coverage goals cannot close this gate.
SSOT ref: quality_gates.rtl_gen.coverage_closure.
Owner: fifo_sync in rtl/fifo_sync.sv via top_module.
- Current reason: Missing coverage closure artifact: cov/coverage.json.
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
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.coverage_closure
