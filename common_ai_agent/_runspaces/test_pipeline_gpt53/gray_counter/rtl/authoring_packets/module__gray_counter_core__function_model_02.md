# RTL Authoring Packet: module__gray_counter_core__function_model_02

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
- Task count: 10
- Required tasks: 10

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
- LLM-actionable open tasks: 10
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0078: Implement output for GC_TXN_HOLD: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_HOLD.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.outputs.output_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=done == 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.outputs.output_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.outputs.output_2

### RTL-0079: Implement output rule for GC_TXN_HOLD: gray_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_HOLD.output_rules.gray_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.output_rules.gray_hold.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: name=gray_hold; port=gray_value; expr=gray_state; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.output_rules.gray_hold
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - gray_hold width matches SSOT value WIDTH
  - gray_hold RTL expression implements SSOT expression gray_state
  - DUT port gray_value is the implementation/observation point for gray_hold
  - gray_hold is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_HOLD.output_rules.gray_hold

### RTL-0080: Implement output rule for GC_TXN_HOLD: bin_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_HOLD.output_rules.bin_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.output_rules.bin_hold.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: name=bin_hold; port=bin_value; expr=gray_to_bin(gray_state); width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.output_rules.bin_hold
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - bin_hold width matches SSOT value WIDTH
  - bin_hold RTL expression implements SSOT expression gray_to_bin(gray_state)
  - DUT port bin_value is the implementation/observation point for bin_hold
  - bin_hold is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_HOLD.output_rules.bin_hold

### RTL-0081: Implement output rule for GC_TXN_HOLD: done_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_HOLD.output_rules.done_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.output_rules.done_hold.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: name=done_hold; port=done; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.output_rules.done_hold
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - done_hold width matches SSOT value 1
  - done_hold RTL expression implements SSOT expression 0
  - DUT port done is the implementation/observation point for done_hold
  - done_hold is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_HOLD.output_rules.done_hold

### RTL-0082: Implement side effect for GC_TXN_HOLD: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_HOLD.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.side_effects.side_effect_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=done_state forced low in non-wrap hold cycles.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.side_effects.side_effect_0

### RTL-0083: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.
SSOT item context: value=gray_value is always a legal WIDTH-bit Gray encoding of bin_state..
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0084: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.
SSOT item context: value=bin_value always equals gray_to_bin(gray_value) combinationally..
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0085: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.
SSOT item context: value=done is asserted for at most one consecutive cycle per wrap event..
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0086: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.
SSOT item context: value=clear has priority over enable on sampled clock edges..
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0087: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.
SSOT item context: value=reset dominates all synchronous controls when asserted..
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.invariants.invariant_4
