# RTL Authoring Packet: module__dma_real_top

- Kind: module
- Owner module: dma_real_top
- Owner file: rtl/dma_real_top.sv
- Task count: 43
- Required tasks: 43

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT top IO contracts: 33

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: dma_real_top in rtl/dma_real_top.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: dma_real_top in rtl/dma_real_top.sv via top_module.
SSOT item context: value=dma_real_top.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: io_list

### RTL-0020: Implement top-level DMA wiring with dual-clock CDC bridge

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: dma_real_top.sv instantiates apb_cfg (pclk), engine (hclk), irq (pclk), and CDC async FIFO bridges. Wire APB slave ports, AHB master ports, and IRQ outputs. CDC FIFO connects pclk domain config writes to hclk domain channel FSM.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: dma_real_top in rtl/dma_real_top.sv via integration.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - top module ports match SSOT io_list exactly including hprot, hmaster, hmastlock, hresp[1:0]
  - dual-clock domains properly separated
  - CDC async FIFO instantiated for config crossing
  - compile clean with iverilog -g2012
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Semantic source_refs covered: cdc_requirements, integration, io_list, sub_modules
- SSOT refs: cdc_requirements, integration, io_list, sub_modules, workflow_todos.rtl-gen[0]

### RTL-0026: Implement dual-clock async FIFO with gray-code pointer sync

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[6]
- Detail: dma_real_async_fifo parameterized dual-clock FIFO. Write port in pclk domain, read port in hclk domain. Gray-code rd_ptr and wr_ptr with 2-stage synchronization. almost_full and almost_empty flags. Power-of-2 depth.
SSOT ref: workflow_todos.rtl-gen[6].
Owner: dma_real_top in rtl/dma_real_top.sv via top_module.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - gray-code pointer conversion correct
  - 2-stage synchronizer on crossed pointers
  - almost_full/almost_empty thresholds configurable
  - full/empty flags never simultaneously true
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[6]
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Semantic source_refs covered: cdc_requirements, memory.internal
- SSOT refs: cdc_requirements, memory.internal, workflow_todos.rtl-gen[6]

### RTL-0027: Implement 2-stage CDC synchronizer and clock gating cell

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[7]
- Detail: dma_real_cdc_sync is parameterized 2-stage flip-flop synchronizer. dma_real_cg_cell wraps library ICG primitive with enable input.
SSOT ref: workflow_todos.rtl-gen[7].
Owner: dma_real_top in rtl/dma_real_top.sv via power.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - 2-stage sync with async reset
  - ICG enable/disable glitch-free
  - parameterized width for multi-bit gray-code sync
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[7]
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Semantic source_refs covered: cdc_requirements, power.domains
- SSOT refs: cdc_requirements, power.domains, workflow_todos.rtl-gen[7]

### RTL-0328: Implement feature multi_channel

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.multi_channel
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.multi_channel.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=multi_channel.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.multi_channel
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.multi_channel

### RTL-0329: Implement feature dual_clock_cdc

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.dual_clock_cdc
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.dual_clock_cdc.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=dual_clock_cdc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.dual_clock_cdc
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.dual_clock_cdc

### RTL-0330: Implement feature round_robin_arb

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.round_robin_arb
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.round_robin_arb.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=round_robin_arb.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.round_robin_arb
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.round_robin_arb

### RTL-0331: Implement feature full_ahb_lite

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.full_ahb_lite
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.full_ahb_lite.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=full_ahb_lite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.full_ahb_lite
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.full_ahb_lite

### RTL-0332: Implement feature per_channel_irq

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.per_channel_irq
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.per_channel_irq.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=per_channel_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.per_channel_irq
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.per_channel_irq

### RTL-0333: Implement feature error_detection

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.error_detection
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.error_detection.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=error_detection.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.error_detection
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.error_detection

### RTL-0334: Implement feature programmable_stride

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.programmable_stride
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.programmable_stride.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=programmable_stride.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.programmable_stride
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.programmable_stride

### RTL-0335: Implement feature bus_timeout

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.bus_timeout
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.bus_timeout.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=bus_timeout.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.bus_timeout
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.bus_timeout

### RTL-0336: Implement feature performance_counters

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.performance_counters
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.performance_counters.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=performance_counters.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.performance_counters
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.performance_counters

### RTL-0337: Implement feature clock_gating

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.clock_gating
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.clock_gating.
Owner: dma_real_top in rtl/dma_real_top.sv via features.
SSOT item context: id=clock_gating.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.clock_gating
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: features.clock_gating

### RTL-0363: Implement security item channel_config

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.channel_config
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.channel_config.
Owner: dma_real_top in rtl/dma_real_top.sv via security.
SSOT item context: name=channel_config.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.channel_config
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: security.assets.channel_config

### RTL-0364: Implement security item transfer_data

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.transfer_data
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.transfer_data.
Owner: dma_real_top in rtl/dma_real_top.sv via security.
SSOT item context: name=transfer_data.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.transfer_data
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: security.assets.transfer_data

### RTL-0365: Implement security item perf_counters

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.perf_counters
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.perf_counters.
Owner: dma_real_top in rtl/dma_real_top.sv via security.
SSOT item context: name=perf_counters.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.perf_counters
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: security.assets.perf_counters

### RTL-0366: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: dma_real_top in rtl/dma_real_top.sv via integration.
SSOT item context: value=APB bus matrix provides psel, penable, pwrite, paddr, pwdata in pclk domain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0367: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: dma_real_top in rtl/dma_real_top.sv via integration.
SSOT item context: value=AHB-Lite bus matrix provides hready, hrdata, hresp[1:0], hgrant in hclk domain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0368: Implement integration item dependencie_2

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_2
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_2.
Owner: dma_real_top in rtl/dma_real_top.sv via integration.
SSOT item context: value=System interrupt controller receives irq_combined in pclk domain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_2
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: integration.dependencies.dependencie_2

### RTL-0369: Implement integration item dependencie_3

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_3
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_3.
Owner: dma_real_top in rtl/dma_real_top.sv via integration.
SSOT item context: value=System reset controller provides presetn and hresetn (may be async).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_3
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: integration.dependencies.dependencie_3

### RTL-0370: Implement DFT item mode

- Priority: high
- Required: True
- Status: pass
- Category: dft.scan
- Source ref: dft.scan.mode
- Detail: This SSOT dft.scan item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: dft.scan.mode.
Owner: dma_real_top in rtl/dma_real_top.sv via dft.
SSOT item context: name=mode; value=muxed_d.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref dft.scan.mode
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: dft.scan.mode

### RTL-0371: Implement DFT item description

- Priority: high
- Required: True
- Status: pass
- Category: dft.scan
- Source ref: dft.scan.description
- Detail: This SSOT dft.scan item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: dft.scan.description.
Owner: dma_real_top in rtl/dma_real_top.sv via dft.
SSOT item context: name=description; value=Standard muxed-D scan insertion via external ATPG tool.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref dft.scan.description
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: dft.scan.description

### RTL-0372: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: dma_real_top in rtl/dma_real_top.sv via synthesis.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0373: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: dma_real_top in rtl/dma_real_top.sv via synthesis.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0374: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: dma_real_top in rtl/dma_real_top.sv via synthesis.
SSOT item context: from=pclk_domain; to=hclk_domain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - synthesis.constraints.constraint_2 transition path pclk_domain -> hclk_domain is encoded or explicitly proven equivalent
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0375: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: dma_real_top in rtl/dma_real_top.sv via synthesis.
SSOT item context: from=pclk_domain; to=hclk_domain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - synthesis.constraints.constraint_3 transition path pclk_domain -> hclk_domain is encoded or explicitly proven equivalent
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0382: Prove module dma_real_top is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.dma_real_top.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.dma_real_top.module_equivalence.
Owner: dma_real_top in rtl/dma_real_top.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.dma_real_top.module_equivalence
  - Primary implementation evidence is in rtl/dma_real_top.sv
- SSOT refs: sub_modules.dma_real_top.module_equivalence

### RTL-0383: Keep RTL observable for scenario SC_001

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_001
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_001.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_001; name=single_channel_transfer; expected=CH0_STATUS.done=1, 4 words transferred, PERF_WORDS=4, irq[0] asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_001
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: CH0_STATUS.done=1, 4 words transferred, PERF_WORDS=4, irq[0] asserted
- SSOT refs: test_requirements.scenarios.SC_001

### RTL-0384: Keep RTL observable for scenario SC_002

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_002
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_002.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_002; name=alignment_error; expected=CH0_STATUS.error=1, err_code=1, no transfer occurs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_002
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: CH0_STATUS.error=1, err_code=1, no transfer occurs
- SSOT refs: test_requirements.scenarios.SC_002

### RTL-0385: Keep RTL observable for scenario SC_003

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_003
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_003.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_003; name=zero_length_error; expected=CH0_STATUS.error=1, err_code=2, no transfer occurs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_003
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: CH0_STATUS.error=1, err_code=2, no transfer occurs
- SSOT refs: test_requirements.scenarios.SC_003

### RTL-0386: Keep RTL observable for scenario SC_004

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_004
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_004.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_004; name=busy_reject; expected=second start ignored, transfer continues.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_004
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: second start ignored, transfer continues
- SSOT refs: test_requirements.scenarios.SC_004

### RTL-0387: Keep RTL observable for scenario SC_005

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_005
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_005.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_005; name=multi_channel_interleaved; expected=both complete, arbiter alternates grants, both irq asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_005
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: both complete, arbiter alternates grants, both irq asserted
- SSOT refs: test_requirements.scenarios.SC_005

### RTL-0388: Keep RTL observable for scenario SC_006

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_006
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_006.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_006; name=bus_error_during_transfer; expected=CH0_STATUS.error=1, err_code=3, transfer aborted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_006
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: CH0_STATUS.error=1, err_code=3, transfer aborted
- SSOT refs: test_requirements.scenarios.SC_006

### RTL-0389: Keep RTL observable for scenario SC_007

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_007
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_007.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_007; name=global_enable_disable; expected=current burst completes, then pauses. Resume when dma_en re-asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_007
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: current burst completes, then pauses. Resume when dma_en re-asserted
- SSOT refs: test_requirements.scenarios.SC_007

### RTL-0390: Keep RTL observable for scenario SC_008

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_008
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_008.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_008; name=interrupt_clear; expected=irq[0] deasserted, CH0_STATUS.done cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_008
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: irq[0] deasserted, CH0_STATUS.done cleared
- SSOT refs: test_requirements.scenarios.SC_008

### RTL-0391: Keep RTL observable for scenario SC_009

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_009
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_009.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_009; name=apb_unmapped_address; expected=pslverr=1, prdata=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_009
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: pslverr=1, prdata=0
- SSOT refs: test_requirements.scenarios.SC_009

### RTL-0392: Keep RTL observable for scenario SC_010

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_010
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_010.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_010; name=stride_transfer; expected=addresses increment by 8 per beat, 4 words transferred, PERF_WORDS=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_010
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: addresses increment by 8 per beat, 4 words transferred, PERF_WORDS=4
- SSOT refs: test_requirements.scenarios.SC_010

### RTL-0393: Keep RTL observable for scenario SC_011

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_011
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_011.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_011; name=bus_timeout; expected=CH0_STATUS.error=1, err_code=4, transfer aborted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_011
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: CH0_STATUS.error=1, err_code=4, transfer aborted
- SSOT refs: test_requirements.scenarios.SC_011

### RTL-0394: Keep RTL observable for scenario SC_012

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_012
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_012.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_012; name=performance_counters; expected=PERF_WORDS=16, PERF_CYCLES > 0, PERF_CYCLES saturates at 32'hFFFFFFFF.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_012
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: PERF_WORDS=16, PERF_CYCLES > 0, PERF_CYCLES saturates at 32'hFFFFFFFF
- SSOT refs: test_requirements.scenarios.SC_012

### RTL-0395: Keep RTL observable for scenario SC_013

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_013
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_013.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_013; name=burst_wrap_boundary; expected=burst splits at 1KB boundary, new NONSEQ beat starts after boundary.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_013
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: burst splits at 1KB boundary, new NONSEQ beat starts after boundary
- SSOT refs: test_requirements.scenarios.SC_013

### RTL-0396: Keep RTL observable for scenario SC_014

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_014
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_014.
Owner: dma_real_top in rtl/dma_real_top.sv via test_requirements.
SSOT item context: id=SC_014; name=clock_gating; expected=clock gating enable follows ch_busy, no spurious transitions.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_014
  - Primary implementation evidence is in rtl/dma_real_top.sv
  - Downstream checker compares RTL-observed behavior against expected result: clock gating enable follows ch_busy, no spurious transitions
- SSOT refs: test_requirements.scenarios.SC_014
