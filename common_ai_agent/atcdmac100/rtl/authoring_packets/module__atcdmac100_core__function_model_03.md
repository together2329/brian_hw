# RTL Authoring Packet: module__atcdmac100_core__function_model_03

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
- Module slice: 4/17 section=function_model task_limit=48
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

### RTL-0153: Implement output for FM_ARBITRATE: bytes_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARBITRATE.outputs.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.outputs.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "by...; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.outputs.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.outputs.bytes_done

### RTL-0154: Implement output rule for FM_ARBITRATE: hbusreq_on_start

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.output_rules.hbusreq_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: name=hbusreq_on_start; port=hbusreq_mst; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0155: Implement output rule for FM_ARBITRATE: htrans_idle_on_start

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.output_rules.htrans_idle_on_start.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: name=htrans_idle_on_start; port=htrans_mst; expr=0; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0156: Implement state update for FM_ARBITRATE: busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: state=busy; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0157: Implement state update for FM_ARBITRATE: active_ch

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.active_ch
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: state=active_ch; expr=active_ch; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0158: Implement state update for FM_ARBITRATE: bytes_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARBITRATE.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: state=bytes_done; expr=0; width=22.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0159: Implement side effect for FM_ARBITRATE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["sets busy and active_ch"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.side_effects.side_effect_0

### RTL-0160: Implement error case for FM_ARBITRATE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_ARBITRATE.
SSOT item context: id=FM_ARBITRATE; name=channel arbitration; port=["hbusreq_mst", "htrans_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["busy", "active_ch", "bytes_done"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARBITRATE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst"] is the implementation/observation point for channel arbitration
- SSOT refs: function_model.transactions.FM_ARBITRATE.error_cases.error_case_0

### RTL-0161: Implement transaction FM_MASTER_READ

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_MASTER_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_MASTER_READ.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_READ

### RTL-0162: Implement precondition for FM_MASTER_READ: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: value=busy and hgrant_mst and hready_mst and not fifo full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_READ.preconditions.precondition_0

### RTL-0163: Implement output for FM_MASTER_READ: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["issues AHB master read from current source address"]; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.output_0

### RTL-0164: Implement output for FM_MASTER_READ: hbusreq_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.hbusreq_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.hbusreq_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hbus...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.hbusreq_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.hbusreq_read

### RTL-0165: Implement output for FM_MASTER_READ: htrans_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.htrans_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.htrans_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "2", "name": "htra...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.htrans_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.htrans_read

### RTL-0166: Implement output for FM_MASTER_READ: hwrite_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.hwrite_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.hwrite_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "hwri...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.hwrite_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.hwrite_read

### RTL-0167: Implement output for FM_MASTER_READ: haddr_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.haddr_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.haddr_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "src_addr_cur", "n...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.haddr_read
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.haddr_read

### RTL-0168: Implement output for FM_MASTER_READ: hsize_word

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.hsize_word
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.hsize_word.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "2", "name": "hsiz...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.hsize_word
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.hsize_word

### RTL-0169: Implement output for FM_MASTER_READ: hburst_incr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.hburst_incr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.hburst_incr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hbur...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.hburst_incr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.hburst_incr

### RTL-0170: Implement output for FM_MASTER_READ: read_data_hold

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_READ.outputs.read_data_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.outputs.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "hrdata_mst", "st...; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.outputs.read_data_hold
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.outputs.read_data_hold

### RTL-0171: Implement output rule for FM_MASTER_READ: hbusreq_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hbusreq_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=hbusreq_read; port=hbusreq_mst; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0172: Implement output rule for FM_MASTER_READ: htrans_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.htrans_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.htrans_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=htrans_read; port=htrans_mst; expr=2; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0173: Implement output rule for FM_MASTER_READ: hwrite_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hwrite_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=hwrite_read; port=hwrite_mst; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0174: Implement output rule for FM_MASTER_READ: haddr_read

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.haddr_read
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.haddr_read.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=haddr_read; port=haddr_mst; expr=src_addr_cur; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0175: Implement output rule for FM_MASTER_READ: hsize_word

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hsize_word
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hsize_word.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=hsize_word; port=hsize_mst; expr=2; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0176: Implement output rule for FM_MASTER_READ: hburst_incr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.output_rules.hburst_incr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: name=hburst_incr; port=hburst_mst; expr=1; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0177: Implement state update for FM_MASTER_READ: read_data_hold

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.state_updates.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: state=read_data_hold; expr=hrdata_mst; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0178: Implement side effect for FM_MASTER_READ: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["captures hrdata_mst for corresponding write beat"]; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.side_effects.side_effect_0

### RTL-0179: Implement error case for FM_MASTER_READ: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_READ.
SSOT item context: id=FM_MASTER_READ; name=AHB master read beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["read_data_hold"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_READ.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hsize_mst", "hburst_mst"] is the implementation/observation point for AHB master read beat
- SSOT refs: function_model.transactions.FM_MASTER_READ.error_cases.error_case_0

### RTL-0180: Implement transaction FM_MASTER_WRITE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_MASTER_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_WRITE

### RTL-0181: Implement precondition for FM_MASTER_WRITE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: value=busy and hgrant_mst and hready_mst and read data available.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.preconditions.precondition_0

### RTL-0182: Implement output for FM_MASTER_WRITE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["issues AHB master write to current destination address"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.output_0

### RTL-0183: Implement output for FM_MASTER_WRITE: hbusreq_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.hbusreq_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.hbusreq_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hbus...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.hbusreq_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.hbusreq_write

### RTL-0184: Implement output for FM_MASTER_WRITE: htrans_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.htrans_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.htrans_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "3", "name": "htra...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.htrans_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.htrans_write

### RTL-0185: Implement output for FM_MASTER_WRITE: hwrite_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.hwrite_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.hwrite_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "hwri...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.hwrite_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.hwrite_write

### RTL-0186: Implement output for FM_MASTER_WRITE: haddr_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.haddr_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.haddr_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "dst_addr_cur", "n...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.haddr_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.haddr_write

### RTL-0187: Implement output for FM_MASTER_WRITE: hwdata_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.hwdata_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.hwdata_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "read_data_hold", ...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.hwdata_write
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.hwdata_write

### RTL-0188: Implement output for FM_MASTER_WRITE: bytes_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "bytes_done + 4",...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.bytes_done

### RTL-0189: Implement output for FM_MASTER_WRITE: src_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.src_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "src_addr_cur + 4...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.src_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.src_addr_cur

### RTL-0190: Implement output for FM_MASTER_WRITE: dst_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_MASTER_WRITE.outputs.dst_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.outputs.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "dst_addr_cur + 4...; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.outputs.dst_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.outputs.dst_addr_cur

### RTL-0191: Implement output rule for FM_MASTER_WRITE: hbusreq_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hbusreq_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: name=hbusreq_write; port=hbusreq_mst; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0192: Implement output rule for FM_MASTER_WRITE: htrans_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.htrans_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: name=htrans_write; port=htrans_mst; expr=3; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0193: Implement output rule for FM_MASTER_WRITE: hwrite_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwrite_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: name=hwrite_write; port=hwrite_mst; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0194: Implement output rule for FM_MASTER_WRITE: haddr_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.haddr_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: name=haddr_write; port=haddr_mst; expr=dst_addr_cur; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0195: Implement output rule for FM_MASTER_WRITE: hwdata_write

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.output_rules.hwdata_write.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: name=hwdata_write; port=hwdata_mst; expr=read_data_hold; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0196: Implement state update for FM_MASTER_WRITE: bytes_done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: state=bytes_done; expr=bytes_done + 4; width=22.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0197: Implement state update for FM_MASTER_WRITE: src_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: state=src_addr_cur; expr=src_addr_cur + 4; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0198: Implement state update for FM_MASTER_WRITE: dst_addr_cur

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.state_updates.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: state=dst_addr_cur; expr=dst_addr_cur + 4; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
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

### RTL-0199: Implement side effect for FM_MASTER_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["increments/decrements/fixes addresses according to control fields and updates bytes_done"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.side_effects.side_effect_0

### RTL-0200: Implement error case for FM_MASTER_WRITE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_MASTER_WRITE.
SSOT item context: id=FM_MASTER_WRITE; name=AHB master write beat; port=["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["bytes_done", "src_addr_cur", "dst_addr_cur"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hbusreq_mst", "htrans_mst", "hwrite_mst", "haddr_mst", "hwdata_mst"] is the implementation/observation point for AHB master write beat
- SSOT refs: function_model.transactions.FM_MASTER_WRITE.error_cases.error_case_0
