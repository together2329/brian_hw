# RTL Authoring Packet: module__debounce_cx1__function_model

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 23
- Required tasks: 23

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 23
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 6/17 section=function_model task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0032: Implement RTL state owner for FL state fl_ctr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fl_ctr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fl_ctr.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.state_variables.
SSOT item context: name=fl_ctr; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fl_ctr
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_ctr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fl_ctr

### RTL-0033: Implement RTL state owner for FL state fl_last

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fl_last
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fl_last.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.state_variables.
SSOT item context: name=fl_last; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fl_last
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_last reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fl_last

### RTL-0034: Implement RTL state owner for FL state fl_db

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fl_db
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fl_db.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.state_variables.
SSOT item context: name=fl_db; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fl_db
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_db reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fl_db

### RTL-0035: Implement transaction FM_STABLE

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_STABLE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_STABLE.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: id=FM_STABLE; name=stable_tick.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_STABLE
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE

### RTL-0036: Implement precondition for FM_STABLE: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_STABLE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.preconditions.precondition_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: value=btn_in == fl_last.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE.preconditions.precondition_0

### RTL-0037: Implement input for FM_STABLE: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_STABLE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.inputs.input_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: id=FM_STABLE; name=stable_tick; port=["db_out"]; signal=["btn_in"]; state=["fl_ctr", "fl_last", "fl_db"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.inputs.input_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out"] is the implementation/observation point for stable_tick
- SSOT refs: function_model.transactions.FM_STABLE.inputs.input_0

### RTL-0038: Implement output for FM_STABLE: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_STABLE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.outputs.output_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: value=fl_ctr increments; if fl_ctr+1 >= THRESH then fl_db = btn_in.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.outputs.output_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE.outputs.output_0

### RTL-0039: Implement output rule for FM_STABLE: db_out_rule

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_STABLE.output_rules.db_out_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.output_rules.db_out_rule.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=db_out_rule; port=db_out; expr=fl_db; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.output_rules.db_out_rule
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - db_out_rule width matches SSOT value 1
  - db_out_rule RTL expression implements SSOT expression fl_db
  - DUT port db_out is the implementation/observation point for db_out_rule
  - db_out_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_STABLE.output_rules.db_out_rule

### RTL-0040: Implement state update for FM_STABLE: fl_ctr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.fl_ctr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.fl_ctr.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=fl_ctr; expr=(fl_ctr + 1) if fl_ctr < 255 else 255; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.fl_ctr
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_ctr width matches SSOT value 8
  - fl_ctr RTL expression implements SSOT expression (fl_ctr + 1) if fl_ctr < 255 else 255
  - fl_ctr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.fl_ctr

### RTL-0041: Implement state update for FM_STABLE: fl_last

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.fl_last
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.fl_last.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=fl_last; expr=btn_in & 1; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.fl_last
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_last width matches SSOT value 1
  - fl_last RTL expression implements SSOT expression btn_in & 1
  - fl_last updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.fl_last

### RTL-0042: Implement state update for FM_STABLE: fl_db

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.fl_db
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.fl_db.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=fl_db; expr=btn_in if (fl_ctr + 1) >= 4 else fl_db; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.fl_db
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_db width matches SSOT value 1
  - fl_db RTL expression implements SSOT expression btn_in if (fl_ctr + 1) >= 4 else fl_db
  - fl_db updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.fl_db

### RTL-0043: Implement side effect for FM_STABLE: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_STABLE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.side_effects.side_effect_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: id=FM_STABLE; name=stable_tick; port=["db_out"]; signal=["fl_db updates when threshold reached"]; state=["fl_ctr", "fl_last", "fl_db"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out"] is the implementation/observation point for stable_tick
- SSOT refs: function_model.transactions.FM_STABLE.side_effects.side_effect_0

### RTL-0044: Implement transaction FM_BOUNCE

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_BOUNCE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_BOUNCE.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: id=FM_BOUNCE; name=bounce_tick.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_BOUNCE

### RTL-0045: Implement precondition for FM_BOUNCE: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_BOUNCE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.preconditions.precondition_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: value=btn_in != fl_last.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_BOUNCE.preconditions.precondition_0

### RTL-0046: Implement input for FM_BOUNCE: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_BOUNCE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.inputs.input_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: id=FM_BOUNCE; name=bounce_tick; port=["db_out"]; signal=["btn_in"]; state=["fl_ctr", "fl_last", "fl_db"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.inputs.input_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out"] is the implementation/observation point for bounce_tick
- SSOT refs: function_model.transactions.FM_BOUNCE.inputs.input_0

### RTL-0047: Implement output for FM_BOUNCE: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_BOUNCE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.outputs.output_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: value=fl_ctr resets to 0; fl_last updates; fl_db unchanged.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.outputs.output_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: function_model.transactions.FM_BOUNCE.outputs.output_0

### RTL-0048: Implement output rule for FM_BOUNCE: db_out_rule

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_BOUNCE.output_rules.db_out_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.output_rules.db_out_rule.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: name=db_out_rule; port=db_out; expr=fl_db; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.output_rules.db_out_rule
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - db_out_rule width matches SSOT value 1
  - db_out_rule RTL expression implements SSOT expression fl_db
  - DUT port db_out is the implementation/observation point for db_out_rule
  - db_out_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_BOUNCE.output_rules.db_out_rule

### RTL-0049: Implement state update for FM_BOUNCE: fl_ctr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_BOUNCE.state_updates.fl_ctr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.state_updates.fl_ctr.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: name=fl_ctr; expr=0; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.state_updates.fl_ctr
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_ctr width matches SSOT value 8
  - fl_ctr RTL expression implements SSOT expression 0
  - fl_ctr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_BOUNCE.state_updates.fl_ctr

### RTL-0050: Implement state update for FM_BOUNCE: fl_last

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_BOUNCE.state_updates.fl_last
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.state_updates.fl_last.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: name=fl_last; expr=btn_in & 1; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.state_updates.fl_last
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_last width matches SSOT value 1
  - fl_last RTL expression implements SSOT expression btn_in & 1
  - fl_last updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_BOUNCE.state_updates.fl_last

### RTL-0051: Implement state update for FM_BOUNCE: fl_db

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_BOUNCE.state_updates.fl_db
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BOUNCE.state_updates.fl_db.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.transactions.FM_BOUNCE.
SSOT item context: name=fl_db; expr=fl_db; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BOUNCE.state_updates.fl_db
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - fl_db width matches SSOT value 1
  - fl_db RTL expression implements SSOT expression fl_db
  - fl_db updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_BOUNCE.state_updates.fl_db

### RTL-0052: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.
SSOT item context: port=["db_out", "db_out"]; signal=fl_ctr resets to 0 whenever btn_in changes.; state=["fl_ctr", "fl_last"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out", "db_out"] is the implementation/observation point for ["db_out", "db_out"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0053: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.
SSOT item context: port=["db_out", "db_out"]; signal=db_out updates only after THRESH stable cycles.; state=["fl_ctr", "fl_db"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out", "db_out"] is the implementation/observation point for ["db_out", "db_out"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0054: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via function_model.
SSOT item context: port=["db_out", "db_out"]; signal=db_out resets to 0 on rst_n low.; state=["fl_db"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - DUT port ["db_out", "db_out"] is the implementation/observation point for ["db_out", "db_out"]
- SSOT refs: function_model.invariants.invariant_2
