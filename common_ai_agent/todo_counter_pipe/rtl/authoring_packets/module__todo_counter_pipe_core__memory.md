# RTL Authoring Packet: module__todo_counter_pipe_core__memory

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 5/8 section=memory task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0217: Implement memory item cnt_reg

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.cnt_reg
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.cnt_reg.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via memory.
SSOT item context: name=cnt_reg; width=WIDTH; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.cnt_reg
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cnt_reg width matches SSOT value WIDTH
  - cnt_reg timing uses SSOT cycle/latency 0
  - cnt_reg storage depth matches SSOT value 1
- SSOT refs: memory.instances.cnt_reg

### RTL-0218: Implement memory item dbg_cycle_reg

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.dbg_cycle_reg
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.dbg_cycle_reg.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via memory.
SSOT item context: name=dbg_cycle_reg; width=WIDTH; depth=1; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.dbg_cycle_reg
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - dbg_cycle_reg width matches SSOT value WIDTH
  - dbg_cycle_reg timing uses SSOT cycle/latency 0
  - dbg_cycle_reg storage depth matches SSOT value 1
- SSOT refs: memory.instances.dbg_cycle_reg
