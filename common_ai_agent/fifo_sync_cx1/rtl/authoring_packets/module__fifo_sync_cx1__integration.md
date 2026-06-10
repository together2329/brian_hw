# RTL Authoring Packet: module__fifo_sync_cx1__integration

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 5
- Required tasks: 5

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 4/11 section=integration task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0088: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0089: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: name=external_clocks; value=["clk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0090: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: name=external_resets; value=["rst_n"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0091: Implement integration item clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: port=clk; signal=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - DUT port clk is the implementation/observation point for clk
- SSOT refs: integration.connections.clk

### RTL-0092: Implement integration item rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_n.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: port=rst_n; signal=rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_n
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - DUT port rst_n is the implementation/observation point for rst_n
- SSOT refs: integration.connections.rst_n
