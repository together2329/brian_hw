# RTL Authoring Packet: module__todo_counter_pipe_core__workflow_todo

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
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
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 9/9 section=workflow_todo task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0020: Implement counter core datapath and FSM

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model transactions FM1-FM9 into core_clk-domain RTL: event edge detection, clear/load priority, up/down arithmetic, saturate/wrap limit logic, terminal count detection, overflow/underflow sticky flags, and dbg_cycle_count free-running counter.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE_COUNTER.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Core FSM implements IDLE/COUNT states with legal transitions
  - cnt register updates match function_model state_variables per transaction
  - Saturate mode clamps cnt at limits; wrap mode wraps
  - Clear(→0) and load(→load_value) take priority over normal count
  - overflow/underflow sticky flags behave per error_handling
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - Semantic source_refs covered: cycle_model.pipeline.S2_COUNT_EVAL, fsm.core_fsm, function_model.transactions
- SSOT refs: cycle_model.pipeline.S2_COUNT_EVAL, fsm.core_fsm, function_model.transactions, workflow_todos.rtl-gen[0]
