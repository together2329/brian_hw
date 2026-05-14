# RTL Authoring Packet: module__uart_lite

- Kind: module
- Owner module: uart_lite
- Owner file: rtl/uart_lite.sv
- Task count: 33
- Required tasks: 33

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
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])
- SSOT top IO contracts: 14

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: uart_lite in rtl/uart_lite.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: uart_lite in rtl/uart_lite.sv via top_module.
SSOT item context: value=uart_lite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: io_list

### RTL-0034: Implement uart_lite top-level module

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[7]
- Detail: Top-level module instantiates uart_lite_core. Maps APB, UART, and interrupt ports. No additional logic — pure wiring wrapper.
SSOT ref: workflow_todos.rtl-gen[7].
Owner: uart_lite in rtl/uart_lite.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Port list matches io_list interfaces
  - Correctly instantiates uart_lite_core with named port connections
  - No logic in top-level module
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[7]
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Semantic source_refs covered: integration, io_list
- SSOT refs: integration, io_list, workflow_todos.rtl-gen[7]

### RTL-0243: Implement security item register_map

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.register_map
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.register_map.
Owner: uart_lite in rtl/uart_lite.sv via security.
SSOT item context: name=register_map.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.register_map
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: security.assets.register_map

### RTL-0244: Implement security item uart_data_stream

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.uart_data_stream
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.uart_data_stream.
Owner: uart_lite in rtl/uart_lite.sv via security.
SSOT item context: name=uart_data_stream.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.uart_data_stream
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: security.assets.uart_data_stream

### RTL-0245: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0246: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0247: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0248: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=PCLK; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port PCLK is the implementation/observation point for PCLK
- SSOT refs: integration.connections.PCLK

### RTL-0249: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: uart_lite in rtl/uart_lite.sv via integration.
SSOT item context: port=PRESETn; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/uart_lite.sv
  - DUT port PRESETn is the implementation/observation point for PRESETn
- SSOT refs: integration.connections.PRESETn

### RTL-0250: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: value=No inferred latches.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0251: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: value=All flops reset according to clock_reset_domains.reset_scheme.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0252: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: value=No package/interface/modport/function/task/for/while constructs in generated RTL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0253: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0254: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0255: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: uart_lite in rtl/uart_lite.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=50.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0263: Prove module uart_lite is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite.module_equivalence.
Owner: uart_lite in rtl/uart_lite.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite.sv
- SSOT refs: sub_modules.uart_lite.module_equivalence

### RTL-0264: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC1; name=Basic TX byte; expected=txd_o outputs start=0, 8 data bits LSB-first, stop=1. tx_empty asserts after frame. bytes_tx increments..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: txd_o outputs start=0, 8 data bits LSB-first, stop=1. tx_empty asserts after frame. bytes_tx increments.
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0265: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC2; name=Basic RX byte; expected=RXDATA returns 0xA5. bytes_rx increments. rx_empty=0 then 1 after read..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: RXDATA returns 0xA5. bytes_rx increments. rx_empty=0 then 1 after read.
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0266: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC3; name=TX FIFO flow control; expected=First FIFO_DEPTH writes accepted (tx_full goes 0→1 on last). Last write ignored. Bytes transmit in order..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: First FIFO_DEPTH writes accepted (tx_full goes 0→1 on last). Last write ignored. Bytes transmit in order.
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0267: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC4; name=RX FIFO flow control; expected=First FIFO_DEPTH bytes fill RX FIFO (rx_full=1). Last byte discarded; rx_overrun flag set..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: First FIFO_DEPTH bytes fill RX FIFO (rx_full=1). Last byte discarded; rx_overrun flag set.
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0268: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC5; name=Parity generation and checking; expected=TX parity bit=1. RX verifies even parity passes. DEBUG_PARITY_ERRS unchanged..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: TX parity bit=1. RX verifies even parity passes. DEBUG_PARITY_ERRS unchanged.
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0269: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC6; name=Parity error detection; expected=parity_err sticky flag set; INT_PENDING.parity_err_pending set; parities_errored increments. Byte still pushed to RX ....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: parity_err sticky flag set; INT_PENDING.parity_err_pending set; parities_errored increments. Byte still pushed to RX ...
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0270: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC7; name=Frame error detection; expected=frame_err sticky flag set; INT_PENDING.frame_err_pending set; frames_errored increments. Byte still pushed..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: frame_err sticky flag set; INT_PENDING.frame_err_pending set; frames_errored increments. Byte still pushed.
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0271: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC8; name=Loopback mode; expected=txd_o toggles; byte appears in RX FIFO without external rxd_i stimulus. Both bytes_tx and bytes_rx increment..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: txd_o toggles; byte appears in RX FIFO without external rxd_i stimulus. Both bytes_tx and bytes_rx increment.
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0272: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC9; name=Break send; expected=txd_o driven low for >= 13 bit times; break_send self-clears after break period; break_detected may trigger on RX sid....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: txd_o driven low for >= 13 bit times; break_send self-clears after break period; break_detected may trigger on RX sid...
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0273: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC10; name=Interrupt masking and W1C clear; expected=irq_o assertion follows INT_PENDING & INT_MASK. W1C clears both PENDING and STATUS sticky bits..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: irq_o assertion follows INT_PENDING & INT_MASK. W1C clears both PENDING and STATUS sticky bits.
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0274: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC11; name=Configurable data width 5-bit; expected=txd_o frame has 5 data bits. RX recovers 0x15 & 0x1F..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: txd_o frame has 5 data bits. RX recovers 0x15 & 0x1F.
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0275: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC12; name=Double stop bit; expected=txd_o frame has 2 stop bits. RX correctly receives with 2 stop bits..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: txd_o frame has 2 stop bits. RX correctly receives with 2 stop bits.
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0276: Keep RTL observable for scenario SC13

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC13
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC13.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC13; name=Odd parity; expected=TX parity bit=1 (makes odd number of 1s). RX expects odd parity..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC13
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: TX parity bit=1 (makes odd number of 1s). RX expects odd parity.
- SSOT refs: test_requirements.scenarios.SC13

### RTL-0277: Keep RTL observable for scenario SC14

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC14
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC14.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC14; name=TX underrun; expected=tx_underrun sticky flag set; txd_o returns to mark (high)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC14
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: tx_underrun sticky flag set; txd_o returns to mark (high).
- SSOT refs: test_requirements.scenarios.SC14

### RTL-0278: Keep RTL observable for scenario SC15

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC15
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC15.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC15; name=False start detection; expected=RX FSM returns to IDLE without receiving byte. No counters increment..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC15
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: RX FSM returns to IDLE without receiving byte. No counters increment.
- SSOT refs: test_requirements.scenarios.SC15

### RTL-0279: Keep RTL observable for scenario SC16

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC16
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC16.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC16; name=Debug counters wrap; expected=Counter wraps: 0xFFFFFFFF → 0x00000000 → 0x00000001..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC16
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Counter wraps: 0xFFFFFFFF → 0x00000000 → 0x00000001.
- SSOT refs: test_requirements.scenarios.SC16
