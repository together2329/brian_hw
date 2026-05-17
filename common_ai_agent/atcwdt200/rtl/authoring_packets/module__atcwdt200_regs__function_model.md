# RTL Authoring Packet: module__atcwdt200_regs__function_model

- Kind: module
- Owner module: atcwdt200_regs
- Owner file: rtl/atcwdt200_regs.sv
- Task count: 42
- Required tasks: 42

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
- Owner refs: dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, dataflow.sinks.sinks_0, decomposition.units.apb_register_block, error_handling, function_model, function_model.transactions.apb_read, function_model.transactions.apb_write, function_model.transactions.write_unlock, registers, registers.register_list
- Module slice: 1/5 section=function_model task_limit=48
- Slice rule: Owner module atcwdt200_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_regs.pclk <= pclk (integration.connections[0])
  - atcwdt200_regs.presetn <= presetn (integration.connections[1])

## Tasks

### RTL-0037: Implement RTL state owner for FL state CR_EN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_EN
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_EN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_EN; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_EN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_EN width matches SSOT value 1
  - CR_EN reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_EN

### RTL-0038: Implement RTL state owner for FL state CR_CLK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_CLK
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_CLK.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_CLK; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_CLK
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_CLK width matches SSOT value 1
  - CR_CLK reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_CLK

### RTL-0039: Implement RTL state owner for FL state CR_INTEN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_INTEN
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_INTEN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_INTEN; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_INTEN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_INTEN width matches SSOT value 1
  - CR_INTEN reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_INTEN

### RTL-0040: Implement RTL state owner for FL state CR_RSTEN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_RSTEN
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_RSTEN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_RSTEN; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_RSTEN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_RSTEN width matches SSOT value 1
  - CR_RSTEN reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_RSTEN

### RTL-0041: Implement RTL state owner for FL state CR_INTTIME

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_INTTIME
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_INTTIME.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_INTTIME; width=INT_TIME_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_INTTIME
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_INTTIME width matches SSOT value INT_TIME_WIDTH
  - CR_INTTIME reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_INTTIME

### RTL-0042: Implement RTL state owner for FL state CR_RSTTIME

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.CR_RSTTIME
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.CR_RSTTIME.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=CR_RSTTIME; width=3; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.CR_RSTTIME
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_RSTTIME width matches SSOT value 3
  - CR_RSTTIME reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.CR_RSTTIME

### RTL-0043: Implement RTL state owner for FL state SR_INTZERO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.SR_INTZERO
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.SR_INTZERO.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=SR_INTZERO; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.SR_INTZERO
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - SR_INTZERO width matches SSOT value 1
  - SR_INTZERO reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.SR_INTZERO

### RTL-0044: Implement RTL state owner for FL state SR_RSTZERO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.SR_RSTZERO
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.SR_RSTZERO.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=SR_RSTZERO; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.SR_RSTZERO
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - SR_RSTZERO width matches SSOT value 1
  - SR_RSTZERO reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.SR_RSTZERO

### RTL-0045: Implement RTL state owner for FL state REG_WEN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.REG_WEN
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.REG_WEN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=REG_WEN; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.REG_WEN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - REG_WEN width matches SSOT value 1
  - REG_WEN reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.REG_WEN

### RTL-0046: Implement RTL state owner for FL state COUNTER

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.COUNTER
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.COUNTER.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=COUNTER; width=COUNTER_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.COUNTER
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - COUNTER width matches SSOT value COUNTER_WIDTH
  - COUNTER reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.COUNTER

### RTL-0047: Implement RTL state owner for FL state STATE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.STATE
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.STATE.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: name=STATE; width=1; reset=ST_INTTIME.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.STATE
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - STATE width matches SSOT value 1
  - STATE reset behavior matches SSOT value ST_INTTIME
- SSOT refs: function_model.state_variables.STATE

### RTL-0048: Implement transaction apb_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.apb_read
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.apb_read.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: id=apb_read; name=APB register read.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.apb_read
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_read

### RTL-0049: Implement precondition for apb_read: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.apb_read.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.preconditions.precondition_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: value=psel and penable are asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_read.preconditions.precondition_0

### RTL-0050: Implement precondition for apb_read: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.apb_read.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.preconditions.precondition_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: value=pwrite is low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_read.preconditions.precondition_1

### RTL-0051: Implement input for apb_read: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.apb_read.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.inputs.input_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: id=apb_read; name=APB register read; port=["prdata"]; signal=["paddr"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["prdata"] is the implementation/observation point for APB register read
- SSOT refs: function_model.transactions.apb_read.inputs.input_0

### RTL-0052: Implement output for apb_read: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.apb_read.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.outputs.output_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: id=apb_read; name=APB register read; port=["prdata"]; signal=["prdata returns selected register value"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["prdata"] is the implementation/observation point for APB register read
- SSOT refs: function_model.transactions.apb_read.outputs.output_0

### RTL-0053: Implement output rule for apb_read: prdata_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.apb_read.output_rules.prdata_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.output_rules.prdata_rule.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: name=prdata_rule; port=prdata; expr=0; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.output_rules.prdata_rule
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - prdata_rule width matches SSOT value 32
  - prdata_rule RTL expression implements SSOT expression 0
  - DUT port prdata is the implementation/observation point for prdata_rule
  - prdata_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.apb_read.output_rules.prdata_rule

### RTL-0054: Implement side effect for apb_read: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.apb_read.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.side_effects.side_effect_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: id=apb_read; name=APB register read; port=["prdata"]; signal=["No architectural state changes on read"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["prdata"] is the implementation/observation point for APB register read
- SSOT refs: function_model.transactions.apb_read.side_effects.side_effect_0

### RTL-0055: Implement error case for apb_read: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.apb_read.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_read.error_cases.error_case_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_read.
SSOT item context: id=apb_read; name=APB register read; port=["prdata"]; signal=["Unsupported offsets return zero in legacy-compatible mode."].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_read.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["prdata"] is the implementation/observation point for APB register read
- SSOT refs: function_model.transactions.apb_read.error_cases.error_case_0

### RTL-0056: Implement transaction apb_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.apb_write
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.apb_write.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.apb_write
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write

### RTL-0057: Implement precondition for apb_write: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.apb_write.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.preconditions.precondition_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: value=psel and penable and pwrite are asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.preconditions.precondition_0

### RTL-0058: Implement input for apb_write: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.apb_write.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.inputs.input_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["paddr"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.inputs.input_0

### RTL-0059: Implement input for apb_write: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.apb_write.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.inputs.input_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["pwdata"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.inputs.input_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.inputs.input_1

### RTL-0060: Implement output for apb_write: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.apb_write.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.outputs.output_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["Protected registers update only when REG_WEN is set according to approved policy"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.outputs.output_0

### RTL-0061: Implement state update for apb_write: CR_FIELDS

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.apb_write.state_updates.CR_FIELDS
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.state_updates.CR_FIELDS.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: name=CR_FIELDS; expr=pwdata & 0x7ff; width=11.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.state_updates.CR_FIELDS
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR_FIELDS width matches SSOT value 11
  - CR_FIELDS RTL expression implements SSOT expression pwdata & 0x7ff
  - CR_FIELDS updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.apb_write.state_updates.CR_FIELDS

### RTL-0062: Implement state update for apb_write: SR_INTZERO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.apb_write.state_updates.SR_INTZERO
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.state_updates.SR_INTZERO.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: name=SR_INTZERO; expr=SR_INTZERO & (((pwdata & 1) ^ 1) & 1); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.state_updates.SR_INTZERO
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - SR_INTZERO width matches SSOT value 1
  - SR_INTZERO RTL expression implements SSOT expression SR_INTZERO & (((pwdata & 1) ^ 1) & 1)
  - SR_INTZERO updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.apb_write.state_updates.SR_INTZERO

### RTL-0063: Implement side effect for apb_write: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.apb_write.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.side_effects.side_effect_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["May update CR"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.side_effects.side_effect_0

### RTL-0064: Implement side effect for apb_write: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.apb_write.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.side_effects.side_effect_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["set REG_WEN"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.side_effects.side_effect_1

### RTL-0065: Implement side effect for apb_write: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.apb_write.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.side_effects.side_effect_2.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["clear SR_INTZERO"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.side_effects.side_effect_2

### RTL-0066: Implement side effect for apb_write: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.apb_write.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.side_effects.side_effect_3.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["or issue restart command"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.side_effects.side_effect_3

### RTL-0067: Implement error case for apb_write: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.apb_write.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.apb_write.error_cases.error_case_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.apb_write.
SSOT item context: id=apb_write; name=APB register write; signal=["Writes without unlock to protected registers have no effect"]; state=["CR_FIELDS", "SR_INTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.apb_write.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.apb_write.error_cases.error_case_0

### RTL-0068: Implement transaction write_unlock

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.write_unlock
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.write_unlock.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: id=write_unlock; name=Write protection unlock.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.write_unlock
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock

### RTL-0069: Implement precondition for write_unlock: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.write_unlock.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.preconditions.precondition_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: value=APB write to WEN offset 0x18.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock.preconditions.precondition_0

### RTL-0070: Implement input for write_unlock: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.write_unlock.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.inputs.input_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: id=write_unlock; name=Write protection unlock; signal=["pwdata"]; state=["REG_WEN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock.inputs.input_0

### RTL-0071: Implement output for write_unlock: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.write_unlock.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.outputs.output_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: id=write_unlock; name=Write protection unlock; signal=["REG_WEN becomes one when lower 16 bits match 0x5aa5"]; state=["REG_WEN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock.outputs.output_0

### RTL-0072: Implement state update for write_unlock: REG_WEN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.write_unlock.state_updates.REG_WEN
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.state_updates.REG_WEN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: name=REG_WEN; expr=(pwdata & 0xffff) == 0x5aa5; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.state_updates.REG_WEN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - REG_WEN width matches SSOT value 1
  - REG_WEN RTL expression implements SSOT expression (pwdata & 0xffff) == 0x5aa5
  - REG_WEN updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.write_unlock.state_updates.REG_WEN

### RTL-0073: Implement side effect for write_unlock: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.write_unlock.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.side_effects.side_effect_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: id=write_unlock; name=Write protection unlock; signal=["Unlock consumption policy pending QA"]; state=["REG_WEN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock.side_effects.side_effect_0

### RTL-0074: Implement error case for write_unlock: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.write_unlock.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.write_unlock.error_cases.error_case_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.transactions.write_unlock.
SSOT item context: id=write_unlock; name=Write protection unlock; signal=["Wrong magic value does not unlock"]; state=["REG_WEN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.write_unlock.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: function_model.transactions.write_unlock.error_cases.error_case_0

### RTL-0115: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: port=["wdt_int", "wdt_rst"]; signal=wdt_int equals SR_INTZERO & CR_INTEN.; state=["CR_EN", "CR_CLK", "CR_INTEN", "CR_RSTEN", "CR_INTTIME", "CR_RSTTIME", "SR_INTZERO", "SR_RSTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for ["wdt_int", "wdt_rst"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0116: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: port=["wdt_int", "wdt_rst"]; signal=wdt_rst equals SR_RSTZERO & CR_RSTEN.; state=["CR_EN", "CR_CLK", "CR_INTEN", "CR_RSTEN", "CR_INTTIME", "CR_RSTTIME", "SR_INTZERO", "SR_RSTZERO"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for ["wdt_int", "wdt_rst"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0117: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: port=["wdt_int", "wdt_rst"]; signal=Counter does not advance while disabled or paused.; state=["STATE"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for ["wdt_int", "wdt_rst"]
- SSOT refs: function_model.invariants.invariant_2

### RTL-0118: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via function_model.
SSOT item context: port=["prdata", "wdt_int", "wdt_rst"]; signal=Reserved register bits read as zero and ignore writes unless QA approves modernized behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - DUT port ["prdata", "wdt_int", "wdt_rst"] is the implementation/observation point for ["prdata", "wdt_int", "wdt_rst"]
- SSOT refs: function_model.invariants.invariant_3
