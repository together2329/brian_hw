# RTL Authoring Packet: module__todo_counter_pipe_core__function_model_01

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
- Task count: 48
- Required tasks: 48

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
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 1/8 section=function_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0043: Implement RTL state owner for FL state cnt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.cnt
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.cnt.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=cnt; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.cnt
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cnt reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.cnt

### RTL-0044: Implement RTL state owner for FL state enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.enable.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=enable; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.enable
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - enable reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.enable

### RTL-0045: Implement RTL state owner for FL state up_down

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.up_down
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.up_down.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=up_down; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.up_down
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - up_down reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.up_down

### RTL-0046: Implement RTL state owner for FL state mode

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.mode
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.mode.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=mode; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.mode
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - mode reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.mode

### RTL-0047: Implement RTL state owner for FL state load_value

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.load_value
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.load_value.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=load_value; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.load_value
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - load_value reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.load_value

### RTL-0048: Implement RTL state owner for FL state term

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.term
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.term.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=term; reset=all-ones (2^WIDTH-1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.term
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - term reset behavior matches SSOT value all-ones (2^WIDTH-1)
- SSOT refs: function_model.state_variables.term

### RTL-0049: Implement RTL state owner for FL state overflow

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.overflow
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.overflow.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=overflow; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.overflow
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - overflow reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.overflow

### RTL-0050: Implement RTL state owner for FL state underflow

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.underflow
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.underflow.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=underflow; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.underflow
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - underflow reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.underflow

### RTL-0051: Implement RTL state owner for FL state tc_pending

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tc_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tc_pending.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=tc_pending; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tc_pending
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - tc_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.tc_pending

### RTL-0052: Implement RTL state owner for FL state ovf_pending

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ovf_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ovf_pending.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=ovf_pending; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ovf_pending
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - ovf_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ovf_pending

### RTL-0053: Implement RTL state owner for FL state unf_pending

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.unf_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.unf_pending.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=unf_pending; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.unf_pending
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - unf_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.unf_pending

### RTL-0054: Implement RTL state owner for FL state inten_tc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.inten_tc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.inten_tc.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=inten_tc; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.inten_tc
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - inten_tc width matches SSOT value 1
  - inten_tc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.inten_tc

### RTL-0055: Implement RTL state owner for FL state inten_ovf

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.inten_ovf
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.inten_ovf.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=inten_ovf; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.inten_ovf
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - inten_ovf width matches SSOT value 1
  - inten_ovf reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.inten_ovf

### RTL-0056: Implement RTL state owner for FL state inten_unf

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.inten_unf
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.inten_unf.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=inten_unf; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.inten_unf
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - inten_unf width matches SSOT value 1
  - inten_unf reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.inten_unf

### RTL-0057: Implement RTL state owner for FL state dbg_cycle_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dbg_cycle_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dbg_cycle_count.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=dbg_cycle_count; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dbg_cycle_count
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - dbg_cycle_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dbg_cycle_count

### RTL-0058: Implement transaction FM1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: id=FM1; name=count_up_normal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0059: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0060: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=up_down == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0061: Implement precondition for FM1: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=0 <= cnt < term.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_2

### RTL-0062: Implement precondition for FM1: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i asserted (rising edge).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_3

### RTL-0063: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0064: Implement output for FM1: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt_new = cnt + 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_0

### RTL-0065: Implement output rule for FM1: interrupt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.interrupt.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: name=interrupt; port=counter_irq; expr=(tc_pending and inten_tc) or (ovf_pending and inten_ovf) or (unf_pending and inten_unf); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.interrupt
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - interrupt width matches SSOT value 1
  - interrupt RTL expression implements SSOT expression (tc_pending and inten_tc) or (ovf_pending and inten_ovf) or (unf_pending and inten_unf)
  - DUT port counter_irq is the implementation/observation point for interrupt
  - interrupt is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.interrupt

### RTL-0066: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt ← cnt + 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0067: Implement side effect for FM1: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=dbg_cycle_count ← dbg_cycle_count + 1 (on every core_clk, not per event).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_1

### RTL-0068: Implement transaction FM2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: id=FM2; name=count_up_terminal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0069: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0070: Implement precondition for FM2: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=up_down == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_1

### RTL-0071: Implement precondition for FM2: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt == term.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_2

### RTL-0072: Implement precondition for FM2: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_3

### RTL-0073: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0074: Implement output for FM2: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=tc_pending ← 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_0

### RTL-0075: Implement output for FM2: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=If mode==0 (saturate): cnt stays at term.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_1

### RTL-0076: Implement output for FM2: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=If mode==1 (wrap): cnt ← 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_2

### RTL-0077: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=tc_pending set to 1 (sticky until W1C clear).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0078: Implement side effect for FM2: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt updated per mode: saturate → term, wrap → 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_1

### RTL-0079: Implement side effect for FM2: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=If wrap: any further up-count from 0 proceeds normally.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_2

### RTL-0080: Implement transaction FM3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: id=FM3; name=count_down_normal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3

### RTL-0081: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0082: Implement precondition for FM3: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=up_down == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_1

### RTL-0083: Implement precondition for FM3: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=0 < cnt <= 2^WIDTH - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_2

### RTL-0084: Implement precondition for FM3: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_3

### RTL-0085: Implement input for FM3: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.inputs.input_0

### RTL-0086: Implement output for FM3: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt_new = cnt - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_0

### RTL-0087: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt ← cnt - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0088: Implement transaction FM4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: id=FM4; name=count_down_terminal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4

### RTL-0089: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0090: Implement precondition for FM4: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=up_down == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_1
