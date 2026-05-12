# RTL Authoring Packet: module__timer_core__dataflow

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
- Task count: 7
- Required tasks: 7

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
- Module slice: 17/17 section=dataflow task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0082: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=Reset clears count, running, and done..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0083: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=start samples load_value into count and asserts running when load_value is non-zero..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0084: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=enable advances the countdown by one while running is high..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0085: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=clear overrides timer progress and returns observable state to idle..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0086: Implement dataflow ordering: ordering_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_0.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=clear is evaluated before countdown decrement..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.ordering.ordering_0

### RTL-0087: Implement dataflow ordering: ordering_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_1.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=start creates a new timer interval before enable tick side effects are considered..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.ordering.ordering_1

### RTL-0088: Implement dataflow ordering: ordering_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_2.
Owner: timer_core in rtl/timer.sv via single_owner.
SSOT item context: value=done is derived from the cycle where count is one and enable is asserted..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: dataflow.ordering.ordering_2
