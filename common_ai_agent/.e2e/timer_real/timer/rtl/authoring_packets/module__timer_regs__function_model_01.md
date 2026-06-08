# RTL Authoring Packet: module__timer_regs__function_model_01

- Kind: module
- Owner module: timer_regs
- Owner file: rtl/timer_regs.sv
- Task count: 48
- Required tasks: 48

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
- Owner refs: error_handling, function_model, function_model.invariants, function_model.state_variables, function_model.transactions.FM_APB_READ_STATUS, function_model.transactions.FM_APB_UNMAPPED_ACCESS, function_model.transactions.FM_APB_WRITE_CTRL, function_model.transactions.FM_APB_WRITE_LOAD, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.LOAD, registers.register_list.STATUS
- Module slice: 1/7 section=function_model task_limit=48
- Slice rule: Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])

## Tasks

### RTL-0042: Implement RTL state owner for FL state irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.irq_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.state_variables.
SSOT item context: name=irq_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.irq_q

### RTL-0043: Implement transaction FM_APB_WRITE_LOAD

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: id=FM_APB_WRITE_LOAD; name=write_load_register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD

### RTL-0044: Implement precondition for FM_APB_WRITE_LOAD: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 1 and paddr == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.preconditions.precondition_0

### RTL-0045: Implement input for FM_APB_WRITE_LOAD: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.inputs.input_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: id=FM_APB_WRITE_LOAD; name=write_load_register; port=["pready", "pslverr"]; signal=["pwdata"]; state=["load_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.inputs.input_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_load_register
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.inputs.input_0

### RTL-0046: Implement output for FM_APB_WRITE_LOAD: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: value=pready == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_0

### RTL-0047: Implement output for FM_APB_WRITE_LOAD: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: value=pslverr == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_1
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.output_1

### RTL-0048: Implement output for FM_APB_WRITE_LOAD: pready_write_load

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pready_write_load
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pready_write_load.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=pready_write_load; port=pready; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.pready_write_load
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_write_load RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_write_load
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pready_write_load

### RTL-0049: Implement output for FM_APB_WRITE_LOAD: pslverr_write_load

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pslverr_write_load
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pslverr_write_load.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=pslverr_write_load; port=pslverr; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.pslverr_write_load
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_write_load RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_write_load
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.pslverr_write_load

### RTL-0050: Implement output for FM_APB_WRITE_LOAD: load_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.load_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.load_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: state=load_q; expr=pwdata & 0xffffffff.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.load_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_WRITE_LOAD.outputs.load_q RTL expression implements SSOT expression pwdata & 0xffffffff
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.load_q

### RTL-0051: Implement output for FM_APB_WRITE_LOAD: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.outputs.irq_q

### RTL-0052: Implement output rule for FM_APB_WRITE_LOAD: pready_write_load

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pready_write_load
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pready_write_load.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=pready_write_load; port=pready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pready_write_load
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_write_load width matches SSOT value 1
  - pready_write_load RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_write_load
  - pready_write_load is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pready_write_load

### RTL-0053: Implement output rule for FM_APB_WRITE_LOAD: pslverr_write_load

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pslverr_write_load
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pslverr_write_load.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=pslverr_write_load; port=pslverr; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pslverr_write_load
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_write_load width matches SSOT value 1
  - pslverr_write_load RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_write_load
  - pslverr_write_load is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.output_rules.pslverr_write_load

### RTL-0054: Implement state update for FM_APB_WRITE_LOAD: load_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.load_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.load_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=load_q; expr=pwdata & 0xffffffff; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.state_updates.load_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - load_q width matches SSOT value 32
  - load_q RTL expression implements SSOT expression pwdata & 0xffffffff
  - load_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.load_q

### RTL-0055: Implement state update for FM_APB_WRITE_LOAD: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.state_updates.irq_q

### RTL-0056: Implement side effect for FM_APB_WRITE_LOAD: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: id=FM_APB_WRITE_LOAD; name=write_load_register; port=["pready", "pslverr"]; signal=["load_q becomes pwdata[31:0]."]; state=["load_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_load_register
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_0

### RTL-0057: Implement side effect for FM_APB_WRITE_LOAD: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_LOAD.
SSOT item context: id=FM_APB_WRITE_LOAD; name=write_load_register; port=["pready", "pslverr"]; signal=["irq_q is deasserted for this APB write transaction."]; state=["load_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_load_register
- SSOT refs: function_model.transactions.FM_APB_WRITE_LOAD.side_effects.side_effect_1

### RTL-0058: Implement transaction FM_APB_WRITE_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: id=FM_APB_WRITE_CTRL; name=write_ctrl_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL

### RTL-0059: Implement precondition for FM_APB_WRITE_CTRL: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 1 and paddr == 4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.preconditions.precondition_0

### RTL-0060: Implement input for FM_APB_WRITE_CTRL: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.inputs.input_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: id=FM_APB_WRITE_CTRL; name=write_ctrl_enable; port=["pready", "pslverr"]; signal=["pwdata"]; state=["enable_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.inputs.input_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_ctrl_enable
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.inputs.input_0

### RTL-0061: Implement output for FM_APB_WRITE_CTRL: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: value=pready == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_0

### RTL-0062: Implement output for FM_APB_WRITE_CTRL: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: value=pslverr == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_1
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.output_1

### RTL-0063: Implement output for FM_APB_WRITE_CTRL: pready_write_ctrl

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pready_write_ctrl
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pready_write_ctrl.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=pready_write_ctrl; port=pready; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.pready_write_ctrl
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_write_ctrl RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_write_ctrl
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pready_write_ctrl

### RTL-0064: Implement output for FM_APB_WRITE_CTRL: pslverr_write_ctrl

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pslverr_write_ctrl
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pslverr_write_ctrl.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=pslverr_write_ctrl; port=pslverr; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.pslverr_write_ctrl
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_write_ctrl RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_write_ctrl
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.pslverr_write_ctrl

### RTL-0065: Implement output for FM_APB_WRITE_CTRL: enable_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.enable_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.enable_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: state=enable_q; expr=pwdata & 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.enable_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_WRITE_CTRL.outputs.enable_q RTL expression implements SSOT expression pwdata & 1
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.enable_q

### RTL-0066: Implement output for FM_APB_WRITE_CTRL: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.outputs.irq_q

### RTL-0067: Implement output rule for FM_APB_WRITE_CTRL: pready_write_ctrl

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pready_write_ctrl
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pready_write_ctrl.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=pready_write_ctrl; port=pready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pready_write_ctrl
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_write_ctrl width matches SSOT value 1
  - pready_write_ctrl RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_write_ctrl
  - pready_write_ctrl is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pready_write_ctrl

### RTL-0068: Implement output rule for FM_APB_WRITE_CTRL: pslverr_write_ctrl

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pslverr_write_ctrl
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pslverr_write_ctrl.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=pslverr_write_ctrl; port=pslverr; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pslverr_write_ctrl
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_write_ctrl width matches SSOT value 1
  - pslverr_write_ctrl RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_write_ctrl
  - pslverr_write_ctrl is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.output_rules.pslverr_write_ctrl

### RTL-0069: Implement state update for FM_APB_WRITE_CTRL: enable_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.enable_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.enable_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=enable_q; expr=pwdata & 1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.state_updates.enable_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - enable_q width matches SSOT value 1
  - enable_q RTL expression implements SSOT expression pwdata & 1
  - enable_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.enable_q

### RTL-0070: Implement state update for FM_APB_WRITE_CTRL: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.state_updates.irq_q

### RTL-0071: Implement side effect for FM_APB_WRITE_CTRL: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: id=FM_APB_WRITE_CTRL; name=write_ctrl_enable; port=["pready", "pslverr"]; signal=["enable_q becomes pwdata[0]."]; state=["enable_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_ctrl_enable
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_0

### RTL-0072: Implement side effect for FM_APB_WRITE_CTRL: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: id=FM_APB_WRITE_CTRL; name=write_ctrl_enable; port=["pready", "pslverr"]; signal=["If ENABLE is written 0, count_q holds its current value on subsequent timer ticks."]; state=["enable_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_ctrl_enable
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_1

### RTL-0073: Implement side effect for FM_APB_WRITE_CTRL: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_2.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_WRITE_CTRL.
SSOT item context: id=FM_APB_WRITE_CTRL; name=write_ctrl_enable; port=["pready", "pslverr"]; signal=["irq_q is deasserted for this APB write transaction."]; state=["enable_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for write_ctrl_enable
- SSOT refs: function_model.transactions.FM_APB_WRITE_CTRL.side_effects.side_effect_2

### RTL-0074: Implement transaction FM_APB_READ_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_READ_STATUS
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: id=FM_APB_READ_STATUS; name=read_status_current_count.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS

### RTL-0075: Implement precondition for FM_APB_READ_STATUS: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_READ_STATUS.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.preconditions.precondition_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 0 and paddr == 8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.preconditions.precondition_0

### RTL-0076: Implement output for FM_APB_READ_STATUS: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: value=prdata == count_q.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.output_0
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.output_0

### RTL-0077: Implement output for FM_APB_READ_STATUS: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: value=pready == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.output_1
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.output_1

### RTL-0078: Implement output for FM_APB_READ_STATUS: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.output_2.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: value=pslverr == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.output_2
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.output_2

### RTL-0079: Implement output for FM_APB_READ_STATUS: prdata_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.prdata_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.prdata_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=prdata_status; port=prdata; expr=count_q & 0xffffffff.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.prdata_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - prdata_status RTL expression implements SSOT expression count_q & 0xffffffff
  - DUT port prdata is the implementation/observation point for prdata_status
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.prdata_status

### RTL-0080: Implement output for FM_APB_READ_STATUS: pready_read_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.pready_read_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.pready_read_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=pready_read_status; port=pready; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.pready_read_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_read_status RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_read_status
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.pready_read_status

### RTL-0081: Implement output for FM_APB_READ_STATUS: pslverr_read_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.pslverr_read_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.pslverr_read_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=pslverr_read_status; port=pslverr; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.pslverr_read_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_read_status RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_read_status
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.pslverr_read_status

### RTL-0082: Implement output for FM_APB_READ_STATUS: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: state=irq_q; expr=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q RTL expression implements SSOT expression 0
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.outputs.irq_q

### RTL-0083: Implement output rule for FM_APB_READ_STATUS: prdata_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.prdata_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.prdata_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=prdata_status; port=prdata; expr=count_q & 0xffffffff; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.output_rules.prdata_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - prdata_status width matches SSOT value 32
  - prdata_status RTL expression implements SSOT expression count_q & 0xffffffff
  - DUT port prdata is the implementation/observation point for prdata_status
  - prdata_status is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.output_rules.prdata_status

### RTL-0084: Implement output rule for FM_APB_READ_STATUS: pready_read_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.pready_read_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.pready_read_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=pready_read_status; port=pready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.output_rules.pready_read_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pready_read_status width matches SSOT value 1
  - pready_read_status RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for pready_read_status
  - pready_read_status is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.output_rules.pready_read_status

### RTL-0085: Implement output rule for FM_APB_READ_STATUS: pslverr_read_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.pslverr_read_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.output_rules.pslverr_read_status.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=pslverr_read_status; port=pslverr; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.output_rules.pslverr_read_status
  - Primary implementation evidence is in rtl/timer_regs.sv
  - pslverr_read_status width matches SSOT value 1
  - pslverr_read_status RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_read_status
  - pslverr_read_status is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.output_rules.pslverr_read_status

### RTL-0086: Implement state update for FM_APB_READ_STATUS: irq_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: name=irq_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q
  - Primary implementation evidence is in rtl/timer_regs.sv
  - irq_q width matches SSOT value 1
  - irq_q RTL expression implements SSOT expression 0
  - irq_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.state_updates.irq_q

### RTL-0087: Implement side effect for FM_APB_READ_STATUS: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_0.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: id=FM_APB_READ_STATUS; name=read_status_current_count; port=["prdata", "pready", "pslverr"]; signal=["STATUS read has no count_q side effect."]; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["prdata", "pready", "pslverr"] is the implementation/observation point for read_status_current_count
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_0

### RTL-0088: Implement side effect for FM_APB_READ_STATUS: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_1.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_APB_READ_STATUS.
SSOT item context: id=FM_APB_READ_STATUS; name=read_status_current_count; port=["prdata", "pready", "pslverr"]; signal=["irq_q is deasserted for this APB read transaction."]; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["prdata", "pready", "pslverr"] is the implementation/observation point for read_status_current_count
- SSOT refs: function_model.transactions.FM_APB_READ_STATUS.side_effects.side_effect_1

### RTL-0089: Implement transaction FM_TICK_DECREMENT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TICK_DECREMENT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TICK_DECREMENT.
Owner: timer_regs in rtl/timer_regs.sv via function_model.transactions.FM_TICK_DECREMENT.
SSOT item context: id=FM_TICK_DECREMENT; name=enabled_decrement_nonzero.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TICK_DECREMENT
  - Primary implementation evidence is in rtl/timer_regs.sv
- SSOT refs: function_model.transactions.FM_TICK_DECREMENT
