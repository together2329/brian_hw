# RTL Authoring Packet: module__gray_code_cx1__function_model

- Kind: module
- Owner module: gray_code_cx1
- Owner file: rtl/gray_code_cx1.sv
- Task count: 9
- Required tasks: 9

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_PRIMARY, io_list, rtl_contract, test_requirements
- Module slice: 5/11 section=function_model task_limit=48
- Slice rule: Owner module gray_code_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_code_cx1.clk <= clk (integration.connections[0])
  - gray_code_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0035: Implement transaction FM_PRIMARY

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PRIMARY
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PRIMARY.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: id=FM_PRIMARY; name=primary_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: function_model.transactions.FM_PRIMARY

### RTL-0036: Implement precondition for FM_PRIMARY: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=rst_n is deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.preconditions.precondition_0

### RTL-0037: Implement precondition for FM_PRIMARY: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_1.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=valid is high.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.preconditions.precondition_1

### RTL-0038: Implement output for FM_PRIMARY: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_0.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=gray_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_0
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_0

### RTL-0039: Implement output for FM_PRIMARY: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_1.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=bin_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_1
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_1

### RTL-0040: Implement output rule for FM_PRIMARY: gray_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.gray_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.gray_out.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: name=gray_out; port=gray_out; expr=bin_in ^ (bin_in >> 1); width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.gray_out
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - gray_out width matches SSOT value 4
  - gray_out RTL expression implements SSOT expression bin_in ^ (bin_in >> 1)
  - DUT port gray_out is the implementation/observation point for gray_out
  - gray_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.gray_out

### RTL-0041: Implement output rule for FM_PRIMARY: bin_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.bin_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.bin_out.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: name=bin_out; port=bin_out; expr=gray_in ^ (gray_in >> 1) ^ (gray_in >> 2) ^ (gray_in >> 3); width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.bin_out
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - bin_out width matches SSOT value 4
  - bin_out RTL expression implements SSOT expression gray_in ^ (gray_in >> 1) ^ (gray_in >> 2) ^ (gray_in >> 3)
  - DUT port bin_out is the implementation/observation point for bin_out
  - bin_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.bin_out

### RTL-0042: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.
SSOT item context: port=["bin_in", "gray_in", "gray_out", "bin_out"]; signal=gray_out is always the XOR-folded encoding of bin_in..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - DUT port ["bin_in", "gray_in", "gray_out", "bin_out"] is the implementation/observation point for ["bin_in", "gray_in", "gray_out", "bin_out"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0043: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via function_model.
SSOT item context: port=["bin_in", "gray_in", "gray_out", "bin_out"]; signal=bin_out is always the cascaded XOR decoding of gray_in..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - DUT port ["bin_in", "gray_in", "gray_out", "bin_out"] is the implementation/observation point for ["bin_in", "gray_in", "gray_out", "bin_out"]
- SSOT refs: function_model.invariants.invariant_1
