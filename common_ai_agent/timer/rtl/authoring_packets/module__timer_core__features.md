# RTL Authoring Packet: module__timer_core__features

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
- Module slice: 9/17 section=features task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0079: Implement feature parameterized_countdown

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.parameterized_countdown
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.parameterized_countdown.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=parameterized_countdown.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.parameterized_countdown
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: features.parameterized_countdown

### RTL-0080: Implement feature done_pulse

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.done_pulse
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.done_pulse.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=done_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.done_pulse
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: features.done_pulse

### RTL-0081: Implement feature clear_priority

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.clear_priority
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.clear_priority.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=clear_priority.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.clear_priority
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: features.clear_priority
