# RTL Authoring Packet: module__arbiter_rr_core__features

- Kind: module
- Owner module: arbiter_rr_core
- Owner file: rtl/arbiter_rr_core.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, dataflow, dataflow.sequence, dataflow.sequence.sequence_0, features, fsm, fsm.arb_fsm, function_model, function_model.transactions, function_model.transactions.FM1, function_model.transactions.FM2
- Module slice: 4/7 section=features task_limit=48
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

### RTL-0117: Implement feature Round-Robin Arbitration

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Round_Robin_Arbitration
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Round_Robin_Arbitration.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via features.
SSOT item context: name=Round-Robin Arbitration; output=gnt_o (one-hot), gnt_valid_o, gnt_idx_o (binary index).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Round_Robin_Arbitration
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: features.Round_Robin_Arbitration

### RTL-0118: Implement feature Request Masking

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Request_Masking
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Request_Masking.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via features.
SSOT item context: name=Request Masking; output=Only unmasked requests participate in arbitration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Request_Masking
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: features.Request_Masking

### RTL-0119: Implement feature Enable/Disable

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Enable_Disable
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Enable_Disable.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via features.
SSOT item context: name=Enable/Disable; output=All grants deasserted when disabled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Enable_Disable
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: features.Enable_Disable
