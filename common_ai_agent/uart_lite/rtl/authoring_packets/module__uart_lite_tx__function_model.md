# RTL Authoring Packet: module__uart_lite_tx__function_model

- Kind: module
- Owner module: uart_lite_tx
- Owner file: rtl/uart_lite_tx.sv
- Task count: 19
- Required tasks: 19

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
- Owner refs: cycle_model, cycle_model.pipeline, cycle_model.pipeline[TX_DATA], cycle_model.pipeline[TX_IDLE], cycle_model.pipeline[TX_PARITY], cycle_model.pipeline[TX_START], cycle_model.pipeline[TX_STOP1], cycle_model.pipeline[TX_STOP2], fsm, fsm.tx_fsm, function_model, function_model.transactions.FM_TX_BYTE
- Module slice: 1/5 section=function_model task_limit=48
- Slice rule: Owner module uart_lite_tx is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0063: Implement transaction FM_TX_BYTE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TX_BYTE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TX_BYTE.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: id=FM_TX_BYTE; name=transmit_byte.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE

### RTL-0064: Implement precondition for FM_TX_BYTE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx_enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.preconditions.precondition_0

### RTL-0065: Implement precondition for FM_TX_BYTE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx_fifo not empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.preconditions.precondition_1

### RTL-0066: Implement precondition for FM_TX_BYTE: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx_active == false.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.preconditions.precondition_2

### RTL-0067: Implement precondition for FM_TX_BYTE: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.preconditions.precondition_3.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=break_send == false.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.preconditions.precondition_3
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.preconditions.precondition_3

### RTL-0068: Implement input for FM_TX_BYTE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_TX_BYTE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.inputs.input_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=byte d popped from tx_fifo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.inputs.input_0

### RTL-0069: Implement output for FM_TX_BYTE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TX_BYTE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.outputs.output_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx line: start bit (0), d[0]..d[DATA_WIDTH-1] LSB-first, parity bit (if parity_en), 1 or 2 stop bits (1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.outputs.output_0

### RTL-0070: Implement output for FM_TX_BYTE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TX_BYTE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.outputs.output_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx_active transitions true → false across the frame.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.outputs.output_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.outputs.output_1

### RTL-0071: Implement output rule for FM_TX_BYTE: tx_serial

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TX_BYTE.output_rules.tx_serial
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.output_rules.tx_serial.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: name=tx_serial; port=tx; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.output_rules.tx_serial
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - tx_serial RTL expression implements SSOT expression 1
  - DUT port tx is the implementation/observation point for tx_serial
  - tx_serial is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TX_BYTE.output_rules.tx_serial

### RTL-0072: Implement state update for FM_TX_BYTE: tx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TX_BYTE.state_updates.tx
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.state_updates.tx.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: name=tx; expr=1; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.state_updates.tx
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - tx reset behavior matches SSOT value 1
  - tx RTL expression implements SSOT expression 1
  - tx updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TX_BYTE.state_updates.tx

### RTL-0073: Implement side effect for FM_TX_BYTE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=debug counter bytes_tx increments by 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_0

### RTL-0074: Implement side effect for FM_TX_BYTE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=tx_fifo level decreases by 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_1

### RTL-0075: Implement side effect for FM_TX_BYTE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: value=STAT.tx_empty updates when FIFO becomes empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.transactions.FM_TX_BYTE.side_effects.side_effect_2

### RTL-0076: Implement error case for FM_TX_BYTE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_TX_BYTE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TX_BYTE.error_cases.error_case_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.transactions.FM_TX_BYTE.
SSOT item context: condition=tx_fifo empty when TX FSM requests byte.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TX_BYTE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - function_model.transactions.FM_TX_BYTE.error_cases.error_case_0 condition is implemented as RTL control logic: tx_fifo empty when TX FSM requests byte
- SSOT refs: function_model.transactions.FM_TX_BYTE.error_cases.error_case_0

### RTL-0110: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.
SSOT item context: value=TX FIFO never underflows during a valid frame — underrun terminates frame early..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0111: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.
SSOT item context: value=RX FIFO never overflows without sticky overrun_err flag..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0112: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.
SSOT item context: value=Register read side effects are exactly those listed in registers.register_list..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0113: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.
SSOT item context: value=Sticky status flags remain set until explicitly cleared via CLR_STAT W1C..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0114: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via function_model.
SSOT item context: value=Debug counters are free-running, read-only, and wrap at 0xFFFFFFFF..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: function_model.invariants.invariant_4
