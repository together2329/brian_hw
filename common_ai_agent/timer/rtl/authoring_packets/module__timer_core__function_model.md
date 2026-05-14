# RTL Authoring Packet: module__timer_core__function_model

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
- Task count: 23
- Required tasks: 23

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 5/17 section=function_model task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0033: Implement RTL state owner for FL state count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.count_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.count_q.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: name=count_q; width=16; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.count_q
  - Primary implementation evidence is in rtl/timer.sv
  - count_q width matches SSOT value 16
  - count_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.count_q

### RTL-0034: Implement RTL state owner for FL state running_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.running_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.running_q.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: name=running_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.running_q
  - Primary implementation evidence is in rtl/timer.sv
  - running_q width matches SSOT value 1
  - running_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.running_q

### RTL-0035: Implement RTL state owner for FL state done_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.done_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.done_q.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: name=done_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.done_q
  - Primary implementation evidence is in rtl/timer.sv
  - done_q width matches SSOT value 1
  - done_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.done_q

### RTL-0036: Implement transaction FM_TICK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TICK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TICK.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: id=FM_TICK; name=timer_control_tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TICK
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK

### RTL-0037: Implement precondition for FM_TICK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TICK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.preconditions.precondition_0.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=rst_n is deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.preconditions.precondition_0

### RTL-0038: Implement precondition for FM_TICK: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TICK.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.preconditions.precondition_1.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=load is in the range 0 to 2**COUNT_WIDTH-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.preconditions.precondition_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.preconditions.precondition_1

### RTL-0039: Implement output for FM_TICK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.outputs.output_0.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=count.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.outputs.output_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.outputs.output_0

### RTL-0040: Implement output for FM_TICK: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.outputs.output_1.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=running.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.outputs.output_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.outputs.output_1

### RTL-0041: Implement output for FM_TICK: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_TICK.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.outputs.output_2.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=done.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.outputs.output_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.outputs.output_2

### RTL-0042: Implement output rule for FM_TICK: count_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK.output_rules.count_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.output_rules.count_next.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=count_next; port=count; expr=0 if clear else (load if start else ((count_q - 1) if (enable and running_q and (count_q > 0)) else count_q)); width=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.output_rules.count_next
  - Primary implementation evidence is in rtl/timer.sv
  - count_next width matches SSOT value 16
  - count_next RTL expression implements SSOT expression 0 if clear else (load if start else ((count_q - 1) if (enable and running_q and (count_q > 0)) else count_q))
  - DUT port count is the implementation/observation point for count_next
  - count_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK.output_rules.count_next

### RTL-0043: Implement output rule for FM_TICK: running_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK.output_rules.running_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.output_rules.running_next.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=running_next; port=running; expr=0 if clear else ((load > 0) if start else (0 if (enable and running_q and (count_q <= 1)) else running_q)); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.output_rules.running_next
  - Primary implementation evidence is in rtl/timer.sv
  - running_next width matches SSOT value 1
  - running_next RTL expression implements SSOT expression 0 if clear else ((load > 0) if start else (0 if (enable and running_q and (count_q <= 1)) else running_q))
  - DUT port running is the implementation/observation point for running_next
  - running_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK.output_rules.running_next

### RTL-0044: Implement output rule for FM_TICK: done_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TICK.output_rules.done_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.output_rules.done_pulse.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=done_pulse; port=done; expr=0 if clear else (0 if start else (1 if (enable and running_q and (count_q == 1)) else 0)); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.output_rules.done_pulse
  - Primary implementation evidence is in rtl/timer.sv
  - done_pulse width matches SSOT value 1
  - done_pulse RTL expression implements SSOT expression 0 if clear else (0 if start else (1 if (enable and running_q and (count_q == 1)) else 0))
  - DUT port done is the implementation/observation point for done_pulse
  - done_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TICK.output_rules.done_pulse

### RTL-0045: Implement state update for FM_TICK: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.state_updates.count_q.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=count_q; expr=0 if clear else (load if start else ((count_q - 1) if (enable and running_q and (count_q > 0)) else count_q)); width=16; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.state_updates.count_q
  - Primary implementation evidence is in rtl/timer.sv
  - count_q width matches SSOT value 16
  - count_q reset behavior matches SSOT value 0
  - count_q RTL expression implements SSOT expression 0 if clear else (load if start else ((count_q - 1) if (enable and running_q and (count_q > 0)) else count_q))
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK.state_updates.count_q

### RTL-0046: Implement state update for FM_TICK: running_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK.state_updates.running_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.state_updates.running_q.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=running_q; expr=0 if clear else ((load > 0) if start else (0 if (enable and running_q and (count_q <= 1)) else running_q)); width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.state_updates.running_q
  - Primary implementation evidence is in rtl/timer.sv
  - running_q width matches SSOT value 1
  - running_q reset behavior matches SSOT value 0
  - running_q RTL expression implements SSOT expression 0 if clear else ((load > 0) if start else (0 if (enable and running_q and (count_q <= 1)) else running_q))
  - running_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK.state_updates.running_q

### RTL-0047: Implement state update for FM_TICK: done_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_TICK.state_updates.done_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.state_updates.done_q.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: name=done_q; expr=0 if clear else (0 if start else (1 if (enable and running_q and (count_q == 1)) else 0)); width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.state_updates.done_q
  - Primary implementation evidence is in rtl/timer.sv
  - done_q width matches SSOT value 1
  - done_q reset behavior matches SSOT value 0
  - done_q RTL expression implements SSOT expression 0 if clear else (0 if start else (1 if (enable and running_q and (count_q == 1)) else 0))
  - done_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_TICK.state_updates.done_q

### RTL-0048: Implement side effect for FM_TICK: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.side_effects.side_effect_0.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=count updates according to start, clear, and enable priority..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.side_effects.side_effect_0

### RTL-0049: Implement side effect for FM_TICK: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.side_effects.side_effect_1.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=running drops when the countdown consumes the final count..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.side_effects.side_effect_1

### RTL-0050: Implement side effect for FM_TICK: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TICK.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.side_effects.side_effect_2.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=done pulses for the terminal countdown tick..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.side_effects.side_effect_2

### RTL-0051: Implement error case for FM_TICK: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_TICK.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TICK.error_cases.error_case_0.
Owner: timer_core in rtl/timer.sv via function_model.transactions.FM_TICK.
SSOT item context: value=No protocol error is generated; out-of-range load values are impossible after port truncation..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TICK.error_cases.error_case_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.transactions.FM_TICK.error_cases.error_case_0

### RTL-0052: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: value=Reset or clear leaves count=0, running=0, and done=0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0053: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: value=done is asserted only on a terminal enabled countdown tick..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0054: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: value=count never underflows below zero because the decrement rule is gated by count > 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0055: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: timer_core in rtl/timer.sv via function_model.
SSOT item context: value=When enable is low and no start or clear is asserted, count and running hold their previous values..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: function_model.invariants.invariant_3
