# RTL Authoring Packet: module__atcdmac100_core__function_model_03

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 39
- Required tasks: 39

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
- LLM-actionable open tasks: 39
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 4/14 section=function_model task_limit=48
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

### RTL-0153: Implement state update for FM_MASTER_WRITE: bytes_done

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=bytes_done; expr=bytes_done + 4; width=22.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done width matches SSOT value 22
  - function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done RTL expression implements SSOT expression bytes_done + 4
  - function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done

### RTL-0154: Implement state update for FM_MASTER_WRITE: src_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=src_addr_cur; expr=src_addr_cur + 4; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur RTL expression implements SSOT expression src_addr_cur + 4
  - function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur

### RTL-0155: Implement state update for FM_MASTER_WRITE: dst_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=dst_addr_cur; expr=dst_addr_cur + 4; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur RTL expression implements SSOT expression dst_addr_cur + 4
  - function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur

### RTL-0156: Implement side effect for FM_MASTER_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["increments/decrements/fixes addresses according to control fields and updates bytes_done"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0

### RTL-0157: Implement error case for FM_MASTER_WRITE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0

### RTL-0158: Implement transaction FM_COMPLETE

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_COMPLETE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_COMPLETE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_COMPLETE; name=terminal count completion.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_COMPLETE

### RTL-0159: Implement precondition for FM_COMPLETE: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_COMPLETE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=bytes_done reaches ChnTranSize without error or abort.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_COMPLETE.preconditions.precondition_0

### RTL-0160: Implement output for FM_COMPLETE: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_COMPLETE; name=terminal count completion; port=["hbusreq_mst", "htrans_mst", "dma_int"]; signal=["updates IntStatus.TC and asserts dma_int if interrupt is unmasked"]; state=["busy", "ch_enable", "int_tc", "chain_pending"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int"] is the implementation/observation point for terminal count completion
- SSOT refs: function_model.transactions.FM_COMPLETE.outputs.output_0

### RTL-0161: Implement output rule for FM_COMPLETE: hbusreq_complete

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_COMPLETE.output_rules.hbusreq_complete
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.output_rules.hbusreq_complete.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hbusreq_complete; port=hbusreq_mst; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.output_rules.hbusreq_complete
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_complete width matches SSOT value 1
  - hbusreq_complete RTL expression implements SSOT expression 0
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_complete
  - hbusreq_complete is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_COMPLETE.output_rules.hbusreq_complete

### RTL-0162: Implement output rule for FM_COMPLETE: htrans_complete

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_COMPLETE.output_rules.htrans_complete
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.output_rules.htrans_complete.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_complete; port=htrans_mst; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.output_rules.htrans_complete
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_complete width matches SSOT value 2
  - htrans_complete RTL expression implements SSOT expression 0
  - DUT port htrans_mst is the implementation/observation point for htrans_complete
  - htrans_complete is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_COMPLETE.output_rules.htrans_complete

### RTL-0163: Implement output rule for FM_COMPLETE: dma_int_tc

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_COMPLETE.output_rules.dma_int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.output_rules.dma_int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_int_tc; port=dma_int; expr=reduction_or((int_tc | (1 << active_ch)) | int_abort | int_error); width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.output_rules.dma_int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int_tc width matches SSOT value 1
  - dma_int_tc RTL expression implements SSOT expression reduction_or((int_tc | (1 << active_ch)) | int_abort | int_error)
  - DUT port dma_int is the implementation/observation point for dma_int_tc
  - dma_int_tc is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_COMPLETE.output_rules.dma_int_tc

### RTL-0164: Implement state update for FM_COMPLETE: busy

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.state_updates.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=busy; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.state_updates.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_COMPLETE.state_updates.busy width matches SSOT value 1
  - function_model.transactions.FM_COMPLETE.state_updates.busy RTL expression implements SSOT expression 0
  - function_model.transactions.FM_COMPLETE.state_updates.busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE.state_updates.busy

### RTL-0165: Implement state update for FM_COMPLETE: ch_enable

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE.state_updates.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.state_updates.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=ch_enable; expr=ch_enable & ~(1 << active_ch); width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.state_updates.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_COMPLETE.state_updates.ch_enable width matches SSOT value 8
  - function_model.transactions.FM_COMPLETE.state_updates.ch_enable RTL expression implements SSOT expression ch_enable & ~(1 << active_ch)
  - function_model.transactions.FM_COMPLETE.state_updates.ch_enable updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE.state_updates.ch_enable

### RTL-0166: Implement state update for FM_COMPLETE: int_tc

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE.state_updates.int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.state_updates.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_tc; expr=int_tc | (1 << active_ch); width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.state_updates.int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_COMPLETE.state_updates.int_tc width matches SSOT value 8
  - function_model.transactions.FM_COMPLETE.state_updates.int_tc RTL expression implements SSOT expression int_tc | (1 << active_ch)
  - function_model.transactions.FM_COMPLETE.state_updates.int_tc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE.state_updates.int_tc

### RTL-0167: Implement state update for FM_COMPLETE: chain_pending

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE.state_updates.chain_pending
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.state_updates.chain_pending.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=chain_pending; expr=1 if CHAIN_TRANSFER_SUPPORT else 0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.state_updates.chain_pending
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_COMPLETE.state_updates.chain_pending width matches SSOT value 1
  - function_model.transactions.FM_COMPLETE.state_updates.chain_pending RTL expression implements SSOT expression 1 if CHAIN_TRANSFER_SUPPORT else 0
  - function_model.transactions.FM_COMPLETE.state_updates.chain_pending updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE.state_updates.chain_pending

### RTL-0168: Implement side effect for FM_COMPLETE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_COMPLETE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_COMPLETE; name=terminal count completion; port=["hbusreq_mst", "htrans_mst", "dma_int"]; signal=["disables completed channel; chain pointer may preload next descriptor when enabled"]; state=["busy", "ch_enable", "int_tc", "chain_pending"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int"] is the implementation/observation point for terminal count completion
- SSOT refs: function_model.transactions.FM_COMPLETE.side_effects.side_effect_0

### RTL-0169: Implement error case for FM_COMPLETE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_COMPLETE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_COMPLETE; name=terminal count completion; port=["hbusreq_mst", "htrans_mst", "dma_int"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["busy", "ch_enable", "int_tc", "chain_pending"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int"] is the implementation/observation point for terminal count completion
- SSOT refs: function_model.transactions.FM_COMPLETE.error_cases.error_case_0

### RTL-0170: Implement transaction FM_ERROR_ABORT

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ERROR_ABORT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ERROR_ABORT; name=error or software abort.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ERROR_ABORT

### RTL-0171: Implement precondition for FM_ERROR_ABORT: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ERROR_ABORT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=hresp_mst indicates error, unaligned address, reserved mode, zero transfer size, or ChAbort bit is written.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.preconditions.precondition_0

### RTL-0172: Implement output for FM_ERROR_ABORT: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ERROR_ABORT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ERROR_ABORT; name=error or software abort; port=["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"]; signal=["updates IntStatus.Error or Abort and asserts dma_int if unmasked"]; state=["busy", "ch_enable", "int_error"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"] is the implementation/observation point for error or software abort
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.outputs.output_0

### RTL-0173: Implement output rule for FM_ERROR_ABORT: hbusreq_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ERROR_ABORT.output_rules.hbusreq_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.output_rules.hbusreq_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hbusreq_error; port=hbusreq_mst; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.output_rules.hbusreq_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_error width matches SSOT value 1
  - hbusreq_error RTL expression implements SSOT expression 0
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_error
  - hbusreq_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.output_rules.hbusreq_error

### RTL-0174: Implement output rule for FM_ERROR_ABORT: htrans_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ERROR_ABORT.output_rules.htrans_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.output_rules.htrans_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_error; port=htrans_mst; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.output_rules.htrans_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_error width matches SSOT value 2
  - htrans_error RTL expression implements SSOT expression 0
  - DUT port htrans_mst is the implementation/observation point for htrans_error
  - htrans_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.output_rules.htrans_error

### RTL-0175: Implement output rule for FM_ERROR_ABORT: dma_int_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_int_error; port=dma_int; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.output_rules.dma_int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int_error width matches SSOT value 1
  - dma_int_error RTL expression implements SSOT expression 1
  - DUT port dma_int is the implementation/observation point for dma_int_error
  - dma_int_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_int_error

### RTL-0176: Implement output rule for FM_ERROR_ABORT: dma_ack_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_ack_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_ack_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_ack_error; port=dma_ack; expr=0; width=REQ_ACK_NUM.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.output_rules.dma_ack_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_ack_error width matches SSOT value REQ_ACK_NUM
  - dma_ack_error RTL expression implements SSOT expression 0
  - DUT port dma_ack is the implementation/observation point for dma_ack_error
  - dma_ack_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.output_rules.dma_ack_error

### RTL-0177: Implement state update for FM_ERROR_ABORT: busy

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ERROR_ABORT.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.state_updates.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=busy; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.state_updates.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ERROR_ABORT.state_updates.busy width matches SSOT value 1
  - function_model.transactions.FM_ERROR_ABORT.state_updates.busy RTL expression implements SSOT expression 0
  - function_model.transactions.FM_ERROR_ABORT.state_updates.busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.state_updates.busy

### RTL-0178: Implement state update for FM_ERROR_ABORT: ch_enable

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=ch_enable; expr=ch_enable & ~(1 << active_ch); width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable width matches SSOT value 8
  - function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable RTL expression implements SSOT expression ch_enable & ~(1 << active_ch)
  - function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.state_updates.ch_enable

### RTL-0179: Implement state update for FM_ERROR_ABORT: int_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ERROR_ABORT.state_updates.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.state_updates.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_error; expr=int_error | (1 << active_ch); width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.state_updates.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_ERROR_ABORT.state_updates.int_error width matches SSOT value 8
  - function_model.transactions.FM_ERROR_ABORT.state_updates.int_error RTL expression implements SSOT expression int_error | (1 << active_ch)
  - function_model.transactions.FM_ERROR_ABORT.state_updates.int_error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.state_updates.int_error

### RTL-0180: Implement side effect for FM_ERROR_ABORT: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ERROR_ABORT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ERROR_ABORT; name=error or software abort; port=["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"]; signal=["disables affected channel; no dma_ack on error"]; state=["busy", "ch_enable", "int_error"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"] is the implementation/observation point for error or software abort
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.side_effects.side_effect_0

### RTL-0181: Implement error case for FM_ERROR_ABORT: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ERROR_ABORT.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ERROR_ABORT.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_ERROR_ABORT; name=error or software abort; port=["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["busy", "ch_enable", "int_error"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ERROR_ABORT.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "dma_int", "dma_ack"] is the implementation/observation point for error or software abort
- SSOT refs: function_model.transactions.FM_ERROR_ABORT.error_cases.error_case_0

### RTL-0182: Implement transaction FM_HANDSHAKE_ACK

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_HANDSHAKE_ACK; name=hardware handshake acknowledge.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK

### RTL-0183: Implement precondition for FM_HANDSHAKE_ACK: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=selected source or destination handshake mode is enabled and SrcBurstSize transfers complete.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.preconditions.precondition_0

### RTL-0184: Implement output for FM_HANDSHAKE_ACK: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_HANDSHAKE_ACK; name=hardware handshake acknowledge; port=["dma_ack", "dma_int"]; signal=["asserts dma_ack for selected request pair until dma_req deasserts"]; state=["active_ch"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["dma_ack", "dma_int"] is the implementation/observation point for hardware handshake acknowledge
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.outputs.output_0

### RTL-0185: Implement output rule for FM_HANDSHAKE_ACK: dma_ack_selected

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_ack_selected
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_ack_selected.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_ack_selected; port=dma_ack; expr=1 << active_ch; width=REQ_ACK_NUM.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_ack_selected
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_ack_selected width matches SSOT value REQ_ACK_NUM
  - dma_ack_selected RTL expression implements SSOT expression 1 << active_ch
  - DUT port dma_ack is the implementation/observation point for dma_ack_selected
  - dma_ack_selected is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_ack_selected

### RTL-0186: Implement output rule for FM_HANDSHAKE_ACK: dma_int_handshake

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_int_handshake
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_int_handshake.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_int_handshake; port=dma_int; expr=reduction_or(int_tc | int_abort | int_error); width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_int_handshake
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int_handshake width matches SSOT value 1
  - dma_int_handshake RTL expression implements SSOT expression reduction_or(int_tc | int_abort | int_error)
  - DUT port dma_int is the implementation/observation point for dma_int_handshake
  - dma_int_handshake is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.output_rules.dma_int_handshake

### RTL-0187: Implement state update for FM_HANDSHAKE_ACK: active_ch

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=active_ch; expr=active_ch; width=3.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch width matches SSOT value 3
  - function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch RTL expression implements SSOT expression active_ch
  - function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.state_updates.active_ch

### RTL-0188: Implement side effect for FM_HANDSHAKE_ACK: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_HANDSHAKE_ACK; name=hardware handshake acknowledge; port=["dma_ack", "dma_int"]; signal=["does not assert ack when an error terminates the channel"]; state=["active_ch"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["dma_ack", "dma_int"] is the implementation/observation point for hardware handshake acknowledge
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.side_effects.side_effect_0

### RTL-0189: Implement error case for FM_HANDSHAKE_ACK: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_HANDSHAKE_ACK; name=hardware handshake acknowledge; port=["dma_ack", "dma_int"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["active_ch"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["dma_ack", "dma_int"] is the implementation/observation point for hardware handshake acknowledge
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0

### RTL-0190: Preserve FL invariant one_channel_serviced

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.one_channel_serviced
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.one_channel_serviced.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: port=["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...; signal={"description": "Controller services one channel at a time.", "expr": "busy == 0 or active_ch < DMA_CH_NUM", "name": ...; state=["active_ch", "busy", "ch_enable"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.one_channel_serviced
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"... is the implementation/observation point for ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...
- SSOT refs: function_model.invariants.one_channel_serviced

### RTL-0191: Preserve FL invariant status_width

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.status_width
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.status_width.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: port=["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...; signal={"description": "Only configured channel status bits are used.", "expr": "(int_tc | int_abort | int_error) < 256", "n...; state=["int_tc", "int_abort", "int_error"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.status_width
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"... is the implementation/observation point for ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...
- SSOT refs: function_model.invariants.status_width
