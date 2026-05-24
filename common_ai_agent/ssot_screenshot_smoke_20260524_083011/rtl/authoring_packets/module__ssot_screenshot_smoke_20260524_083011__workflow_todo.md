# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__workflow_todo

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011
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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 14/15 section=workflow_todo task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0021: Resolve production multi-module connection contracts before top integration signoff

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: The SSOT may declare manifest child modules before machine-readable wiring is approved. Child module drafts may proceed from owner packets; top wiring, PASS, and signoff must remain blocked until SSOT authors integration.connections or sub_modules[].connections records.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via workflow_todos.owner.
SSOT item context: id=RTL_RESOLVE_CONNECTION_CONTRACTS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - integration.connections or sub_modules[].connections lists every active child module connection as module/port/signal data
  - rtl_authoring_plan.execution_policy.connection_contract_gap.status becomes ok
  - Top/gate authoring packet integration_signoff_allowed is true after rerunning rtl-gen TODO derivation
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Semantic source_refs covered: integration.connections, quality_gates.rtl_gen, sub_modules[].connections
- SSOT refs: integration.connections, quality_gates.rtl_gen, sub_modules[].connections, workflow_todos.rtl-gen[1]
