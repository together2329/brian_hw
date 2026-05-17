# RTL Authoring Packet: module__pl330realverify_regs__function_model

- Kind: module
- Owner module: pl330realverify_regs
- Owner file: rtl/pl330realverify_regs.sv
- Task count: 41
- Required tasks: 41

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
- LLM-actionable open tasks: 41
- Human-locked open tasks: 0
- Owner refs: cycle_model.handshake_rules.APB_ACCESS, decomposition.units.apb_registers, error_handling, error_handling.error_sources, function_model.transactions.FM_APB_READ, function_model.transactions.FM_APB_WRITE, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_RESET, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, rtl_contract, rtl_contract.input_map
- Module slice: 2/8 section=function_model task_limit=48
- Slice rule: Owner module pl330realverify_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])

## Tasks

### RTL-0097: Implement transaction FM_RESET

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RESET.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset_architecture.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RESET
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_RESET

### RTL-0098: Implement precondition for FM_RESET: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: value=dmacresetn == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_RESET.preconditions.precondition_0

### RTL-0099: Implement input for FM_RESET: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_RESET.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.inputs.input_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset_architecture; port=["dmac_irq", "pready", "pslverr"]; signal=["dmacresetn"]; state=["sar", "dar", "loop_remaining", "status", "error_code", "rd_buf", "intstatus", "inten"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["dmac_irq", "pready", "pslverr"] is the implementation/observation point for reset_architecture
- SSOT refs: function_model.transactions.FM_RESET.inputs.input_0

### RTL-0100: Implement output for FM_RESET: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset_architecture; port=["dmac_irq", "pready", "pslverr"]; signal=["All externally visible output valids and interrupt are deasserted during reset."]; state=["sar", "dar", "loop_remaining", "status", "error_code", "rd_buf", "intstatus", "inten"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["dmac_irq", "pready", "pslverr"] is the implementation/observation point for reset_architecture
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_0

### RTL-0101: Implement output rule for FM_RESET: irq_reset

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.irq_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.irq_reset.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=irq_reset; port=dmac_irq; expr=0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.irq_reset
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - irq_reset width matches SSOT value 1
  - irq_reset RTL expression implements SSOT expression 0
  - DUT port dmac_irq is the implementation/observation point for irq_reset
  - irq_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.irq_reset

### RTL-0102: Implement output rule for FM_RESET: pready_reset

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.pready_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.pready_reset.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=pready_reset; port=pready; expr=0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.pready_reset
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - pready_reset width matches SSOT value 1
  - pready_reset RTL expression implements SSOT expression 0
  - DUT port pready is the implementation/observation point for pready_reset
  - pready_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.pready_reset

### RTL-0103: Implement output rule for FM_RESET: pslverr_reset

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.pslverr_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.pslverr_reset.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=pslverr_reset; port=pslverr; expr=0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.pslverr_reset
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - pslverr_reset width matches SSOT value 1
  - pslverr_reset RTL expression implements SSOT expression 0
  - DUT port pslverr is the implementation/observation point for pslverr_reset
  - pslverr_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.pslverr_reset

### RTL-0104: Implement state update for FM_RESET: sar

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.sar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.sar.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=sar; expr=0; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.sar
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - sar width matches SSOT value 32
  - sar RTL expression implements SSOT expression 0
  - sar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.sar

### RTL-0105: Implement state update for FM_RESET: dar

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.dar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.dar.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=dar; expr=0; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.dar
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - dar width matches SSOT value 32
  - dar RTL expression implements SSOT expression 0
  - dar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.dar

### RTL-0106: Implement state update for FM_RESET: loop_remaining

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.loop_remaining
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.loop_remaining.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=loop_remaining; expr=0; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.loop_remaining
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - loop_remaining width matches SSOT value 8
  - loop_remaining RTL expression implements SSOT expression 0
  - loop_remaining updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.loop_remaining

### RTL-0107: Implement state update for FM_RESET: status

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.status.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=status; expr=0; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.status
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - status width matches SSOT value 4
  - status RTL expression implements SSOT expression 0
  - status updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.status

### RTL-0108: Implement state update for FM_RESET: error_code

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.error_code
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.error_code.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=error_code; expr=0; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.error_code
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - error_code width matches SSOT value 4
  - error_code RTL expression implements SSOT expression 0
  - error_code updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.error_code

### RTL-0109: Implement state update for FM_RESET: rd_buf

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.rd_buf
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.rd_buf.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=rd_buf; expr=0; width=64.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.rd_buf
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - rd_buf width matches SSOT value 64
  - rd_buf RTL expression implements SSOT expression 0
  - rd_buf updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.rd_buf

### RTL-0110: Implement state update for FM_RESET: intstatus

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.intstatus
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.intstatus.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=intstatus; expr=0; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - intstatus width matches SSOT value 32
  - intstatus RTL expression implements SSOT expression 0
  - intstatus updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.intstatus

### RTL-0111: Implement state update for FM_RESET: inten

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.inten
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.inten.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: name=inten; expr=0; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.inten
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - inten width matches SSOT value 32
  - inten RTL expression implements SSOT expression 0
  - inten updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.inten

### RTL-0112: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset_architecture; port=["dmac_irq", "pready", "pslverr"]; signal=["All architectural state returns to declared reset values."]; state=["sar", "dar", "loop_remaining", "status", "error_code", "rd_buf", "intstatus", "inten"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["dmac_irq", "pready", "pslverr"] is the implementation/observation point for reset_architecture
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0113: Implement transaction FM_APB_WRITE

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_WRITE.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE

### RTL-0114: Implement precondition for FM_APB_WRITE: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.preconditions.precondition_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE.preconditions.precondition_0

### RTL-0115: Implement precondition for FM_APB_WRITE: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_WRITE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.preconditions.precondition_1.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 1 and pready == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_WRITE.preconditions.precondition_1

### RTL-0116: Implement input for FM_APB_WRITE: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_WRITE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.inputs.input_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=["paddr"]; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.inputs.input_0

### RTL-0117: Implement input for FM_APB_WRITE: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_WRITE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.inputs.input_1.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=["pwdata"]; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.inputs.input_1
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.inputs.input_1

### RTL-0118: Implement input for FM_APB_WRITE: input_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_WRITE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.inputs.input_2.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=["pstrb"]; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.inputs.input_2
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.inputs.input_2

### RTL-0119: Implement output for FM_APB_WRITE: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.outputs.output_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=["pready acknowledges the access; pslverr reports illegal address/access/strobe."]; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.outputs.output_0

### RTL-0120: Implement output rule for FM_APB_WRITE: apb_write_ready

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_ready.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=apb_write_ready; port=pready; expr=1; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.output_rules.apb_write_ready
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - apb_write_ready width matches SSOT value 1
  - apb_write_ready RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for apb_write_ready
  - apb_write_ready is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_ready

### RTL-0121: Implement output rule for FM_APB_WRITE: apb_write_error

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_error.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=apb_write_error; port=pslverr; expr=1 if illegal_apb_access == 1 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.output_rules.apb_write_error
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - apb_write_error width matches SSOT value 1
  - apb_write_error RTL expression implements SSOT expression 1 if illegal_apb_access == 1 else 0
  - DUT port pslverr is the implementation/observation point for apb_write_error
  - apb_write_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_WRITE.output_rules.apb_write_error

### RTL-0122: Implement state update for FM_APB_WRITE: inten

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE.state_updates.inten
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.state_updates.inten.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=inten; expr=((inten & (~write_mask_32)) | (pwdata & write_mask_32)) if (apb_addr_inten == 1 and illegal_apb_access == 0) else inten; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.state_updates.inten
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - inten width matches SSOT value 32
  - inten RTL expression implements SSOT expression ((inten & (~write_mask_32)) | (pwdata & write_mask_32)) if (apb_addr_inten == 1 and illegal_apb_access == 0) else inten
  - inten updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE.state_updates.inten

### RTL-0123: Implement state update for FM_APB_WRITE: intstatus

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE.state_updates.intstatus
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.state_updates.intstatus.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=intstatus; expr=(intstatus & (~pwdata)) if (apb_addr_intstatus == 1 and illegal_apb_access == 0) else intstatus; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.state_updates.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - intstatus width matches SSOT value 32
  - intstatus RTL expression implements SSOT expression (intstatus & (~pwdata)) if (apb_addr_intstatus == 1 and illegal_apb_access == 0) else intstatus
  - intstatus updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE.state_updates.intstatus

### RTL-0124: Implement state update for FM_APB_WRITE: sar

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE.state_updates.sar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.state_updates.sar.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=sar; expr=pwdata if (apb_addr_sar == 1 and channel_idle == 1 and illegal_apb_access == 0) else sar; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.state_updates.sar
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - sar width matches SSOT value 32
  - sar RTL expression implements SSOT expression pwdata if (apb_addr_sar == 1 and channel_idle == 1 and illegal_apb_access == 0) else sar
  - sar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE.state_updates.sar

### RTL-0125: Implement state update for FM_APB_WRITE: dar

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_WRITE.state_updates.dar
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.state_updates.dar.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: name=dar; expr=pwdata if (apb_addr_dar == 1 and channel_idle == 1 and illegal_apb_access == 0) else dar; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.state_updates.dar
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - dar width matches SSOT value 32
  - dar RTL expression implements SSOT expression pwdata if (apb_addr_dar == 1 and channel_idle == 1 and illegal_apb_access == 0) else dar
  - dar updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_WRITE.state_updates.dar

### RTL-0126: Implement side effect for FM_APB_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.side_effects.side_effect_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=["Writable register fields update only through declared write_effect rules; reserved fields ignore writes."]; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.side_effects.side_effect_0

### RTL-0127: Implement error case for FM_APB_WRITE: ERR_APB_ILLEGAL

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APB_WRITE.error_cases.ERR_APB_ILLEGAL
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_WRITE.error_cases.ERR_APB_ILLEGAL.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_WRITE.
SSOT item context: id=FM_APB_WRITE; name=apb_register_write; port=["pready", "pslverr"]; signal=[{"condition": "illegal_apb_access == 1", "id": "ERR_APB_ILLEGAL", "result": "pslverr asserted for the completing acc...; state=["inten", "intstatus", "sar", "dar"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_WRITE.error_cases.ERR_APB_ILLEGAL
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for apb_register_write
- SSOT refs: function_model.transactions.FM_APB_WRITE.error_cases.ERR_APB_ILLEGAL

### RTL-0128: Implement transaction FM_APB_READ

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_READ.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: id=FM_APB_READ; name=apb_register_read.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ

### RTL-0129: Implement precondition for FM_APB_READ: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.preconditions.precondition_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ.preconditions.precondition_0

### RTL-0130: Implement precondition for FM_APB_READ: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_READ.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.preconditions.precondition_1.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 0 and pready == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: function_model.transactions.FM_APB_READ.preconditions.precondition_1

### RTL-0131: Implement input for FM_APB_READ: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_APB_READ.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.inputs.input_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: id=FM_APB_READ; name=apb_register_read; port=["pready", "pslverr", "prdata"]; signal=["paddr"]; state=["status"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr", "prdata"] is the implementation/observation point for apb_register_read
- SSOT refs: function_model.transactions.FM_APB_READ.inputs.input_0

### RTL-0132: Implement output for FM_APB_READ: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.outputs.output_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: id=FM_APB_READ; name=apb_register_read; port=["pready", "pslverr", "prdata"]; signal=["prdata returns the decoded register value with reserved bits forced to zero."]; state=["status"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr", "prdata"] is the implementation/observation point for apb_register_read
- SSOT refs: function_model.transactions.FM_APB_READ.outputs.output_0

### RTL-0133: Implement output rule for FM_APB_READ: apb_read_ready

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_ready.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: name=apb_read_ready; port=pready; expr=1; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.output_rules.apb_read_ready
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - apb_read_ready width matches SSOT value 1
  - apb_read_ready RTL expression implements SSOT expression 1
  - DUT port pready is the implementation/observation point for apb_read_ready
  - apb_read_ready is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ.output_rules.apb_read_ready

### RTL-0134: Implement output rule for FM_APB_READ: apb_read_error

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_error.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: name=apb_read_error; port=pslverr; expr=1 if illegal_apb_access == 1 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.output_rules.apb_read_error
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - apb_read_error width matches SSOT value 1
  - apb_read_error RTL expression implements SSOT expression 1 if illegal_apb_access == 1 else 0
  - DUT port pslverr is the implementation/observation point for apb_read_error
  - apb_read_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ.output_rules.apb_read_error

### RTL-0135: Implement output rule for FM_APB_READ: apb_read_data

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.output_rules.apb_read_data.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: name=apb_read_data; port=prdata; expr=0 if illegal_apb_access == 1 else (register_read_value & 0xFFFFFFFF); width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.output_rules.apb_read_data
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - apb_read_data width matches SSOT value 32
  - apb_read_data RTL expression implements SSOT expression 0 if illegal_apb_access == 1 else (register_read_value & 0xFFFFFFFF)
  - DUT port prdata is the implementation/observation point for apb_read_data
  - apb_read_data is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_READ.output_rules.apb_read_data

### RTL-0136: Implement state update for FM_APB_READ: status

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_READ.state_updates.status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.state_updates.status.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: name=status; expr=status; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.state_updates.status
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - status width matches SSOT value 4
  - status RTL expression implements SSOT expression status
  - status updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_READ.state_updates.status

### RTL-0137: Implement side effect for FM_APB_READ: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_READ.side_effects.side_effect_0.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via function_model.transactions.FM_APB_READ.
SSOT item context: id=FM_APB_READ; name=apb_register_read; port=["pready", "pslverr", "prdata"]; signal=["APB reads do not alter architectural state."]; state=["status"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DUT port ["pready", "pslverr", "prdata"] is the implementation/observation point for apb_register_read
- SSOT refs: function_model.transactions.FM_APB_READ.side_effects.side_effect_0
