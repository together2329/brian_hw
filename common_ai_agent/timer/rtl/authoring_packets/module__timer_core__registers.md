# RTL Authoring Packet: module__timer_core__registers

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
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 8/17 section=registers task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0068: Implement architectural state count_q

- Priority: high
- Required: True
- Status: pass
- Category: registers.architectural_state
- Source ref: registers.architectural_state.count_q
- Detail: Architectural state listed outside the register map still needs RTL storage and reset/update ownership.
SSOT ref: registers.architectural_state.count_q.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=count_q; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State storage is present in RTL
  - Reset/update behavior matches SSOT
  - State is observable if required by registers/debug/coverage
  - Traceability keeps source_ref registers.architectural_state.count_q
  - Primary implementation evidence is in rtl/timer.sv
  - count_q reset behavior matches SSOT value 0
- SSOT refs: registers.architectural_state.count_q

### RTL-0069: Implement architectural state running_q

- Priority: high
- Required: True
- Status: pass
- Category: registers.architectural_state
- Source ref: registers.architectural_state.running_q
- Detail: Architectural state listed outside the register map still needs RTL storage and reset/update ownership.
SSOT ref: registers.architectural_state.running_q.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=running_q; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State storage is present in RTL
  - Reset/update behavior matches SSOT
  - State is observable if required by registers/debug/coverage
  - Traceability keeps source_ref registers.architectural_state.running_q
  - Primary implementation evidence is in rtl/timer.sv
  - running_q reset behavior matches SSOT value 0
- SSOT refs: registers.architectural_state.running_q

### RTL-0070: Implement architectural state done_q

- Priority: high
- Required: True
- Status: pass
- Category: registers.architectural_state
- Source ref: registers.architectural_state.done_q
- Detail: Architectural state listed outside the register map still needs RTL storage and reset/update ownership.
SSOT ref: registers.architectural_state.done_q.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: name=done_q; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State storage is present in RTL
  - Reset/update behavior matches SSOT
  - State is observable if required by registers/debug/coverage
  - Traceability keeps source_ref registers.architectural_state.done_q
  - Primary implementation evidence is in rtl/timer.sv
  - done_q reset behavior matches SSOT value 0
- SSOT refs: registers.architectural_state.done_q
