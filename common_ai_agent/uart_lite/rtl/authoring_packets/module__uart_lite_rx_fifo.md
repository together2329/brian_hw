# RTL Authoring Packet: module__uart_lite_rx_fifo

- Kind: module
- Owner module: uart_lite_rx_fifo
- Owner file: rtl/uart_lite_rx_fifo.sv
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
- Owner refs: dataflow, dataflow.rx_path, memory, memory.instances

## Tasks

### RTL-0028: Implement RX FIFO with parameterized FIFO_DEPTH

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Synchronous FIFO with wr_ptr/rd_ptr counters, empty/full combinatorial flags, write-push on RX FSM byte ready, read-pop on APB RXDATA read. Width = DATA_WIDTH.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: uart_lite_rx_fifo in rtl/uart_lite_rx_fifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_RX_FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - FIFO depth matches FIFO_DEPTH parameter
  - Empty/full flags are combinatorial
  - Push to full FIFO discarded (rx_overrun set)
  - Read from empty FIFO returns 0
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/uart_lite_rx_fifo.sv
  - Semantic source_refs covered: dataflow.rx_path, memory.instances.rx_fifo
- SSOT refs: dataflow.rx_path, memory.instances.rx_fifo, workflow_todos.rtl-gen[1]

### RTL-0258: Prove module uart_lite_rx_fifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_rx_fifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_rx_fifo.module_equivalence.
Owner: uart_lite_rx_fifo in rtl/uart_lite_rx_fifo.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_rx_fifo.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_rx_fifo.sv
- SSOT refs: sub_modules.uart_lite_rx_fifo.module_equivalence
