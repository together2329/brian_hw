# RTL Authoring Packet: module__pwm_gen_cx1__function_model

- Kind: module
- Owner module: pwm_gen_cx1
- Owner file: rtl/pwm_gen_cx1.sv
- Task count: 18
- Required tasks: 18

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
- Owner refs: function_model, function_model.transactions, function_model.transactions.FM_TICK, function_model.transactions.FM_WRITE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 6/18 section=function_model task_limit=48
- Slice rule: Owner module pwm_gen_cx1 is split into 18 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0033: Implement RTL state owner for FL state duty_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.duty_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.duty_reg.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.
SSOT item context: name=duty_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.duty_reg
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - duty_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.duty_reg

### RTL-0034: Implement RTL state owner for FL state counter

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.counter
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.counter.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.
SSOT item context: name=counter; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.counter
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - counter reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.counter

### RTL-0035: Implement transaction FM_WRITE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_WRITE.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: id=FM_WRITE; name=duty_write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_WRITE
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE

### RTL-0036: Implement precondition for FM_WRITE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.preconditions.precondition_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=wr_en == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.preconditions.precondition_0

### RTL-0037: Implement input for FM_WRITE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_WRITE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.inputs.input_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: id=FM_WRITE; name=duty_write; port=["pwm_out"]; signal=["duty_in"]; state=["duty_reg", "counter"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.inputs.input_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - DUT port ["pwm_out"] is the implementation/observation point for duty_write
- SSOT refs: function_model.transactions.FM_WRITE.inputs.input_0

### RTL-0038: Implement output for FM_WRITE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.outputs.output_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=duty_reg updated to duty_in; pwm_out reflects new duty vs current counter.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.outputs.output_0

### RTL-0039: Implement output rule for FM_WRITE: pwm_out_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_WRITE.output_rules.pwm_out_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.output_rules.pwm_out_rule.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=pwm_out_rule; port=pwm_out; expr=1 if counter < duty_in else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.output_rules.pwm_out_rule
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - pwm_out_rule width matches SSOT value 1
  - pwm_out_rule RTL expression implements SSOT expression 1 if counter < duty_in else 0
  - DUT port pwm_out is the implementation/observation point for pwm_out_rule
  - pwm_out_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_WRITE.output_rules.pwm_out_rule

### RTL-0040: Implement state update for FM_WRITE: duty_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WRITE.state_updates.duty_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.state_updates.duty_reg.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=duty_reg; expr=duty_in & 0xff; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.state_updates.duty_reg
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - duty_reg width matches SSOT value 8
  - duty_reg RTL expression implements SSOT expression duty_in & 0xff
  - duty_reg updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WRITE.state_updates.duty_reg

### RTL-0041: Implement state update for FM_WRITE: counter

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WRITE.state_updates.counter
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.state_updates.counter.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=counter; expr=(counter + 1) & 0xff; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.state_updates.counter
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - counter width matches SSOT value 8
  - counter RTL expression implements SSOT expression (counter + 1) & 0xff
  - counter updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WRITE.state_updates.counter

### RTL-0042: Implement side effect for FM_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.side_effects.side_effect_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: id=FM_WRITE; name=duty_write; port=["pwm_out"]; signal=["duty_reg updated"]; state=["duty_reg", "counter"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - DUT port ["pwm_out"] is the implementation/observation point for duty_write
- SSOT refs: function_model.transactions.FM_WRITE.side_effects.side_effect_0

### RTL-0043: Implement transaction FM_TICK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TICK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TICK.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_TICK.
SSOT item context: id=FM_TICK; name=counter_tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TICK
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_TICK

### RTL-0044: Implement precondition for FM_TICK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TICK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.preconditions.precondition_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_TICK.
SSOT item context: value=wr_en == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_TICK.preconditions.precondition_0

### RTL-0045: Implement output for FM_TICK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.outputs.output_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_TICK.
SSOT item context: value=counter increments; pwm_out = (counter < duty_reg).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.outputs.output_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.transactions.FM_TICK.outputs.output_0

### RTL-0046: Implement output rule for FM_TICK: pwm_out_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK.output_rules.pwm_out_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.output_rules.pwm_out_rule.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_TICK.
SSOT item context: name=pwm_out_rule; port=pwm_out; expr=1 if counter < duty_reg else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.output_rules.pwm_out_rule
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - pwm_out_rule width matches SSOT value 1
  - pwm_out_rule RTL expression implements SSOT expression 1 if counter < duty_reg else 0
  - DUT port pwm_out is the implementation/observation point for pwm_out_rule
  - pwm_out_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK.output_rules.pwm_out_rule

### RTL-0047: Implement state update for FM_TICK: counter

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK.state_updates.counter
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.state_updates.counter.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.transactions.FM_TICK.
SSOT item context: name=counter; expr=(counter + 1) & 0xff; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.state_updates.counter
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - counter width matches SSOT value 8
  - counter RTL expression implements SSOT expression (counter + 1) & 0xff
  - counter updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK.state_updates.counter

### RTL-0048: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.
SSOT item context: signal=counter wraps from 255 to 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0049: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.
SSOT item context: port=["pwm_out", "pwm_out"]; signal=pwm_out = (counter_q < duty_reg) combinationally.; state=["duty_reg"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - DUT port ["pwm_out", "pwm_out"] is the implementation/observation point for ["pwm_out", "pwm_out"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0050: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via function_model.
SSOT item context: port=["pwm_out", "pwm_out"]; signal=duty_reg resets to 0 on rst_n low.; state=["duty_reg"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - DUT port ["pwm_out", "pwm_out"] is the implementation/observation point for ["pwm_out", "pwm_out"]
- SSOT refs: function_model.invariants.invariant_2
