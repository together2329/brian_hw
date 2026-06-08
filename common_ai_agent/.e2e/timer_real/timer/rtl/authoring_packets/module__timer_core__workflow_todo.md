# RTL Authoring Packet: module__timer_core__workflow_todo

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, dataflow.count_path, dataflow.irq_path, decomposition, features, fsm, function_model, function_model.state_variables, function_model.state_variables.count_q, function_model.state_variables.enable_q, function_model.state_variables.load_q, function_model.transactions.FM_DISABLED_HOLD
- Module slice: 8/8 section=workflow_todo task_limit=48
- Slice rule: Owner module timer_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_core.pclk <= pclk (integration.connections[13])
  - timer_core.presetn <= presetn (integration.connections[14])
  - timer_core.load_q <= load_q (integration.connections[15])
  - timer_core.enable_q <= enable_q (integration.connections[16])
  - timer_core.count_q <= count_q (integration.connections[17])
  - timer_core.irq <= irq (integration.connections[18])

## Tasks

### RTL-0022: Implement enable-controlled decrement, reload, hold, and irq pulse logic.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: In timer_core, while enable_q is 1 decrement count_q each pclk cycle when count_q>0; when enable_q is 1 and count_q==0 assert irq for one cycle and reload count_q from load_q; when enable_q is 0 hold count_q and keep irq low.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: timer_core in rtl/timer_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_COUNTER_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Enabled nonzero count decrements by one per cycle.
  - Enabled zero count reloads from LOAD and pulses irq high for one cycle.
  - Disabled state holds count_q and keeps irq low.
  - FL-vs-RTL scoreboard comparisons pass for counter and irq scenarios.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/timer_core.sv
  - Semantic source_refs covered: cycle_model.pipeline.TICK_DECREMENT, cycle_model.pipeline.TICK_RELOAD_IRQ, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, interrupts.sources.TIMER_ZERO
- SSOT refs: cycle_model.pipeline.TICK_DECREMENT, cycle_model.pipeline.TICK_RELOAD_IRQ, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, interrupts.sources.TIMER_ZERO, workflow_todos.rtl-gen[2]
