# RTL Authoring Packet: module__mctp_assembler_scratch_axi_write_ingress__workflow_todo

- Kind: module
- Owner module: mctp_assembler_scratch_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_axi_write_ingress.sv
- Task count: 1
- Required tasks: 1

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
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 6/7 section=workflow_todo task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_axi_write_ingress is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0020: Implement AXI write ingress and no-ID one-outstanding write behavior.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: AW/W/B channels must follow io_list and cycle_model handshake rules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.handshake_rules.axi_write_channels.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_compile_passes
  - lint_passes
  - axi_write_module_present
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Semantic source_refs covered: cycle_model.handshake_rules.axi_write_channels, io_list.interfaces.axi_write_slave
- SSOT refs: cycle_model.handshake_rules.axi_write_channels, io_list.interfaces.axi_write_slave, workflow_todos.rtl-gen[0]
