# RTL Authoring Packet: module__cortex_m0lite_core__function_model

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 28
- Required tasks: 28

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0072: Implement RTL state owner for FL state pc_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=pc_q; width=XLEN; reset=RESET_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - pc_q width matches SSOT value XLEN
  - pc_q reset behavior matches SSOT value RESET_PC
- SSOT refs: function_model.state_variables.pc_q

### RTL-0073: Implement RTL state owner for FL state rf_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rf_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rf_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=rf_q; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rf_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - rf_q width matches SSOT value 32
  - rf_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rf_q

### RTL-0074: Implement RTL state owner for FL state nzcv_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.nzcv_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.nzcv_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=nzcv_q; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.nzcv_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - nzcv_q width matches SSOT value 4
  - nzcv_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.nzcv_q

### RTL-0075: Implement RTL state owner for FL state trap_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.trap_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.trap_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=trap_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.trap_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_q width matches SSOT value 1
  - trap_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.trap_q

### RTL-0076: Implement transaction FM_CPU_STEP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_CPU_STEP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_CPU_STEP.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: id=FM_CPU_STEP; name=cpu_cycle_step.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP

### RTL-0077: Implement precondition for FM_CPU_STEP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=core_rst_n_sync and bus_rst_n_sync are deasserted..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_0

### RTL-0078: Implement precondition for FM_CPU_STEP: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=instr_valid indicates a 16-bit instruction word is available from the IF path..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_1

### RTL-0079: Implement precondition for FM_CPU_STEP: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Any data access waits for the declared AHB-Lite ready/response contract..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.preconditions.precondition_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.preconditions.precondition_2

### RTL-0080: Implement output for FM_CPU_STEP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=pc_dbg.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_0

### RTL-0081: Implement output for FM_CPU_STEP: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=retire.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_1

### RTL-0082: Implement output for FM_CPU_STEP: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CPU_STEP.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.outputs.output_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=trap.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.outputs.output_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.outputs.output_2

### RTL-0083: Implement output rule for FM_CPU_STEP: retire_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=retire_pulse; port=retire; expr=1 when one instruction commits without trap, else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - retire_pulse width matches SSOT value 1
  - retire_pulse RTL expression implements SSOT expression 1 when one instruction commits without trap, else 0
  - DUT port retire is the implementation/observation point for retire_pulse
  - retire_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CPU_STEP.output_rules.retire_pulse

### RTL-0084: Implement output rule for FM_CPU_STEP: trap_flag

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=trap_flag; port=trap; expr=1 when illegal opcode, bus error, or misalignment is detected at commit boundary; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.output_rules.trap_flag
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_flag width matches SSOT value 1
  - trap_flag RTL expression implements SSOT expression 1 when illegal opcode, bus error, or misalignment is detected at commit boundary
  - DUT port trap is the implementation/observation point for trap_flag
  - trap_flag is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CPU_STEP.output_rules.trap_flag

### RTL-0085: Implement state update for FM_CPU_STEP: pc_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CPU_STEP.state_updates.pc_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.pc_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=pc_q; expr=pc+2 on normal flow; branch target on taken branch; trap vector on exception; width=XLEN; reset=RESET_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.pc_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - pc_q width matches SSOT value XLEN
  - pc_q reset behavior matches SSOT value RESET_PC
  - pc_q RTL expression implements SSOT expression pc+2 on normal flow; branch target on taken branch; trap vector on exception
  - pc_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CPU_STEP.state_updates.pc_q

### RTL-0086: Implement state update for FM_CPU_STEP: rf_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CPU_STEP.state_updates.rf_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.rf_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=rf_q; expr=register writeback on ALU/LDR/MOV commit only; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.rf_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - rf_q width matches SSOT value 32
  - rf_q reset behavior matches SSOT value 0
  - rf_q RTL expression implements SSOT expression register writeback on ALU/LDR/MOV commit only
  - rf_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CPU_STEP.state_updates.rf_q

### RTL-0087: Implement state update for FM_CPU_STEP: nzcv_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: name=nzcv_q; expr=updated by arithmetic/compare instructions per ARM-like semantics; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - nzcv_q width matches SSOT value 4
  - nzcv_q reset behavior matches SSOT value 0
  - nzcv_q RTL expression implements SSOT expression updated by arithmetic/compare instructions per ARM-like semantics
  - nzcv_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CPU_STEP.state_updates.nzcv_q

### RTL-0088: Implement side effect for FM_CPU_STEP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Successful ALU/MOV/LDR instructions update the destination architectural register at commit..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_0

### RTL-0089: Implement side effect for FM_CPU_STEP: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Arithmetic and compare instructions update NZCV according to flag_formulas..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_1

### RTL-0090: Implement side effect for FM_CPU_STEP: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Taken branches redirect pc_q and flush IF/ID before the next fetch..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_2

### RTL-0091: Implement side effect for FM_CPU_STEP: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_3.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Trap conditions suppress retire of the offending instruction and update exception metadata only..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.side_effects.side_effect_3

### RTL-0092: Implement error case for FM_CPU_STEP: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Illegal instruction encoding -> trap_code=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.error_cases.error_case_0

### RTL-0093: Implement error case for FM_CPU_STEP: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Instruction/data bus error (HRESP=1) -> trap_code=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.error_cases.error_case_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.error_cases.error_case_1

### RTL-0094: Implement error case for FM_CPU_STEP: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CPU_STEP.error_cases.error_case_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=Misaligned word access -> trap_code=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CPU_STEP.error_cases.error_case_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.transactions.FM_CPU_STEP.error_cases.error_case_2

### RTL-0095: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=R15 reflects architectural PC view at commit..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0096: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=No architectural state update on trapped instruction except exception metadata..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0097: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=At most one retire pulse per cycle..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0098: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=x0-like behavior is not used; all R0-R15 are normal ARM-style architectural registers..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0099: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.
SSOT item context: value=No instruction commits while trap_q is active until trap vectoring completes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: function_model.invariants.invariant_4
