# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: rv32i_min
- Owner file: rtl/rv32i_min.sv
- Task count: 4
- Required tasks: 4

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
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
- Owner refs: integration, integration.connections, io_list
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- Tool-evidence blockers:
  - dut_compile: DUT compile artifact is not clean.
  - dut_lint: DUT lint artifact is not clean.
  - dynamic_todo_closure: 9 required non-closure TODO(s) remain open.
- Tool-evidence runbook:
  - dut_compile: stages=ssot-rtl, dut_compile; artifact=rv32i_min/rtl/rtl_compile.json
  - dut_lint: stages=lint, dut_lint; artifact=rv32i_min/lint/dut_lint.json
  - dynamic_todo_closure: stages=audit-rtl; artifact=rv32i_min/rtl/rtl_todo_plan.json
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])
  - rv32i_min_memwb.d_addr <= d_addr (integration.connections[3])
  - rv32i_min_memwb.d_wdata <= d_wdata (integration.connections[4])
  - rv32i_min_memwb.d_rdata <= d_rdata (integration.connections[5])
  - rv32i_min_memwb.d_we <= d_we (integration.connections[6])
  - rv32i_min_memwb.d_be <= d_be (integration.connections[7])
  - rv32i_min_memwb.d_valid <= d_valid (integration.connections[8])
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])
- SSOT top IO contracts: 24

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
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
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: DUT compile artifact is not clean.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: DUT lint artifact is not clean.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 9 required non-closure TODO(s) remain open.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure
