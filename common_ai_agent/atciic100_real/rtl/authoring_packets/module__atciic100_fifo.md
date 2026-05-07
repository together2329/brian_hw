# RTL Authoring Packet: module__atciic100_fifo

- Kind: module
- Owner module: atciic100_fifo
- Owner file: rtl/atciic100_fifo.v
- Task count: 3
- Required tasks: 3

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: memory, memory.instances
- SSOT connection contracts:
  - atciic100_fifo.data_in <= pwdata (sub_modules[0].connections[2])
  - atciic100_fifo.data_out <= tx_data (sub_modules[1].connections[1])

## Tasks

### RTL-0028: Implement FIFO Buffer

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Parameterized depth pointer logic. Full/Empty flags.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: atciic100_fifo in rtl/atciic100_fifo.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO.
- Current reason: Owner RTL file is missing: rtl/atciic100_fifo.v.
- Criteria:
  - Depth parameterizable
  - Full/Empty/Half flags correct
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/atciic100_fifo.v
  - Semantic source_refs covered: memory
- SSOT refs: memory, workflow_todos.rtl-gen[1]

### RTL-0183: Implement memory item tx_rx_fifo

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.tx_rx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.tx_rx_fifo.
Owner: atciic100_fifo in rtl/atciic100_fifo.v via memory.
SSOT item context: name=tx_rx_fifo; width=8; depth=FIFO_DEPTH; latency=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_fifo.v.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.tx_rx_fifo
  - Primary implementation evidence is in rtl/atciic100_fifo.v
  - tx_rx_fifo width matches SSOT value 8
  - tx_rx_fifo timing uses SSOT cycle/latency 0
  - tx_rx_fifo storage depth matches SSOT value FIFO_DEPTH
- SSOT refs: memory.instances.tx_rx_fifo

### RTL-0220: Prove module atciic100_fifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_fifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_fifo.module_equivalence.
Owner: atciic100_fifo in rtl/atciic100_fifo.v via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_fifo.v.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_fifo.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_fifo.v
- SSOT refs: sub_modules.atciic100_fifo.module_equivalence
