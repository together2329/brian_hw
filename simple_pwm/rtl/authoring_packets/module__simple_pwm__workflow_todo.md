# RTL Authoring Packet: module__simple_pwm__workflow_todo

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
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
- Owner refs: top_module, function_model, cycle_model
- Module slice: 14/14 section=workflow_todo task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0020: Implement PWM counter with period rollover

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Implement a free-running counter that increments each clock cycle when enable=1 and wraps to 0 when it reaches the period input value. When enable=0, counter stays at 0.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: simple_pwm in rtl/simple_pwm.sv via workflow_todos.owner.
SSOT item context: id=RTL_001.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Counter increments when enable=1
  - Counter wraps to 0 when counter+1 == period
  - Counter stays at 0 when enable=0
  - Counter width is COUNTER_WIDTH parameter
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Semantic source_refs covered: function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3
- SSOT refs: function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3, workflow_todos.rtl-gen[0]

### RTL-0021: Implement duty-cycle comparison and pwm_out output

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Compare counter value with duty_cycle input each clock cycle. Drive pwm_out=1 when counter < duty_cycle, pwm_out=0 when counter >= duty_cycle. When enable=0, force pwm_out=0.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: simple_pwm in rtl/simple_pwm.sv via workflow_todos.owner.
SSOT item context: id=RTL_002.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - pwm_out=1 when enable=1 and counter < duty_cycle
  - pwm_out=0 when enable=1 and counter >= duty_cycle
  - pwm_out=0 when enable=0
  - Comparison is combinational (same-cycle)
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Semantic source_refs covered: function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3
- SSOT refs: function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3, workflow_todos.rtl-gen[1]
