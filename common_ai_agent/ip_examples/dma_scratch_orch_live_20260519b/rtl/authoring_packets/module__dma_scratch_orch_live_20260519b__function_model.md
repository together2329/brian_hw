# RTL Authoring Packet: module__dma_scratch_orch_live_20260519b__function_model

- Kind: module
- Owner module: dma_scratch_orch_live_20260519b
- Owner file: rtl/dma_scratch_orch_live_20260519b.sv
- Task count: 44
- Required tasks: 44

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 5/15 section=function_model task_limit=48
- Slice rule: Owner module dma_scratch_orch_live_20260519b is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 21

## Tasks

### RTL-0078: Implement RTL state owner for FL state state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.state.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=state; reset=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.state
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - state reset behavior matches SSOT value IDLE
- SSOT refs: function_model.state_variables.state

### RTL-0079: Implement RTL state owner for FL state error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.error
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.error.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=error; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.error
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - error reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.error

### RTL-0080: Implement RTL state owner for FL state fm1_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fm1_observed
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fm1_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm1_observed; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fm1_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm1_observed width matches SSOT value 1
  - fm1_observed reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fm1_observed

### RTL-0081: Implement RTL state owner for FL state fm2_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fm2_observed
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fm2_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm2_observed; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fm2_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm2_observed width matches SSOT value 1
  - fm2_observed reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fm2_observed

### RTL-0082: Implement RTL state owner for FL state fm3_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fm3_observed
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fm3_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm3_observed; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fm3_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm3_observed width matches SSOT value 1
  - fm3_observed reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fm3_observed

### RTL-0083: Implement RTL state owner for FL state fm4_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fm4_observed
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fm4_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm4_observed; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fm4_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm4_observed width matches SSOT value 1
  - fm4_observed reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fm4_observed

### RTL-0084: Implement transaction FM1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0085: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=Feature trigger is asserted under legal configuration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0086: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=["Inputs described by io_list and dataflow"]; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0087: Implement output for FM1: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=["Architectural output matches feature definition"]; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.outputs.output_0

### RTL-0088: Implement output for FM1: irq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.irq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.irq.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=[{"description": "Auto-injected benign observable rule so the function_model has at least one scoreboard-visible outp...; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.irq
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.outputs.irq

### RTL-0089: Implement output for FM1: fm1_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.fm1_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.fm1_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=[{"description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific a...; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.fm1_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.outputs.fm1_observed

### RTL-0090: Implement output rule for FM1: irq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.irq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.irq.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=irq; port=irq; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.irq
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - irq width matches SSOT value 1
  - irq RTL expression implements SSOT expression 0
  - DUT port irq is the implementation/observation point for irq
  - irq is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.irq

### RTL-0091: Implement state update for FM1: fm1_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.fm1_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.fm1_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm1_observed; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.fm1_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm1_observed width matches SSOT value 1
  - fm1_observed RTL expression implements SSOT expression 1
  - fm1_observed updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.fm1_observed

### RTL-0092: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=["Architectural state updates according to FSM/control policy"]; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0093: Implement error case for FM1: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM1.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.error_cases.error_case_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM1; name=feature_1; port=["irq"]; signal=[{"condition": "Downstream protocol response is non-OKAY or invalid", "result": "Set error status and block signoff u...; state=["fm1_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for feature_1
- SSOT refs: function_model.transactions.FM1.error_cases.error_case_0

### RTL-0094: Implement transaction FM2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0095: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=Feature trigger is asserted under legal configuration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0096: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2; signal=["Inputs described by io_list and dataflow"]; state=["fm2_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0097: Implement output for FM2: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2; signal=["Architectural output matches feature definition"]; state=["fm2_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_0

### RTL-0098: Implement output for FM2: fm2_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.fm2_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.fm2_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2; signal=[{"description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific a...; state=["fm2_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.fm2_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.outputs.fm2_observed

### RTL-0099: Implement state update for FM2: fm2_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.fm2_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.fm2_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm2_observed; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.fm2_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm2_observed width matches SSOT value 1
  - fm2_observed RTL expression implements SSOT expression 1
  - fm2_observed updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.fm2_observed

### RTL-0100: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2; signal=["Architectural state updates according to FSM/control policy"]; state=["fm2_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0101: Implement error case for FM2: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM2.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.error_cases.error_case_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM2; name=feature_2; signal=[{"condition": "Downstream protocol response is non-OKAY or invalid", "result": "Set error status and block signoff u...; state=["fm2_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM2.error_cases.error_case_0

### RTL-0102: Implement transaction FM3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3

### RTL-0103: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=Feature trigger is asserted under legal configuration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0104: Implement input for FM3: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3; signal=["Inputs described by io_list and dataflow"]; state=["fm3_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.inputs.input_0

### RTL-0105: Implement output for FM3: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3; signal=["Architectural output matches feature definition"]; state=["fm3_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_0

### RTL-0106: Implement output for FM3: fm3_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.fm3_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.fm3_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3; signal=[{"description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific a...; state=["fm3_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.fm3_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.outputs.fm3_observed

### RTL-0107: Implement state update for FM3: fm3_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.fm3_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.fm3_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm3_observed; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.fm3_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm3_observed width matches SSOT value 1
  - fm3_observed RTL expression implements SSOT expression 1
  - fm3_observed updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.fm3_observed

### RTL-0108: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3; signal=["Architectural state updates according to FSM/control policy"]; state=["fm3_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0109: Implement error case for FM3: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM3.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.error_cases.error_case_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM3; name=feature_3; signal=[{"condition": "Downstream protocol response is non-OKAY or invalid", "result": "Set error status and block signoff u...; state=["fm3_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM3.error_cases.error_case_0

### RTL-0110: Implement transaction FM4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4

### RTL-0111: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=Feature trigger is asserted under legal configuration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0112: Implement input for FM4: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM4.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.inputs.input_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4; signal=["Inputs described by io_list and dataflow"]; state=["fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.inputs.input_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.inputs.input_0

### RTL-0113: Implement output for FM4: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4; signal=["Architectural output matches feature definition"]; state=["fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_0

### RTL-0114: Implement output for FM4: fm4_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.fm4_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.fm4_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4; signal=[{"description": "Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific a...; state=["fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.fm4_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.outputs.fm4_observed

### RTL-0115: Implement state update for FM4: fm4_observed

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM4.state_updates.fm4_observed
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.state_updates.fm4_observed.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: name=fm4_observed; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.state_updates.fm4_observed
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fm4_observed width matches SSOT value 1
  - fm4_observed RTL expression implements SSOT expression 1
  - fm4_observed updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM4.state_updates.fm4_observed

### RTL-0116: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4; signal=["Architectural state updates according to FSM/control policy"]; state=["fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0117: Implement error case for FM4: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM4.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.error_cases.error_case_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: id=FM4; name=feature_4; signal=[{"condition": "Downstream protocol response is non-OKAY or invalid", "result": "Set error status and block signoff u...; state=["fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: function_model.transactions.FM4.error_cases.error_case_0

### RTL-0118: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: port=["irq"]; signal=No externally visible output changes except through declared interfaces, registers, interrupts, or debug signals.; state=["fm1_observed", "fm2_observed", "fm3_observed", "fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for ["irq"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0119: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: port=["irq"]; signal=All state updates are synchronous to the declared clock and return to reset values under the declared reset policy.; state=["fm1_observed", "fm2_observed", "fm3_observed", "fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for ["irq"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0120: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: port=["irq"]; signal=Every declared error source has a defined architectural effect and recovery path.; state=["state", "error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for ["irq"]
- SSOT refs: function_model.invariants.invariant_2

### RTL-0121: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: port=["irq"]; signal=Data movement and ordering follow the dataflow section without bypassing declared buffers or counters.; state=["fm1_observed", "fm2_observed", "fm3_observed", "fm4_observed"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - DUT port ["irq"] is the implementation/observation point for ["irq"]
- SSOT refs: function_model.invariants.invariant_3
