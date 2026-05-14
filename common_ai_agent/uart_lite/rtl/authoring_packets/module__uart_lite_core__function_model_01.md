# RTL Authoring Packet: module__uart_lite_core__function_model_01

- Kind: module
- Owner module: uart_lite_core
- Owner file: rtl/uart_lite_core.sv
- Task count: 48
- Required tasks: 48

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, decomposition.units.execute, error_handling, features, function_model, function_model.state_variables, function_model.transactions
- Module slice: 1/6 section=function_model task_limit=48
- Slice rule: Owner module uart_lite_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])

## Tasks

### RTL-0055: Implement RTL state owner for FL state tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_fifo.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=tx_fifo; reset=empty (wr_ptr=0, rd_ptr=0, count=0).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_fifo
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - tx_fifo reset behavior matches SSOT value empty (wr_ptr=0, rd_ptr=0, count=0)
- SSOT refs: function_model.state_variables.tx_fifo

### RTL-0056: Implement RTL state owner for FL state rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rx_fifo.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=rx_fifo; reset=empty (wr_ptr=0, rd_ptr=0, count=0).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_fifo
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - rx_fifo reset behavior matches SSOT value empty (wr_ptr=0, rd_ptr=0, count=0)
- SSOT refs: function_model.state_variables.rx_fifo

### RTL-0057: Implement RTL state owner for FL state tx_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_active
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_active.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=tx_active.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_active
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.tx_active

### RTL-0058: Implement RTL state owner for FL state rx_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rx_active
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rx_active.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=rx_active.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_active
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.rx_active

### RTL-0059: Implement RTL state owner for FL state baud_divisor

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.baud_divisor
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.baud_divisor.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=baud_divisor; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.baud_divisor
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - baud_divisor reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.baud_divisor

### RTL-0060: Implement RTL state owner for FL state parity_en

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.parity_en
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.parity_en.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=parity_en; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.parity_en
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - parity_en reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.parity_en

### RTL-0061: Implement RTL state owner for FL state parity_odd

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.parity_odd
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.parity_odd.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=parity_odd; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.parity_odd
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - parity_odd reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.parity_odd

### RTL-0062: Implement RTL state owner for FL state stop_bits

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.stop_bits
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.stop_bits.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=stop_bits; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.stop_bits
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - stop_bits reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.stop_bits

### RTL-0063: Implement RTL state owner for FL state data_width

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.data_width
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.data_width.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=data_width; reset=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.data_width
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - data_width reset behavior matches SSOT value 3
- SSOT refs: function_model.state_variables.data_width

### RTL-0064: Implement RTL state owner for FL state loopback

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.loopback
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.loopback.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=loopback; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.loopback
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - loopback reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.loopback

### RTL-0065: Implement RTL state owner for FL state bytes_tx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.bytes_tx
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.bytes_tx.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=bytes_tx; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.bytes_tx
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - bytes_tx reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.bytes_tx

### RTL-0066: Implement RTL state owner for FL state bytes_rx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.bytes_rx
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.bytes_rx.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=bytes_rx; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.bytes_rx
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - bytes_rx reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.bytes_rx

### RTL-0067: Implement RTL state owner for FL state frames_errored

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.frames_errored
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.frames_errored.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=frames_errored; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.frames_errored
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - frames_errored reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.frames_errored

### RTL-0068: Implement RTL state owner for FL state parities_errored

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.parities_errored
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.parities_errored.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: name=parities_errored; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.parities_errored
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - parities_errored reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.parities_errored

### RTL-0069: Implement transaction FM_TX

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TX
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TX.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: id=FM_TX; name=tx_byte_transfer.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TX
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX

### RTL-0070: Implement precondition for FM_TX: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.preconditions.precondition_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=TX FIFO not empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.preconditions.precondition_0

### RTL-0071: Implement precondition for FM_TX: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.preconditions.precondition_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=tx_active == false (TX FSM idle).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.preconditions.precondition_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.preconditions.precondition_1

### RTL-0072: Implement precondition for FM_TX: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.preconditions.precondition_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=baud_divisor > 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.preconditions.precondition_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.preconditions.precondition_2

### RTL-0073: Implement precondition for FM_TX: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.preconditions.precondition_3.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=break_send == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.preconditions.precondition_3
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.preconditions.precondition_3

### RTL-0074: Implement input for FM_TX: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_TX.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.inputs.input_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=tx_fifo head byte (DATA_WIDTH bits).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.inputs.input_0

### RTL-0075: Implement input for FM_TX: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_TX.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.inputs.input_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=CONTROL parity_en, parity_odd, stop_bits, data_width.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.inputs.input_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.inputs.input_1

### RTL-0076: Implement output for FM_TX: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TX.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.outputs.output_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=txd_o toggles per UART frame: start(0) + DATA_WIDTH LSB-first data + optional parity + STOP_BITS stop(1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.outputs.output_0

### RTL-0077: Implement side effect for FM_TX: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.side_effects.side_effect_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Head byte popped from TX FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.side_effects.side_effect_0

### RTL-0078: Implement side effect for FM_TX: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.side_effects.side_effect_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=bytes_tx incremented by 1 (wraps at 2^32).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.side_effects.side_effect_1

### RTL-0079: Implement side effect for FM_TX: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.side_effects.side_effect_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=tx_empty status updated (1 if FIFO now empty).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.side_effects.side_effect_2

### RTL-0080: Implement side effect for FM_TX: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.side_effects.side_effect_3.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=INT_PENDING.tx_empty_pending tracks tx_empty level.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_TX.side_effects.side_effect_3

### RTL-0081: Implement error case for FM_TX: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_TX.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX.error_cases.error_case_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: condition=TX FIFO underrun (FIFO goes empty mid-frame due to internal error).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX.error_cases.error_case_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - function_model.transactions.FM_TX.error_cases.error_case_0 condition is implemented as RTL control logic: TX FIFO underrun (FIFO goes empty mid-frame due to internal error)
- SSOT refs: function_model.transactions.FM_TX.error_cases.error_case_0

### RTL-0082: Implement transaction FM_RX

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RX
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RX.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: id=FM_RX; name=rx_byte_receive.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RX
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX

### RTL-0083: Implement precondition for FM_RX: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.preconditions.precondition_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=RX FSM idle (rx_active == false).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.preconditions.precondition_0

### RTL-0084: Implement precondition for FM_RX: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.preconditions.precondition_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=baud_divisor > 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.preconditions.precondition_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.preconditions.precondition_1

### RTL-0085: Implement precondition for FM_RX: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.preconditions.precondition_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Falling edge detected on rxd_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.preconditions.precondition_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.preconditions.precondition_2

### RTL-0086: Implement input for FM_RX: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RX.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.inputs.input_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=rxd_i serial line.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.inputs.input_0

### RTL-0087: Implement input for FM_RX: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RX.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.inputs.input_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=CONTROL parity_en, parity_odd, stop_bits, data_width.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.inputs.input_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.inputs.input_1

### RTL-0088: Implement output for FM_RX: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RX.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.outputs.output_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Received DATA_WIDTH byte pushed into RX FIFO on success.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.outputs.output_0

### RTL-0089: Implement output for FM_RX: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RX.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.outputs.output_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=STATUS flags updated: frame_err, parity_err, rx_overrun as applicable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.outputs.output_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.outputs.output_1

### RTL-0090: Implement side effect for FM_RX: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.side_effects.side_effect_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Received byte pushed into RX FIFO if not full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.side_effects.side_effect_0

### RTL-0091: Implement side effect for FM_RX: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.side_effects.side_effect_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=bytes_rx incremented by 1 on success (wraps at 2^32).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.side_effects.side_effect_1

### RTL-0092: Implement side effect for FM_RX: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.side_effects.side_effect_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=rx_not_empty status updated.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.side_effects.side_effect_2

### RTL-0093: Implement side effect for FM_RX: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.side_effects.side_effect_3.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=INT_PENDING.rx_not_empty_pending tracks !rx_empty level.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_RX.side_effects.side_effect_3

### RTL-0094: Implement error case for FM_RX: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.error_cases.error_case_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: condition=Stop bit sampled low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.error_cases.error_case_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - function_model.transactions.FM_RX.error_cases.error_case_0 condition is implemented as RTL control logic: Stop bit sampled low
- SSOT refs: function_model.transactions.FM_RX.error_cases.error_case_0

### RTL-0095: Implement error case for FM_RX: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.error_cases.error_case_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: condition=Parity mismatch (calculated != received).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.error_cases.error_case_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - function_model.transactions.FM_RX.error_cases.error_case_1 condition is implemented as RTL control logic: Parity mismatch (calculated != received)
- SSOT refs: function_model.transactions.FM_RX.error_cases.error_case_1

### RTL-0096: Implement error case for FM_RX: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX.error_cases.error_case_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: condition=RX FIFO full when new byte ready to push.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX.error_cases.error_case_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - function_model.transactions.FM_RX.error_cases.error_case_2 condition is implemented as RTL control logic: RX FIFO full when new byte ready to push
- SSOT refs: function_model.transactions.FM_RX.error_cases.error_case_2

### RTL-0097: Implement transaction FM_LOOPBACK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_LOOPBACK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_LOOPBACK.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: id=FM_LOOPBACK; name=loopback_mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK

### RTL-0098: Implement precondition for FM_LOOPBACK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=loopback == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0

### RTL-0099: Implement precondition for FM_LOOPBACK: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=TX FIFO not empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.preconditions.precondition_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.preconditions.precondition_1

### RTL-0100: Implement precondition for FM_LOOPBACK: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=baud_divisor > 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.preconditions.precondition_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.preconditions.precondition_2

### RTL-0101: Implement input for FM_LOOPBACK: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_LOOPBACK.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.inputs.input_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=tx_fifo head byte.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.inputs.input_0

### RTL-0102: Implement output for FM_LOOPBACK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_LOOPBACK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.outputs.output_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=txd_o toggles normally AND rxd_i sampling path receives txd_o instead of external rxd_i (loopback mux before synchron....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.outputs.output_0
