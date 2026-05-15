# RTL Authoring Packet: module__spi_shift__function_model_01

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
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
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, features, fsm, fsm.channel_level, function_model, function_model.transactions
- Module slice: 1/7 section=function_model task_limit=48
- Slice rule: Owner module spi_shift is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0055: Implement RTL state owner for FL state ctrl_enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_enable.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=ctrl_enable; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_enable
  - Primary implementation evidence is in rtl/spi_shift.sv
  - ctrl_enable reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctrl_enable

### RTL-0056: Implement RTL state owner for FL state ctrl_mode

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_mode
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_mode.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=ctrl_mode; reset={cpol:CPOL_RESET,cpha:CPHA_RESET,lsb_first:LSB_FIRST_RESET,continuous_cs:0,loopback:0}.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_mode
  - Primary implementation evidence is in rtl/spi_shift.sv
  - ctrl_mode reset behavior matches SSOT value {cpol:CPOL_RESET,cpha:CPHA_RESET,lsb_first:LSB_FIRST_RESET,continuous_cs:0,loopback:0}
- SSOT refs: function_model.state_variables.ctrl_mode

### RTL-0057: Implement RTL state owner for FL state active_cs

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.active_cs
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.active_cs.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=active_cs; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.active_cs
  - Primary implementation evidence is in rtl/spi_shift.sv
  - active_cs reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.active_cs

### RTL-0058: Implement RTL state owner for FL state frame_bits

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.frame_bits
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.frame_bits.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=frame_bits; reset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.frame_bits
  - Primary implementation evidence is in rtl/spi_shift.sv
  - frame_bits reset behavior matches SSOT value 8
- SSOT refs: function_model.state_variables.frame_bits

### RTL-0059: Implement RTL state owner for FL state prescale_div

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.prescale_div
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.prescale_div.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=prescale_div; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.prescale_div
  - Primary implementation evidence is in rtl/spi_shift.sv
  - prescale_div reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.prescale_div

### RTL-0060: Implement RTL state owner for FL state tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_fifo.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=tx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_fifo
  - Primary implementation evidence is in rtl/spi_shift.sv
  - tx_fifo reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.tx_fifo

### RTL-0061: Implement RTL state owner for FL state rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rx_fifo.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=rx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_fifo
  - Primary implementation evidence is in rtl/spi_shift.sv
  - rx_fifo reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.rx_fifo

### RTL-0062: Implement RTL state owner for FL state busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.busy
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.busy.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=busy; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.busy
  - Primary implementation evidence is in rtl/spi_shift.sv
  - busy reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.busy

### RTL-0063: Implement RTL state owner for FL state sticky_errors

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sticky_errors
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sticky_errors.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=sticky_errors; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sticky_errors
  - Primary implementation evidence is in rtl/spi_shift.sv
  - sticky_errors reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sticky_errors

### RTL-0064: Implement RTL state owner for FL state int_pending

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_pending.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: name=int_pending; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_pending
  - Primary implementation evidence is in rtl/spi_shift.sv
  - int_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_pending

### RTL-0065: Implement transaction FM_APB_TX_PUSH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_TX_PUSH
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_APB_TX_PUSH; name=apb_write_txdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH

### RTL-0066: Implement precondition for FM_APB_TX_PUSH: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=APB write handshake to TXDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0

### RTL-0067: Implement input for FM_APB_TX_PUSH: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=PWDATA[DATA_WIDTH-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.inputs.input_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0

### RTL-0068: Implement output for FM_APB_TX_PUSH: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=TX FIFO occupancy increments by one when not full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0

### RTL-0069: Implement side effect for FM_APB_TX_PUSH: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=If tx_fifo full, payload is discarded and STATUS.tx_overrun set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0

### RTL-0070: Implement side effect for FM_APB_TX_PUSH: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=tx_empty/tx_full level indicators update.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1

### RTL-0071: Implement error case for FM_APB_TX_PUSH: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=unsupported PSTRB for TXDATA width.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0 condition is implemented as RTL control logic: unsupported PSTRB for TXDATA width
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0

### RTL-0072: Implement transaction FM_FRAME_LAUNCH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FRAME_LAUNCH
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_FRAME_LAUNCH; name=launch_frame.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH

### RTL-0073: Implement precondition for FM_FRAME_LAUNCH: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=CTRL.start pulse observed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_0

### RTL-0074: Implement precondition for FM_FRAME_LAUNCH: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=ctrl_enable == 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_1

### RTL-0075: Implement precondition for FM_FRAME_LAUNCH: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_2.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=busy == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_2
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_2

### RTL-0076: Implement precondition for FM_FRAME_LAUNCH: precondition_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_3.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=tx_fifo not empty.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_3
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_3

### RTL-0077: Implement precondition for FM_FRAME_LAUNCH: precondition_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_4.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=cs_sel in [0, NUM_CS-1].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_4
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_4

### RTL-0078: Implement precondition for FM_FRAME_LAUNCH: precondition_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_5
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_5.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=frame_bits in [4, 32].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_5
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.preconditions.precondition_5

### RTL-0079: Implement output for FM_FRAME_LAUNCH: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=busy transitions to 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_0

### RTL-0080: Implement output for FM_FRAME_LAUNCH: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=One TX word is consumed from TX FIFO for shift register load.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.outputs.output_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.outputs.output_1

### RTL-0081: Implement side effect for FM_FRAME_LAUNCH: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=csn_o drives exactly one active-low bit at selected CS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_0

### RTL-0082: Implement side effect for FM_FRAME_LAUNCH: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=SCLK idle level driven per CPOL before first active edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.side_effects.side_effect_1

### RTL-0083: Implement error case for FM_FRAME_LAUNCH: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=cs_sel illegal or frame_bits illegal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_0 condition is implemented as RTL control logic: cs_sel illegal or frame_bits illegal
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_0

### RTL-0084: Implement error case for FM_FRAME_LAUNCH: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=CTRL.enable == 0 or tx_fifo empty or busy==1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_1
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_1 condition is implemented as RTL control logic: CTRL.enable == 0 or tx_fifo empty or busy==1
- SSOT refs: function_model.transactions.FM_FRAME_LAUNCH.error_cases.error_case_1

### RTL-0085: Implement transaction FM_SHIFT_SAMPLE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_SHIFT_SAMPLE; name=shift_and_sample_bits.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE

### RTL-0086: Implement precondition for FM_SHIFT_SAMPLE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=busy == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.preconditions.precondition_0

### RTL-0087: Implement input for FM_SHIFT_SAMPLE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.inputs.input_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=miso_i sampled on mode-dependent sample edges or internal mosi_o if loopback=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.inputs.input_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.inputs.input_0

### RTL-0088: Implement output for FM_SHIFT_SAMPLE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=mosi_o presents serialized transmit bits with configured bit order.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_0

### RTL-0089: Implement output for FM_SHIFT_SAMPLE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=rx_shift_reg accumulates sampled bits.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.outputs.output_1

### RTL-0090: Implement side effect for FM_SHIFT_SAMPLE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=bit_index progresses from 0 to frame_bits-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_0

### RTL-0091: Implement side effect for FM_SHIFT_SAMPLE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=done asserted when terminal sample edge occurs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.side_effects.side_effect_1

### RTL-0092: Implement error case for FM_SHIFT_SAMPLE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_SHIFT_SAMPLE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SHIFT_SAMPLE.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=none during legal frame.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SHIFT_SAMPLE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_SHIFT_SAMPLE.error_cases.error_case_0 condition is implemented as RTL control logic: none during legal frame
- SSOT refs: function_model.transactions.FM_SHIFT_SAMPLE.error_cases.error_case_0

### RTL-0093: Implement transaction FM_FRAME_COMPLETE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FRAME_COMPLETE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_FRAME_COMPLETE; name=complete_frame_and_store_rx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE

### RTL-0094: Implement precondition for FM_FRAME_COMPLETE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=terminal sample edge reached.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.preconditions.precondition_0

### RTL-0095: Implement output for FM_FRAME_COMPLETE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=busy transitions to 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_0

### RTL-0096: Implement output for FM_FRAME_COMPLETE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=STATUS.done pulse/latched event generated.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.outputs.output_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.outputs.output_1

### RTL-0097: Implement side effect for FM_FRAME_COMPLETE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=If RX FIFO has space, received frame pushed; else discard and STATUS.rx_overrun set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0

### RTL-0098: Implement side effect for FM_FRAME_COMPLETE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=CS deasserts to CS_IDLE unless continuous_cs holds across back-to-back frame.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1

### RTL-0099: Implement side effect for FM_FRAME_COMPLETE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=Interrupt pending bits update for done and FIFO level.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2

### RTL-0100: Implement error case for FM_FRAME_COMPLETE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=RX FIFO full.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_FRAME_COMPLETE.error_cases.error_case_0 condition is implemented as RTL control logic: RX FIFO full
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.error_cases.error_case_0

### RTL-0101: Implement transaction FM_APB_RX_POP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_RX_POP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_RX_POP.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_APB_RX_POP; name=apb_read_rxdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP

### RTL-0102: Implement precondition for FM_APB_RX_POP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=APB read handshake to RXDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0
