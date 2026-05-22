# RTL Authoring Packet: module__dma_scratch_ui_live_20260519a__synthesis

- Kind: module
- Owner module: dma_scratch_ui_live_20260519a
- Owner file: rtl/dma_scratch_ui_live_20260519a.sv
- Task count: 11
- Required tasks: 11

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
- Module slice: 11/15 section=synthesis task_limit=48
- Slice rule: Owner module dma_scratch_ui_live_20260519a is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 36

## Tasks

### RTL-0205: Implement synthesis item sdc_file

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.sdc_file
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.sdc_file.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=sdc_file; value=syn/constraints/dma_scratch_ui_live_20260519a.sdc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.sdc_file
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.sdc_file

### RTL-0206: Implement synthesis item generated_from_ssot

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.generated_from_ssot
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.generated_from_ssot.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=generated_from_ssot; value=True.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.generated_from_ssot
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.generated_from_ssot

### RTL-0207: Implement synthesis item clock_groups

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.clock_groups
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.clock_groups.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=clock_groups.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.clock_groups
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.clock_groups

### RTL-0208: Implement synthesis item false_paths

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.false_paths
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.false_paths.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=false_paths; value=[{"from": "rst_n", "reason": "asynchronous_reset_assertion", "to": "all_registers"}].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.false_paths
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.false_paths

### RTL-0209: Implement synthesis item input_delay_ns

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.input_delay_ns
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.input_delay_ns.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=input_delay_ns; value=1.0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.input_delay_ns
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.input_delay_ns

### RTL-0210: Implement synthesis item output_delay_ns

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.output_delay_ns
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.output_delay_ns.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=output_delay_ns; value=1.0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.output_delay_ns
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.output_delay_ns

### RTL-0211: Implement synthesis item driving_cell

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.driving_cell
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.driving_cell.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=driving_cell; value=generic.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.driving_cell
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.driving_cell

### RTL-0212: Implement synthesis item load_pf

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.load_pf
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.load_pf.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=load_pf; value=0.05.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.load_pf
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.constraints.load_pf

### RTL-0213: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0214: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0215: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: name=frequency_mhz_min; value=100.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min
