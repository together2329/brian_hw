# RTL Authoring Packet: module__pl330realverify__synthesis

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
- Task count: 12
- Required tasks: 12

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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 6/9 section=synthesis task_limit=48
- Slice rule: Owner module pl330realverify is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])
- SSOT top IO contracts: 46

## Tasks

### RTL-0363: Implement synthesis item clock

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.clock
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.clock.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=clock; value={"frequency_mhz": 500, "name": "dmaclk", "period_ns": 2.0}.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.clock
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.clock

### RTL-0364: Implement synthesis item reset

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.reset
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.reset.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=reset; value={"async_assert": true, "name": "dmacresetn", "polarity": "active_low", "sync_deassert": true}.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.reset
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.reset

### RTL-0365: Implement synthesis item io_delay_ns

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.io_delay_ns
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.io_delay_ns.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=io_delay_ns; value=0.2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.io_delay_ns
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.io_delay_ns

### RTL-0366: Implement synthesis item max_fanout

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.max_fanout
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.max_fanout.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=max_fanout; value=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.max_fanout
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.max_fanout

### RTL-0367: Implement synthesis item max_transition_ns

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.max_transition_ns
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.max_transition_ns.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=max_transition_ns; value=0.25.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.max_transition_ns
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.max_transition_ns

### RTL-0368: Implement synthesis item false_paths

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.false_paths
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.false_paths.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=false_paths; value=[{"from": "dmacresetn", "reason": "Asynchronous reset assertion path.", "to": "all_registers"}].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.false_paths
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.false_paths

### RTL-0369: Implement synthesis item multicycle_paths

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.multicycle_paths
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.multicycle_paths.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=multicycle_paths.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.multicycle_paths
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.constraints.multicycle_paths

### RTL-0370: Implement synthesis item technology

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.technology
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.technology.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=technology; value=generic.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.technology
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.ppa_targets.technology

### RTL-0371: Implement synthesis item target_frequency_mhz

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.target_frequency_mhz
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.target_frequency_mhz.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=target_frequency_mhz; value=500.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.target_frequency_mhz
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.ppa_targets.target_frequency_mhz

### RTL-0372: Implement synthesis item area_um2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=area_um2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.ppa_targets.area_um2

### RTL-0373: Implement synthesis item power_mw

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=power_mw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.ppa_targets.power_mw

### RTL-0374: Implement synthesis item utilization_pct

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.utilization_pct
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.utilization_pct.
Owner: pl330realverify in rtl/pl330realverify.sv via synthesis.
SSOT item context: name=utilization_pct; value=60.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.utilization_pct
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: synthesis.ppa_targets.utilization_pct
