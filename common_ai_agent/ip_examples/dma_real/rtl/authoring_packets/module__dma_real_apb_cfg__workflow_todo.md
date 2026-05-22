# RTL Authoring Packet: module__dma_real_apb_cfg__workflow_todo

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 7/8 section=workflow_todo task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0021: Implement APB slave configuration decode with dual-clock awareness

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: dma_real_apb_cfg decodes paddr to global and per-channel registers including STRIDE, GLOBAL_TIMEOUT, PERF counters. Writes pushed into CDC FIFO for hclk domain. Readback synchronized from hclk domain.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via io_list.interfaces.apb_slave.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - all register offsets decoded correctly per SSOT register map
  - new registers (STRIDE, GLOBAL_TIMEOUT, PERF_WORDS, PERF_CYCLES) implemented
  - write_effect implemented for each field
  - CDC FIFO push on config write
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - Semantic source_refs covered: cdc_requirements, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: cdc_requirements, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]
