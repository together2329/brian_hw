# RTL Authoring Packet: module__arbiter_rr_core__workflow_todo

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, features, fsm, fsm.arb_fsm, function_model, function_model.transactions, function_model.transactions.FM1, function_model.transactions.FM2
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module arbiter_rr_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
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

### RTL-0027: Implement round-robin arbitration core with priority rotation

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model.FM1 output_rules (grant one-hot, grant_valid, grant_index) and state_updates (last_winner rotation) into arbiter_rr_core.sv. Implement circular priority scan starting from (last_winner+1)%NUM_REQ over masked requests. Register outputs for 1-cycle latency per cycle_model.pipeline.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE_ARB.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - gnt_o is one-hot or all-zero every cycle
  - gnt_valid_o is 1 iff a valid grant is asserted
  - gnt_idx_o equals index of the asserted gnt_o bit when gnt_valid_o=1
  - last_winner updates to current grant_index when gnt_valid_o=1
  - Priority rotates so last winner has lowest priority next cycle
  - All outputs zero when CTRL.enable=0 or no unmasked requests
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - Semantic source_refs covered: cycle_model.latency.arbitration, cycle_model.pipeline, function_model.transactions.FM1, function_model.transactions.FM2
- SSOT refs: cycle_model.latency.arbitration, cycle_model.pipeline, function_model.transactions.FM1, function_model.transactions.FM2, workflow_todos.rtl-gen[0]
