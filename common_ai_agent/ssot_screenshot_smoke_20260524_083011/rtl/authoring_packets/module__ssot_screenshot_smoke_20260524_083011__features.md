# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__features

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
- Module slice: 8/15 section=features task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0103: Implement feature approved_primary_behavior

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.approved_primary_behavior
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.approved_primary_behavior.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=approved_primary_behavior; output=Externally observable outputs, status, counters, interrupts, and/or responses match the approved behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.approved_primary_behavior
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: features.approved_primary_behavior
