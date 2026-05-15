# RTL Authoring Packet: module__spi_shift__function_model_02

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
- Task count: 13
- Required tasks: 13

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
- Module slice: 2/7 section=function_model task_limit=48
- Slice rule: Owner module spi_shift is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0103: Implement output for FM_APB_RX_POP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_RX_POP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=Returns oldest RX word when FIFO non-empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.outputs.output_0

### RTL-0104: Implement side effect for FM_APB_RX_POP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=RX FIFO occupancy decrements on successful pop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_APB_RX_POP.side_effects.side_effect_0

### RTL-0105: Implement error case for FM_APB_RX_POP: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=RX FIFO empty.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0 condition is implemented as RTL control logic: RX FIFO empty
- SSOT refs: function_model.transactions.FM_APB_RX_POP.error_cases.error_case_0

### RTL-0106: Implement transaction FM_INT_CLEAR

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_INT_CLEAR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_INT_CLEAR.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: id=FM_INT_CLEAR; name=w1c_interrupt_and_status_clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_INT_CLEAR
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_INT_CLEAR

### RTL-0107: Implement precondition for FM_INT_CLEAR: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INT_CLEAR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INT_CLEAR.preconditions.precondition_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=APB write handshake to INT_CLEAR.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INT_CLEAR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_INT_CLEAR.preconditions.precondition_0

### RTL-0108: Implement output for FM_INT_CLEAR: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_INT_CLEAR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INT_CLEAR.outputs.output_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=Selected sticky pending/status bits cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INT_CLEAR.outputs.output_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_INT_CLEAR.outputs.output_0

### RTL-0109: Implement side effect for FM_INT_CLEAR: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_INT_CLEAR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INT_CLEAR.side_effects.side_effect_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: value=FIFO level-derived pending bits remain level-sensitive and unaffected by W1C.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INT_CLEAR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.transactions.FM_INT_CLEAR.side_effects.side_effect_0

### RTL-0110: Implement error case for FM_INT_CLEAR: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_INT_CLEAR.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INT_CLEAR.error_cases.error_case_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.transactions.
SSOT item context: condition=write to read-only register or bad byte strobes.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INT_CLEAR.error_cases.error_case_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - function_model.transactions.FM_INT_CLEAR.error_cases.error_case_0 condition is implemented as RTL control logic: write to read-only register or bad byte strobes
- SSOT refs: function_model.transactions.FM_INT_CLEAR.error_cases.error_case_0

### RTL-0111: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: value=Only one csn_o bit may be active-low during an active frame..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0112: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: value=No frame launch consumes TX FIFO unless all launch preconditions are true..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0113: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: value=irq_o equals OR(INT_PENDING & INT_MASK) at all times..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0114: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: value=sclk_o is a generated output waveform; no internal sequential process is clocked by sclk_o..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0115: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: spi_shift in rtl/spi_shift.sv via function_model.
SSOT item context: value=Sticky bits clear only via reset or INT_CLEAR W1C semantics..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: function_model.invariants.invariant_4
