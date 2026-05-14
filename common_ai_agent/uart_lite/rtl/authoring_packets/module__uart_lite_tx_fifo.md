# RTL Authoring Packet: module__uart_lite_tx_fifo

- Kind: module
- Owner module: uart_lite_tx_fifo
- Owner file: rtl/uart_lite_tx_fifo.sv
- Task count: 4
- Required tasks: 4

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
- Owner refs: dataflow, dataflow.tx_path, memory, memory.instances

## Tasks

### RTL-0027: Implement TX FIFO with parameterized FIFO_DEPTH

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Synchronous FIFO with wr_ptr/rd_ptr counters, empty/full combinatorial flags, write-push on APB TXDATA write, read-pop on TX FSM request. Width = DATA_WIDTH.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: uart_lite_tx_fifo in rtl/uart_lite_tx_fifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TX_FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - FIFO depth matches FIFO_DEPTH parameter
  - Empty/full flags are combinatorial
  - Write to full FIFO is ignored
  - Read from empty FIFO returns 0
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/uart_lite_tx_fifo.sv
  - Semantic source_refs covered: dataflow.tx_path, memory.instances.tx_fifo
- SSOT refs: dataflow.tx_path, memory.instances.tx_fifo, workflow_todos.rtl-gen[0]

### RTL-0190: Implement memory item tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.tx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.tx_fifo.
Owner: uart_lite_tx_fifo in rtl/uart_lite_tx_fifo.sv via memory.
SSOT item context: name=tx_fifo; width=8; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.tx_fifo
  - Primary implementation evidence is in rtl/uart_lite_tx_fifo.sv
  - tx_fifo width matches SSOT value 8
  - tx_fifo timing uses SSOT cycle/latency 0
  - tx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.tx_fifo

### RTL-0191: Implement memory item rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.rx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.rx_fifo.
Owner: uart_lite_tx_fifo in rtl/uart_lite_tx_fifo.sv via memory.
SSOT item context: name=rx_fifo; width=8; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.rx_fifo
  - Primary implementation evidence is in rtl/uart_lite_tx_fifo.sv
  - rx_fifo width matches SSOT value 8
  - rx_fifo timing uses SSOT cycle/latency 0
  - rx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.rx_fifo

### RTL-0257: Prove module uart_lite_tx_fifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_tx_fifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_tx_fifo.module_equivalence.
Owner: uart_lite_tx_fifo in rtl/uart_lite_tx_fifo.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_tx_fifo.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_tx_fifo.sv
- SSOT refs: sub_modules.uart_lite_tx_fifo.module_equivalence
