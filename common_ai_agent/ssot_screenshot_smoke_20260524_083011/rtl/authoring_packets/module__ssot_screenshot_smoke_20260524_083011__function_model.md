# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__function_model

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011
- Owner file: rtl/ssot_screenshot_smoke_20260524_083011.sv
- Task count: 41
- Required tasks: 41

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 5/15 section=function_model task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0036: Implement RTL state owner for FL state busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.busy
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.busy.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=busy; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.busy
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - busy reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.busy

### RTL-0037: Implement RTL state owner for FL state error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.error
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.error

### RTL-0038: Implement RTL state owner for FL state accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.accepted_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.accepted_count.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=accepted_count; output=True; width=16; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.accepted_count
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - accepted_count width matches SSOT value 16
  - accepted_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.accepted_count

### RTL-0039: Implement transaction FM_RESET

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RESET.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_RESET; name=reset.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RESET
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_RESET

### RTL-0040: Implement precondition for FM_RESET: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=reset asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_RESET.preconditions.precondition_0

### RTL-0041: Implement input for FM_RESET: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RESET.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.inputs.input_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_RESET; name=reset; port=["accepted_count"]; signal=["clock"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.inputs.input_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["accepted_count"] is the implementation/observation point for reset
- SSOT refs: function_model.transactions.FM_RESET.inputs.input_0

### RTL-0042: Implement input for FM_RESET: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RESET.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.inputs.input_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_RESET; name=reset; port=["accepted_count"]; signal=["reset"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.inputs.input_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["accepted_count"] is the implementation/observation point for reset
- SSOT refs: function_model.transactions.FM_RESET.inputs.input_1

### RTL-0043: Implement output for FM_RESET: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=busy == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_0

### RTL-0044: Implement output for FM_RESET: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=error == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_1

### RTL-0045: Implement output for FM_RESET: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_2.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=registers and counters equal approved reset defaults.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_2
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_2

### RTL-0046: Implement output for FM_RESET: accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.accepted_count.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=accepted_count; port=accepted_count; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.accepted_count
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - accepted_count RTL expression implements SSOT expression 0
  - DUT port accepted_count is the implementation/observation point for accepted_count
- SSOT refs: function_model.transactions.FM_RESET.outputs.accepted_count

### RTL-0047: Implement output rule for FM_RESET: accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.accepted_count.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=accepted_count; port=accepted_count; expr=0; width=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.accepted_count
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - accepted_count width matches SSOT value 16
  - accepted_count RTL expression implements SSOT expression 0
  - DUT port accepted_count is the implementation/observation point for accepted_count
  - accepted_count is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.accepted_count

### RTL-0048: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_RESET; name=reset; port=["accepted_count"]; signal=["clears transient protocol state"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["accepted_count"] is the implementation/observation point for reset
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0049: Implement side effect for FM_RESET: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_RESET; name=reset; port=["accepted_count"]; signal=["clears pending non-retained status"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["accepted_count"] is the implementation/observation point for reset
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_1

### RTL-0050: Implement transaction FM_PRIMARY

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PRIMARY
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PRIMARY.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_PRIMARY; name=primary_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_PRIMARY

### RTL-0051: Implement precondition for FM_PRIMARY: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=valid input transaction or packet is accepted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.preconditions.precondition_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.preconditions.precondition_0

### RTL-0052: Implement input for FM_PRIMARY: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_PRIMARY.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.inputs.input_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["busy", "error"]; signal=["external interface signals"]; state=["busy"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.inputs.input_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["busy", "error"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.inputs.input_0

### RTL-0053: Implement input for FM_PRIMARY: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_PRIMARY.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.inputs.input_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["busy", "error"]; signal=["configuration/register state"]; state=["busy"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.inputs.input_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["busy", "error"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.inputs.input_1

### RTL-0054: Implement output for FM_PRIMARY: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=Accept one byte-oriented valid-ready transaction when valid and ready are high; output result equals data_in XOR comm....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_0

### RTL-0055: Implement output for FM_PRIMARY: busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.busy.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=busy; port=busy; expr=busy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.busy
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - busy RTL expression implements SSOT expression busy
  - DUT port busy is the implementation/observation point for busy
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.busy

### RTL-0056: Implement output for FM_PRIMARY: error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; port=error; expr=error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error RTL expression implements SSOT expression error
  - DUT port error is the implementation/observation point for error
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.error

### RTL-0057: Implement output rule for FM_PRIMARY: busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.busy.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=busy; port=busy; expr=busy; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.busy
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - busy width matches SSOT value 1
  - busy RTL expression implements SSOT expression busy
  - DUT port busy is the implementation/observation point for busy
  - busy is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.busy

### RTL-0058: Implement output rule for FM_PRIMARY: error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; port=error; expr=error; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error width matches SSOT value 1
  - error RTL expression implements SSOT expression error
  - DUT port error is the implementation/observation point for error
  - error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.error

### RTL-0059: Implement state update for FM_PRIMARY: busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PRIMARY.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.state_updates.busy.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=busy; expr=1; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.state_updates.busy
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
  - busy RTL expression implements SSOT expression 1
  - busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PRIMARY.state_updates.busy

### RTL-0060: Implement side effect for FM_PRIMARY: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["busy", "error"]; signal=["updates status, counters, events, and observable outputs according to approved Q&A"]; state=["busy"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["busy", "error"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0

### RTL-0061: Implement error case for FM_PRIMARY: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PRIMARY.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.error_cases.error_case_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["busy", "error"]; signal=[{"condition": "malformed input or invalid control policy", "result": "error status follows error_handling section"}]; state=["busy"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.error_cases.error_case_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["busy", "error"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.error_cases.error_case_0

### RTL-0062: Implement transaction FM_CSR

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_CSR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_CSR.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_CSR
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_CSR

### RTL-0063: Implement precondition for FM_CSR: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CSR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.preconditions.precondition_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=firmware/control bus access is accepted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_CSR.preconditions.precondition_0

### RTL-0064: Implement input for FM_CSR: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CSR.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.inputs.input_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=["address"]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.inputs.input_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.inputs.input_0

### RTL-0065: Implement input for FM_CSR: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CSR.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.inputs.input_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=["write data"]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.inputs.input_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.inputs.input_1

### RTL-0066: Implement input for FM_CSR: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CSR.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.inputs.input_2.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=["write enable"]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.inputs.input_2
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.inputs.input_2

### RTL-0067: Implement input for FM_CSR: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CSR.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.inputs.input_3.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=["byte strobes"]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.inputs.input_3
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.inputs.input_3

### RTL-0068: Implement output for FM_CSR: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CSR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.outputs.output_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: value=read data and side effects match registers.register_list.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.outputs.output_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.transactions.FM_CSR.outputs.output_0

### RTL-0069: Implement output for FM_CSR: error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CSR.outputs.error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.outputs.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; port=error; expr=error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.outputs.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error RTL expression implements SSOT expression error
  - DUT port error is the implementation/observation point for error
- SSOT refs: function_model.transactions.FM_CSR.outputs.error

### RTL-0070: Implement output rule for FM_CSR: error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CSR.output_rules.error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.output_rules.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; port=error; expr=error; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.output_rules.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error width matches SSOT value 1
  - error RTL expression implements SSOT expression error
  - DUT port error is the implementation/observation point for error
  - error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CSR.output_rules.error

### RTL-0071: Implement state update for FM_CSR: error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CSR.state_updates.error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.state_updates.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=error; expr=error; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.state_updates.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error width matches SSOT value 1
  - error reset behavior matches SSOT value 0
  - error RTL expression implements SSOT expression error
  - error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CSR.state_updates.error

### RTL-0072: Implement side effect for FM_CSR: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CSR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.side_effects.side_effect_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=["RW and W1C fields update exactly as specified"]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.side_effects.side_effect_0

### RTL-0073: Implement error case for FM_CSR: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_CSR.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CSR.error_cases.error_case_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=FM_CSR; name=control_status_access; port=["error"]; signal=[{"condition": "unsupported address or illegal access", "result": "bus error/status error according to error_handling"}]; state=["error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CSR.error_cases.error_case_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["error"] is the implementation/observation point for control_status_access
- SSOT refs: function_model.transactions.FM_CSR.error_cases.error_case_0

### RTL-0074: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: port=["accepted_count", "busy", "error", "error"]; signal=No output, counter, status bit, or interrupt may change except as a consequence of an approved transaction, event, re...; state=["busy", "accepted_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - DUT port ["accepted_count", "busy", "error", "error"] is the implementation/observation point for ["accepted_count", "busy", "error", "error"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0075: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: signal=The function_model is the scoreboard source of truth for tb-gen.; state=["accepted_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0076: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: signal=Any behavior not represented here must be escalated to ssot-gen before RTL signoff..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: function_model.invariants.invariant_2
