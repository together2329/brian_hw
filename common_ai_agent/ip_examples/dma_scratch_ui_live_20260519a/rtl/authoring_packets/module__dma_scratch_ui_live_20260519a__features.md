# RTL Authoring Packet: module__dma_scratch_ui_live_20260519a__features

- Kind: module
- Owner module: dma_scratch_ui_live_20260519a
- Owner file: rtl/dma_scratch_ui_live_20260519a.sv
- Task count: 5
- Required tasks: 5

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 8/15 section=features task_limit=48
- Slice rule: Owner module dma_scratch_ui_live_20260519a is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 36

## Tasks

### RTL-0185: Implement feature csr_programming

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.csr_programming
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.csr_programming.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: id=csr_programming.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.csr_programming
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: features.csr_programming

### RTL-0186: Implement feature scratch_dma_copy

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.scratch_dma_copy
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.scratch_dma_copy.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: id=scratch_dma_copy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.scratch_dma_copy
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: features.scratch_dma_copy

### RTL-0187: Implement feature error_reporting

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.error_reporting
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.error_reporting.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: id=error_reporting.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.error_reporting
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: features.error_reporting

### RTL-0188: Implement feature irq_generation

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.irq_generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.irq_generation.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: id=irq_generation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.irq_generation
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: features.irq_generation

### RTL-0189: Implement feature synthesis_policy_ready

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.synthesis_policy_ready
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.synthesis_policy_ready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: id=synthesis_policy_ready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.synthesis_policy_ready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: features.synthesis_policy_ready
