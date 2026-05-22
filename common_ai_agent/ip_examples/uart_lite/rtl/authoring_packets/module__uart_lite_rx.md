# RTL Authoring Packet: module__uart_lite_rx

- Kind: module
- Owner module: uart_lite_rx
- Owner file: rtl/uart_lite_rx.sv
- Task count: 47
- Required tasks: 47

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, cycle_model.pipeline[RX_DATA], cycle_model.pipeline[RX_IDLE], cycle_model.pipeline[RX_PARITY], cycle_model.pipeline[RX_START_CONFIRM], cycle_model.pipeline[RX_START_DETECT], cycle_model.pipeline[RX_STOP1], cycle_model.pipeline[RX_STOP2], fsm, fsm.rx_fsm, function_model, function_model.transactions.FM_RX_BYTE
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0029: Implement RX FSM with 2-FF synchronizer and oversampling

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: From fsm.rx_fsm and cycle_model pipeline: implement RX_IDLE → RX_START_DETECT → RX_START_CONFIRM → RX_DATA → RX_PARITY (if parity_en) → RX_STOP1 → RX_STOP2 (if stop_bits=1). Sample at oversample count 7 of 16. Detect framing/parity errors.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPL_RX_FSM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RX FSM states and all declared transitions implemented
  - Mid-bit sampling at oversample count 7
  - 2-FF synchronizer on rx input
  - Spurious start bit rejection implemented
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - Semantic source_refs covered: cdc_requirements, cycle_model.pipeline.rx_stages, fsm.rx_fsm
- SSOT refs: cdc_requirements, cycle_model.pipeline.rx_stages, fsm.rx_fsm, workflow_todos.rtl-gen[2]

### RTL-0077: Implement transaction FM_RX_BYTE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RX_BYTE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RX_BYTE.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: id=FM_RX_BYTE; name=receive_byte.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE

### RTL-0078: Implement precondition for FM_RX_BYTE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=rx_enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.preconditions.precondition_0

### RTL-0079: Implement precondition for FM_RX_BYTE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=rx_active == false.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.preconditions.precondition_1

### RTL-0080: Implement precondition for FM_RX_BYTE: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.preconditions.precondition_2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=rx_fifo not full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.preconditions.precondition_2

### RTL-0081: Implement input for FM_RX_BYTE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RX_BYTE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.inputs.input_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=rx line serial stream after 2-FF synchronizer.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.inputs.input_0

### RTL-0082: Implement output for FM_RX_BYTE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RX_BYTE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.outputs.output_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=byte d reconstructed from sampled bits pushed to rx_fifo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.outputs.output_0

### RTL-0083: Implement output for FM_RX_BYTE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RX_BYTE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.outputs.output_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=STAT.rx_not_empty set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.outputs.output_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.outputs.output_1

### RTL-0084: Implement output rule for FM_RX_BYTE: rx_irq

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RX_BYTE.output_rules.rx_irq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.output_rules.rx_irq.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: name=rx_irq; port=uart_irq; expr=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.output_rules.rx_irq
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - rx_irq RTL expression implements SSOT expression 0
  - DUT port uart_irq is the implementation/observation point for rx_irq
  - rx_irq is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RX_BYTE.output_rules.rx_irq

### RTL-0085: Implement state update for FM_RX_BYTE: uart_irq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RX_BYTE.state_updates.uart_irq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.state_updates.uart_irq.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: name=uart_irq; expr=0; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.state_updates.uart_irq
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - uart_irq reset behavior matches SSOT value 0
  - uart_irq RTL expression implements SSOT expression 0
  - uart_irq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RX_BYTE.state_updates.uart_irq

### RTL-0086: Implement side effect for FM_RX_BYTE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=debug counter bytes_rx increments by 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_0

### RTL-0087: Implement side effect for FM_RX_BYTE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=rx_fifo level increases by 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_1

### RTL-0088: Implement side effect for FM_RX_BYTE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=If parity_en and parity mismatch: parity_err sticky set, parities_errored incremented.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_2

### RTL-0089: Implement side effect for FM_RX_BYTE: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_3.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: value=If stop bit(s) not high: frame_err sticky set, frames_errored incremented.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: function_model.transactions.FM_RX_BYTE.side_effects.side_effect_3

### RTL-0090: Implement error case for FM_RX_BYTE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: condition=rx_fifo full when new byte ready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - function_model.transactions.FM_RX_BYTE.error_cases.error_case_0 condition is implemented as RTL control logic: rx_fifo full when new byte ready
- SSOT refs: function_model.transactions.FM_RX_BYTE.error_cases.error_case_0

### RTL-0091: Implement error case for FM_RX_BYTE: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: condition=spurious start bit (mid-bit sample high).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.error_cases.error_case_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - function_model.transactions.FM_RX_BYTE.error_cases.error_case_1 condition is implemented as RTL control logic: spurious start bit (mid-bit sample high)
- SSOT refs: function_model.transactions.FM_RX_BYTE.error_cases.error_case_1

### RTL-0092: Implement error case for FM_RX_BYTE: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: condition=frame_err: stop bit sampled low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.error_cases.error_case_2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - function_model.transactions.FM_RX_BYTE.error_cases.error_case_2 condition is implemented as RTL control logic: frame_err: stop bit sampled low
- SSOT refs: function_model.transactions.FM_RX_BYTE.error_cases.error_case_2

### RTL-0093: Implement error case for FM_RX_BYTE: error_case_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RX_BYTE.error_cases.error_case_3.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via function_model.transactions.FM_RX_BYTE.
SSOT item context: condition=parity_err: computed parity != received parity bit.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RX_BYTE.error_cases.error_case_3
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - function_model.transactions.FM_RX_BYTE.error_cases.error_case_3 condition is implemented as RTL control logic: parity_err: computed parity != received parity bit
- SSOT refs: function_model.transactions.FM_RX_BYTE.error_cases.error_case_3

### RTL-0118: Implement handshake rule: tx

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.tx
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.tx.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.handshake_rules.
SSOT item context: signal=tx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.tx
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.handshake_rules.tx appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.tx

### RTL-0119: Implement handshake rule: rx

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.rx
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.rx.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.handshake_rules.
SSOT item context: signal=rx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.rx
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.handshake_rules.rx appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.rx

### RTL-0120: Implement handshake rule: PREADY

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PREADY
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PREADY.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.handshake_rules.
SSOT item context: signal=PREADY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PREADY
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.handshake_rules.PREADY appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PREADY

### RTL-0121: Implement handshake rule: PSLVERR

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PSLVERR
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PSLVERR.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.handshake_rules.
SSOT item context: signal=PSLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PSLVERR
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.handshake_rules.PSLVERR appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PSLVERR

### RTL-0128: Implement pipeline stage: RX_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_IDLE.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_IDLE; action=Monitor synchronized rx for falling edge; assert rx_active=false; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_IDLE
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.RX_IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_IDLE

### RTL-0129: Implement pipeline stage: RX_START_DETECT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_START_DETECT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_START_DETECT.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_START_DETECT; action=On falling edge, wait until oversample count 7; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_START_DETECT
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_START_DETECT timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.RX_START_DETECT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_START_DETECT

### RTL-0130: Implement pipeline stage: RX_START_CONFIRM

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_START_CONFIRM
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_START_CONFIRM.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_START_CONFIRM; action=At oversample count 7, sample synchronized rx. If low → confirmed start, advance. If high → spurious, return to RX_IDLE.; cycle=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_START_CONFIRM
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_START_CONFIRM timing uses SSOT cycle/latency 2
  - cycle_model.pipeline.RX_START_CONFIRM appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_START_CONFIRM

### RTL-0131: Implement pipeline stage: RX_DATA

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_DATA
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_DATA.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_DATA; action=At oversample count 7 of each subsequent bit period, sample rx into rx_shift_reg LSB-first; repeat DATA_WIDTH times; cycle=3..2+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_DATA
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_DATA timing uses SSOT cycle/latency 3..2+DATA_WIDTH
  - cycle_model.pipeline.RX_DATA appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_DATA

### RTL-0132: Implement pipeline stage: RX_PARITY

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_PARITY
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_PARITY.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_PARITY; action=At oversample count 7, sample parity bit; compute expected parity; compare. (present only if parity_en=1); cycle=3+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_PARITY
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_PARITY timing uses SSOT cycle/latency 3+DATA_WIDTH
  - cycle_model.pipeline.RX_PARITY appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_PARITY

### RTL-0133: Implement pipeline stage: RX_STOP1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_STOP1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_STOP1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_STOP1; action=At oversample count 7, sample stop bit. If high → valid. If low → frame_err.; cycle=4+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_STOP1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_STOP1 timing uses SSOT cycle/latency 4+DATA_WIDTH
  - cycle_model.pipeline.RX_STOP1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_STOP1

### RTL-0134: Implement pipeline stage: RX_STOP2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_STOP2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_STOP2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via cycle_model.pipeline.
SSOT item context: stage=RX_STOP2; action=At oversample count 7, sample second stop bit. (present only if stop_bits=1); cycle=5+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_STOP2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - cycle_model.pipeline.RX_STOP2 timing uses SSOT cycle/latency 5+DATA_WIDTH
  - cycle_model.pipeline.RX_STOP2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_STOP2

### RTL-0221: Implement FSM state rx_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_0

### RTL-0222: Implement FSM state rx_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_START_DETECT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_1

### RTL-0223: Implement FSM state rx_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_START_CONFIRM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_2

### RTL-0224: Implement FSM state rx_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_3.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_DATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_3
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_3

### RTL-0225: Implement FSM state rx_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_4.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_PARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_4
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_4

### RTL-0226: Implement FSM state rx_fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_5.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_STOP1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_5
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_5

### RTL-0227: Implement FSM state rx_fsm.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_6.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: value=RX_STOP2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_6
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: fsm.rx_fsm.states.state_6

### RTL-0228: Implement FSM transition rx_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_0.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_IDLE; to=RX_START_DETECT; condition=rx_synced falling edge detected.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_0 condition is implemented as RTL control logic: rx_synced falling edge detected
  - fsm.rx_fsm.transitions.transition_0 transition path RX_IDLE -> RX_START_DETECT is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_0

### RTL-0229: Implement FSM transition rx_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_1.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_START_DETECT; to=RX_START_CONFIRM; condition=mid-bit sample at oversample count 7 confirms low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_1 condition is implemented as RTL control logic: mid-bit sample at oversample count 7 confirms low
  - fsm.rx_fsm.transitions.transition_1 transition path RX_START_DETECT -> RX_START_CONFIRM is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_1

### RTL-0230: Implement FSM transition rx_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_2.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_START_DETECT; to=RX_IDLE; condition=mid-bit sample at oversample count 7 is high (spurious edge).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_2 condition is implemented as RTL control logic: mid-bit sample at oversample count 7 is high (spurious edge)
  - fsm.rx_fsm.transitions.transition_2 transition path RX_START_DETECT -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_2

### RTL-0231: Implement FSM transition rx_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_3.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_START_CONFIRM; to=RX_DATA; condition=full bit period from start confirm; oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_3 condition is implemented as RTL control logic: full bit period from start confirm; oversample tick
  - fsm.rx_fsm.transitions.transition_3 transition path RX_START_CONFIRM -> RX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_3

### RTL-0232: Implement FSM transition rx_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_4.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_DATA; to=RX_PARITY; condition=DATA_WIDTH bits sampled at centre and parity_en=1 and oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_4 condition is implemented as RTL control logic: DATA_WIDTH bits sampled at centre and parity_en=1 and oversample tick
  - fsm.rx_fsm.transitions.transition_4 transition path RX_DATA -> RX_PARITY is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_4

### RTL-0233: Implement FSM transition rx_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_5.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_DATA; to=RX_STOP1; condition=DATA_WIDTH bits sampled at centre and parity_en=0 and oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_5 condition is implemented as RTL control logic: DATA_WIDTH bits sampled at centre and parity_en=0 and oversample tick
  - fsm.rx_fsm.transitions.transition_5 transition path RX_DATA -> RX_STOP1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_5

### RTL-0234: Implement FSM transition rx_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_6.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_PARITY; to=RX_STOP1; condition=parity bit sampled at centre and oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_6 condition is implemented as RTL control logic: parity bit sampled at centre and oversample tick
  - fsm.rx_fsm.transitions.transition_6 transition path RX_PARITY -> RX_STOP1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_6

### RTL-0235: Implement FSM transition rx_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_7.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_STOP1; to=RX_IDLE; condition=stop_bits=0; stop bit sampled high at centre and oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_7 condition is implemented as RTL control logic: stop_bits=0; stop bit sampled high at centre and oversample tick
  - fsm.rx_fsm.transitions.transition_7 transition path RX_STOP1 -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_7

### RTL-0236: Implement FSM transition rx_fsm.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_8.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_STOP1; to=RX_STOP2; condition=stop_bits=1 and oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_8 condition is implemented as RTL control logic: stop_bits=1 and oversample tick
  - fsm.rx_fsm.transitions.transition_8 transition path RX_STOP1 -> RX_STOP2 is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_8

### RTL-0237: Implement FSM transition rx_fsm.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_9.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via fsm.rx_fsm.
SSOT item context: from=RX_STOP2; to=RX_IDLE; condition=oversample tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_9
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
  - fsm.rx_fsm.transitions.transition_9 condition is implemented as RTL control logic: oversample tick
  - fsm.rx_fsm.transitions.transition_9 transition path RX_STOP2 -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_9

### RTL-0264: Prove module uart_lite_rx is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_rx.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_rx.module_equivalence.
Owner: uart_lite_rx in rtl/uart_lite_rx.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_rx.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_rx.sv
- SSOT refs: sub_modules.uart_lite_rx.module_equivalence
