# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: arm_m0_min
- Owner file: rtl/arm_m0_min.sv
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
  - dut_compile: Missing canonical DUT compile artifact: rtl/rtl_compile.json.
  - dut_lint: Missing canonical DUT lint artifact: lint/dut_lint.json.
  - dynamic_todo_closure: 71 required non-closure TODO(s) remain open.
  - protocol_assertion_evidence: Missing protocol assertion artifact: verify/protocol_assertions.sva.
  - fl_rtl_goal_audit: Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.
  - coverage_closure: Missing coverage closure artifact: cov/coverage.json.
- Tool-evidence runbook:
  - common_ai_agent_authoring: stages=ssot-rtl; artifact=arm_m0_min/rtl/rtl_authoring_provenance.json
  - dut_compile: stages=ssot-rtl, dut_compile; artifact=arm_m0_min/rtl/rtl_compile.json
  - dut_lint: stages=lint, dut_lint; artifact=arm_m0_min/lint/dut_lint.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=arm_m0_min/rtl/rtl_todo_plan.json
  - protocol_assertion_evidence: stages=ssot-protocol-assertions, sim; artifact=arm_m0_min/verify/protocol_assertions.sva
  - fl_rtl_goal_audit: stages=ssot-fl-model, ssot-equiv-goals, ssot-tb-cocotb, sim, goal-audit; artifact=arm_m0_min/sim/fl_rtl_goal_audit.json
  - coverage_closure: stages=sim, coverage; artifact=arm_m0_min/cov/coverage.json
- SSOT connection contracts:
  - arm_m0_min_if.i_haddr <= i_haddr (integration.connections[0])
  - arm_m0_min_if.i_htrans <= i_htrans (integration.connections[1])
  - arm_m0_min_if.i_hready <= i_hready (integration.connections[2])
  - arm_m0_min_if.i_hrdata <= i_hrdata (integration.connections[3])
  - arm_m0_min_if.i_hresp <= i_hresp (integration.connections[4])
  - arm_m0_min_ex.d_haddr <= d_haddr (integration.connections[5])
  - arm_m0_min_ex.d_htrans <= d_htrans (integration.connections[6])
  - arm_m0_min_ex.d_hwrite <= d_hwrite (integration.connections[7])
  - arm_m0_min_ex.d_hwdata <= d_hwdata (integration.connections[8])
  - arm_m0_min_ex.d_hready <= d_hready (integration.connections[9])
  - arm_m0_min_ex.d_hrdata <= d_hrdata (integration.connections[10])
  - arm_m0_min_ex.d_hresp <= d_hresp (integration.connections[11])
- SSOT top IO contracts: 23

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
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
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
- Current reason: Missing canonical DUT compile artifact: rtl/rtl_compile.json.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
- Current reason: Missing canonical DUT lint artifact: lint/dut_lint.json.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
- Current reason: 71 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure

### RTL-0024: Gate: production RTL has protocol assertion generation and clean simulation evidence

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.protocol_assertion_evidence
- Detail: PL330-level RTL needs protocol-checker style evidence for interface, ordering, valid/ready, reset, and backpressure rules. The assertion source comes from SSOT cycle_model; the pass condition comes from real simulation evidence.
SSOT ref: quality_gates.rtl_gen.protocol_assertion_evidence.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
- Current reason: Missing protocol assertion artifact: verify/protocol_assertions.sva.
- Criteria:
  - verify/protocol_assertions.sva exists
  - verify/protocol_assertions.summary.json has assertions_total > 0
  - sim/assertion_failures.jsonl exists after simulation
  - assertion_failures.jsonl is newer than or equal to every listed DUT RTL source
  - assertion_failures.jsonl has zero non-empty failure records
  - Assertion rules trace to SSOT cycle_model/interface contracts
  - Traceability keeps source_ref quality_gates.rtl_gen.protocol_assertion_evidence
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.protocol_assertion_evidence

### RTL-0025: Gate: production RTL passes FL-vs-RTL goal audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.fl_rtl_goal_audit
- Detail: Passing compile/lint is not enough. The final RTL must be proven against FunctionalModel-derived equivalence goals using real RTL-observed evidence.
SSOT ref: quality_gates.rtl_gen.fl_rtl_goal_audit.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
- Current reason: Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.
- Criteria:
  - sim/fl_rtl_goal_audit.json exists
  - fl_rtl_goal_audit.json is newer than or equal to every listed DUT RTL source
  - fl_rtl_goal_audit status is pass
  - failed_checks is zero
  - blockers list is empty
  - sim/fl_rtl_compare.json exists and is newer than or equal to every listed DUT RTL source
  - Every required unblocked verify/equivalence_goals.json goal is checked and passed by fl_rtl_compare
  - Traceability keeps source_ref quality_gates.rtl_gen.fl_rtl_goal_audit
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.fl_rtl_goal_audit

### RTL-0026: Gate: production RTL closes SSOT functional coverage goals

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.coverage_closure
- Detail: Coverage must be measured from passing RTL-observed scoreboard evidence. Raw FL-only coverage or weakened coverage goals cannot close this gate.
SSOT ref: quality_gates.rtl_gen.coverage_closure.
Owner: arm_m0_min in rtl/arm_m0_min.sv via top_module.
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
  - Primary implementation evidence is in rtl/arm_m0_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.coverage_closure
