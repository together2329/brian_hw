# RTL Authoring Packet: module__edge_det_cx1__features

- Kind: module
- Owner module: edge_det_cx1
- Owner file: rtl/edge_det_cx1.sv
- Task count: 3
- Required tasks: 3

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
- Owner refs: cycle_model, dataflow, decomposition, decomposition.units.edge_detect, decomposition.units.sync2ff, fsm, function_model, function_model.state_variables, function_model.state_variables.prev_sync, function_model.state_variables.sync1, function_model.state_variables.sync2, function_model.transactions, function_model.transactions.FM_FALL, function_model.transactions.FM_RISE, function_model.transactions.FM_STABLE, io_list
- Module slice: 7/12 section=features task_limit=48
- Slice rule: Owner module edge_det_cx1 is split into 12 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0077: Implement feature 2-flop synchronizer

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.item_2_flop_synchronizer
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.item_2_flop_synchronizer.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=2-flop synchronizer; output=sync2 is CDC-safe version of sig_in.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.item_2_flop_synchronizer
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: features.item_2_flop_synchronizer

### RTL-0078: Implement feature Rising edge detect

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Rising_edge_detect
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Rising_edge_detect.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=Rising edge detect; output=rise_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Rising_edge_detect
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: features.Rising_edge_detect

### RTL-0079: Implement feature Falling edge detect

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Falling_edge_detect
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Falling_edge_detect.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=Falling edge detect; output=fall_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Falling_edge_detect
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: features.Falling_edge_detect
