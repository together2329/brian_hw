# RTL Authoring Packet: module__uart_lite_core__features

- Kind: module
- Owner module: uart_lite_core
- Owner file: rtl/uart_lite_core.sv
- Task count: 7
- Required tasks: 7

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, decomposition.units.execute, error_handling, features, function_model, function_model.state_variables, function_model.transactions
- Module slice: 3/6 section=features task_limit=48
- Slice rule: Owner module uart_lite_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])

## Tasks

### RTL-0235: Implement feature TX byte transmission

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.TX_byte_transmission
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.TX_byte_transmission.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=TX byte transmission; output=Serial UART frame on txd_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.TX_byte_transmission
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.TX_byte_transmission

### RTL-0236: Implement feature RX byte reception

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.RX_byte_reception
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.RX_byte_reception.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=RX byte reception; output=Received byte readable via RXDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.RX_byte_reception
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.RX_byte_reception

### RTL-0237: Implement feature Loopback test mode

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Loopback_test_mode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Loopback_test_mode.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Loopback test mode; output=Transmitted bytes received internally without external loopback wiring.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Loopback_test_mode
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Loopback_test_mode

### RTL-0238: Implement feature Software break send

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Software_break_send
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Software_break_send.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Software break send; output=Break condition on txd_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Software_break_send
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Software_break_send

### RTL-0239: Implement feature Configurable framing

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Configurable_framing
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Configurable_framing.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Configurable framing; output=Frames with 5-8 data bits, none/even/odd parity, 1-2 stop bits.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Configurable_framing
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Configurable_framing

### RTL-0240: Implement feature Error detection and reporting

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Error_detection_and_reporting
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Error_detection_and_reporting.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Error detection and reporting; output=STATUS sticky flags, INT_PENDING, irq_o, debug counters.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Error_detection_and_reporting
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Error_detection_and_reporting

### RTL-0241: Implement feature Debug counters

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Debug_counters
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Debug_counters.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Debug counters; output=bytes_tx, bytes_rx, frames_errored, parities_errored.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Debug_counters
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Debug_counters
