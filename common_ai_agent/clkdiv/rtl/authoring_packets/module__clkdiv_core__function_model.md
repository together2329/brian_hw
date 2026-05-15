# RTL Authoring Packet: module__clkdiv_core__function_model

- Kind: module
- Owner module: clkdiv_core
- Owner file: rtl/clkdiv_core.sv
- Task count: 30
- Required tasks: 30

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
- LLM-actionable open tasks: 30
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow, dataflow.clock_path, dataflow.control_path, fsm, fsm.divider_fsm, function_model, function_model.state_variables, function_model.transactions.FM_DIVIDE
- Module slice: 1/5 section=function_model task_limit=48
- Slice rule: Owner module clkdiv_core is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - clkdiv_core.clk_i <= clk_i (sub_modules[1].connections[0])
  - clkdiv_core.rst_ni <= rst_ni (sub_modules[1].connections[1])
  - clkdiv_core.enable_i <= enable (sub_modules[1].connections[2])
  - clkdiv_core.divisor_i <= active_divisor (sub_modules[1].connections[3])
  - clkdiv_core.clk_o <= clk_o (sub_modules[1].connections[4])
  - clkdiv_core.locked_o <= locked_o (sub_modules[1].connections[5])
  - clkdiv_core.terminal_event_o <= terminal_event (sub_modules[1].connections[6])
  - clkdiv_core.clk_i <= clk_i (integration.connections[11])
  - clkdiv_core.rst_ni <= rst_ni (integration.connections[12])
  - clkdiv_core.enable_i <= enable (integration.connections[13])
  - clkdiv_core.divisor_i <= active_divisor (integration.connections[14])
  - clkdiv_core.clk_o <= clk_o (integration.connections[15])

## Tasks

### RTL-0047: Implement RTL state owner for FL state enable

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.enable.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=enable; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.enable
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - enable reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.enable

### RTL-0048: Implement RTL state owner for FL state pending_divisor

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pending_divisor
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pending_divisor.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=pending_divisor; reset=2.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pending_divisor
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - pending_divisor reset behavior matches SSOT value 2
- SSOT refs: function_model.state_variables.pending_divisor

### RTL-0049: Implement RTL state owner for FL state active_divisor

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.active_divisor
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.active_divisor.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=active_divisor; reset=2.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.active_divisor
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - active_divisor reset behavior matches SSOT value 2
- SSOT refs: function_model.state_variables.active_divisor

### RTL-0050: Implement RTL state owner for FL state counter

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.counter
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.counter.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=counter; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.counter
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - counter reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.counter

### RTL-0051: Implement RTL state owner for FL state clk_state

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.clk_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.clk_state.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=clk_state; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.clk_state
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - clk_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.clk_state

### RTL-0052: Implement RTL state owner for FL state irq_pending

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.irq_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.irq_pending.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.state_variables.
SSOT item context: name=irq_pending; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.irq_pending
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - irq_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.irq_pending

### RTL-0053: Implement transaction FM_DIVIDE

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DIVIDE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DIVIDE.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: id=FM_DIVIDE; name=integer_clock_divide.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE

### RTL-0054: Implement precondition for FM_DIVIDE: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=rst_ni is deasserted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.preconditions.precondition_0

### RTL-0055: Implement precondition for FM_DIVIDE: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=CTRL.enable == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.preconditions.precondition_1

### RTL-0056: Implement precondition for FM_DIVIDE: precondition_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.preconditions.precondition_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=active_divisor >= 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.preconditions.precondition_2

### RTL-0057: Implement input for FM_DIVIDE: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_DIVIDE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.inputs.input_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=clk_i rising edge.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.inputs.input_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.inputs.input_0

### RTL-0058: Implement input for FM_DIVIDE: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_DIVIDE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.inputs.input_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=active_divisor.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.inputs.input_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.inputs.input_1

### RTL-0059: Implement input for FM_DIVIDE: input_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_DIVIDE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.inputs.input_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=CTRL.irq_enable.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.inputs.input_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.inputs.input_2

### RTL-0060: Implement output for FM_DIVIDE: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DIVIDE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.outputs.output_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=clk_o toggles exactly when counter reaches active_divisor-1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.outputs.output_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.outputs.output_0

### RTL-0061: Implement output for FM_DIVIDE: output_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DIVIDE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.outputs.output_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=locked_o is 1 after the first terminal reload while enabled.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.outputs.output_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.outputs.output_1

### RTL-0062: Implement output for FM_DIVIDE: output_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DIVIDE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.outputs.output_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=irq_o is 1 when irq_pending and CTRL.irq_enable are both 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.outputs.output_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.outputs.output_2

### RTL-0063: Implement output rule for FM_DIVIDE: divided_clock

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DIVIDE.output_rules.divided_clock
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.output_rules.divided_clock.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: name=divided_clock; port=clk_o; expr=((~clk_state) & 1) if terminal_count else clk_state; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.output_rules.divided_clock
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - divided_clock width matches SSOT value 1
  - divided_clock RTL expression implements SSOT expression ((~clk_state) & 1) if terminal_count else clk_state
  - DUT port clk_o is the implementation/observation point for divided_clock
  - divided_clock is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DIVIDE.output_rules.divided_clock

### RTL-0064: Implement output rule for FM_DIVIDE: lock_indicator

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DIVIDE.output_rules.lock_indicator
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.output_rules.lock_indicator.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: name=lock_indicator; port=locked_o; expr=1 if enable and first_reload_seen else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.output_rules.lock_indicator
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - lock_indicator width matches SSOT value 1
  - lock_indicator RTL expression implements SSOT expression 1 if enable and first_reload_seen else 0
  - DUT port locked_o is the implementation/observation point for lock_indicator
  - lock_indicator is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DIVIDE.output_rules.lock_indicator

### RTL-0065: Implement output rule for FM_DIVIDE: interrupt

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DIVIDE.output_rules.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.output_rules.interrupt.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: name=interrupt; port=irq_o; expr=1 if irq_pending and irq_enable else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.output_rules.interrupt
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - interrupt width matches SSOT value 1
  - interrupt RTL expression implements SSOT expression 1 if irq_pending and irq_enable else 0
  - DUT port irq_o is the implementation/observation point for interrupt
  - interrupt is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DIVIDE.output_rules.interrupt

### RTL-0066: Implement side effect for FM_DIVIDE: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=If counter == active_divisor-1, counter resets to 0 and clk_state toggles..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.side_effects.side_effect_0

### RTL-0067: Implement side effect for FM_DIVIDE: side_effect_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=If counter != active_divisor-1, counter increments by one and clk_state is stable..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.side_effects.side_effect_1

### RTL-0068: Implement side effect for FM_DIVIDE: side_effect_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=At terminal count, active_divisor loads pending_divisor for the next half-period..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.side_effects.side_effect_2

### RTL-0069: Implement side effect for FM_DIVIDE: side_effect_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_3.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=At terminal count, irq_pending is set when CTRL.irq_enable=1..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.side_effects.side_effect_3

### RTL-0070: Implement side effect for FM_DIVIDE: side_effect_4

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.side_effects.side_effect_4.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: value=When enable=0, counter=0, clk_state=0, locked_o=0..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.side_effects.side_effect_4
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.transactions.FM_DIVIDE.side_effects.side_effect_4

### RTL-0071: Implement error case for FM_DIVIDE: error_case_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DIVIDE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.error_cases.error_case_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: condition=APB write to DIVISOR with value 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - function_model.transactions.FM_DIVIDE.error_cases.error_case_0 condition is implemented as RTL control logic: APB write to DIVISOR with value 0
- SSOT refs: function_model.transactions.FM_DIVIDE.error_cases.error_case_0

### RTL-0072: Implement error case for FM_DIVIDE: error_case_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DIVIDE.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DIVIDE.error_cases.error_case_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.transactions.FM_DIVIDE.
SSOT item context: condition=APB access to unsupported address.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DIVIDE.error_cases.error_case_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - function_model.transactions.FM_DIVIDE.error_cases.error_case_1 condition is implemented as RTL control logic: APB access to unsupported address
- SSOT refs: function_model.transactions.FM_DIVIDE.error_cases.error_case_1

### RTL-0073: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.
SSOT item context: value=clk_o changes only on clk_i rising edges while rst_ni is deasserted..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0074: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.
SSOT item context: value=DIVISOR writes do not directly toggle clk_o..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0075: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.
SSOT item context: value=Reserved register fields read as zero and ignore writes..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0076: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: clkdiv_core in rtl/clkdiv_core.sv via function_model.
SSOT item context: value=irq_pending remains set until INTCLR.clear_irq is written as 1..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: function_model.invariants.invariant_3
