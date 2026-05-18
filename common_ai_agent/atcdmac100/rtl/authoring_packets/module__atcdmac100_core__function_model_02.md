# RTL Authoring Packet: module__atcdmac100_core__function_model_02

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
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
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 3/14 section=function_model task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= hresetn (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0105: Implement output rule for FM_AHB_WRITE: hready_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.hready_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.hready_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hready_write; port=hready; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.output_rules.hready_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hready_write width matches SSOT value 1
  - hready_write RTL expression implements SSOT expression 1
  - DUT port hready is the implementation/observation point for hready_write
  - hready_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_WRITE.output_rules.hready_write

### RTL-0106: Implement output rule for FM_AHB_WRITE: hresp_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hresp_write; port=hresp; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresp_write width matches SSOT value 2
  - hresp_write RTL expression implements SSOT expression 0
  - DUT port hresp is the implementation/observation point for hresp_write
  - hresp_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write

### RTL-0107: Implement output rule for FM_AHB_WRITE: dma_int_after_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_int_after_write; port=dma_int; expr=reduction_or((int_tc | int_abort | int_error) & ch_enable); width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int_after_write width matches SSOT value 1
  - dma_int_after_write RTL expression implements SSOT expression reduction_or((int_tc | int_abort | int_error) & ch_enable)
  - DUT port dma_int is the implementation/observation point for dma_int_after_write
  - dma_int_after_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write

### RTL-0108: Implement state update for FM_AHB_WRITE: dmac_reset_pulse

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=dmac_reset_pulse; expr=1 if haddr == 32 and (hwdata & 1) else 0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse width matches SSOT value 1
  - function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse RTL expression implements SSOT expression 1 if haddr == 32 and (hwdata & 1) else 0
  - function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse

### RTL-0109: Implement state update for FM_AHB_WRITE: int_tc

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_tc; expr=int_tc & ~((hwdata >> 16) & 255) if haddr == 48 else int_tc; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.state_updates.int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_tc width matches SSOT value 8
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_tc RTL expression implements SSOT expression int_tc & ~((hwdata >> 16) & 255) if haddr == 48 else int_tc
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_tc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AHB_WRITE.state_updates.int_tc

### RTL-0110: Implement state update for FM_AHB_WRITE: int_abort

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_abort
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_abort; expr=int_abort & ~((hwdata >> 8) & 255) if haddr == 48 else int_abort; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.state_updates.int_abort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_abort width matches SSOT value 8
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_abort RTL expression implements SSOT expression int_abort & ~((hwdata >> 8) & 255) if haddr == 48 else int_abort
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_abort updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AHB_WRITE.state_updates.int_abort

### RTL-0111: Implement state update for FM_AHB_WRITE: int_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_error; expr=int_error & ~(hwdata & 255) if haddr == 48 else int_error; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.state_updates.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_error width matches SSOT value 8
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_error RTL expression implements SSOT expression int_error & ~(hwdata & 255) if haddr == 48 else int_error
  - function_model.transactions.FM_AHB_WRITE.state_updates.int_error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AHB_WRITE.state_updates.int_error

### RTL-0112: Implement state update for FM_AHB_WRITE: ch_enable

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=ch_enable; expr=ch_enable & ~(hwdata & ch_enable) if haddr == 64 else ch_enable; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable width matches SSOT value 8
  - function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable RTL expression implements SSOT expression ch_enable & ~(hwdata & ch_enable) if haddr == 64 else ch_enable
  - function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable

### RTL-0113: Implement side effect for FM_AHB_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["updates writable DMAC/channel registers; W1C clears IntStatus bits; ChAbort write-one aborts enabled channels"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0

### RTL-0114: Implement error case for FM_AHB_WRITE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0

### RTL-0115: Implement transaction FM_AHB_READ

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AHB_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AHB_READ.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_READ

### RTL-0116: Implement precondition for FM_AHB_READ: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AHB_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=hsel and hreadyin and htrans[1] and not hwrite.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_READ.preconditions.precondition_0

### RTL-0117: Implement output for FM_AHB_READ: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["hrdata returns IdRev, DMACfg, IntStatus, ChEN, and channel windows"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.outputs.output_0

### RTL-0118: Implement output rule for FM_AHB_READ: hready_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hready_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hready_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hready_read; port=hready; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.output_rules.hready_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hready_read width matches SSOT value 1
  - hready_read RTL expression implements SSOT expression 1
  - DUT port hready is the implementation/observation point for hready_read
  - hready_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_READ.output_rules.hready_read

### RTL-0119: Implement output rule for FM_AHB_READ: hresp_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hresp_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hresp_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hresp_read; port=hresp; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.output_rules.hresp_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresp_read width matches SSOT value 2
  - hresp_read RTL expression implements SSOT expression 0
  - DUT port hresp is the implementation/observation point for hresp_read
  - hresp_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_READ.output_rules.hresp_read

### RTL-0120: Implement output rule for FM_AHB_READ: hrdata_id_cfg_status

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hrdata_id_cfg_status; port=hrdata; expr=0x01021012 if haddr == 0 else ((CHAIN_TRANSFER_SUPPORT << 31) | (REQ_ACK_NUM << 10) | (FIFO_DEPTH << 4) | DMA_CH_NUM)...; width=32.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hrdata_id_cfg_status width matches SSOT value 32
  - hrdata_id_cfg_status RTL expression implements SSOT expression 0x01021012 if haddr == 0 else ((CHAIN_TRANSFER_SUPPORT << 31) | (REQ_ACK_NUM << 10) | (FIFO_DEPTH << 4) | DMA_CH_NUM)...
  - DUT port hrdata is the implementation/observation point for hrdata_id_cfg_status
  - hrdata_id_cfg_status is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status

### RTL-0121: Implement side effect for FM_AHB_READ: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["no architectural state changes"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0

### RTL-0122: Implement error case for FM_AHB_READ: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_AHB_READ.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.error_cases.error_case_0

### RTL-0123: Implement transaction FM_ARBITRATE

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ARBITRATE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ARBITRATE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ARBITRATE

### RTL-0124: Implement precondition for FM_ARBITRATE: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=one or more ChnCtrl.Enable bits are set and DMA is not busy.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0

### RTL-0125: Implement output for FM_ARBITRATE: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["select high priority channel first; round-robin among same priority channels"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.output_0

### RTL-0126: Implement output rule for FM_ARBITRATE: hbusreq_on_start

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hbusreq_on_start; port=hbusreq_mst; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_on_start width matches SSOT value 1
  - hbusreq_on_start RTL expression implements SSOT expression 1
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_on_start
  - hbusreq_on_start is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start

### RTL-0127: Implement output rule for FM_ARBITRATE: htrans_idle_on_start

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_idle_on_start; port=htrans_mst; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_idle_on_start width matches SSOT value 2
  - htrans_idle_on_start RTL expression implements SSOT expression 0
  - DUT port htrans_mst is the implementation/observation point for htrans_idle_on_start
  - htrans_idle_on_start is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start

### RTL-0128: Implement state update for FM_ARBITRATE: busy

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=busy; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.state_updates.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ARBITRATE.state_updates.busy width matches SSOT value 1
  - function_model.transactions.FM_ARBITRATE.state_updates.busy RTL expression implements SSOT expression 1
  - function_model.transactions.FM_ARBITRATE.state_updates.busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ARBITRATE.state_updates.busy

### RTL-0129: Implement state update for FM_ARBITRATE: active_ch

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.active_ch
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=active_ch; expr=active_ch; width=3.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.state_updates.active_ch
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ARBITRATE.state_updates.active_ch width matches SSOT value 3
  - function_model.transactions.FM_ARBITRATE.state_updates.active_ch RTL expression implements SSOT expression active_ch
  - function_model.transactions.FM_ARBITRATE.state_updates.active_ch updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ARBITRATE.state_updates.active_ch

### RTL-0130: Implement state update for FM_ARBITRATE: bytes_done

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=bytes_done; expr=0; width=22.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.state_updates.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ARBITRATE.state_updates.bytes_done width matches SSOT value 22
  - function_model.transactions.FM_ARBITRATE.state_updates.bytes_done RTL expression implements SSOT expression 0
  - function_model.transactions.FM_ARBITRATE.state_updates.bytes_done updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ARBITRATE.state_updates.bytes_done

### RTL-0131: Implement side effect for FM_ARBITRATE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["sets busy and active_ch"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0

### RTL-0132: Implement error case for FM_ARBITRATE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0

### RTL-0133: Implement transaction FM_MASTER_READ

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_MASTER_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_MASTER_READ.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_READ

### RTL-0134: Implement precondition for FM_MASTER_READ: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=busy and hgrant_mst and hready_mst and not fifo full.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0

### RTL-0135: Implement output for FM_MASTER_READ: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["issues AHB master read from current source address"]; state=["read_data_hold"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.output_0

### RTL-0136: Implement output rule for FM_MASTER_READ: hbusreq_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hbusreq_read; port=hbusreq_mst; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_read width matches SSOT value 1
  - hbusreq_read RTL expression implements SSOT expression 1
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_read
  - hbusreq_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read

### RTL-0137: Implement output rule for FM_MASTER_READ: htrans_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.htrans_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.htrans_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_read; port=htrans_mst; expr=2; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.htrans_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_read width matches SSOT value 2
  - htrans_read RTL expression implements SSOT expression 2
  - DUT port htrans_mst is the implementation/observation point for htrans_read
  - htrans_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.htrans_read

### RTL-0138: Implement output rule for FM_MASTER_READ: hwrite_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hwrite_read; port=hwrite_mst; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwrite_read width matches SSOT value 1
  - hwrite_read RTL expression implements SSOT expression 0
  - DUT port hwrite_mst is the implementation/observation point for hwrite_read
  - hwrite_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read

### RTL-0139: Implement output rule for FM_MASTER_READ: haddr_read

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.haddr_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.haddr_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=haddr_read; port=haddr_mst; expr=src_addr_cur; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.haddr_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - haddr_read width matches SSOT value ADDR_WIDTH
  - haddr_read RTL expression implements SSOT expression src_addr_cur
  - DUT port haddr_mst is the implementation/observation point for haddr_read
  - haddr_read is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.haddr_read

### RTL-0140: Implement output rule for FM_MASTER_READ: hsize_word

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hsize_word
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hsize_word.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hsize_word; port=hsize_mst; expr=2; width=3.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.hsize_word
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hsize_word width matches SSOT value 3
  - hsize_word RTL expression implements SSOT expression 2
  - DUT port hsize_mst is the implementation/observation point for hsize_word
  - hsize_word is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.hsize_word

### RTL-0141: Implement output rule for FM_MASTER_READ: hburst_incr

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hburst_incr; port=hburst_mst; expr=1; width=3.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hburst_incr width matches SSOT value 3
  - hburst_incr RTL expression implements SSOT expression 1
  - DUT port hburst_mst is the implementation/observation point for hburst_incr
  - hburst_incr is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr

### RTL-0142: Implement state update for FM_MASTER_READ: read_data_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=read_data_hold; expr=hrdata_mst; width=32.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold width matches SSOT value 32
  - function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold RTL expression implements SSOT expression hrdata_mst
  - function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold

### RTL-0143: Implement side effect for FM_MASTER_READ: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["captures hrdata_mst for corresponding write beat"]; state=["read_data_hold"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0

### RTL-0144: Implement error case for FM_MASTER_READ: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["read_data_hold"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0

### RTL-0145: Implement transaction FM_MASTER_WRITE

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_MASTER_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_WRITE

### RTL-0146: Implement precondition for FM_MASTER_WRITE: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=busy and hgrant_mst and hready_mst and read data available.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0

### RTL-0147: Implement output for FM_MASTER_WRITE: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["issues AHB master write to current destination address"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.output_0

### RTL-0148: Implement output rule for FM_MASTER_WRITE: hbusreq_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hbusreq_write; port=hbusreq_mst; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_write width matches SSOT value 1
  - hbusreq_write RTL expression implements SSOT expression 1
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_write
  - hbusreq_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write

### RTL-0149: Implement output rule for FM_MASTER_WRITE: htrans_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_write; port=htrans_mst; expr=3; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_write width matches SSOT value 2
  - htrans_write RTL expression implements SSOT expression 3
  - DUT port htrans_mst is the implementation/observation point for htrans_write
  - htrans_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write

### RTL-0150: Implement output rule for FM_MASTER_WRITE: hwrite_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hwrite_write; port=hwrite_mst; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwrite_write width matches SSOT value 1
  - hwrite_write RTL expression implements SSOT expression 1
  - DUT port hwrite_mst is the implementation/observation point for hwrite_write
  - hwrite_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write

### RTL-0151: Implement output rule for FM_MASTER_WRITE: haddr_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=haddr_write; port=haddr_mst; expr=dst_addr_cur; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - haddr_write width matches SSOT value ADDR_WIDTH
  - haddr_write RTL expression implements SSOT expression dst_addr_cur
  - DUT port haddr_mst is the implementation/observation point for haddr_write
  - haddr_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write

### RTL-0152: Implement output rule for FM_MASTER_WRITE: hwdata_write

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hwdata_write; port=hwdata_mst; expr=read_data_hold; width=32.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwdata_write width matches SSOT value 32
  - hwdata_write RTL expression implements SSOT expression read_data_hold
  - DUT port hwdata_mst is the implementation/observation point for hwdata_write
  - hwdata_write is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write
