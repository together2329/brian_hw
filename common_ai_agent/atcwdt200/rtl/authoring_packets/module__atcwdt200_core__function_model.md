# RTL Authoring Packet: module__atcwdt200_core__function_model

- Kind: module
- Owner module: atcwdt200_core
- Owner file: rtl/atcwdt200_core.sv
- Task count: 40
- Required tasks: 40

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, dataflow.sequence.sequence_2, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sinks.sinks_1, dataflow.sinks.sinks_2, decomposition.units.watchdog_core, fsm, fsm.watchdog, function_model, function_model.transactions.restart, function_model.transactions.timeout_decode, function_model.transactions.watchdog_tick
- Module slice: 1/6 section=function_model task_limit=48
- Slice rule: Owner module atcwdt200_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_core.pclk <= pclk (integration.connections[2])
  - atcwdt200_core.presetn <= presetn (integration.connections[3])

## Tasks

### RTL-0075: Implement transaction restart

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.restart
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.restart.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.restart
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart

### RTL-0076: Implement precondition for restart: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.restart.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.preconditions.precondition_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: value=Unlocked APB write to RES offset 0x14 with lower 16 bits 0xcafe.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.preconditions.precondition_0

### RTL-0077: Implement input for restart: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.restart.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.inputs.input_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command; signal=["pwdata"]; state=["COUNTER", "STATE"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.inputs.input_0

### RTL-0078: Implement input for restart: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.restart.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.inputs.input_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command; signal=["REG_WEN"]; state=["COUNTER", "STATE"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.inputs.input_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.inputs.input_1

### RTL-0079: Implement output for restart: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.restart.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.outputs.output_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command; signal=["COUNTER resets to zero and STATE becomes ST_INTTIME"]; state=["COUNTER", "STATE"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.outputs.output_0

### RTL-0080: Implement state update for restart: COUNTER

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.restart.state_updates.COUNTER
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.state_updates.COUNTER.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: name=COUNTER; expr=0; width=COUNTER_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.state_updates.COUNTER
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - COUNTER width matches SSOT value COUNTER_WIDTH
  - COUNTER RTL expression implements SSOT expression 0
  - COUNTER updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.restart.state_updates.COUNTER

### RTL-0081: Implement state update for restart: STATE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.restart.state_updates.STATE
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.state_updates.STATE.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: name=STATE; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.state_updates.STATE
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - STATE width matches SSOT value 1
  - STATE RTL expression implements SSOT expression 0
  - STATE updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.restart.state_updates.STATE

### RTL-0082: Implement side effect for restart: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.restart.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.side_effects.side_effect_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command; signal=["Restart command is a pulse"]; state=["COUNTER", "STATE"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.side_effects.side_effect_0

### RTL-0083: Implement error case for restart: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.restart.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.restart.error_cases.error_case_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.restart.
SSOT item context: id=restart; name=Watchdog restart command; signal=["Wrong magic or locked write has no restart effect"]; state=["COUNTER", "STATE"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.restart.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.restart.error_cases.error_case_0

### RTL-0084: Implement transaction watchdog_tick

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.watchdog_tick
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.watchdog_tick.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.watchdog_tick
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.watchdog_tick

### RTL-0085: Implement precondition for watchdog_tick: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.watchdog_tick.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.preconditions.precondition_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: value=CR_EN is set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.watchdog_tick.preconditions.precondition_0

### RTL-0086: Implement precondition for watchdog_tick: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.watchdog_tick.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.preconditions.precondition_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: value=wdt_pause synchronized value is zero.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.watchdog_tick.preconditions.precondition_1

### RTL-0087: Implement input for watchdog_tick: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["pclk_tick"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_0

### RTL-0088: Implement input for watchdog_tick: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["extclk_rising_pulse"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_1

### RTL-0089: Implement input for watchdog_tick: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_2.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["CR_CLK"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_2
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_2

### RTL-0090: Implement input for watchdog_tick: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_3.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["CR_INTTIME"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_3
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_3

### RTL-0091: Implement input for watchdog_tick: input_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_4.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["CR_RSTTIME"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_4
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_4

### RTL-0092: Implement input for watchdog_tick: input_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_5
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_5.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["STATE"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_5
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_5

### RTL-0093: Implement input for watchdog_tick: input_6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_6
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_6.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["restart_cmd"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_6
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_6

### RTL-0094: Implement input for watchdog_tick: input_7

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_7
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_7.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["inttime_end"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_7
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_7

### RTL-0095: Implement input for watchdog_tick: input_8

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.watchdog_tick.inputs.input_8
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.inputs.input_8.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["rsttime_end"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.inputs.input_8
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.inputs.input_8

### RTL-0096: Implement output for watchdog_tick: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.watchdog_tick.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.outputs.output_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["wdt_int and wdt_rst reflect timeout status gated by enables"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.outputs.output_0

### RTL-0097: Implement output rule for watchdog_tick: wdt_int_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.watchdog_tick.output_rules.wdt_int_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.output_rules.wdt_int_rule.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=wdt_int_rule; port=wdt_int; expr=SR_INTZERO & CR_INTEN; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.output_rules.wdt_int_rule
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - wdt_int_rule width matches SSOT value 1
  - wdt_int_rule RTL expression implements SSOT expression SR_INTZERO & CR_INTEN
  - DUT port wdt_int is the implementation/observation point for wdt_int_rule
  - wdt_int_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.watchdog_tick.output_rules.wdt_int_rule

### RTL-0098: Implement output rule for watchdog_tick: wdt_rst_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.watchdog_tick.output_rules.wdt_rst_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.output_rules.wdt_rst_rule.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=wdt_rst_rule; port=wdt_rst; expr=SR_RSTZERO & CR_RSTEN; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.output_rules.wdt_rst_rule
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - wdt_rst_rule width matches SSOT value 1
  - wdt_rst_rule RTL expression implements SSOT expression SR_RSTZERO & CR_RSTEN
  - DUT port wdt_rst is the implementation/observation point for wdt_rst_rule
  - wdt_rst_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.watchdog_tick.output_rules.wdt_rst_rule

### RTL-0099: Implement state update for watchdog_tick: COUNTER

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.watchdog_tick.state_updates.COUNTER
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.state_updates.COUNTER.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=COUNTER; expr=0 if (restart_cmd or inttime_end) else (COUNTER + 1); width=COUNTER_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.state_updates.COUNTER
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - COUNTER width matches SSOT value COUNTER_WIDTH
  - COUNTER RTL expression implements SSOT expression 0 if (restart_cmd or inttime_end) else (COUNTER + 1)
  - COUNTER updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.watchdog_tick.state_updates.COUNTER

### RTL-0100: Implement state update for watchdog_tick: SR_INTZERO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.watchdog_tick.state_updates.SR_INTZERO
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.state_updates.SR_INTZERO.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=SR_INTZERO; expr=1 if inttime_end else SR_INTZERO; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.state_updates.SR_INTZERO
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - SR_INTZERO width matches SSOT value 1
  - SR_INTZERO RTL expression implements SSOT expression 1 if inttime_end else SR_INTZERO
  - SR_INTZERO updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.watchdog_tick.state_updates.SR_INTZERO

### RTL-0101: Implement state update for watchdog_tick: SR_RSTZERO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.watchdog_tick.state_updates.SR_RSTZERO
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.state_updates.SR_RSTZERO.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=SR_RSTZERO; expr=1 if rsttime_end else SR_RSTZERO; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.state_updates.SR_RSTZERO
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - SR_RSTZERO width matches SSOT value 1
  - SR_RSTZERO RTL expression implements SSOT expression 1 if rsttime_end else SR_RSTZERO
  - SR_RSTZERO updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.watchdog_tick.state_updates.SR_RSTZERO

### RTL-0102: Implement state update for watchdog_tick: STATE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.watchdog_tick.state_updates.STATE
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.state_updates.STATE.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=STATE; expr=1 if (inttime_end and not restart_cmd) else (0 if restart_cmd else STATE); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.state_updates.STATE
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - STATE width matches SSOT value 1
  - STATE RTL expression implements SSOT expression 1 if (inttime_end and not restart_cmd) else (0 if restart_cmd else STATE)
  - STATE updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.watchdog_tick.state_updates.STATE

### RTL-0103: Implement state update for watchdog_tick: CR_EN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.watchdog_tick.state_updates.CR_EN
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.state_updates.CR_EN.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: name=CR_EN; expr=0 if rsttime_end else CR_EN; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.state_updates.CR_EN
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - CR_EN width matches SSOT value 1
  - CR_EN RTL expression implements SSOT expression 0 if rsttime_end else CR_EN
  - CR_EN updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.watchdog_tick.state_updates.CR_EN

### RTL-0104: Implement side effect for watchdog_tick: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.watchdog_tick.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.side_effects.side_effect_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["Timeout table uses the observed reference counter bit taps."]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.side_effects.side_effect_0

### RTL-0105: Implement error case for watchdog_tick: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.watchdog_tick.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.watchdog_tick.error_cases.error_case_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.watchdog_tick.
SSOT item context: id=watchdog_tick; name=Watchdog tick and timeout update; port=["wdt_int", "wdt_rst"]; signal=["No counting while paused or disabled"]; state=["COUNTER", "SR_INTZERO", "SR_RSTZERO", "STATE", "CR_EN"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.watchdog_tick.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - DUT port ["wdt_int", "wdt_rst"] is the implementation/observation point for Watchdog tick and timeout update
- SSOT refs: function_model.transactions.watchdog_tick.error_cases.error_case_0

### RTL-0106: Implement transaction timeout_decode

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.timeout_decode
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.timeout_decode.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.timeout_decode
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode

### RTL-0107: Implement precondition for timeout_decode: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.timeout_decode.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.preconditions.precondition_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: value=COUNTER advances.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.preconditions.precondition_0

### RTL-0108: Implement input for timeout_decode: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.timeout_decode.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.inputs.input_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["CR_INTTIME"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.inputs.input_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.inputs.input_0

### RTL-0109: Implement input for timeout_decode: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.timeout_decode.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.inputs.input_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["CR_RSTTIME"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.inputs.input_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.inputs.input_1

### RTL-0110: Implement input for timeout_decode: input_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.timeout_decode.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.inputs.input_2.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["COUNTER"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.inputs.input_2
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.inputs.input_2

### RTL-0111: Implement output for timeout_decode: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.timeout_decode.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.outputs.output_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["inttime_end and rsttime_end predicates"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.outputs.output_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.outputs.output_0

### RTL-0112: Implement state update for timeout_decode: TIMEOUT_PREDICATES

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.timeout_decode.state_updates.TIMEOUT_PREDICATES
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.state_updates.TIMEOUT_PREDICATES.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: name=TIMEOUT_PREDICATES; expr=0; width=2.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.state_updates.TIMEOUT_PREDICATES
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - TIMEOUT_PREDICATES width matches SSOT value 2
  - TIMEOUT_PREDICATES RTL expression implements SSOT expression 0
  - TIMEOUT_PREDICATES updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.timeout_decode.state_updates.TIMEOUT_PREDICATES

### RTL-0113: Implement side effect for timeout_decode: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.timeout_decode.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.side_effects.side_effect_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["Drives watchdog_tick state updates"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.side_effects.side_effect_0

### RTL-0114: Implement error case for timeout_decode: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.timeout_decode.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.timeout_decode.error_cases.error_case_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via function_model.transactions.timeout_decode.
SSOT item context: id=timeout_decode; name=Timeout interval decode; signal=["Unsupported encodings are not expected if table is locked"]; state=["TIMEOUT_PREDICATES"].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.timeout_decode.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: function_model.transactions.timeout_decode.error_cases.error_case_0
