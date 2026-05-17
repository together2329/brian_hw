# RTL Authoring Packet: module__pl330realverify_channel_fsm__function_model

- Kind: module
- Owner module: pl330realverify_channel_fsm
- Owner file: rtl/pl330realverify_channel_fsm.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 44
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.backpressure, cycle_model.ordering, cycle_model.pipeline, decomposition.units.channel_control, fsm, fsm.channel_fsm, function_model, function_model.transactions.FM_FAULT, function_model.transactions.FM_TRANSFER, function_model.transactions.FM_WFP
- Module slice: 1/5 section=function_model task_limit=48
- Slice rule: Owner module pl330realverify_channel_fsm is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_channel_fsm.clk_i <= dmaclk (sub_modules[1].connections[0])
  - pl330realverify_channel_fsm.rst_ni <= dmacresetn (sub_modules[1].connections[1])
  - pl330realverify_channel_fsm.start_cmd_i <= start_cmd (sub_modules[1].connections[2])
  - pl330realverify_channel_fsm.halt_cmd_i <= halt_cmd (sub_modules[1].connections[3])
  - pl330realverify_channel_fsm.selected_event_i <= selected_event (sub_modules[1].connections[4])
  - pl330realverify_channel_fsm.state_o <= channel_state (sub_modules[1].connections[5])
  - pl330realverify_channel_fsm.state_o <= channel_state (integration.connections[11])

## Tasks

### RTL-0139: Implement precondition for FM_TRANSFER: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_TRANSFER.preconditions.precondition_0

### RTL-0140: Implement precondition for FM_TRANSFER: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: value=start_cmd == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_TRANSFER.preconditions.precondition_1

### RTL-0141: Implement precondition for FM_TRANSFER: precondition_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: value=fault_inject == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.preconditions.precondition_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_TRANSFER.preconditions.precondition_2

### RTL-0142: Implement precondition for FM_TRANSFER: precondition_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_3.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: value=(sar % (DATA_WIDTH // 8)) == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.preconditions.precondition_3
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_TRANSFER.preconditions.precondition_3

### RTL-0143: Implement precondition for FM_TRANSFER: precondition_4

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.preconditions.precondition_4.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: value=(dar % (DATA_WIDTH // 8)) == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.preconditions.precondition_4
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_TRANSFER.preconditions.precondition_4

### RTL-0144: Implement input for FM_TRANSFER: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_TRANSFER.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.inputs.input_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["rdata"]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.inputs.input_0

### RTL-0145: Implement input for FM_TRANSFER: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_TRANSFER.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.inputs.input_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["rresp"]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.inputs.input_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.inputs.input_1

### RTL-0146: Implement input for FM_TRANSFER: input_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_TRANSFER.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.inputs.input_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["bresp"]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.inputs.input_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.inputs.input_2

### RTL-0147: Implement input for FM_TRANSFER: input_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_TRANSFER.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.inputs.input_3.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["loop_count"]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.inputs.input_3
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.inputs.input_3

### RTL-0148: Implement output for FM_TRANSFER: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_TRANSFER.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.outputs.output_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["Each successful beat writes the captured read data to the destination address."]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.outputs.output_0

### RTL-0149: Implement output for FM_TRANSFER: output_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_TRANSFER.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.outputs.output_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["Final successful beat sets status COMPLETED and raises the channel-complete pending bit."]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.outputs.output_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.outputs.output_1

### RTL-0150: Implement output rule for FM_TRANSFER: write_payload

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TRANSFER.output_rules.write_payload
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.output_rules.write_payload.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: name=write_payload; port=wdata; expr=rd_buf; width=64.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.output_rules.write_payload
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - write_payload width matches SSOT value 64
  - write_payload RTL expression implements SSOT expression rd_buf
  - DUT port wdata is the implementation/observation point for write_payload
  - write_payload is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TRANSFER.output_rules.write_payload

### RTL-0151: Implement output rule for FM_TRANSFER: write_strobes

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TRANSFER.output_rules.write_strobes
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.output_rules.write_strobes.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: name=write_strobes; port=wstrb; expr=(1 << (DATA_WIDTH // 8)) - 1; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.output_rules.write_strobes
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - write_strobes width matches SSOT value 8
  - write_strobes RTL expression implements SSOT expression (1 << (DATA_WIDTH // 8)) - 1
  - DUT port wstrb is the implementation/observation point for write_strobes
  - write_strobes is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TRANSFER.output_rules.write_strobes

### RTL-0152: Implement output rule for FM_TRANSFER: irq_after_transfer

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_TRANSFER.output_rules.irq_after_transfer
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.output_rules.irq_after_transfer.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: name=irq_after_transfer; port=dmac_irq; expr=1 if ((intstatus | complete_irq_mask) & inten) != 0 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.output_rules.irq_after_transfer
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - irq_after_transfer width matches SSOT value 1
  - irq_after_transfer RTL expression implements SSOT expression 1 if ((intstatus | complete_irq_mask) & inten) != 0 else 0
  - DUT port dmac_irq is the implementation/observation point for irq_after_transfer
  - irq_after_transfer is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_TRANSFER.output_rules.irq_after_transfer

### RTL-0160: Implement side effect for FM_TRANSFER: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TRANSFER.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.side_effects.side_effect_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["SAR and DAR increment by DATA_WIDTH/8 bytes after each successful write response."]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.side_effects.side_effect_0

### RTL-0161: Implement side effect for FM_TRANSFER: side_effect_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_TRANSFER.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.side_effects.side_effect_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_TRANSFER.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=["loop_remaining decrements after each successful write response."]; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.side_effects.side_effect_1

### RTL-0164: Implement transaction FM_WFP

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_WFP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_WFP.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: id=FM_WFP; name=wait_for_peripheral_event.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_WFP
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_WFP

### RTL-0165: Implement precondition for FM_WFP: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WFP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.preconditions.precondition_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_WFP.preconditions.precondition_0

### RTL-0166: Implement precondition for FM_WFP: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WFP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.preconditions.precondition_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: value=start_cmd == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_WFP.preconditions.precondition_1

### RTL-0167: Implement precondition for FM_WFP: precondition_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WFP.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.preconditions.precondition_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: value=wfp_enable == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.preconditions.precondition_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_WFP.preconditions.precondition_2

### RTL-0168: Implement input for FM_WFP: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_WFP.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.inputs.input_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: id=FM_WFP; name=wait_for_peripheral_event; port=["dmac_irq"]; signal=["peripheral_events"]; state=["status", "loop_remaining"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for wait_for_peripheral_event
- SSOT refs: function_model.transactions.FM_WFP.inputs.input_0

### RTL-0169: Implement input for FM_WFP: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_WFP.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.inputs.input_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: id=FM_WFP; name=wait_for_peripheral_event; port=["dmac_irq"]; signal=["wfp_event"]; state=["status", "loop_remaining"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.inputs.input_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for wait_for_peripheral_event
- SSOT refs: function_model.transactions.FM_WFP.inputs.input_1

### RTL-0170: Implement output for FM_WFP: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_WFP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.outputs.output_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: id=FM_WFP; name=wait_for_peripheral_event; port=["dmac_irq"]; signal=["Channel remains WAITING_FOR_PERIPHERAL until the selected event bit is sampled high."]; state=["status", "loop_remaining"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for wait_for_peripheral_event
- SSOT refs: function_model.transactions.FM_WFP.outputs.output_0

### RTL-0172: Implement state update for FM_WFP: status

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WFP.state_updates.status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.state_updates.status.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: name=status; expr=1 if selected_event == 1 else 2; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.state_updates.status
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - status width matches SSOT value 4
  - status RTL expression implements SSOT expression 1 if selected_event == 1 else 2
  - status updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WFP.state_updates.status

### RTL-0173: Implement state update for FM_WFP: loop_remaining

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WFP.state_updates.loop_remaining
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.state_updates.loop_remaining.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: name=loop_remaining; expr=loop_remaining; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.state_updates.loop_remaining
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - loop_remaining width matches SSOT value 8
  - loop_remaining RTL expression implements SSOT expression loop_remaining
  - loop_remaining updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WFP.state_updates.loop_remaining

### RTL-0174: Implement side effect for FM_WFP: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_WFP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WFP.side_effects.side_effect_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_WFP.
SSOT item context: id=FM_WFP; name=wait_for_peripheral_event; port=["dmac_irq"]; signal=["No AXI transaction is issued while selected_event is zero."]; state=["status", "loop_remaining"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WFP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for wait_for_peripheral_event
- SSOT refs: function_model.transactions.FM_WFP.side_effects.side_effect_0

### RTL-0175: Implement transaction FM_FAULT

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FAULT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FAULT.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FAULT
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_FAULT

### RTL-0176: Implement precondition for FM_FAULT: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FAULT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.preconditions.precondition_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=dmacresetn == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_FAULT.preconditions.precondition_0

### RTL-0177: Implement precondition for FM_FAULT: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FAULT.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.preconditions.precondition_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=fault_condition == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: function_model.transactions.FM_FAULT.preconditions.precondition_1

### RTL-0178: Implement input for FM_FAULT: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_FAULT.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.inputs.input_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=["fault_condition"]; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.inputs.input_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.inputs.input_0

### RTL-0179: Implement input for FM_FAULT: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_FAULT.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.inputs.input_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=["fault_code"]; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.inputs.input_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.inputs.input_1

### RTL-0180: Implement output for FM_FAULT: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_FAULT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.outputs.output_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=["Fault status is latched and a channel-fault pending interrupt is set."]; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.outputs.output_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.outputs.output_0

### RTL-0181: Implement output rule for FM_FAULT: irq_after_fault

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FAULT.output_rules.irq_after_fault
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.output_rules.irq_after_fault.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: name=irq_after_fault; port=dmac_irq; expr=1 if ((intstatus | fault_irq_mask) & inten) != 0 else 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.output_rules.irq_after_fault
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - irq_after_fault width matches SSOT value 1
  - irq_after_fault RTL expression implements SSOT expression 1 if ((intstatus | fault_irq_mask) & inten) != 0 else 0
  - DUT port dmac_irq is the implementation/observation point for irq_after_fault
  - irq_after_fault is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FAULT.output_rules.irq_after_fault

### RTL-0182: Implement state update for FM_FAULT: status

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FAULT.state_updates.status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.state_updates.status.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: name=status; expr=8; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.state_updates.status
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - status width matches SSOT value 4
  - status RTL expression implements SSOT expression 8
  - status updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FAULT.state_updates.status

### RTL-0183: Implement state update for FM_FAULT: error_code

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FAULT.state_updates.error_code
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.state_updates.error_code.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: name=error_code; expr=fault_code; width=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.state_updates.error_code
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - error_code width matches SSOT value 4
  - error_code RTL expression implements SSOT expression fault_code
  - error_code updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FAULT.state_updates.error_code

### RTL-0184: Implement state update for FM_FAULT: intstatus

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FAULT.state_updates.intstatus
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.state_updates.intstatus.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: name=intstatus; expr=intstatus | fault_irq_mask; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.state_updates.intstatus
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - intstatus width matches SSOT value 32
  - intstatus RTL expression implements SSOT expression intstatus | fault_irq_mask
  - intstatus updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FAULT.state_updates.intstatus

### RTL-0185: Implement side effect for FM_FAULT: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FAULT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.side_effects.side_effect_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=["First fault wins until software clears INTSTATUS and restarts the channel."]; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.side_effects.side_effect_0

### RTL-0186: Implement error case for FM_FAULT: ERR_UNALIGNED

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FAULT.error_cases.ERR_UNALIGNED
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.error_cases.ERR_UNALIGNED.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=[{"condition": "addresses_aligned == 0", "id": "ERR_UNALIGNED", "result": "status=FAULTED and error_code=ERR_UNALIGNE...; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.error_cases.ERR_UNALIGNED
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.error_cases.ERR_UNALIGNED

### RTL-0187: Implement error case for FM_FAULT: ERR_DEBUG_REJECT

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FAULT.error_cases.ERR_DEBUG_REJECT
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.error_cases.ERR_DEBUG_REJECT.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_completion; port=["dmac_irq"]; signal=[{"condition": "debug_execute == 1 and manager_busy == 1", "id": "ERR_DEBUG_REJECT", "result": "debug command rejecte...; state=["status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.error_cases.ERR_DEBUG_REJECT
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq"] is the implementation/observation point for fault_completion
- SSOT refs: function_model.transactions.FM_FAULT.error_cases.ERR_DEBUG_REJECT

### RTL-0197: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.
SSOT item context: port=["pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "dmac_irq"]; signal=not (write_beat_done == 1 and read_buffer_valid == 0); state=["rd_buf"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "dmac_irq"] is the implementation/observation point for ["pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "dmac_irq"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0198: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.
SSOT item context: port=["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "...; signal=not (status == 6 and error_code != 0); state=["status", "error_code"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "... is the implementation/observation point for ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "...
- SSOT refs: function_model.invariants.invariant_1

### RTL-0199: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.
SSOT item context: port=["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "...; signal=not (status == 8 and error_code == 0); state=["status", "error_code"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "... is the implementation/observation point for ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "pready", "pslverr", "prdata", "wdata", "wstrb", "dmac_irq", "...
- SSOT refs: function_model.invariants.invariant_2

### RTL-0200: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.
SSOT item context: port=["dmac_irq", "pready", "pslverr", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq", "dmac_irq", "dmac_irq"]; signal=(intstatus & (~0x1FFFF)) == 0; state=["intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq", "dmac_irq", "dmac_irq"] is the implementation/observation point for ["dmac_irq", "pready", "pslverr", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq", "dmac_irq", "dmac_irq"]
- SSOT refs: function_model.invariants.invariant_3

### RTL-0201: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via function_model.
SSOT item context: port=["dmac_irq", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq"]; signal=loop_remaining >= 0; state=["loop_remaining"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - DUT port ["dmac_irq", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq"] is the implementation/observation point for ["dmac_irq", "pready", "pslverr", "wdata", "wstrb", "dmac_irq", "dmac_irq"]
- SSOT refs: function_model.invariants.invariant_4
