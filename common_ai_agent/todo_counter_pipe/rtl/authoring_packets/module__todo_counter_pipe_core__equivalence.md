# RTL Authoring Packet: module__todo_counter_pipe_core__equivalence

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 7/8 section=equivalence task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0260: Prove module todo_counter_pipe_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.todo_counter_pipe_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.todo_counter_pipe_core.module_equivalence.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.todo_counter_pipe_core.module_equivalence
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: sub_modules.todo_counter_pipe_core.module_equivalence
