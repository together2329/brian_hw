# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 7
- Required tasks: 7

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_engine.busy <= engine_busy (observed_named_port_map)
  - pl330_target_engine.channel_state <= engine_channel_state (observed_named_port_map)
  - pl330_target_engine.clk <= clk (observed_named_port_map)
  - pl330_target_engine.cmd_channel <= engine_cmd_channel (observed_named_port_map)
  - pl330_target_engine.cmd_dst_addr <= engine_cmd_dst_addr (observed_named_port_map)
  - pl330_target_engine.cmd_len <= engine_cmd_len (observed_named_port_map)
  - pl330_target_engine.cmd_opcode <= engine_cmd_opcode (observed_named_port_map)
  - pl330_target_engine.cmd_privileged <= engine_cmd_privileged (observed_named_port_map)
- Tool-evidence blockers:
  - dynamic_todo_closure: 6 required non-closure TODO(s) remain open.
  - protocol_assertion_evidence: Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.
  - fl_rtl_goal_audit: FL-vs-RTL goal audit is not clean.
  - coverage_closure: Coverage closure report is not pass.
- Tool-evidence runbook:
  - dynamic_todo_closure: stages=audit-rtl; artifact=pl330_target/rtl/rtl_todo_plan.json
  - protocol_assertion_evidence: stages=ssot-protocol-assertions, sim; artifact=pl330_target/verify/protocol_assertions.sva
  - fl_rtl_goal_audit: stages=ssot-fl-model, ssot-equiv-goals, ssot-tb-cocotb, sim, goal-audit; artifact=pl330_target/sim/fl_rtl_goal_audit.json
  - coverage_closure: stages=sim, coverage; artifact=pl330_target/cov/coverage.json
- SSOT top IO contracts: 11

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
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
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: DUT-only lint artifact passed with zero errors, warnings, and suppression violations.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: 6 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure

### RTL-0024: Gate: production RTL has protocol assertion generation and clean simulation evidence

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.protocol_assertion_evidence
- Detail: PL330-level RTL needs protocol-checker style evidence for interface, ordering, valid/ready, reset, and backpressure rules. The assertion source comes from SSOT cycle_model; the pass condition comes from real simulation evidence.
SSOT ref: quality_gates.rtl_gen.protocol_assertion_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.
- Criteria:
  - verify/protocol_assertions.sva exists
  - verify/protocol_assertions.summary.json has assertions_total > 0
  - sim/assertion_failures.jsonl exists after simulation
  - assertion_failures.jsonl is newer than or equal to every listed DUT RTL source
  - assertion_failures.jsonl has zero non-empty failure records
  - Assertion rules trace to SSOT cycle_model/interface contracts
  - Traceability keeps source_ref quality_gates.rtl_gen.protocol_assertion_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.protocol_assertion_evidence

### RTL-0025: Gate: production RTL passes FL-vs-RTL goal audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.fl_rtl_goal_audit
- Detail: Passing compile/lint is not enough. The final RTL must be proven against FunctionalModel-derived equivalence goals using real RTL-observed evidence.
SSOT ref: quality_gates.rtl_gen.fl_rtl_goal_audit.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
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
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.fl_rtl_goal_audit

### RTL-0026: Gate: production RTL closes SSOT functional coverage goals

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.coverage_closure
- Detail: Coverage must be measured from passing RTL-observed scoreboard evidence. Raw FL-only coverage or weakened coverage goals cannot close this gate.
SSOT ref: quality_gates.rtl_gen.coverage_closure.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Coverage closure report is not pass.
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
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.coverage_closure
