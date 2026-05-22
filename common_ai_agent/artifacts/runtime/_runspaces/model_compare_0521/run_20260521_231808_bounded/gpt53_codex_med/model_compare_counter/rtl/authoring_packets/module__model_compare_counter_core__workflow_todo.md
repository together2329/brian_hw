# RTL Authoring Packet: module__model_compare_counter_core__workflow_todo

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
- Module slice: 10/10 section=workflow_todo task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0020: Implement clear-priority sequential next-state logic.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: In rtl/model_compare_counter_core.sv code reset, clear, enable, idle branches with clear overriding enable in same sampled cycle.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_PRIORITY_SEQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - If clear=1 and enable=1 at edge, resulting count/wrapped/valid are zero
  - Branch order and behavior match FM_CLEAR/FM_UPDATE/FM_IDLE
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - Semantic source_refs covered: cycle_model.ordering, function_model.transactions.FM_CLEAR, function_model.transactions.FM_UPDATE
- SSOT refs: cycle_model.ordering, function_model.transactions.FM_CLEAR, function_model.transactions.FM_UPDATE, workflow_todos.rtl-gen[0]

### RTL-0021: Generate wrapped pulse from overflow carry-out only on enabled updates.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Compute 9-bit sum for count+step and drive wrapped for one cycle when carry-out is set, while idle/clear force wrapped low.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_OVERFLOW_PULSE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - wrapped asserted exactly on overflowing FM_UPDATE cycles
  - wrapped deasserted on clear and idle cycles
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.invariants, function_model.transactions.FM_UPDATE
- SSOT refs: cycle_model.pipeline, function_model.invariants, function_model.transactions.FM_UPDATE, workflow_todos.rtl-gen[1]

### RTL-0022: Implement valid one-cycle pulse for accepted enabled updates.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Drive valid high only in enable && !clear branch and low otherwise, including reset and clear cycles.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_VALID_PULSE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - valid=1 for each accepted update cycle
  - valid=0 during reset, clear, and idle cycles
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - Semantic source_refs covered: function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE
- SSOT refs: function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE, workflow_todos.rtl-gen[2]
