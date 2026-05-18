# RTL Authoring Packet: module__atcdmac100_core__coverage

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 13
- Required tasks: 13

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
- LLM-actionable open tasks: 13
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 12/14 section=coverage task_limit=48
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

### RTL-0332: Provide RTL evidence for coverage bin FCOV_REG_IDCFG

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_REG_IDCFG
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_REG_IDCFG.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_REG_IDCFG.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_REG_IDCFG
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_REG_IDCFG can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_REG_IDCFG

### RTL-0333: Provide RTL evidence for coverage bin FCOV_INT_W1C

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_INT_W1C
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_INT_W1C.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_INT_W1C.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_INT_W1C
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_INT_W1C can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_INT_W1C

### RTL-0334: Provide RTL evidence for coverage bin FCOV_DMA_READ_WRITE

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_DMA_READ_WRITE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_DMA_READ_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_DMA_READ_WRITE.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_DMA_READ_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_DMA_READ_WRITE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_DMA_READ_WRITE

### RTL-0335: Provide RTL evidence for coverage bin FCOV_DMA_WRITE

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_DMA_WRITE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_DMA_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_DMA_WRITE.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_DMA_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_DMA_WRITE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_DMA_WRITE

### RTL-0336: Provide RTL evidence for coverage bin FCOV_TC_INT

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_TC_INT
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_TC_INT.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_TC_INT.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_TC_INT
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_TC_INT can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_TC_INT

### RTL-0337: Provide RTL evidence for coverage bin FCOV_ERROR_ABORT

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_ERROR_ABORT
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_ERROR_ABORT.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_ERROR_ABORT.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_ERROR_ABORT
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_ERROR_ABORT can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_ERROR_ABORT

### RTL-0338: Provide RTL evidence for coverage bin FCOV_REQ_ACK

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_REQ_ACK
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_REQ_ACK.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_REQ_ACK.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_REQ_ACK
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_REQ_ACK can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_REQ_ACK

### RTL-0339: Provide RTL evidence for coverage bin FCOV_PRIORITY

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_PRIORITY
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_PRIORITY.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=FCOV_PRIORITY.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_PRIORITY
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FCOV_PRIORITY can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_PRIORITY

### RTL-0340: Provide RTL evidence for coverage bin CCOV_AHB_SLAVE_ACCESS

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.CCOV_AHB_SLAVE_ACCESS
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.CCOV_AHB_SLAVE_ACCESS.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=CCOV_AHB_SLAVE_ACCESS.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.CCOV_AHB_SLAVE_ACCESS
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - CCOV_AHB_SLAVE_ACCESS can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.CCOV_AHB_SLAVE_ACCESS

### RTL-0341: Provide RTL evidence for coverage bin CCOV_MASTER_READ_WRITE

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.CCOV_MASTER_READ_WRITE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.CCOV_MASTER_READ_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=CCOV_MASTER_READ_WRITE.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.CCOV_MASTER_READ_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - CCOV_MASTER_READ_WRITE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.CCOV_MASTER_READ_WRITE

### RTL-0342: Provide RTL evidence for coverage bin CCOV_WAIT_STATE

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.CCOV_WAIT_STATE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.CCOV_WAIT_STATE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=CCOV_WAIT_STATE.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.CCOV_WAIT_STATE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - CCOV_WAIT_STATE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.CCOV_WAIT_STATE

### RTL-0343: Provide RTL evidence for coverage bin CCOV_HANDSHAKE_WAIT

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.CCOV_HANDSHAKE_WAIT
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.CCOV_HANDSHAKE_WAIT.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=CCOV_HANDSHAKE_WAIT.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.CCOV_HANDSHAKE_WAIT
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - CCOV_HANDSHAKE_WAIT can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.CCOV_HANDSHAKE_WAIT

### RTL-0344: Provide RTL evidence for coverage bin CCOV_ERROR_RESPONSE

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.CCOV_ERROR_RESPONSE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.CCOV_ERROR_RESPONSE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=CCOV_ERROR_RESPONSE.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.CCOV_ERROR_RESPONSE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - CCOV_ERROR_RESPONSE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.CCOV_ERROR_RESPONSE
