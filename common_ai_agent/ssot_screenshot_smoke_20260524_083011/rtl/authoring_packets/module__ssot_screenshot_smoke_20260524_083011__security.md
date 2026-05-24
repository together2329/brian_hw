# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__security

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011
- Owner file: rtl/ssot_screenshot_smoke_20260524_083011.sv
- Task count: 2
- Required tasks: 2

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
- Module slice: 10/15 section=security task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0113: Implement security item configuration_state

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.configuration_state
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.configuration_state.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=configuration_state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.configuration_state
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: security.assets.configuration_state

### RTL-0114: Implement security item observable_results

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.observable_results
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.observable_results.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: name=observable_results.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.observable_results
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
- SSOT refs: security.assets.observable_results
