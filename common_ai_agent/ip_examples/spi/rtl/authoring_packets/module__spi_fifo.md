# RTL Authoring Packet: module__spi_fifo

- Kind: module
- Owner module: spi_fifo
- Owner file: rtl/spi_fifo.sv
- Task count: 31
- Required tasks: 31

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
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.backpressure, cycle_model.pipeline.S0_APB_CFG, cycle_model.pipeline.S5_COMPLETE, dataflow, dataflow.rx_path, dataflow.tx_path, function_model, function_model.state_variables.rx_fifo, function_model.state_variables.tx_fifo, function_model.transactions.FM_APB_RX_POP, function_model.transactions.FM_APB_TX_PUSH, function_model.transactions.FM_FRAME_COMPLETE.side_effects, memory, memory.instances
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_fifo.rx_push_data <= rx_word (integration.connections[3])

## Tasks

### RTL-0060: Implement RTL state owner for FL state tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_fifo.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.state_variables.tx_fifo.
SSOT item context: name=tx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
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
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.state_variables.rx_fifo.
SSOT item context: name=rx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - rx_fifo reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.rx_fifo

### RTL-0065: Implement transaction FM_APB_TX_PUSH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_TX_PUSH
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: id=FM_APB_TX_PUSH; name=apb_write_txdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH

### RTL-0066: Implement precondition for FM_APB_TX_PUSH: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: value=APB write handshake to TXDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.preconditions.precondition_0

### RTL-0067: Implement input for FM_APB_TX_PUSH: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: value=PWDATA[DATA_WIDTH-1:0].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.inputs.input_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.inputs.input_0

### RTL-0068: Implement output for FM_APB_TX_PUSH: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: value=TX FIFO occupancy increments by one when not full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.outputs.output_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.outputs.output_0

### RTL-0069: Implement side effect for FM_APB_TX_PUSH: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: value=If tx_fifo full, payload is discarded and STATUS.tx_overrun set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_0

### RTL-0070: Implement side effect for FM_APB_TX_PUSH: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: value=tx_empty/tx_full level indicators update.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.side_effects.side_effect_1

### RTL-0071: Implement error case for FM_APB_TX_PUSH: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_TX_PUSH.
SSOT item context: condition=unsupported PSTRB for TXDATA width.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0 condition is implemented as RTL control logic: unsupported PSTRB for TXDATA width
- SSOT refs: function_model.transactions.FM_APB_TX_PUSH.error_cases.error_case_0

### RTL-0093: Implement transaction FM_FRAME_COMPLETE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FRAME_COMPLETE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_FRAME_COMPLETE.side_effects.
SSOT item context: id=FM_FRAME_COMPLETE; name=complete_frame_and_store_rx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE

### RTL-0097: Implement side effect for FM_FRAME_COMPLETE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_FRAME_COMPLETE.side_effects.
SSOT item context: value=If RX FIFO has space, received frame pushed; else discard and STATUS.rx_overrun set.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_0

### RTL-0098: Implement side effect for FM_FRAME_COMPLETE: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_FRAME_COMPLETE.side_effects.
SSOT item context: value=CS deasserts to CS_IDLE unless continuous_cs holds across back-to-back frame.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_1

### RTL-0099: Implement side effect for FM_FRAME_COMPLETE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_FRAME_COMPLETE.side_effects.
SSOT item context: value=Interrupt pending bits update for done and FIFO level.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_FRAME_COMPLETE.side_effects.side_effect_2

### RTL-0101: Implement transaction FM_APB_RX_POP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_RX_POP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_RX_POP.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_RX_POP.
SSOT item context: id=FM_APB_RX_POP; name=apb_read_rxdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP

### RTL-0102: Implement precondition for FM_APB_RX_POP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_RX_POP.
SSOT item context: value=APB read handshake to RXDATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.preconditions.precondition_0

### RTL-0103: Implement output for FM_APB_RX_POP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_RX_POP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.outputs.output_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_RX_POP.
SSOT item context: value=Returns oldest RX word when FIFO non-empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.outputs.output_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.outputs.output_0

### RTL-0104: Implement side effect for FM_APB_RX_POP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_RX_POP.
SSOT item context: value=RX FIFO occupancy decrements on successful pop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0

### RTL-0105: Implement error case for FM_APB_RX_POP: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0.
Owner: spi_fifo in rtl/spi_fifo.sv via function_model.transactions.FM_APB_RX_POP.
SSOT item context: condition=RX FIFO empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0 condition is implemented as RTL control logic: RX FIFO empty
- SSOT refs: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0

### RTL-0116: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0117: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0118: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0119: Implement handshake rule: APB

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.APB
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.APB.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: signal=APB.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.APB
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.handshake_rules.APB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.APB

### RTL-0120: Implement handshake rule: CTRL.start

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.CTRL_start
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.CTRL_start.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: signal=CTRL.start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.CTRL_start
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.handshake_rules.CTRL_start appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.CTRL_start

### RTL-0124: Implement pipeline stage: S0_APB_CFG

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_APB_CFG
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_APB_CFG.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.pipeline.S0_APB_CFG.
SSOT item context: stage=S0_APB_CFG; action=Program mode/prescale/CS and push TX words; cycle=t.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_APB_CFG
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.pipeline.S0_APB_CFG timing uses SSOT cycle/latency t
  - cycle_model.pipeline.S0_APB_CFG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_APB_CFG

### RTL-0129: Implement pipeline stage: S5_COMPLETE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S5_COMPLETE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S5_COMPLETE.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.pipeline.S5_COMPLETE.
SSOT item context: stage=S5_COMPLETE; action=Push RX word if possible, update done/errors/pending, manage CS hold/deassert; cycle=terminal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S5_COMPLETE
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.pipeline.S5_COMPLETE timing uses SSOT cycle/latency terminal
  - cycle_model.pipeline.S5_COMPLETE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S5_COMPLETE

### RTL-0133: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.backpressure.
SSOT item context: value=TX backpressure appears as tx_full; writes are dropped with tx_overrun when full..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0134: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.backpressure.
SSOT item context: value=RX backpressure appears as rx_full at completion; received frame is dropped with rx_overrun when full..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0135: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: value=Probe launch_accept, sample_edge, shift_edge, bit_index, cs_active, tx_fifo_level, rx_fifo_level, done_event.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0193: Implement memory item tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.tx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.tx_fifo.
Owner: spi_fifo in rtl/spi_fifo.sv via memory.instances.
SSOT item context: name=tx_fifo; width=32; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.tx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - tx_fifo width matches SSOT value 32
  - tx_fifo timing uses SSOT cycle/latency 0
  - tx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.tx_fifo

### RTL-0194: Implement memory item rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.rx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.rx_fifo.
Owner: spi_fifo in rtl/spi_fifo.sv via memory.instances.
SSOT item context: name=rx_fifo; width=32; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.rx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - rx_fifo width matches SSOT value 32
  - rx_fifo timing uses SSOT cycle/latency 0
  - rx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.rx_fifo

### RTL-0244: Prove module spi_fifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi_fifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_fifo.module_equivalence.
Owner: spi_fifo in rtl/spi_fifo.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_fifo.module_equivalence
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: sub_modules.spi_fifo.module_equivalence
