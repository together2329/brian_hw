# RTL Authoring Packet: module__uart_lite_core__function_model_02

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
- Module slice: 2/6 section=function_model task_limit=48
- Slice rule: Owner module uart_lite_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])

## Tasks

### RTL-0103: Implement side effect for FM_LOOPBACK: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Byte circulates: TX FIFO → TX FSM → loopback mux → RX synchronizer → RX FSM → RX FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0

### RTL-0104: Implement side effect for FM_LOOPBACK: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Both bytes_tx and bytes_rx increment.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1

### RTL-0105: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=TX FSM and RX FSM operate independently except for loopback mux sharing..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0106: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Register read side effects are exactly those listed in registers.register_list..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0107: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Sticky error flags (frame_err, parity_err, rx_overrun, tx_underrun, break_detected) latch on first event and hold unt....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0108: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=Debug counters are free-running and do not roll over to affect core function..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0109: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.
SSOT item context: value=FIFO depth is parameter FIFO_DEPTH; writes to full FIFO are ignored; reads from empty FIFO return 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.invariants.invariant_4
