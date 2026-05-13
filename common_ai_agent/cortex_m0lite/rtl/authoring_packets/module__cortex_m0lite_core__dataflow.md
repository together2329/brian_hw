# RTL Authoring Packet: module__cortex_m0lite_core__dataflow

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 7
- Required tasks: 7

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 9/9 section=dataflow task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
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

### RTL-0147: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=IF issues instruction fetch request and captures instruction when i_hready is high..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0148: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=ID decodes instruction, reads regfile, and computes immediate/control..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0149: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=EX executes ALU/branch/address generation and launches data AHB for LDR/STR..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0150: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=WB commits architectural state and emits retire pulse..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0151: Implement dataflow ordering: ordering_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=Reset dominates all control..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.ordering.ordering_0

### RTL-0152: Implement dataflow ordering: ordering_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=Trap dominates writeback and starts flush sequence..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.ordering.ordering_1

### RTL-0153: Implement dataflow ordering: ordering_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via dataflow.
SSOT item context: value=Branch taken flushes IF/ID before next fetch..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: dataflow.ordering.ordering_2
