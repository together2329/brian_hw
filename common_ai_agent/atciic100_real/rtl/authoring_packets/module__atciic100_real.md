# RTL Authoring Packet: module__atciic100_real

- Kind: module
- Owner module: atciic100_real
- Owner file: rtl/atciic100_real.sv
- Task count: 43
- Required tasks: 43

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 42
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_fifo.data_in <= pwdata (sub_modules[0].connections[2])
  - atciic100_apbslv.cmd_reg <= cmd (sub_modules[1].connections[0])
  - atciic100_fifo.data_out <= tx_data (sub_modules[1].connections[1])
  - atciic100_gsf.scl_in <= scl_filtered (sub_modules[1].connections[2])
  - atciic100_apbslv.data_in <= pwdata (sub_modules[2].connections[0])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])
- SSOT top IO contracts: 15

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: open
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
SSOT item context: value=atciic100_real.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: io_list

### RTL-0031: Integrate Modules in Top Wrapper

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: Instantiate sub-modules and wire ports.
SSOT ref: workflow_todos.rtl-gen[4].
Owner: atciic100_real in rtl/atciic100_real.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.v.
- Criteria:
  - Integration compile passes
  - All top-level ports connected
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/atciic100_real.v
  - Semantic source_refs covered: sub_modules
- SSOT refs: sub_modules, workflow_todos.rtl-gen[4]

### RTL-0184: Implement interrupt item IRQ_COMB

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.IRQ_COMB
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.IRQ_COMB.
Owner: atciic100_real in rtl/atciic100_real.sv via interrupts.
SSOT item context: name=IRQ_COMB; clear=W1C.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.IRQ_COMB
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - IRQ_COMB clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.IRQ_COMB

### RTL-0210: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: atciic100_real in rtl/atciic100_real.sv via error_handling.
SSOT item context: value=Software clears status bits.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0211: Implement error/fault item recovery_1

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_1
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_1.
Owner: atciic100_real in rtl/atciic100_real.sv via error_handling.
SSOT item context: value=Issue CMD Reset (0x5).
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_1
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: error_handling.recovery.recovery_1

### RTL-0212: Implement security item I2C_Data

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.I2C_Data
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.I2C_Data.
Owner: atciic100_real in rtl/atciic100_real.sv via security.
SSOT item context: name=I2C_Data.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.I2C_Data
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: security.assets.I2C_Data

### RTL-0213: Implement integration item APB Bus

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.APB_Bus
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.APB_Bus.
Owner: atciic100_real in rtl/atciic100_real.sv via integration.
SSOT item context: name=APB Bus.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.APB_Bus
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: integration.dependencies.APB_Bus

### RTL-0214: Implement synthesis item pclk

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.pclk
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.pclk.
Owner: atciic100_real in rtl/atciic100_real.sv via synthesis.
SSOT item context: name=pclk.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.pclk
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: synthesis.constraints.pclk

### RTL-0215: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: atciic100_real in rtl/atciic100_real.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=100.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0216: Implement synthesis item area_um2

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2.
Owner: atciic100_real in rtl/atciic100_real.sv via synthesis.
SSOT item context: name=area_um2.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: synthesis.ppa_targets.area_um2

### RTL-0217: Implement synthesis item power_mw

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw.
Owner: atciic100_real in rtl/atciic100_real.sv via synthesis.
SSOT item context: name=power_mw.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: synthesis.ppa_targets.power_mw

### RTL-0222: Prove module atciic100_real is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_real.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_real.module_equivalence.
Owner: atciic100_real in rtl/atciic100_real.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_real.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: sub_modules.atciic100_real.module_equivalence

### RTL-0032: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0033: Implement parameter FIFO_DEPTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.FIFO_DEPTH.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=FIFO_DEPTH.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.FIFO_DEPTH
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.FIFO_DEPTH

### RTL-0034: Implement parameter INDEX_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.INDEX_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.INDEX_WIDTH.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=INDEX_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.INDEX_WIDTH
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.INDEX_WIDTH

### RTL-0035: Implement parameter TP_AUTOACK

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.TP_AUTOACK
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TP_AUTOACK.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=TP_AUTOACK.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TP_AUTOACK
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.TP_AUTOACK

### RTL-0036: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0037: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: atciic100_real in rtl/atciic100_real.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: parameters.RESET_POLARITY

### RTL-0223: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC1; name=Reset; expected=Registers default, FIFO empty.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Registers default, FIFO empty
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0224: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC2; name=APB Read; expected=0x0202.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: 0x0202
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0225: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC3; name=APB Write; expected=Setup updated.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Setup updated
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0226: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC4; name=Master TX; expected=Data on bus.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Data on bus
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0227: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC5; name=Master RX; expected=Data in FIFO.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Data in FIFO
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0228: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC6; name=Slave TX; expected=Data driven.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Data driven
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0229: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC7; name=Slave RX; expected=Data in FIFO.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Data in FIFO
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0230: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC8; name=Gen Call; expected=GenCall status.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: GenCall status
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0231: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC9; name=Arb Lose; expected=ArbLost status.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: ArbLost status
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0232: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC10; name=FIFO Full; expected=Full status.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Full status
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0233: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC11; name=DMA Flow; expected=Req/Ack handshake.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Req/Ack handshake
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0234: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: id=SC12; name=Glitch; expected=Ignored.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - Downstream checker compares RTL-observed behavior against expected result: Ignored
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0235: Provide RTL evidence for coverage bin coverage_bin_0

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_0
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_0.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Reset.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_0
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_0 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_0

### RTL-0236: Provide RTL evidence for coverage bin coverage_bin_1

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_1
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_1.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=APB_R.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_1
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_1 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_1

### RTL-0237: Provide RTL evidence for coverage bin coverage_bin_2

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_2
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_2.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=APB_W.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_2
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_2 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_2

### RTL-0238: Provide RTL evidence for coverage bin coverage_bin_3

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_3
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_3.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Master_TX.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_3
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_3 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_3

### RTL-0239: Provide RTL evidence for coverage bin coverage_bin_4

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_4
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_4.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Master_RX.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_4
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_4 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_4

### RTL-0240: Provide RTL evidence for coverage bin coverage_bin_5

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_5
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_5.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Slave_TX.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_5
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_5 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_5

### RTL-0241: Provide RTL evidence for coverage bin coverage_bin_6

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_6
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_6.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Slave_RX.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_6
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_6 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_6

### RTL-0242: Provide RTL evidence for coverage bin coverage_bin_7

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_7
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_7.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Gen_Call.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_7
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_7 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_7

### RTL-0243: Provide RTL evidence for coverage bin coverage_bin_8

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_8
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_8.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Arb_Lose.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_8
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_8 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_8

### RTL-0244: Provide RTL evidence for coverage bin coverage_bin_9

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_9
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_9.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=FIFO_Full.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_9
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_9 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_9

### RTL-0245: Provide RTL evidence for coverage bin coverage_bin_10

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_10
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_10.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=DMA.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_10
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_10 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_10

### RTL-0246: Provide RTL evidence for coverage bin coverage_bin_11

- Priority: normal
- Required: True
- Status: open
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.coverage_bin_11
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.coverage_bin_11.
Owner: atciic100_real in rtl/atciic100_real.sv via test_requirements.
SSOT item context: value=Glitch.
- Current reason: Owner RTL file is missing: rtl/atciic100_real.sv.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.coverage_bin_11
  - Primary implementation evidence is in rtl/atciic100_real.sv
  - test_requirements.coverage_goals.planned_bins.coverage_bin_11 can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.coverage_bin_11
