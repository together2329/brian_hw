# RTL Authoring Packet: module__pulse_gen_core__function_model

- Kind: module
- Owner module: pulse_gen_core
- Owner file: rtl/pulse_gen_core.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, features, features.pulse_fire, fsm, fsm.pulse_fsm, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_FIRE
- Module slice: 1/6 section=function_model task_limit=48
- Slice rule: Owner module pulse_gen_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_core.status_busy_i <= pulse_gen_regs.status_busy (integration.connections[14])
  - pulse_gen_core.status_done_o <= pulse_gen_regs.status_done (integration.connections[15])

## Tasks

### RTL-0043: Implement RTL state owner for FL state fsm_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fsm_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fsm_state.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=fsm_state; reset=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fsm_state
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm_state reset behavior matches SSOT value IDLE
- SSOT refs: function_model.state_variables.fsm_state

### RTL-0044: Implement RTL state owner for FL state pulse_counter

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pulse_counter
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pulse_counter.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=pulse_counter; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pulse_counter
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_counter reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.pulse_counter

### RTL-0045: Implement RTL state owner for FL state latched_width

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.latched_width
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.latched_width.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=latched_width; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.latched_width
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - latched_width reset behavior matches SSOT value 1
- SSOT refs: function_model.state_variables.latched_width

### RTL-0046: Implement RTL state owner for FL state latched_polarity

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.latched_polarity
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.latched_polarity.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=latched_polarity; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.latched_polarity
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - latched_polarity reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.latched_polarity

### RTL-0047: Implement RTL state owner for FL state ctrl_fire

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_fire
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_fire.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=ctrl_fire; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_fire
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - ctrl_fire reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctrl_fire

### RTL-0048: Implement RTL state owner for FL state ctrl_enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_enable.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=ctrl_enable; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_enable
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - ctrl_enable reset behavior matches SSOT value 1
- SSOT refs: function_model.state_variables.ctrl_enable

### RTL-0049: Implement RTL state owner for FL state ctrl_hw_trig_en

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_hw_trig_en
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_hw_trig_en.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=ctrl_hw_trig_en; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_hw_trig_en
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - ctrl_hw_trig_en reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctrl_hw_trig_en

### RTL-0050: Implement RTL state owner for FL state status_busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status_busy
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status_busy.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=status_busy; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status_busy
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - status_busy reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status_busy

### RTL-0051: Implement RTL state owner for FL state status_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status_done
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status_done.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=status_done; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status_done
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - status_done reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status_done

### RTL-0052: Implement RTL state owner for FL state fired_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fired_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fired_count.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.state_variables.
SSOT item context: name=fired_count; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fired_count
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fired_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fired_count

### RTL-0053: Implement transaction FM_FIRE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FIRE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FIRE.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: id=FM_FIRE; name=fire_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FIRE
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE

### RTL-0054: Implement precondition for FM_FIRE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FIRE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.preconditions.precondition_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=ctrl_enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.preconditions.precondition_0

### RTL-0055: Implement precondition for FM_FIRE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FIRE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.preconditions.precondition_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=status_busy == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.preconditions.precondition_1

### RTL-0056: Implement precondition for FM_FIRE: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FIRE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.preconditions.precondition_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=(ctrl_fire == 1) or (trigger_i == 1 and ctrl_hw_trig_en == 1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.preconditions.precondition_2

### RTL-0057: Implement input for FM_FIRE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FIRE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.inputs.input_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=trigger event: ctrl_fire or trigger_i level.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.inputs.input_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.inputs.input_0

### RTL-0058: Implement input for FM_FIRE: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FIRE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.inputs.input_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=latched_width = max(registers.PULSE_WIDTH.width, 1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.inputs.input_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.inputs.input_1

### RTL-0059: Implement input for FM_FIRE: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FIRE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.inputs.input_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=latched_polarity = registers.CTRL.polarity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.inputs.input_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.inputs.input_2

### RTL-0060: Implement output for FM_FIRE: pulse_out_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FIRE.outputs.pulse_out_active
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.outputs.pulse_out_active.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=pulse_out_active; port=pulse_out; expr=latched_polarity ? 1'b0 : 1'b1; width=PULSE_OUT_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.outputs.pulse_out_active
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_out_active width matches SSOT value PULSE_OUT_WIDTH
  - pulse_out_active RTL expression implements SSOT expression latched_polarity ? 1'b0 : 1'b1
  - DUT port pulse_out is the implementation/observation point for pulse_out_active
- SSOT refs: function_model.transactions.FM_FIRE.outputs.pulse_out_active

### RTL-0061: Implement output for FM_FIRE: pulse_out_idle

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FIRE.outputs.pulse_out_idle
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.outputs.pulse_out_idle.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=pulse_out_idle; port=pulse_out; expr=latched_polarity ? 1'b1 : 1'b0; width=PULSE_OUT_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.outputs.pulse_out_idle
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_out_idle width matches SSOT value PULSE_OUT_WIDTH
  - pulse_out_idle RTL expression implements SSOT expression latched_polarity ? 1'b1 : 1'b0
  - DUT port pulse_out is the implementation/observation point for pulse_out_idle
- SSOT refs: function_model.transactions.FM_FIRE.outputs.pulse_out_idle

### RTL-0062: Implement output for FM_FIRE: irq_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FIRE.outputs.irq_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.outputs.irq_o.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=irq_o; port=irq_o; expr=status_done & INT_ENABLE.done_ie; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.outputs.irq_o
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - irq_o width matches SSOT value 1
  - irq_o RTL expression implements SSOT expression status_done & INT_ENABLE.done_ie
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: function_model.transactions.FM_FIRE.outputs.irq_o

### RTL-0063: Implement output rule for FM_FIRE: pulse_out_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FIRE.output_rules.pulse_out_active
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.output_rules.pulse_out_active.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=pulse_out_active; port=pulse_out; expr=latched_polarity ? 1'b0 : 1'b1; width=PULSE_OUT_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.output_rules.pulse_out_active
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_out_active width matches SSOT value PULSE_OUT_WIDTH
  - pulse_out_active RTL expression implements SSOT expression latched_polarity ? 1'b0 : 1'b1
  - DUT port pulse_out is the implementation/observation point for pulse_out_active
  - pulse_out_active is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FIRE.output_rules.pulse_out_active

### RTL-0064: Implement output rule for FM_FIRE: pulse_out_idle

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FIRE.output_rules.pulse_out_idle
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.output_rules.pulse_out_idle.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=pulse_out_idle; port=pulse_out; expr=latched_polarity ? 1'b1 : 1'b0; width=PULSE_OUT_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.output_rules.pulse_out_idle
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_out_idle width matches SSOT value PULSE_OUT_WIDTH
  - pulse_out_idle RTL expression implements SSOT expression latched_polarity ? 1'b1 : 1'b0
  - DUT port pulse_out is the implementation/observation point for pulse_out_idle
  - pulse_out_idle is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FIRE.output_rules.pulse_out_idle

### RTL-0065: Implement output rule for FM_FIRE: irq_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FIRE.output_rules.irq_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.output_rules.irq_o.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=irq_o; port=irq_o; expr=status_done & INT_ENABLE.done_ie; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.output_rules.irq_o
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - irq_o width matches SSOT value 1
  - irq_o RTL expression implements SSOT expression status_done & INT_ENABLE.done_ie
  - DUT port irq_o is the implementation/observation point for irq_o
  - irq_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FIRE.output_rules.irq_o

### RTL-0066: Implement state update for FM_FIRE: fsm_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.fsm_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.fsm_state.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=fsm_state; expr=IDLE→PULSE on trigger; PULSE→DONE when counter==width-1; DONE→IDLE after 1 cycle or W1C; reset=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.fsm_state
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm_state reset behavior matches SSOT value IDLE
  - fsm_state RTL expression implements SSOT expression IDLE→PULSE on trigger; PULSE→DONE when counter==width-1; DONE→IDLE after 1 cycle or W1C
  - fsm_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.fsm_state

### RTL-0067: Implement state update for FM_FIRE: pulse_counter

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.pulse_counter
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.pulse_counter.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=pulse_counter; expr=0 in IDLE/DONE; increments each cycle in PULSE; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.pulse_counter
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - pulse_counter reset behavior matches SSOT value 0
  - pulse_counter RTL expression implements SSOT expression 0 in IDLE/DONE; increments each cycle in PULSE
  - pulse_counter updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.pulse_counter

### RTL-0068: Implement state update for FM_FIRE: latched_width

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.latched_width
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.latched_width.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=latched_width; expr=captured from PULSE_WIDTH register at trigger; held constant during PULSE; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.latched_width
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - latched_width reset behavior matches SSOT value 1
  - latched_width RTL expression implements SSOT expression captured from PULSE_WIDTH register at trigger; held constant during PULSE
  - latched_width updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.latched_width

### RTL-0069: Implement state update for FM_FIRE: latched_polarity

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.latched_polarity
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.latched_polarity.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=latched_polarity; expr=captured from CTRL.polarity at trigger; held constant during PULSE; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.latched_polarity
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - latched_polarity reset behavior matches SSOT value 0
  - latched_polarity RTL expression implements SSOT expression captured from CTRL.polarity at trigger; held constant during PULSE
  - latched_polarity updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.latched_polarity

### RTL-0070: Implement state update for FM_FIRE: status_busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.status_busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.status_busy.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=status_busy; expr=1 while fsm_state==PULSE; 0 otherwise; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.status_busy
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - status_busy reset behavior matches SSOT value 0
  - status_busy RTL expression implements SSOT expression 1 while fsm_state==PULSE; 0 otherwise
  - status_busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.status_busy

### RTL-0071: Implement state update for FM_FIRE: status_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.status_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.status_done.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=status_done; expr=set to 1 at PULSE→DONE transition; cleared by W1C write to STATUS.done; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.status_done
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - status_done reset behavior matches SSOT value 0
  - status_done RTL expression implements SSOT expression set to 1 at PULSE→DONE transition; cleared by W1C write to STATUS.done
  - status_done updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.status_done

### RTL-0072: Implement state update for FM_FIRE: fired_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.fired_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.fired_count.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=fired_count; expr=fired_count + 1 at PULSE→DONE transition; wraps at 2^16; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.fired_count
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fired_count reset behavior matches SSOT value 0
  - fired_count RTL expression implements SSOT expression fired_count + 1 at PULSE→DONE transition; wraps at 2^16
  - fired_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.fired_count

### RTL-0073: Implement state update for FM_FIRE: ctrl_fire

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FIRE.state_updates.ctrl_fire
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.state_updates.ctrl_fire.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: name=ctrl_fire; expr=set to 1 by APB write; auto-clears to 0 after one PCLK; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.state_updates.ctrl_fire
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - ctrl_fire reset behavior matches SSOT value 0
  - ctrl_fire RTL expression implements SSOT expression set to 1 by APB write; auto-clears to 0 after one PCLK
  - ctrl_fire updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FIRE.state_updates.ctrl_fire

### RTL-0074: Implement side effect for FM_FIRE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FIRE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.side_effects.side_effect_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=fsm_state transitions: IDLE → PULSE → DONE → IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.side_effects.side_effect_0

### RTL-0075: Implement side effect for FM_FIRE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FIRE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.side_effects.side_effect_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=pulse_counter increments each PCLK cycle while in PULSE state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.side_effects.side_effect_1

### RTL-0076: Implement side effect for FM_FIRE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FIRE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.side_effects.side_effect_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=fired_count increments by 1 at PULSE→DONE transition.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.side_effects.side_effect_2

### RTL-0077: Implement side effect for FM_FIRE: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FIRE.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.side_effects.side_effect_3.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: value=ctrl_fire auto-clears to 0 after one PCLK cycle (self-clearing trigger).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.transactions.FM_FIRE.side_effects.side_effect_3

### RTL-0078: Implement error case for FM_FIRE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FIRE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.error_cases.error_case_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: condition=trigger while status_busy==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - function_model.transactions.FM_FIRE.error_cases.error_case_0 condition is implemented as RTL control logic: trigger while status_busy==1
- SSOT refs: function_model.transactions.FM_FIRE.error_cases.error_case_0

### RTL-0079: Implement error case for FM_FIRE: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FIRE.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.error_cases.error_case_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: condition=PULSE_WIDTH.width written as 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.error_cases.error_case_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - function_model.transactions.FM_FIRE.error_cases.error_case_1 condition is implemented as RTL control logic: PULSE_WIDTH.width written as 0
- SSOT refs: function_model.transactions.FM_FIRE.error_cases.error_case_1

### RTL-0080: Implement error case for FM_FIRE: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FIRE.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FIRE.error_cases.error_case_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.transactions.FM_FIRE.
SSOT item context: condition=ctrl_enable==0 when trigger arrives.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FIRE.error_cases.error_case_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - function_model.transactions.FM_FIRE.error_cases.error_case_2 condition is implemented as RTL control logic: ctrl_enable==0 when trigger arrives
- SSOT refs: function_model.transactions.FM_FIRE.error_cases.error_case_2

### RTL-0081: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=pulse_out is at idle_level whenever fsm_state != PULSE..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0082: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=pulse_out is never asserted for more or fewer cycles than latched_width..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0083: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=STATUS.busy and pulse_out active are always coincident..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0084: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=A new pulse cannot start while STATUS.busy==1 (non-reentrant)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0085: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=irq_o is a pure combinational function of STATUS.done and INT_ENABLE.done_ie..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_4

### RTL-0086: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via function_model.
SSOT item context: value=ctrl_fire is self-clearing: it is 1 for exactly one PCLK cycle after being written..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: function_model.invariants.invariant_5
