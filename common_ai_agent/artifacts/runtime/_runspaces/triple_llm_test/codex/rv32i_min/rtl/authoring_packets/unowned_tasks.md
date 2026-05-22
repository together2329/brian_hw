# RTL Authoring Packet: unowned_tasks

- Kind: unowned
- Owner module: <none>
- Owner file: <none>
- Task count: 2
- Required tasks: 2

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
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
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

## Tasks

### RTL-0141: Implement memory item id_ex_reg

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.id_ex_reg
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.id_ex_reg.
SSOT item context: name=id_ex_reg; width=192; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.id_ex_reg
  - id_ex_reg width matches SSOT value 192
  - id_ex_reg timing uses SSOT cycle/latency 0
  - id_ex_reg storage depth matches SSOT value 1
- SSOT refs: memory.instances.id_ex_reg

### RTL-0142: Implement memory item ex_mem_wb_reg

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.ex_mem_wb_reg
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.ex_mem_wb_reg.
SSOT item context: name=ex_mem_wb_reg; width=160; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.ex_mem_wb_reg
  - ex_mem_wb_reg width matches SSOT value 160
  - ex_mem_wb_reg timing uses SSOT cycle/latency 0
  - ex_mem_wb_reg storage depth matches SSOT value 1
- SSOT refs: memory.instances.ex_mem_wb_reg
