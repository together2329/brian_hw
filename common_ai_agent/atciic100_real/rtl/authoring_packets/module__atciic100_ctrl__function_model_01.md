# RTL Authoring Packet: module__atciic100_ctrl__function_model_01

- Kind: module
- Owner module: atciic100_ctrl
- Owner file: rtl/atciic100_ctrl.v
- Task count: 48
- Required tasks: 48

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, fsm, fsm.iic_phase, function_model, function_model.transactions
- Module slice: 1/7 section=function_model task_limit=48
- Slice rule: Owner module atciic100_ctrl is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])

## Tasks

### RTL-0053: Implement RTL state owner for FL state cmd

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.cmd
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.cmd.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=cmd; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.cmd
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - cmd reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.cmd

### RTL-0054: Implement RTL state owner for FL state cfg

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.cfg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.cfg.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=cfg; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.cfg
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - cfg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.cfg

### RTL-0055: Implement RTL state owner for FL state int_en

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_en
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_en.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=int_en; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_en
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - int_en reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_en

### RTL-0056: Implement RTL state owner for FL state int_st

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_st
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_st.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=int_st; reset=1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_st
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - int_st reset behavior matches SSOT value 1
- SSOT refs: function_model.state_variables.int_st

### RTL-0057: Implement RTL state owner for FL state setup

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.setup
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.setup.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=setup; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.setup
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - setup reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.setup

### RTL-0058: Implement RTL state owner for FL state addr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.addr.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=addr; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.addr
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.addr

### RTL-0059: Implement RTL state owner for FL state ctrl

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=ctrl; reset=7936.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - ctrl reset behavior matches SSOT value 7936
- SSOT refs: function_model.state_variables.ctrl

### RTL-0060: Implement RTL state owner for FL state phase

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.phase
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.phase.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=phase; reset=IDLE.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.phase
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - phase reset behavior matches SSOT value IDLE
- SSOT refs: function_model.state_variables.phase

### RTL-0061: Implement RTL state owner for FL state fifo_count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fifo_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fifo_count.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=fifo_count; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fifo_count
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - fifo_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fifo_count

### RTL-0062: Implement RTL state owner for FL state master

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.master
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.master.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=master; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.master
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - master reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.master

### RTL-0063: Implement RTL state owner for FL state trans

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.trans
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.trans.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=trans; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.trans
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - trans reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.trans

### RTL-0064: Implement RTL state owner for FL state arb_lost

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.arb_lost
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.arb_lost.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=arb_lost; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.arb_lost
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - arb_lost reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.arb_lost

### RTL-0065: Implement RTL state owner for FL state datacnt

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.datacnt
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.datacnt.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: name=datacnt; reset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.datacnt
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - datacnt reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.datacnt

### RTL-0066: Implement transaction FM1

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM1; name=reset.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1

### RTL-0067: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=presetn == 0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0068: Implement output for FM1: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=All registers reset to default.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.outputs.output_0

### RTL-0069: Implement output for FM1: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=FIFO cleared.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.outputs.output_1

### RTL-0070: Implement output for FM1: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=FSM=IDLE.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.outputs.output_2

### RTL-0071: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=i2c_int goes low.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0072: Implement side effect for FM1: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Bus lines released (open drain).
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_1

### RTL-0073: Implement transaction FM2

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM2; name=csr_read.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2

### RTL-0074: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=psel==1 && penable==1 && pwrite==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0075: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=paddr.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0076: Implement output for FM2: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=prdata = RegisterFile[paddr].
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2.outputs.output_0

### RTL-0077: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=APB read completes in 2 cycles (setup then access phase).
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0078: Implement side effect for FM2: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=INT_ST read does not clear W1C bits (only write-1 clears).
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_1

### RTL-0079: Implement transaction FM3

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM3; name=csr_write.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3

### RTL-0080: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=psel==1 && penable==1 && pwrite==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0081: Implement input for FM3: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=paddr.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.inputs.input_0

### RTL-0082: Implement input for FM3: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=pwdata.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.inputs.input_1

### RTL-0083: Implement output for FM3: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=RegisterFile[paddr] updated.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.outputs.output_0

### RTL-0084: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=CMD triggers action if valid.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0085: Implement side effect for FM3: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=SETUP updates timing.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_1

### RTL-0086: Implement transaction FM4

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM4; name=master_send.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4

### RTL-0087: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=master==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0088: Implement precondition for FM4: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=trans==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_1

### RTL-0089: Implement precondition for FM4: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=cmd==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_2

### RTL-0090: Implement precondition for FM4: precondition_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_3.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=fifo_count > 0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_3
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_3

### RTL-0091: Implement input for FM4: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM4.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=addr.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.inputs.input_0

### RTL-0092: Implement input for FM4: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM4.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.inputs.input_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=data.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.inputs.input_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.inputs.input_1

### RTL-0093: Implement output for FM4: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=SCL/SDA signals driven for Start->Addr->Data->Stop.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.outputs.output_0

### RTL-0094: Implement output for FM4: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Target slave ACK/NACK.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.outputs.output_1

### RTL-0095: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=datacnt decrements.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0096: Implement side effect for FM4: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=ByteTrans interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_1

### RTL-0097: Implement side effect for FM4: side_effect_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Cmpl interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_2

### RTL-0098: Implement error case for FM4: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM4.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=No ACK from slave.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM4.error_cases.error_case_0 condition is implemented as RTL control logic: No ACK from slave
- SSOT refs: function_model.transactions.FM4.error_cases.error_case_0

### RTL-0099: Implement error case for FM4: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM4.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.error_cases.error_case_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=Arbitration Lost.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.error_cases.error_case_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM4.error_cases.error_case_1 condition is implemented as RTL control logic: Arbitration Lost
- SSOT refs: function_model.transactions.FM4.error_cases.error_case_1

### RTL-0100: Implement transaction FM5

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM5
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM5.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM5; name=master_recv.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM5
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5
