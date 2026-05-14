# RTL Authoring Packet: module__spi_shift__workflow_todo

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, features, fsm, fsm.channel_level, function_model, function_model.transactions
- Module slice: 7/7 section=workflow_todo task_limit=48
- Slice rule: Owner module spi_shift is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0027: Implement frame launch/shift/sample engine

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Create FSM and datapath for launch gate, CPOL/CPHA edges, lsb/msb order, CS handling, and completion events.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: spi_shift in rtl/spi_shift.sv via workflow_todos.owner.
SSOT item context: id=RTL_SPI_SHIFT_ENGINE.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - All fsm states/transitions implemented
  - No internal clocking on sclk_o
  - Cycle rules and ordering assertions pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/spi_shift.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm.channel_level, function_model.transactions.FM_SHIFT_SAMPLE
- SSOT refs: cycle_model.pipeline, fsm.channel_level, function_model.transactions.FM_SHIFT_SAMPLE, workflow_todos.rtl-gen[0]
