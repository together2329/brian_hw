# RTL Authoring Packet: module__simple_pwm__function_model

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 28
- Required tasks: 28

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
- LLM-actionable open tasks: 28
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 5/14 section=function_model task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0029: Implement RTL state owner for FL state counter

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.counter
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.counter.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter; reset=0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.counter
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.counter

### RTL-0030: Implement transaction FM1

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0031: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0032: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=counter < duty_cycle.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0033: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["duty_cycle"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0034: Implement input for FM1: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["period"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.inputs.input_1

### RTL-0035: Implement output for FM1: pwm_out

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.pwm_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=[{"name": "pwm_out", "value": 1}]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.outputs.pwm_out

### RTL-0036: Implement output rule for FM1: pwm_out_high

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.pwm_out_high
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.pwm_out_high.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=pwm_out_high; port=pwm_out; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.pwm_out_high
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - pwm_out_high width matches SSOT value 1
  - pwm_out_high RTL expression implements SSOT expression 1
  - DUT port pwm_out is the implementation/observation point for pwm_out_high
  - pwm_out_high is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.pwm_out_high

### RTL-0037: Implement state update for FM1: counter_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.counter_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.counter_next.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter_next; expr=counter + 1 if (counter + 1) < period else 0; width=COUNTER_WIDTH.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.counter_next
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter_next width matches SSOT value COUNTER_WIDTH
  - counter_next RTL expression implements SSOT expression counter + 1 if (counter + 1) < period else 0
  - counter_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.counter_next

### RTL-0038: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM1; name=pwm_active_high; port=["pwm_out"]; signal=["counter increments by 1"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_high
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0039: Implement transaction FM2

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0040: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0041: Implement precondition for FM2: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=counter >= duty_cycle.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_1

### RTL-0042: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low; port=["pwm_out"]; signal=["duty_cycle"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_low
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0043: Implement input for FM2: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low; port=["pwm_out"]; signal=["period"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_low
- SSOT refs: function_model.transactions.FM2.inputs.input_1

### RTL-0044: Implement output for FM2: pwm_out

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.pwm_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low; port=["pwm_out"]; signal=[{"name": "pwm_out", "value": 0}]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_low
- SSOT refs: function_model.transactions.FM2.outputs.pwm_out

### RTL-0045: Implement output rule for FM2: pwm_out_low

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.pwm_out_low
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.pwm_out_low.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=pwm_out_low; port=pwm_out; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.pwm_out_low
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - pwm_out_low width matches SSOT value 1
  - pwm_out_low RTL expression implements SSOT expression 0
  - DUT port pwm_out is the implementation/observation point for pwm_out_low
  - pwm_out_low is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.pwm_out_low

### RTL-0046: Implement state update for FM2: counter_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.counter_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.counter_next.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter_next; expr=counter + 1 if (counter + 1) < period else 0; width=COUNTER_WIDTH.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.counter_next
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter_next width matches SSOT value COUNTER_WIDTH
  - counter_next RTL expression implements SSOT expression counter + 1 if (counter + 1) < period else 0
  - counter_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.counter_next

### RTL-0047: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM2; name=pwm_active_low; port=["pwm_out"]; signal=["counter increments by 1"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_active_low
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0048: Implement transaction FM3

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM3; name=pwm_idle.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM3

### RTL-0049: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: value=enable == 0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0050: Implement output for FM3: pwm_out

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.pwm_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM3; name=pwm_idle; port=["pwm_out"]; signal=[{"name": "pwm_out", "value": 0}]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_idle
- SSOT refs: function_model.transactions.FM3.outputs.pwm_out

### RTL-0051: Implement output rule for FM3: pwm_out_off

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.pwm_out_off
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.pwm_out_off.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=pwm_out_off; port=pwm_out; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.pwm_out_off
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - pwm_out_off width matches SSOT value 1
  - pwm_out_off RTL expression implements SSOT expression 0
  - DUT port pwm_out is the implementation/observation point for pwm_out_off
  - pwm_out_off is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3.output_rules.pwm_out_off

### RTL-0052: Implement state update for FM3: counter_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.counter_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.counter_next.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: name=counter_next; expr=0; width=COUNTER_WIDTH.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.counter_next
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - counter_next width matches SSOT value COUNTER_WIDTH
  - counter_next RTL expression implements SSOT expression 0
  - counter_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.counter_next

### RTL-0053: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: id=FM3; name=pwm_idle; port=["pwm_out"]; signal=["counter resets to 0"]; state=["counter_next"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out"] is the implementation/observation point for pwm_idle
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0054: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: port=["pwm_out", "pwm_out", "pwm_out"]; signal=pwm_out is 0 whenever enable is 0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out", "pwm_out", "pwm_out"] is the implementation/observation point for ["pwm_out", "pwm_out", "pwm_out"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0055: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: port=["pwm_out", "pwm_out", "pwm_out"]; signal=counter resets to 0 when it reaches period; state=["counter"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out", "pwm_out", "pwm_out"] is the implementation/observation point for ["pwm_out", "pwm_out", "pwm_out"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0056: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: simple_pwm in rtl/simple_pwm.sv via function_model.
SSOT item context: port=["pwm_out", "pwm_out", "pwm_out"]; signal=counter is 0 whenever enable is 0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - DUT port ["pwm_out", "pwm_out", "pwm_out"] is the implementation/observation point for ["pwm_out", "pwm_out", "pwm_out"]
- SSOT refs: function_model.invariants.invariant_2
