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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, decomposition, decomposition.owners, decomposition.source_refs, error_handling, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM_AHB_READ, function_model.transactions.FM_AHB_WRITE, function_model.transactions.FM_ARBITRATE, function_model.transactions.FM_COMPLETE, function_model.transactions.FM_ERROR_ABORT, function_model.transactions.FM_HANDSHAKE_ACK
- Module slice: 3/17 section=function_model task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
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

### RTL-0105: Implement state update for FM_RESET: int_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=int_error; expr=0; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.int_error width matches SSOT value 8
  - function_model.transactions.FM_RESET.state_updates.int_error RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.int_error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.int_error

### RTL-0106: Implement state update for FM_RESET: bytes_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=bytes_done; expr=0; width=22.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.bytes_done width matches SSOT value 22
  - function_model.transactions.FM_RESET.state_updates.bytes_done RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.bytes_done updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.bytes_done

### RTL-0107: Implement state update for FM_RESET: src_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.src_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=src_addr_cur; expr=0; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.src_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.src_addr_cur

### RTL-0108: Implement state update for FM_RESET: dst_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.dst_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=dst_addr_cur; expr=0; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.dst_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.dst_addr_cur

### RTL-0109: Implement state update for FM_RESET: read_data_hold

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.read_data_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=read_data_hold; expr=0; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.read_data_hold
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.read_data_hold width matches SSOT value 32
  - function_model.transactions.FM_RESET.state_updates.read_data_hold RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.read_data_hold updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.read_data_hold

### RTL-0110: Implement state update for FM_RESET: chain_pending

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.chain_pending
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.chain_pending.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: state=chain_pending; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.chain_pending
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.chain_pending width matches SSOT value 1
  - function_model.transactions.FM_RESET.state_updates.chain_pending RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.chain_pending updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.chain_pending

### RTL-0111: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["disable all channels, clear active state, clear interrupt status"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0112: Implement error case for FM_RESET: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RESET.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.error_cases.error_case_0

### RTL-0113: Implement transaction FM_AHB_WRITE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AHB_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AHB_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_WRITE

### RTL-0114: Implement precondition for FM_AHB_WRITE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: value=hsel and hreadyin and htrans[1] and hwrite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0

### RTL-0115: Implement output for FM_AHB_WRITE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["hready=1"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.output_0

### RTL-0116: Implement output for FM_AHB_WRITE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.output_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["hresp=OKAY for valid register writes"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.output_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.output_1

### RTL-0117: Implement output for FM_AHB_WRITE: hready_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.hready_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.hready_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hrea...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.hready_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.hready_write

### RTL-0118: Implement output for FM_AHB_WRITE: hresp_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.hresp_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.hresp_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "hres...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.hresp_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.hresp_write

### RTL-0119: Implement output for FM_AHB_WRITE: dma_int_after_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.dma_int_after_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.dma_int_after_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "reduction_or((int...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.dma_int_after_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.dma_int_after_write

### RTL-0120: Implement output for FM_AHB_WRITE: dmac_reset_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.dmac_reset_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.dmac_reset_pulse.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "1 if haddr == 32...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.dmac_reset_pulse
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.dmac_reset_pulse

### RTL-0121: Implement output for FM_AHB_WRITE: int_tc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "int_tc & ~((hwda...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.int_tc

### RTL-0122: Implement output for FM_AHB_WRITE: int_abort

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.int_abort
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.int_abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "int_abort & ~((h...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.int_abort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.int_abort

### RTL-0123: Implement output for FM_AHB_WRITE: int_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "int_error & ~(hw...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.int_error

### RTL-0124: Implement output for FM_AHB_WRITE: ch_enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "ch_enable & ~(hw...; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.ch_enable

### RTL-0125: Implement output rule for FM_AHB_WRITE: hready_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.hready_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.hready_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: name=hready_write; port=hready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0126: Implement output rule for FM_AHB_WRITE: hresp_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.hresp_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: name=hresp_write; port=hresp; expr=0; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0127: Implement output rule for FM_AHB_WRITE: dma_int_after_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.output_rules.dma_int_after_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: name=dma_int_after_write; port=dma_int; expr=reduction_or((int_tc | int_abort | int_error) & ch_enable); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0128: Implement state update for FM_AHB_WRITE: dmac_reset_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.dmac_reset_pulse.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: state=dmac_reset_pulse; expr=1 if haddr == 32 and (hwdata & 1) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0129: Implement state update for FM_AHB_WRITE: int_tc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: state=int_tc; expr=int_tc & ~((hwdata >> 16) & 255) if haddr == 48 else int_tc; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0130: Implement state update for FM_AHB_WRITE: int_abort

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_abort
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: state=int_abort; expr=int_abort & ~((hwdata >> 8) & 255) if haddr == 48 else int_abort; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0131: Implement state update for FM_AHB_WRITE: int_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: state=int_error; expr=int_error & ~(hwdata & 255) if haddr == 48 else int_error; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0132: Implement state update for FM_AHB_WRITE: ch_enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.state_updates.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: state=ch_enable; expr=ch_enable & ~(hwdata & ch_enable) if haddr == 64 else ch_enable; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0133: Implement side effect for FM_AHB_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["updates writable DMAC/channel registers; W1C clears IntStatus bits; ChAbort write-one aborts enabled channels"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.side_effects.side_effect_0

### RTL-0134: Implement error case for FM_AHB_WRITE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_WRITE.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.error_cases.error_case_0

### RTL-0135: Implement transaction FM_AHB_READ

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AHB_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AHB_READ.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_READ

### RTL-0136: Implement precondition for FM_AHB_READ: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AHB_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: value=hsel and hreadyin and htrans[1] and not hwrite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_READ.preconditions.precondition_0

### RTL-0137: Implement output for FM_AHB_READ: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["hrdata returns IdRev, DMACfg, IntStatus, ChEN, and channel windows"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.outputs.output_0

### RTL-0138: Implement output for FM_AHB_READ: hready_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_READ.outputs.hready_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.outputs.hready_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hrea....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.outputs.hready_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.outputs.hready_read

### RTL-0139: Implement output for FM_AHB_READ: hresp_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_READ.outputs.hresp_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.outputs.hresp_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "hres....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.outputs.hresp_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.outputs.hresp_read

### RTL-0140: Implement output for FM_AHB_READ: hrdata_id_cfg_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_READ.outputs.hrdata_id_cfg_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.outputs.hrdata_id_cfg_status.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0x01021012 if had....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.outputs.hrdata_id_cfg_status
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.outputs.hrdata_id_cfg_status

### RTL-0141: Implement output rule for FM_AHB_READ: hready_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hready_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hready_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: name=hready_read; port=hready; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0142: Implement output rule for FM_AHB_READ: hresp_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hresp_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hresp_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: name=hresp_read; port=hresp; expr=0; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0143: Implement output rule for FM_AHB_READ: hrdata_id_cfg_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.output_rules.hrdata_id_cfg_status.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: name=hrdata_id_cfg_status; port=hrdata; expr=0x01021012 if haddr == 0 else ((CHAIN_TRANSFER_SUPPORT << 31) | (REQ_ACK_NUM << 10) | (FIFO_DEPTH << 4) | DMA_CH_NUM)...; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0144: Implement side effect for FM_AHB_READ: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["no architectural state changes"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.side_effects.side_effect_0

### RTL-0145: Implement error case for FM_AHB_READ: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_AHB_READ.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_READ.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_AHB_READ.
SSOT item context: id=FM_AHB_READ; name=AHB slave register read; port=["hready", "hresp", "hrdata"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_READ.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "hrdata"] is the implementation/observation point for AHB slave register read
- SSOT refs: function_model.transactions.FM_AHB_READ.error_cases.error_case_0

### RTL-0146: Implement transaction FM_ARBITRATE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ARBITRATE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ARBITRATE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ARBITRATE

### RTL-0147: Implement precondition for FM_ARBITRATE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: value=one or more ChnCtrl.Enable bits are set and DMA is not busy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_ARBITRATE.preconditions.precondition_0

### RTL-0148: Implement output for FM_ARBITRATE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["select high priority channel first; round-robin among same priority channels"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.output_0

### RTL-0149: Implement output for FM_ARBITRATE: hbusreq_on_start

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.hbusreq_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.hbusreq_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hbus...; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.hbusreq_on_start
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.hbusreq_on_start

### RTL-0150: Implement output for FM_ARBITRATE: htrans_idle_on_start

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.htrans_idle_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.htrans_idle_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "htra...; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.htrans_idle_on_start
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.htrans_idle_on_start

### RTL-0151: Implement output for FM_ARBITRATE: busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "1", "state": "bu...; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.busy

### RTL-0152: Implement output for FM_ARBITRATE: active_ch

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.active_ch
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "active_ch", "sta...; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.active_ch
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.active_ch
