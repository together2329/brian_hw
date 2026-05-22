# RTL Authoring Packet: module__model_compare_counter_core__memory

- Kind: module
- Owner module: model_compare_counter_core
- Owner file: rtl/model_compare_counter_core.sv
- Task count: 3
- Required tasks: 3

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE, io_list
- Module slice: 6/10 section=memory task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0120: Implement memory item count_state_ff

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.count_state_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.count_state_ff.
SSOT item context: name=count_state_ff; width=8; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.count_state_ff
  - count_state_ff width matches SSOT value 8
  - count_state_ff timing uses SSOT cycle/latency 0
  - count_state_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.count_state_ff

### RTL-0121: Implement memory item wrapped_state_ff

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.wrapped_state_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.wrapped_state_ff.
SSOT item context: name=wrapped_state_ff; width=1; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.wrapped_state_ff
  - wrapped_state_ff width matches SSOT value 1
  - wrapped_state_ff timing uses SSOT cycle/latency 0
  - wrapped_state_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.wrapped_state_ff

### RTL-0122: Implement memory item valid_state_ff

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.valid_state_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.valid_state_ff.
SSOT item context: name=valid_state_ff; width=1; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.valid_state_ff
  - valid_state_ff width matches SSOT value 1
  - valid_state_ff timing uses SSOT cycle/latency 0
  - valid_state_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.valid_state_ff
