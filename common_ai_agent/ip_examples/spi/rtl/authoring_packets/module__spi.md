# RTL Authoring Packet: module__spi

- Kind: module
- Owner module: spi
- Owner file: rtl/spi.sv
- Task count: 30
- Required tasks: 30

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
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])
  - spi_fifo.rx_push_data <= rx_word (integration.connections[3])
  - spi.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 16

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: spi in rtl/spi.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: spi in rtl/spi.sv via top_module.
SSOT item context: value=spi.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: io_list

### RTL-0226: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: spi in rtl/spi.sv via security.
SSOT item context: value=Correct APB register access policy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: security.assets.asset_0

### RTL-0227: Implement security item asset_1

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: spi in rtl/spi.sv via security.
SSOT item context: value=Integrity of serialized command/data words.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: security.assets.asset_1

### RTL-0228: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: spi in rtl/spi.sv via security.
SSOT item context: value=Integrity of interrupt/error telemetry.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: security.assets.asset_2

### RTL-0229: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: value=External SPI slave device timing is out of scope; this IP only guarantees generated SCLK/MOSI/CS waveform contract..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0230: Implement integration item start_req

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.start_req
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.start_req.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: signal=start_req; from=spi_regs.start_pulse; to=spi_shift.start_req.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.start_req
  - Primary implementation evidence is in rtl/spi.sv
  - integration.connections.start_req transition path spi_regs.start_pulse -> spi_shift.start_req is encoded or explicitly proven equivalent
- SSOT refs: integration.connections.start_req

### RTL-0231: Implement integration item ctrl_cfg

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.ctrl_cfg
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.ctrl_cfg.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: signal=ctrl_cfg; from=spi_regs.ctrl_cfg; to=spi_shift.ctrl_cfg.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.ctrl_cfg
  - Primary implementation evidence is in rtl/spi.sv
  - integration.connections.ctrl_cfg transition path spi_regs.ctrl_cfg -> spi_shift.ctrl_cfg is encoded or explicitly proven equivalent
- SSOT refs: integration.connections.ctrl_cfg

### RTL-0232: Implement integration item tx_word

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.tx_word
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.tx_word.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: signal=tx_word; from=spi_fifo.tx_pop_data; to=spi_shift.tx_word.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.tx_word
  - Primary implementation evidence is in rtl/spi.sv
  - integration.connections.tx_word transition path spi_fifo.tx_pop_data -> spi_shift.tx_word is encoded or explicitly proven equivalent
- SSOT refs: integration.connections.tx_word

### RTL-0233: Implement integration item rx_word

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rx_word
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rx_word.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: signal=rx_word; from=spi_shift.rx_word; to=spi_fifo.rx_push_data.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rx_word
  - Primary implementation evidence is in rtl/spi.sv
  - integration.connections.rx_word transition path spi_shift.rx_word -> spi_fifo.rx_push_data is encoded or explicitly proven equivalent
- SSOT refs: integration.connections.rx_word

### RTL-0234: Implement integration item irq_o

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.irq_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq_o.
Owner: spi in rtl/spi.sv via integration.
SSOT item context: signal=irq_o; from=spi_int.irq_o; to=spi.irq_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq_o
  - Primary implementation evidence is in rtl/spi.sv
  - integration.connections.irq_o transition path spi_int.irq_o -> spi.irq_o is encoded or explicitly proven equivalent
- SSOT refs: integration.connections.irq_o

### RTL-0235: Implement DFT item strategy

- Priority: high
- Required: True
- Status: pass
- Category: dft.scan
- Source ref: dft.scan.strategy
- Detail: This SSOT dft.scan item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: dft.scan.strategy.
Owner: spi in rtl/spi.sv via dft.
SSOT item context: name=strategy; value=single_clock_scan.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref dft.scan.strategy
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: dft.scan.strategy

### RTL-0236: Implement DFT item assumptions

- Priority: high
- Required: True
- Status: pass
- Category: dft.scan
- Source ref: dft.scan.assumptions
- Detail: This SSOT dft.scan item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: dft.scan.assumptions.
Owner: spi in rtl/spi.sv via dft.
SSOT item context: name=assumptions; value=["PCLK is controllable in test mode.", "PRESETn can be asserted/deasserted from test controller."].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref dft.scan.assumptions
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: dft.scan.assumptions

### RTL-0237: Implement DFT item test_point_0

- Priority: high
- Required: True
- Status: pass
- Category: dft.test_points
- Source ref: dft.test_points.test_point_0
- Detail: This SSOT dft.test_points item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: dft.test_points.test_point_0.
Owner: spi in rtl/spi.sv via dft.
SSOT item context: value=FIFO full/empty boundary conditions should be controllable via APB writes and frame completions..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref dft.test_points.test_point_0
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: dft.test_points.test_point_0

### RTL-0238: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: spi in rtl/spi.sv via synthesis.
SSOT item context: value=Use PCLK as only sequential clock..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0239: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: spi in rtl/spi.sv via synthesis.
SSOT item context: value=Do not infer latches..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0240: Implement synthesis item fmax_mhz

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.fmax_mhz
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.fmax_mhz.
Owner: spi in rtl/spi.sv via synthesis.
SSOT item context: name=fmax_mhz; value=100.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.fmax_mhz
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: synthesis.ppa_targets.fmax_mhz

### RTL-0241: Implement synthesis item area_priority

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_priority
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_priority.
Owner: spi in rtl/spi.sv via synthesis.
SSOT item context: name=area_priority; value=balanced.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_priority
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: synthesis.ppa_targets.area_priority

### RTL-0242: Implement synthesis item power_priority

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_priority
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_priority.
Owner: spi in rtl/spi.sv via synthesis.
SSOT item context: name=power_priority; value=low_dynamic_when_idle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_priority
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: synthesis.ppa_targets.power_priority

### RTL-0248: Prove module spi is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi.module_equivalence.
Owner: spi in rtl/spi.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi.module_equivalence
  - Primary implementation evidence is in rtl/spi.sv
- SSOT refs: sub_modules.spi.module_equivalence

### RTL-0249: Keep RTL observable for scenario SC_APB_CONFIG

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_APB_CONFIG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_APB_CONFIG.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_APB_CONFIG; name=APB config/readback; expected=Readback matches writes; RO/WO behavior and PSLVERR policy hold.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_APB_CONFIG
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: Readback matches writes; RO/WO behavior and PSLVERR policy hold
- SSOT refs: test_requirements.scenarios.SC_APB_CONFIG

### RTL-0250: Keep RTL observable for scenario SC_BASIC_TRANSFER

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_BASIC_TRANSFER
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_BASIC_TRANSFER.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_BASIC_TRANSFER; name=Basic frame transfer; expected=busy asserts then clears, done pending sets, RXDATA returns sampled value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_BASIC_TRANSFER
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: busy asserts then clears, done pending sets, RXDATA returns sampled value
- SSOT refs: test_requirements.scenarios.SC_BASIC_TRANSFER

### RTL-0251: Keep RTL observable for scenario SC_CPOL_CPHA_SWEEP

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_CPOL_CPHA_SWEEP
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_CPOL_CPHA_SWEEP.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_CPOL_CPHA_SWEEP; name=CPOL/CPHA sweep; expected=edge launch/sample ordering follows mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_CPOL_CPHA_SWEEP
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge launch/sample ordering follows mode
- SSOT refs: test_requirements.scenarios.SC_CPOL_CPHA_SWEEP

### RTL-0252: Keep RTL observable for scenario SC_LSB_FIRST

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_LSB_FIRST
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_LSB_FIRST.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_LSB_FIRST; name=LSB-first ordering; expected=MOSI bit order reversed relative to MSB-first.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_LSB_FIRST
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: MOSI bit order reversed relative to MSB-first
- SSOT refs: test_requirements.scenarios.SC_LSB_FIRST

### RTL-0253: Keep RTL observable for scenario SC_WIDTH_SWEEP

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_WIDTH_SWEEP
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_WIDTH_SWEEP.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_WIDTH_SWEEP; name=Frame width sweep; expected=exact configured bit count shifted/sampled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_WIDTH_SWEEP
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: exact configured bit count shifted/sampled
- SSOT refs: test_requirements.scenarios.SC_WIDTH_SWEEP

### RTL-0254: Keep RTL observable for scenario SC_FIFO_LIMITS

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_FIFO_LIMITS
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_FIFO_LIMITS.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_FIFO_LIMITS; name=FIFO boundary behavior; expected=tx_overrun and rx_overrun sticky behavior with data drop policy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_FIFO_LIMITS
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: tx_overrun and rx_overrun sticky behavior with data drop policy
- SSOT refs: test_requirements.scenarios.SC_FIFO_LIMITS

### RTL-0255: Keep RTL observable for scenario SC_IRQ_W1C

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_IRQ_W1C
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_IRQ_W1C.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_IRQ_W1C; name=Interrupt mask and W1C; expected=irq_o == OR(INT_PENDING & INT_MASK); W1C clears sticky only.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_IRQ_W1C
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: irq_o == OR(INT_PENDING & INT_MASK); W1C clears sticky only
- SSOT refs: test_requirements.scenarios.SC_IRQ_W1C

### RTL-0256: Keep RTL observable for scenario SC_ERROR_PATHS

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_ERROR_PATHS
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_ERROR_PATHS.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_ERROR_PATHS; name=Error paths; expected=PSLVERR and corresponding sticky bits/pending bits set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_ERROR_PATHS
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: PSLVERR and corresponding sticky bits/pending bits set
- SSOT refs: test_requirements.scenarios.SC_ERROR_PATHS

### RTL-0257: Keep RTL observable for scenario SC_PRESCALE_TIMING

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PRESCALE_TIMING
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PRESCALE_TIMING.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_PRESCALE_TIMING; name=Prescale timing; expected=SCLK half-period equals divisor+1 PCLK cycles.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PRESCALE_TIMING
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: SCLK half-period equals divisor+1 PCLK cycles
- SSOT refs: test_requirements.scenarios.SC_PRESCALE_TIMING

### RTL-0258: Keep RTL observable for scenario SC_LOOPBACK_DEBUG

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_LOOPBACK_DEBUG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_LOOPBACK_DEBUG.
Owner: spi in rtl/spi.sv via test_requirements.
SSOT item context: id=SC_LOOPBACK_DEBUG; name=Loopback and debug observability; expected=RX equals MOSI sequence and debug counters/probes align.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_LOOPBACK_DEBUG
  - Primary implementation evidence is in rtl/spi.sv
  - Downstream checker compares RTL-observed behavior against expected result: RX equals MOSI sequence and debug counters/probes align
- SSOT refs: test_requirements.scenarios.SC_LOOPBACK_DEBUG
