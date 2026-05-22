# RTL Authoring Packet: module__atcdmac100_core__features

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 6
- Required tasks: 6

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
- Module slice: 10/17 section=features task_limit=48
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

### RTL-0338: Implement feature ahb_slave_registers

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.ahb_slave_registers
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.ahb_slave_registers.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=ahb_slave_registers.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.ahb_slave_registers
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.ahb_slave_registers

### RTL-0339: Implement feature multi_channel_dma

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.multi_channel_dma
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.multi_channel_dma.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=multi_channel_dma.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.multi_channel_dma
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.multi_channel_dma

### RTL-0340: Implement feature priority_round_robin

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.priority_round_robin
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.priority_round_robin.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=priority_round_robin.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.priority_round_robin
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.priority_round_robin

### RTL-0341: Implement feature hardware_handshake

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.hardware_handshake
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.hardware_handshake.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=hardware_handshake.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.hardware_handshake
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.hardware_handshake

### RTL-0342: Implement feature chain_transfer

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.chain_transfer
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.chain_transfer.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=chain_transfer.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.chain_transfer
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.chain_transfer

### RTL-0343: Implement feature interrupt_status

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.interrupt_status
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.interrupt_status.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via features.
SSOT item context: id=interrupt_status.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.interrupt_status
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: features.interrupt_status
