# RTL Authoring Packet: module__uart_lite_tx__workflow_todo

- Kind: module
- Owner module: uart_lite_tx
- Owner file: rtl/uart_lite_tx.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, cycle_model.pipeline[TX_DATA], cycle_model.pipeline[TX_IDLE], cycle_model.pipeline[TX_PARITY], cycle_model.pipeline[TX_START], cycle_model.pipeline[TX_STOP1], cycle_model.pipeline[TX_STOP2], fsm, fsm.tx_fsm, function_model, function_model.transactions.FM_TX_BYTE
- Module slice: 5/5 section=workflow_todo task_limit=48
- Slice rule: Owner module uart_lite_tx is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0028: Implement TX FSM with parity generation

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: From fsm.tx_fsm states and transitions: implement TX_IDLE → TX_START → TX_DATA → TX_PARITY (if parity_en) → TX_STOP1 → TX_STOP2 (if stop_bits=1). Compute even/odd parity across DATA_WIDTH bits.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPL_TX_FSM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - TX FSM states and all declared transitions implemented
  - Parity computed per CTRL.parity_en and CTRL.parity_odd
  - Baud tick gating applied
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - Semantic source_refs covered: cycle_model.pipeline.tx_stages, fsm.tx_fsm
- SSOT refs: cycle_model.pipeline.tx_stages, fsm.tx_fsm, workflow_todos.rtl-gen[1]
