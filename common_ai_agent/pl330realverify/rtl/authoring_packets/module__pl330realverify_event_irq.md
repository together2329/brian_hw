# RTL Authoring Packet: module__pl330realverify_event_irq

- Kind: module
- Owner module: pl330realverify_event_irq
- Owner file: rtl/pl330realverify_event_irq.sv
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
- Owner refs: decomposition.units.event_interrupt, function_model, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_WFP, interrupts, io_list, io_list.interfaces.event_inputs, io_list.interfaces.interrupt_output, registers, registers.register_list.CONTROL, registers.register_list.INTEN, registers.register_list.INTSTATUS
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_event_irq.clk_i <= dmaclk (sub_modules[5].connections[0])
  - pl330realverify_event_irq.rst_ni <= dmacresetn (sub_modules[5].connections[1])
  - pl330realverify_event_irq.peripheral_events_i <= peripheral_events (sub_modules[5].connections[2])
  - pl330realverify_event_irq.irq_o <= dmac_irq (sub_modules[5].connections[3])
  - pl330realverify_event_irq.peripheral_events_i <= peripheral_events (integration.connections[21])
  - pl330realverify_event_irq.irq_o <= dmac_irq (integration.connections[22])

## Tasks

### RTL-0171: Implement output rule for FM_WFP: irq_during_wfp

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_WFP.output_rules.irq_during_wfp
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.output_rules.irq_during_wfp.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_WFP.
SSOT item context: name=irq_during_wfp; port=dmac_irq; expr=1 if (intstatus & inten) != 0 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.output_rules.irq_during_wfp
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - irq_during_wfp width matches SSOT value 1
  - irq_during_wfp RTL expression implements SSOT expression 1 if (intstatus & inten) != 0 else 0
  - DUT port dmac_irq is the implementation/observation point for irq_during_wfp
  - irq_during_wfp is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_WFP.output_rules.irq_during_wfp

### RTL-0188: Implement transaction FM_IRQ_CLEAR

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_IRQ_CLEAR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: id=FM_IRQ_CLEAR; name=interrupt_write_one_to_clear.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR

### RTL-0189: Implement precondition for FM_IRQ_CLEAR: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_0.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_0

### RTL-0190: Implement precondition for FM_IRQ_CLEAR: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_1.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: value=apb_addr_intstatus == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_1

### RTL-0191: Implement precondition for FM_IRQ_CLEAR: precondition_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_2.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: value=psel == 1 and penable == 1 and pwrite == 1 and pready == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_2
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.preconditions.precondition_2

### RTL-0192: Implement input for FM_IRQ_CLEAR: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_IRQ_CLEAR.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.inputs.input_0.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: id=FM_IRQ_CLEAR; name=interrupt_write_one_to_clear; port=["dmac_irq"]; signal=["pwdata"]; state=["intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for interrupt_write_one_to_clear
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.inputs.input_0

### RTL-0193: Implement output for FM_IRQ_CLEAR: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_IRQ_CLEAR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.outputs.output_0.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: id=FM_IRQ_CLEAR; name=interrupt_write_one_to_clear; port=["dmac_irq"]; signal=["dmac_irq reflects the enabled pending status after the W1C clear."]; state=["intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for interrupt_write_one_to_clear
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.outputs.output_0

### RTL-0194: Implement output rule for FM_IRQ_CLEAR: irq_after_w1c

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_IRQ_CLEAR.output_rules.irq_after_w1c
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.output_rules.irq_after_w1c.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: name=irq_after_w1c; port=dmac_irq; expr=1 if ((intstatus & (~pwdata)) & inten) != 0 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.output_rules.irq_after_w1c
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - irq_after_w1c width matches SSOT value 1
  - irq_after_w1c RTL expression implements SSOT expression 1 if ((intstatus & (~pwdata)) & inten) != 0 else 0
  - DUT port dmac_irq is the implementation/observation point for irq_after_w1c
  - irq_after_w1c is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.output_rules.irq_after_w1c

### RTL-0195: Implement state update for FM_IRQ_CLEAR: intstatus

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_IRQ_CLEAR.state_updates.intstatus
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.state_updates.intstatus.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: name=intstatus; expr=intstatus & (~pwdata); width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.state_updates.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - intstatus width matches SSOT value 32
  - intstatus RTL expression implements SSOT expression intstatus & (~pwdata)
  - intstatus updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.state_updates.intstatus

### RTL-0196: Implement side effect for FM_IRQ_CLEAR: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_IRQ_CLEAR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IRQ_CLEAR.side_effects.side_effect_0.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via function_model.transactions.FM_IRQ_CLEAR.
SSOT item context: id=FM_IRQ_CLEAR; name=interrupt_write_one_to_clear; port=["dmac_irq"]; signal=["Only bits written as one are cleared; bits written as zero retain their prior value."]; state=["intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IRQ_CLEAR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for interrupt_write_one_to_clear
- SSOT refs: function_model.transactions.FM_IRQ_CLEAR.side_effects.side_effect_0

### RTL-0241: Implement CSR/register INTEN

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTEN.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTEN.
SSOT item context: name=INTEN; width=32; reset=0; access=rw; offset=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTEN
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - INTEN width matches SSOT value 32
  - INTEN reset behavior matches SSOT value 0
  - INTEN access policy rw is implemented without read/write shortcuts
  - INTEN decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.INTEN

### RTL-0242: Implement field INTEN.ch_complete_en

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.ch_complete_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.ch_complete_en.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTEN.
SSOT item context: name=ch_complete_en; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.ch_complete_en
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - ch_complete_en reset behavior matches SSOT value 0
  - ch_complete_en access policy rw is implemented without read/write shortcuts
  - ch_complete_en readback returns implemented RTL state when readable
  - ch_complete_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.ch_complete_en

### RTL-0243: Implement field INTEN.ch_fault_en

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.ch_fault_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.ch_fault_en.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTEN.
SSOT item context: name=ch_fault_en; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.ch_fault_en
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - ch_fault_en reset behavior matches SSOT value 0
  - ch_fault_en access policy rw is implemented without read/write shortcuts
  - ch_fault_en readback returns implemented RTL state when readable
  - ch_fault_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.ch_fault_en

### RTL-0244: Implement field INTEN.dbg_done_en

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.dbg_done_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.dbg_done_en.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTEN.
SSOT item context: name=dbg_done_en; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.dbg_done_en
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - dbg_done_en reset behavior matches SSOT value 0
  - dbg_done_en access policy rw is implemented without read/write shortcuts
  - dbg_done_en readback returns implemented RTL state when readable
  - dbg_done_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.dbg_done_en

### RTL-0245: Implement field INTEN.reserved_31_17

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.reserved_31_17
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.reserved_31_17.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTEN.
SSOT item context: name=reserved_31_17; reset=0; access=reserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.reserved_31_17
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - reserved_31_17 reset behavior matches SSOT value 0
  - reserved_31_17 access policy reserved is implemented without read/write shortcuts
  - reserved_31_17 readback returns implemented RTL state when readable
  - reserved_31_17 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.reserved_31_17

### RTL-0246: Implement CSR/register INTSTATUS

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTSTATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTSTATUS.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTSTATUS.
SSOT item context: name=INTSTATUS; width=32; reset=0; access=w1c; offset=36.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTSTATUS
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - INTSTATUS width matches SSOT value 32
  - INTSTATUS reset behavior matches SSOT value 0
  - INTSTATUS access policy w1c is implemented without read/write shortcuts
  - INTSTATUS decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.INTSTATUS

### RTL-0247: Implement field INTSTATUS.ch_complete

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTSTATUS.fields.ch_complete
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTSTATUS.fields.ch_complete.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTSTATUS.
SSOT item context: name=ch_complete; reset=0; access=w1c.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTSTATUS.fields.ch_complete
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - ch_complete reset behavior matches SSOT value 0
  - ch_complete access policy w1c is implemented without read/write shortcuts
  - ch_complete readback returns implemented RTL state when readable
  - ch_complete write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTSTATUS.fields.ch_complete

### RTL-0248: Implement field INTSTATUS.ch_fault

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTSTATUS.fields.ch_fault
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTSTATUS.fields.ch_fault.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTSTATUS.
SSOT item context: name=ch_fault; reset=0; access=w1c.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTSTATUS.fields.ch_fault
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - ch_fault reset behavior matches SSOT value 0
  - ch_fault access policy w1c is implemented without read/write shortcuts
  - ch_fault readback returns implemented RTL state when readable
  - ch_fault write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTSTATUS.fields.ch_fault

### RTL-0249: Implement field INTSTATUS.dbg_done

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTSTATUS.fields.dbg_done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTSTATUS.fields.dbg_done.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTSTATUS.
SSOT item context: name=dbg_done; reset=0; access=w1c.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTSTATUS.fields.dbg_done
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - dbg_done reset behavior matches SSOT value 0
  - dbg_done access policy w1c is implemented without read/write shortcuts
  - dbg_done readback returns implemented RTL state when readable
  - dbg_done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTSTATUS.fields.dbg_done

### RTL-0250: Implement field INTSTATUS.reserved_31_17

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTSTATUS.fields.reserved_31_17
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTSTATUS.fields.reserved_31_17.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.INTSTATUS.
SSOT item context: name=reserved_31_17; reset=0; access=reserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTSTATUS.fields.reserved_31_17
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - reserved_31_17 reset behavior matches SSOT value 0
  - reserved_31_17 access policy reserved is implemented without read/write shortcuts
  - reserved_31_17 readback returns implemented RTL state when readable
  - reserved_31_17 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTSTATUS.fields.reserved_31_17

### RTL-0264: Implement CSR/register CONTROL

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CONTROL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CONTROL.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=CONTROL; width=32; reset=0; access=rw; offset=276.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CONTROL
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - CONTROL width matches SSOT value 32
  - CONTROL reset behavior matches SSOT value 0
  - CONTROL access policy rw is implemented without read/write shortcuts
  - CONTROL decode uses SSOT address/offset 276
- SSOT refs: registers.register_list.CONTROL

### RTL-0265: Implement field CONTROL.start

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.start.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=start; reset=0; access=rw1p.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.start
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - start reset behavior matches SSOT value 0
  - start access policy rw1p is implemented without read/write shortcuts
  - start readback returns implemented RTL state when readable
  - start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.start

### RTL-0266: Implement field CONTROL.halt

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.halt
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.halt.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=halt; reset=0; access=rw1p.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.halt
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - halt reset behavior matches SSOT value 0
  - halt access policy rw1p is implemented without read/write shortcuts
  - halt readback returns implemented RTL state when readable
  - halt write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.halt

### RTL-0267: Implement field CONTROL.wfp_enable

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.wfp_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.wfp_enable.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=wfp_enable; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.wfp_enable
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - wfp_enable reset behavior matches SSOT value 0
  - wfp_enable access policy rw is implemented without read/write shortcuts
  - wfp_enable readback returns implemented RTL state when readable
  - wfp_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.wfp_enable

### RTL-0268: Implement field CONTROL.wfp_event

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.wfp_event
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.wfp_event.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=wfp_event; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.wfp_event
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - wfp_event reset behavior matches SSOT value 0
  - wfp_event access policy rw is implemented without read/write shortcuts
  - wfp_event readback returns implemented RTL state when readable
  - wfp_event write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.wfp_event

### RTL-0269: Implement field CONTROL.fault_inject

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.fault_inject
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.fault_inject.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=fault_inject; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.fault_inject
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - fault_inject reset behavior matches SSOT value 0
  - fault_inject access policy rw is implemented without read/write shortcuts
  - fault_inject readback returns implemented RTL state when readable
  - fault_inject write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.fault_inject

### RTL-0270: Implement field CONTROL.reserved_31_17

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.reserved_31_17
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.reserved_31_17.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via registers.register_list.CONTROL.
SSOT item context: name=reserved_31_17; reset=0; access=reserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.reserved_31_17
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - reserved_31_17 reset behavior matches SSOT value 0
  - reserved_31_17 access policy reserved is implemented without read/write shortcuts
  - reserved_31_17 readback returns implemented RTL state when readable
  - reserved_31_17 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.reserved_31_17

### RTL-0380: Prove module pl330realverify_event_irq is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.pl330realverify_event_irq.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330realverify_event_irq.module_equivalence.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330realverify_event_irq.module_equivalence
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
- SSOT refs: sub_modules.pl330realverify_event_irq.module_equivalence

### RTL-0086: Implement and connect port peripheral_events

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.event_inputs.ports.peripheral_events
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.event_inputs.ports.peripheral_events.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via io_list.interfaces.event_inputs.
SSOT item context: name=peripheral_events; width=32; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.event_inputs.ports.peripheral_events
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - peripheral_events width matches SSOT value 32
  - peripheral_events port direction remains input
- SSOT refs: io_list.interfaces.event_inputs.ports.peripheral_events

### RTL-0087: Implement and connect port dmac_irq

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_output.ports.dmac_irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_output.ports.dmac_irq.
Owner: pl330realverify_event_irq in rtl/pl330realverify_event_irq.sv via io_list.interfaces.interrupt_output.
SSOT item context: name=dmac_irq; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_output.ports.dmac_irq
  - Primary implementation evidence is in rtl/pl330realverify_event_irq.sv
  - dmac_irq width matches SSOT value 1
  - dmac_irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt_output.ports.dmac_irq
