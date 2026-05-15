# RTL Authoring Packet: module__pulse_gen_core__features

- Kind: module
- Owner module: pulse_gen_core
- Owner file: rtl/pulse_gen_core.sv
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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, features, features.pulse_fire, fsm, fsm.pulse_fsm, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_FIRE
- Module slice: 4/6 section=features task_limit=48
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

### RTL-0132: Implement feature pulse_fire

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.pulse_fire
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.pulse_fire.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via features.pulse_fire.
SSOT item context: name=pulse_fire; output=pulse_out[PULSE_OUT_WIDTH-1:0] driven to active level for exactly PULSE_WIDTH_CYCLES PCLK cycles.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.pulse_fire
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: features.pulse_fire

### RTL-0133: Implement feature runtime_width_config

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.runtime_width_config
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.runtime_width_config.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via features.
SSOT item context: name=runtime_width_config; output=Next pulse uses updated width.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.runtime_width_config
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: features.runtime_width_config

### RTL-0134: Implement feature interrupt_on_done

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.interrupt_on_done
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.interrupt_on_done.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via features.
SSOT item context: name=interrupt_on_done; output=irq_o asserted for exactly the interval between pulse completion and software STATUS.done W1C write.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.interrupt_on_done
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: features.interrupt_on_done
