# RTL Authoring Packet: module__pl330realverify_datapath_pl330realverify_event_irq

- Kind: module
- Owner module: pl330realverify_datapath/pl330realverify_event_irq
- Owner file: rtl/pl330realverify_datapath.sv, rtl/pl330realverify_event_irq.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20

## Tasks

### RTL-0031: Implement address/count datapath, rd_buf, event selection, interrupt pending/enable, and fault classification

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: Implement pl330realverify_datapath and pl330realverify_event_irq using function_model state updates/output rules, dataflow read/write/loop/event/interrupt paths, memory.instances, interrupts.clear_policy, and error_handling propagation/recovery rules.
SSOT ref: workflow_todos.rtl-gen[4].
Owner: pl330realverify_datapath/pl330realverify_event_irq in rtl/pl330realverify_datapath.sv, rtl/pl330realverify_event_irq.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_DATAPATH_AND_INTERRUPTS.
- Current reason: Owner RTL file is missing: rtl/pl330realverify_datapath.sv, rtl/pl330realverify_event_irq.sv.
- Criteria:
  - rd_buf captures read data and wdata/wstrb output rules match rtl_contract/function_model
  - SAR/DAR increment by DATA_WIDTH/8 only after successful write responses
  - loop_remaining decrements and terminal status/interrupts follow FM_TRANSFER
  - INTSTATUS W1C and dmac_irq OR-reduction of INTSTATUS & INTEN follow FM_IRQ_CLEAR and interrupts.output.expression
  - ERR_UNALIGNED, ERR_DEBUG_REJECT, ERR_AXI_RD, ERR_AXI_WR, and ERR_EVENT_TIMEOUT follow error_handling
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/pl330realverify_datapath.sv, rtl/pl330realverify_event_irq.sv
  - Semantic source_refs covered: dataflow, error_handling, function_model.state_variables, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_TRANSFER, interrupts, memory.instances
- SSOT refs: dataflow, error_handling, function_model.state_variables, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_TRANSFER, interrupts, memory.instances, workflow_todos.rtl-gen[4]
