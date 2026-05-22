# RTL Authoring Packet: module__edge_detector_regs

- Kind: module
- Owner module: edge_detector_regs
- Owner file: rtl/edge_detector_regs.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4

## Tasks

### RTL-0028: Implement APB CSR register block

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Translate registers.register_list into APB decode, register read/write, W1C behavior, and PSLVERR generation.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: edge_detector_regs in rtl/edge_detector_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Register block is present in edge_detector_regs.sv
  - All APB accesses to valid/invalid addresses produce correct PREADY/PSLVERR
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/edge_detector_regs.sv
  - Semantic source_refs covered: io_list.interfaces.apb_csr, registers.register_list
- SSOT refs: io_list.interfaces.apb_csr, registers.register_list, workflow_todos.rtl-gen[1]
