# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 4
- Required tasks: 4

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

- Quality profile: standard
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Tool-evidence blockers:
  - common_ai_agent_authoring: RTL audit has not run yet.
  - dut_compile: RTL audit has not run yet.
  - dut_lint: RTL audit has not run yet.
  - dynamic_todo_closure: RTL audit has not run yet.
- Tool-evidence runbook:
  - common_ai_agent_authoring: stages=ssot-rtl; artifact=debounce_cx1/rtl/rtl_authoring_provenance.json
  - dut_compile: stages=ssot-rtl, dut_compile; artifact=debounce_cx1/rtl/rtl_compile.json
  - dut_lint: stages=lint, dut_lint; artifact=debounce_cx1/lint/dut_lint.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=debounce_cx1/rtl/rtl_todo_plan.json
- SSOT top IO contracts: 4

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: planned
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
- Current reason: RTL audit has not run yet.
- Criteria:
  - rtl/rtl_authoring_provenance.json exists
  - provenance agent is common_ai_agent
  - provenance workflow is rtl-gen
  - provenance surface is atlas_ui, textual_ui, or headless_common_engine
  - provenance todo_plan_sha256 matches the current rtl_todo_plan.json
  - provenance rtl_files lists every SSOT manifest RTL file
  - provenance rtl_files covers the current DUT filelist sources
  - Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0018: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: planned
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
- Current reason: RTL audit has not run yet.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0019: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: planned
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
- Current reason: RTL audit has not run yet.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0020: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: planned
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure
