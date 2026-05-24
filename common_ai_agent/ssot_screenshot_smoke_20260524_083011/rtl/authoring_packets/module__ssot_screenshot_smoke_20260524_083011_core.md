# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011_core

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011_core
- Owner file: rtl/ssot_screenshot_smoke_20260524_083011.sv
- Task count: 1
- Required tasks: 1

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0

## Tasks

### RTL-0020: Implement every approved SSOT behavior in RTL-owned manifest modules

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Use function_model transactions, cycle_model timing, interfaces, registers, error handling, debug observability, and sub_modules ownership to implement the DUT without placeholder tie-offs or fixed IP templates.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: ssot_screenshot_smoke_20260524_083011_core in rtl/ssot_screenshot_smoke_20260524_083011.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPLEMENT_APPROVED_BEHAVIOR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Every required rtl_todo_plan task reaches todo_completion.status=pass after audit
  - DUT-only compile/lint reports are fresh and clean after the final RTL edit
  - RTL preserves SSOT authority: SSOT, FunctionalModel, coverage goals, interface rules, and performance targets are not edited to make RTL pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Semantic source_refs covered: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, sub_modules
- SSOT refs: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, sub_modules, workflow_todos.rtl-gen[0]
