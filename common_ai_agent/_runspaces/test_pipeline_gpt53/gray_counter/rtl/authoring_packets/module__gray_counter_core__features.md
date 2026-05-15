# RTL Authoring Packet: module__gray_counter_core__features

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
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
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 5/9 section=features task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0116: Implement feature Gray increment progression

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Gray_increment_progression
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Gray_increment_progression.
Owner: gray_counter_core in rtl/gray_counter_core.sv via features.
SSOT item context: name=Gray increment progression; output=gray_value advances one legal Gray step.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Gray_increment_progression
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: features.Gray_increment_progression

### RTL-0117: Implement feature Wrap pulse generation

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Wrap_pulse_generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Wrap_pulse_generation.
Owner: gray_counter_core in rtl/gray_counter_core.sv via features.
SSOT item context: name=Wrap pulse generation; output=done asserted for exactly one cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Wrap_pulse_generation
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: features.Wrap_pulse_generation

### RTL-0118: Implement feature Deterministic clear/reset

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Deterministic_clear_reset
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Deterministic_clear_reset.
Owner: gray_counter_core in rtl/gray_counter_core.sv via features.
SSOT item context: name=Deterministic clear/reset; output=gray_value=0, bin_value=0, done=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Deterministic_clear_reset
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: features.Deterministic_clear_reset
