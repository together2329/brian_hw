# RTL Authoring Packet: module__fifo_sync_cx1__features

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 6
- Required tasks: 6

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
- Module slice: 7/11 section=features task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0076: Implement feature fifo_write

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.fifo_write
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.fifo_write.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=fifo_write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.fifo_write
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.fifo_write

### RTL-0077: Implement feature fifo_read

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.fifo_read
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.fifo_read.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=fifo_read.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.fifo_read
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.fifo_read

### RTL-0078: Implement feature full_flag

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.full_flag
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.full_flag.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=full_flag.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.full_flag
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.full_flag

### RTL-0079: Implement feature empty_flag

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.empty_flag
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.empty_flag.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=empty_flag.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.empty_flag
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.empty_flag

### RTL-0080: Implement feature reset_behavior

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.reset_behavior
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.reset_behavior.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=reset_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.reset_behavior
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.reset_behavior

### RTL-0081: Implement feature lint_clean

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.lint_clean
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.lint_clean.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via features.
SSOT item context: name=lint_clean.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.lint_clean
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features.lint_clean
