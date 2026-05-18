# RTL Authoring Packet: module__atcdmac100_core__function_model_05

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 3
- Required tasks: 3

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
- Module slice: 6/17 section=function_model task_limit=48
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

### RTL-0249: Implement error case for FM_HANDSHAKE_ACK: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.transactions.FM_HANDSHAKE_ACK.
SSOT item context: id=FM_HANDSHAKE_ACK; name=hardware handshake acknowledge; port=["dma_ack", "dma_int"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["active_ch"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["dma_ack", "dma_int"] is the implementation/observation point for hardware handshake acknowledge
- SSOT refs: function_model.transactions.FM_HANDSHAKE_ACK.error_cases.error_case_0

### RTL-0250: Preserve FL invariant one_channel_serviced

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.one_channel_serviced
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.one_channel_serviced.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: port=["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...; signal={"description": "Controller services one channel at a time.", "expr": "busy == 0 or active_ch < DMA_CH_NUM", "name": ...; state=["active_ch", "busy", "ch_enable"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.one_channel_serviced
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"... is the implementation/observation point for ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...
- SSOT refs: function_model.invariants.one_channel_serviced

### RTL-0251: Preserve FL invariant status_width

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.status_width
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.status_width.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: port=["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...; signal={"description": "Only configured channel status bits are used.", "expr": "(int_tc | int_abort | int_error) < 256", "n...; state=["int_tc", "int_abort", "int_error"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.status_width
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"... is the implementation/observation point for ["hready", "hresp", "dma_int", "htrans_mst", "hready", "hresp", "dma_int", "hready", "hresp", "hrdata", "hbusreq_mst"...
- SSOT refs: function_model.invariants.status_width
