# RTL Authoring Packet: module__dma_real_channel__workflow_todo

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
- Task count: 2
- Required tasks: 2

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 8/9 section=workflow_todo task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0023: Implement per-channel FSM with stride, timeout, and performance counters

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: dma_real_channel implements IDLE/CFG/REQUEST/READ/WRITE/UPDATE/DONE/ERROR FSM. Latches src_addr, dst_addr, remaining, stride from CDC config. Addresses increment by stride (not hardcoded 4). Timeout counter monitors hready. Performance counters increment. Generate-based instantiation for N_CHANNELS.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - all FSM states and transitions match SSOT including timeout and FIFO overflow
  - address counters increment by stride per beat
  - timeout counter triggers error code 4
  - perf_words increments per word, perf_cycles per active cycle
  - generate block for N_CHANNELS
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - Semantic source_refs covered: error_handling, fsm.per_channel, function_model.transactions, registers.register_list
- SSOT refs: error_handling, fsm.per_channel, function_model.transactions, registers.register_list, workflow_todos.rtl-gen[3]

### RTL-0028: Implement hclk-domain engine connecting arbiter, channels, AHB master, and clock gating

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[8]
- Detail: dma_real_engine instantiates arbiter, N_CHANNELS channel instances (via generate), shared AHB master, and per-channel clock gating cells. Mux channel requests to AHB master based on arbiter grant.
SSOT ref: workflow_todos.rtl-gen[8].
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - generate block instantiates N_CHANNELS channel and FIFO instances
  - per-channel CG cell enable tied to ch_busy or ch_start_pending
  - AHB master mux selects granted channel
  - compile clean
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[8]
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - Semantic source_refs covered: cycle_model.pipeline, power.domains, sub_modules
- SSOT refs: cycle_model.pipeline, power.domains, sub_modules, workflow_todos.rtl-gen[8]
