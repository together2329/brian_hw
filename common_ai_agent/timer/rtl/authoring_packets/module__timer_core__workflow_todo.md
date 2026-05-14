# RTL Authoring Packet: module__timer_core__workflow_todo

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 16/17 section=workflow_todo task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0020: Implement timer control priority from the SSOT.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: clear must override countdown progress, start must load load_value, enable must decrement only while running, and done must pulse on the terminal tick.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: timer_core in rtl/timer.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_CONTROL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - clear returns count, running, and done to zero.
  - start loads load_value through the COUNT_WIDTH parameterized datapath.
  - enable decrements count only while running is true.
  - done pulses on count==1 with enable and running asserted.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/timer.sv
  - Semantic source_refs covered: cycle_model.handshake_rules.enabled_tick, fsm.control.transitions, function_model.transactions.FM_TICK
- SSOT refs: cycle_model.handshake_rules.enabled_tick, fsm.control.transitions, function_model.transactions.FM_TICK, workflow_todos.rtl-gen[0]

### RTL-0021: Preserve waveform-observable timer state.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Expose count, running, and done exactly as declared in debug_observability so sim_debug can correlate source, hierarchy, waveform, and scoreboard events.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: timer_core in rtl/timer.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_OBSERVABILITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - count is driven from the timer state register.
  - running is driven from the timer state register.
  - done is a visible pulse output.
  - waveform probes include every debug_observability.waveform_must_probe signal.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/timer.sv
  - Semantic source_refs covered: debug_observability.waveform_must_probe, io_list.interfaces.timer_ctrl, test_requirements.scenarios.SC_COUNTDOWN_DONE
- SSOT refs: debug_observability.waveform_must_probe, io_list.interfaces.timer_ctrl, test_requirements.scenarios.SC_COUNTDOWN_DONE, workflow_todos.rtl-gen[1]

### RTL-0022: Keep timer input and output widths user-editable.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Use COUNT_WIDTH for load_value and count so the timer can be resized by changing the SSOT parameter.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: timer_core in rtl/timer.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_PARAMETERIZATION.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - COUNT_WIDTH parameter controls load_value width.
  - COUNT_WIDTH parameter controls count width.
  - No hard-coded count datapath width is used outside the parameter declaration.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/timer.sv
  - Semantic source_refs covered: coding_rules.port_declaration_default, io_list.interfaces.timer_ctrl.ports.load_value, parameters.COUNT_WIDTH
- SSOT refs: coding_rules.port_declaration_default, io_list.interfaces.timer_ctrl.ports.load_value, parameters.COUNT_WIDTH, workflow_todos.rtl-gen[2]
