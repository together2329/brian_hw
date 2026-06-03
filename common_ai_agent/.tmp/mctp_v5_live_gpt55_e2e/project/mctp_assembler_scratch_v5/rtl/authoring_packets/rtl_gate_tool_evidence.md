# RTL Authoring Packet: rtl_gate_tool_evidence

- Kind: gate
- Owner module: mctp_assembler_scratch_v5
- Owner file: rtl/mctp_assembler_scratch_v5.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])
  - mctp_assembler_scratch_v5_sram_packer.sram_wr_valid <= pack_wr_valid (integration.connections[2])
  - mctp_assembler_scratch_v5_axi_read_egress.m_axi_rvalid <= m_axi_rvalid (integration.connections[3])
  - mctp_assembler_scratch_v5_apb_regfile.pready <= pready (integration.connections[4])
- SSOT top IO contracts: 55

## Tasks

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
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
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0017: Gate: DUT-only RTL compile report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_compile
- Detail: Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.
SSOT ref: quality_gates.rtl_gen.dut_compile.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
- Current reason: DUT-only compile artifact passed with zero errors, diagnostics, and style violations.
- Criteria:
  - rtl/rtl_compile.json exists
  - rtl_compile.json reports dut_only=true
  - rtl_compile.json passed=true with zero errors, diagnostics, and style violations
  - rtl_compile.json is newer than or equal to every listed DUT RTL source
  - rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_compile
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_compile

### RTL-0018: Gate: DUT-only lint report passes after the final RTL edit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dut_lint
- Detail: Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.
SSOT ref: quality_gates.rtl_gen.dut_lint.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
- Current reason: DUT-only lint artifact passed with zero errors, warnings, and suppression violations.
- Criteria:
  - lint/dut_lint.json exists
  - dut_lint.json reports dut_only=true
  - dut_lint.json passed=true with zero errors and zero warnings
  - dut_lint.json is newer than or equal to every listed DUT RTL source
  - dut_lint.json rtl_files covers the current DUT filelist RTL/header sources
  - No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.dut_lint
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dut_lint

### RTL-0019: Gate: every required rtl_todo_plan item is closed before rtl-gen PASS

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.dynamic_todo_closure
- Detail: rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.
SSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
- Current reason: Every required non-closure TODO has pass status.
- Criteria:
  - Every required non-closure task has todo_completion.status=pass
  - open_required_todos is zero
  - all_required_todos_pass is true
  - Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.dynamic_todo_closure
