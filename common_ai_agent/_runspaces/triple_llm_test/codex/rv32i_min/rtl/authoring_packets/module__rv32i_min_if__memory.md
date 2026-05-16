# RTL Authoring Packet: module__rv32i_min_if__memory

- Kind: module
- Owner module: rv32i_min_if
- Owner file: rtl/rv32i_min_if.sv
- Task count: 1
- Required tasks: 1

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, function_model, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, io_list, io_list.interfaces.instr_bus
- Module slice: 4/6 section=memory task_limit=48
- Slice rule: Owner module rv32i_min_if is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])

## Tasks

### RTL-0140: Implement memory item if_id_reg

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.if_id_reg
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.if_id_reg.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via semantic_terms:if.
SSOT item context: name=if_id_reg; width=64; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.if_id_reg
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - if_id_reg width matches SSOT value 64
  - if_id_reg timing uses SSOT cycle/latency 0
  - if_id_reg storage depth matches SSOT value 1
- SSOT refs: memory.instances.if_id_reg
