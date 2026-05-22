# RTL Authoring Packet: module__uart_lite_baud_gen

- Kind: module
- Owner module: uart_lite_baud_gen
- Owner file: rtl/uart_lite_baud_gen.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.baud_generator
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0030: Implement baud rate generator

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Counter-based baud tick generator: baud_tick = 1 when counter == (BAUD.baud_div * OVERSAMPLE) - 1. Separate counters for TX (baud tick) and RX (oversample counter 0..OVERSAMPLE-1).
SSOT ref: workflow_todos.rtl-gen[3].
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPL_BAUD_GEN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Baud tick period = (baud_div + 1) * OVERSAMPLE PCLK cycles
  - RX mid-bit detection at oversample count 7
  - BAUD register change takes effect at next frame boundary
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - Semantic source_refs covered: cycle_model.baud_generator, registers.BAUD
- SSOT refs: cycle_model.baud_generator, registers.BAUD, workflow_todos.rtl-gen[3]

### RTL-0265: Prove module uart_lite_baud_gen is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_baud_gen.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_baud_gen.module_equivalence.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_baud_gen.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: sub_modules.uart_lite_baud_gen.module_equivalence
