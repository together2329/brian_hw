# RTL Authoring Packet: module__pulse_gen__synthesis

- Kind: module
- Owner module: pulse_gen
- Owner file: rtl/pulse_gen.sv
- Task count: 6
- Required tasks: 6

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
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 6/9 section=synthesis task_limit=48
- Slice rule: Owner module pulse_gen is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen.PRDATA <= pulse_gen_regs.PRDATA (integration.connections[7])
  - pulse_gen.PREADY <= 1'b1 (zero-wait-state) (integration.connections[8])
  - pulse_gen.PSLVERR <= pulse_gen_regs.PSLVERR (integration.connections[9])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0160: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: value=No inferred latches.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0161: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: value=All flops reset via async_assert_sync_deassert on PRESETn.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0162: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: value=No package/interface/modport/function/task/for/while constructs.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0163: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: name=area_um2_max.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0164: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: name=power_mw_max.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0165: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: pulse_gen in rtl/pulse_gen.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=50.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min
