# RTL Authoring Packet: module__cortex_m0lite_core__workflow_todo

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 9/10 section=workflow_todo task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0027: Implement rule-based instruction decode without fixed opcode lookup table.

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Decoder must derive op class from isa_spec.decode_rule_set, enforce field constraints, resolve class overlap by priority, and raise illegal trap on decode miss.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via function_model.transactions.FM_CPU_STEP.
SSOT item context: id=todo_decode_rules.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - No fixed opcode table is used as the implementation source.
  - All supported op classes decode deterministically.
  - decode_overlap_resolved and decode_illegal_path are observable coverage events.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - Semantic source_refs covered: function_model.transactions.FM_CPU_STEP.decode_rules, isa_spec.decode_rule_set, isa_spec.decode_style
- SSOT refs: function_model.transactions.FM_CPU_STEP.decode_rules, isa_spec.decode_rule_set, isa_spec.decode_style, workflow_todos.rtl-gen[0]

### RTL-0028: Implement forwarding and load-use stall behavior.

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: ALU-to-ALU dependencies forward, load-use dependency inserts exactly one bubble, and branch flag dependencies observe the latest committed/forwarded flags.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via coverage_tap.
SSOT item context: id=todo_forwarding_matrix.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - No RAW hazard mismatch in directed hazard tests.
  - hazard_stall_cycles and hazard_matrix bins are covered.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - Semantic source_refs covered: coverage_tap.cycle.hazard_matrix, cycle_model.handshake_rules, test_requirements.scenarios.SC_HAZARD_FORWARD
- SSOT refs: coverage_tap.cycle.hazard_matrix, cycle_model.handshake_rules, test_requirements.scenarios.SC_HAZARD_FORWARD, workflow_todos.rtl-gen[1]

### RTL-0029: Implement precise trap entry and pipeline flush.

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Illegal opcode, bus error, and misaligned access suppress offending retire, update EXC_CAUSE, pulse trap, and clear in-flight pipeline state before fetch resumes.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via error_handling.
SSOT item context: id=todo_trap_vectoring.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Trap code priority follows error_handling.priority.
  - SC_TRAP_PATHS passes with scoreboard evidence.
  - trap_entry_cycles coverage closes.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - Semantic source_refs covered: error_handling, fsm.control, test_requirements.scenarios.SC_TRAP_PATHS
- SSOT refs: error_handling, fsm.control, test_requirements.scenarios.SC_TRAP_PATHS, workflow_todos.rtl-gen[2]
