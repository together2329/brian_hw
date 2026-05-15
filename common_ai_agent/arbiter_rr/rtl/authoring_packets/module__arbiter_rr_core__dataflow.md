# RTL Authoring Packet: module__arbiter_rr_core__dataflow

- Kind: module
- Owner module: arbiter_rr_core
- Owner file: rtl/arbiter_rr_core.sv
- Task count: 1
- Required tasks: 1

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, dataflow, dataflow.sequence, dataflow.sequence.sequence_0, decomposition.units.arbitrate, features, fsm, fsm.arb_fsm, function_model, function_model.transactions, function_model.transactions.FM1, function_model.transactions.FM2
- Module slice: 7/7 section=dataflow task_limit=48
- Slice rule: Owner module arbiter_rr_core is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_core.clk_i <= PCLK (integration.connections[12])
  - arbiter_rr_core.rst_ni <= PRESETn (integration.connections[13])
  - arbiter_rr_core.req_i <= req_i (integration.connections[14])
  - arbiter_rr_core.mask_i <= req_mask (integration.connections[15])
  - arbiter_rr_core.enable_i <= arb_enable (integration.connections[16])
  - arbiter_rr_core.gnt_o <= gnt_o (integration.connections[17])
  - arbiter_rr_core.gnt_valid_o <= gnt_valid_o (integration.connections[18])
  - arbiter_rr_core.gnt_idx_o <= gnt_idx_o (integration.connections[19])
  - arbiter_rr_core.winner_oh_o <= status_winner (integration.connections[20])
  - arbiter_rr_core.active_req_o <= status_active_req (integration.connections[21])

## Tasks

### RTL-0120: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via dataflow.sequence.sequence_0.
SSOT item context: value=req_i → mask → priority_rotate → encode → register → gnt_o / gnt_idx_o / gnt_valid_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: dataflow.sequence.sequence_0
