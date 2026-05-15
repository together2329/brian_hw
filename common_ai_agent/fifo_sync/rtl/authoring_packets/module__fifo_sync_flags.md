# RTL Authoring Packet: module__fifo_sync_flags

- Kind: module
- Owner module: fifo_sync_flags
- Owner file: rtl/fifo_sync_flags.sv
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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, decomposition.units.flag_generation, function_model, function_model.transactions.output_rules
- SSOT connection contracts:
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
  - fifo_sync_flags.almost_empty_o <= almost_empty_o (integration.connections[12])

## Tasks

### RTL-0029: Implement combinational flag generation

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: full_o = (count == DEPTH), empty_o = (count == 0), almost_full_o = (count >= ALMOST_FULL_THRESHOLD), almost_empty_o = (count <= ALMOST_EMPTY_THRESHOLD), count_o = count. Flags are combinational functions of registered count.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO_FLAGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All 5 flags/count outputs match function_model output_rules expressions
  - Flags are combinational functions of count
  - Threshold comparisons use parameterized thresholds (runtime-writable via APB when USE_APB=1)
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - Semantic source_refs covered: function_model.transactions.FM1.output_rules, function_model.transactions.FM2.output_rules
- SSOT refs: function_model.transactions.FM1.output_rules, function_model.transactions.FM2.output_rules, workflow_todos.rtl-gen[2]

### RTL-0246: Prove module fifo_sync_flags is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.fifo_sync_flags.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.fifo_sync_flags.module_equivalence.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.fifo_sync_flags.module_equivalence
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: sub_modules.fifo_sync_flags.module_equivalence
