# RTL Authoring Packet: module__pulse_gen_core__workflow_todo

- Kind: module
- Owner module: pulse_gen_core
- Owner file: rtl/pulse_gen_core.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, decomposition.units.pulse_generation, features, features.pulse_fire, fsm, fsm.pulse_fsm, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_FIRE
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module pulse_gen_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_core.status_busy_i <= pulse_gen_regs.status_busy (integration.connections[14])
  - pulse_gen_core.status_done_o <= pulse_gen_regs.status_done (integration.connections[15])

## Tasks

### RTL-0020: Implement pulse_gen_core FSM, counter, and output driver

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model FM_FIRE transaction, cycle_model pipeline, and fsm.pulse_fsm into RTL state machine with pulse counter, latched width/polarity capture, and pulse_out driver. ctrl_fire auto-clears after 1 cycle. irq_o = status_done & int_enable combinational.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_PULSE_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - FSM has exactly 3 states: IDLE, PULSE, DONE with transitions matching fsm.pulse_fsm
  - pulse_out asserts for exactly latched_width cycles (1-cycle latency from trigger)
  - STATUS.busy mirrors PULSE state
  - STATUS.done set at PULSE→DONE transition, cleared by W1C
  - fired_count increments at PULSE→DONE, wraps at 2^16
  - ctrl_fire self-clears after 1 PCLK cycle
  - Non-reentrant: triggers ignored while busy
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm.pulse_fsm, function_model.transactions.FM_FIRE
- SSOT refs: cycle_model.pipeline, fsm.pulse_fsm, function_model.transactions.FM_FIRE, workflow_todos.rtl-gen[0]
