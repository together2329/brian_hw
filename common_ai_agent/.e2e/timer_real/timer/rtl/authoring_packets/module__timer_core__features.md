# RTL Authoring Packet: module__timer_core__features

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
- Task count: 4
- Required tasks: 4

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
- Module slice: 4/8 section=features task_limit=48
- Slice rule: Owner module timer_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_core.pclk <= pclk (integration.connections[13])
  - timer_core.presetn <= presetn (integration.connections[14])
  - timer_core.load_q <= load_q (integration.connections[15])
  - timer_core.enable_q <= enable_q (integration.connections[16])
  - timer_core.count_q <= count_q (integration.connections[17])
  - timer_core.irq <= irq (integration.connections[18])

## Tasks

### RTL-0176: Implement feature Programmable load register

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Programmable_load_register
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Programmable_load_register.
Owner: timer_core in rtl/timer_core.sv via features.
SSOT item context: name=Programmable load register; output=Future reload value for count_q..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Programmable_load_register
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: features.Programmable_load_register

### RTL-0177: Implement feature Enable-controlled down counter

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Enable_controlled_down_counter
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Enable_controlled_down_counter.
Owner: timer_core in rtl/timer_core.sv via features.
SSOT item context: name=Enable-controlled down counter; output=STATUS reflects current count_q..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Enable_controlled_down_counter
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: features.Enable_controlled_down_counter

### RTL-0178: Implement feature Periodic irq pulse and reload

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Periodic_irq_pulse_and_reload
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Periodic_irq_pulse_and_reload.
Owner: timer_core in rtl/timer_core.sv via features.
SSOT item context: name=Periodic irq pulse and reload; output=Single-cycle irq pulse and continued counting from LOAD..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Periodic_irq_pulse_and_reload
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: features.Periodic_irq_pulse_and_reload

### RTL-0179: Implement feature Disable hold

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Disable_hold
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Disable_hold.
Owner: timer_core in rtl/timer_core.sv via features.
SSOT item context: name=Disable hold; output=No decrement and irq remains deasserted..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Disable_hold
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: features.Disable_hold
