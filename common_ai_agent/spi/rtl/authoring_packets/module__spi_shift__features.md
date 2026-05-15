# RTL Authoring Packet: module__spi_shift__features

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.launch_gate, cycle_model.ordering, cycle_model.pipeline, cycle_model.pipeline.S1_LAUNCH_CHECK, cycle_model.pipeline.S2_ASSERT_CS, cycle_model.pipeline.S3_SHIFT, cycle_model.pipeline.S4_SAMPLE, cycle_model.pipeline.S5_COMPLETE, dataflow, dataflow.control_path, features, features.APB-programmed frame transfer, features.Programmable SPI mode and bit order, fsm, fsm.channel_level
- Module slice: 4/6 section=features task_limit=48
- Slice rule: Owner module spi_shift is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0221: Implement feature APB-programmed frame transfer

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.APB_programmed_frame_transfer
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.APB_programmed_frame_transfer.
Owner: spi_shift in rtl/spi_shift.sv via features.
SSOT item context: name=APB-programmed frame transfer; output=Serialized frame on mosi_o/sclk_o and optional received frame in RX FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.APB_programmed_frame_transfer
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: features.APB_programmed_frame_transfer

### RTL-0222: Implement feature Programmable SPI mode and bit order

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Programmable_SPI_mode_and_bit_order
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Programmable_SPI_mode_and_bit_order.
Owner: spi_shift in rtl/spi_shift.sv via features.
SSOT item context: name=Programmable SPI mode and bit order; output=Protocol-compliant phase/polarity behavior and chosen bit ordering.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Programmable_SPI_mode_and_bit_order
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: features.Programmable_SPI_mode_and_bit_order

### RTL-0223: Implement feature Interrupt and sticky error reporting

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Interrupt_and_sticky_error_reporting
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Interrupt_and_sticky_error_reporting.
Owner: spi_shift in rtl/spi_shift.sv via features.
SSOT item context: name=Interrupt and sticky error reporting; output=irq_o and software-readable status/error telemetry.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Interrupt_and_sticky_error_reporting
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: features.Interrupt_and_sticky_error_reporting
