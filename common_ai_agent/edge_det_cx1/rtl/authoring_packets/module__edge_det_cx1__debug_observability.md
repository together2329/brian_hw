# RTL Authoring Packet: module__edge_det_cx1__debug_observability

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
- Module slice: 11/12 section=debug_observability task_limit=48
- Slice rule: Owner module edge_det_cx1 is split into 12 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0084: Implement debug/observability item sync1

- Priority: high
- Required: True
- Status: pass
- Category: debug_observability.signals
- Source ref: debug_observability.signals.sync1
- Detail: This SSOT debug_observability.signals item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: debug_observability.signals.sync1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=sync1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref debug_observability.signals.sync1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: debug_observability.signals.sync1

### RTL-0085: Implement debug/observability item sync2

- Priority: high
- Required: True
- Status: pass
- Category: debug_observability.signals
- Source ref: debug_observability.signals.sync2
- Detail: This SSOT debug_observability.signals item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: debug_observability.signals.sync2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=sync2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref debug_observability.signals.sync2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: debug_observability.signals.sync2

### RTL-0086: Implement debug/observability item prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: debug_observability.signals
- Source ref: debug_observability.signals.prev_sync
- Detail: This SSOT debug_observability.signals item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: debug_observability.signals.prev_sync.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: name=prev_sync.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref debug_observability.signals.prev_sync
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: debug_observability.signals.prev_sync
