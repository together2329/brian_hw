# RTL Authoring Packet: module__adder_kogge_stone

- Kind: module
- Owner module: adder_kogge_stone
- Owner file: rtl/adder_kogge_stone.sv
- Task count: 46
- Required tasks: 46

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])
  - adder_kogge_stone_regs.clk_i <= PCLK (integration.connections[2])
  - adder_kogge_stone_regs.rst_ni <= PRESETn (integration.connections[3])
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
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via top_module.
SSOT item context: value=adder_kogge_stone.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: io_list

### RTL-0029: Implement top-level wrapper adder_kogge_stone.sv

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Instantiate regs and core modules. Wire APB ports to regs. Wire datapath ports to core. Tie or mux top-level a_i/b_i/cin_i with APB shadow per custom.assumptions.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top-level module name matches top_module.name
  - All IO list ports present and connected
  - Manifest hierarchy evidence passes
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Semantic source_refs covered: integration, io_list, sub_modules
- SSOT refs: integration, io_list, sub_modules, workflow_todos.rtl-gen[2]

### RTL-0122: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via error_handling.
SSOT item context: action=retry APB access with valid address.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0123: Implement security item register_map

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.register_map
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.register_map.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via security.
SSOT item context: name=register_map.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.register_map
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: security.assets.register_map

### RTL-0124: Implement security item adder_result

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.adder_result
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.adder_result.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via security.
SSOT item context: name=adder_result.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.adder_result
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: security.assets.adder_result

### RTL-0125: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0126: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0127: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0128: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0129: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0130: Implement integration item PCLK

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0131: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0132: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: value=No inferred latches.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0133: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: value=All flops reset according to clock_reset_domains.reset_scheme.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0134: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: value=No package/interface/modport/function/task/for/while constructs in generated RTL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0135: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0136: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0137: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=50.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0140: Prove module adder_kogge_stone is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.adder_kogge_stone.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.adder_kogge_stone.module_equivalence.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.adder_kogge_stone.module_equivalence
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: sub_modules.adder_kogge_stone.module_equivalence

### RTL-0030: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0031: Implement parameter ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ADDR_WIDTH.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via parameters.
SSOT item context: name=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ADDR_WIDTH
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: parameters.ADDR_WIDTH

### RTL-0032: Implement parameter APB_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_DATA_WIDTH.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via parameters.
SSOT item context: name=APB_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_DATA_WIDTH
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: parameters.APB_DATA_WIDTH

### RTL-0033: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via parameters.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0034: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
- SSOT refs: parameters.RESET_POLARITY

### RTL-0035: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0036: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0037: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.paddr.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=paddr; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.paddr
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - paddr width matches SSOT value 8
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.paddr

### RTL-0038: Implement and connect port psel

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.psel.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.psel
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.psel

### RTL-0039: Implement and connect port penable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.penable.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.penable
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.penable

### RTL-0040: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.pwrite.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.pwrite
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.pwrite

### RTL-0041: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.pwdata.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.pwdata
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.pwdata

### RTL-0042: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.prdata.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.prdata
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.prdata

### RTL-0043: Implement and connect port pready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.pready.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.pready
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.pready

### RTL-0044: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.pslverr.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.pslverr
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.pslverr

### RTL-0045: Implement and connect port a_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.adder_datapath.ports.a_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.adder_datapath.ports.a_i.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=a_i; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.adder_datapath.ports.a_i
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - a_i width matches SSOT value DATA_WIDTH
  - a_i port direction remains input
- SSOT refs: io_list.interfaces.adder_datapath.ports.a_i

### RTL-0046: Implement and connect port b_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.adder_datapath.ports.b_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.adder_datapath.ports.b_i.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=b_i; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.adder_datapath.ports.b_i
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - b_i width matches SSOT value DATA_WIDTH
  - b_i port direction remains input
- SSOT refs: io_list.interfaces.adder_datapath.ports.b_i

### RTL-0047: Implement and connect port cin_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.adder_datapath.ports.cin_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.adder_datapath.ports.cin_i.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=cin_i; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.adder_datapath.ports.cin_i
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - cin_i width matches SSOT value 1
  - cin_i port direction remains input
- SSOT refs: io_list.interfaces.adder_datapath.ports.cin_i

### RTL-0048: Implement and connect port sum_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.adder_datapath.ports.sum_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.adder_datapath.ports.sum_o.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=sum_o; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.adder_datapath.ports.sum_o
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - sum_o width matches SSOT value DATA_WIDTH
  - sum_o port direction remains output
- SSOT refs: io_list.interfaces.adder_datapath.ports.sum_o

### RTL-0049: Implement and connect port cout_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.adder_datapath.ports.cout_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.adder_datapath.ports.cout_o.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via io_list.
SSOT item context: name=cout_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.adder_datapath.ports.cout_o
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - cout_o width matches SSOT value 1
  - cout_o port direction remains output
- SSOT refs: io_list.interfaces.adder_datapath.ports.cout_o

### RTL-0141: Keep RTL observable for scenario SC_BASIC

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_BASIC
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_BASIC.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_BASIC; name=Basic addition; expected=SUM_RESULT=0x99999999, COUT_RESULT=0, STATUS.done=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_BASIC
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: SUM_RESULT=0x99999999, COUT_RESULT=0, STATUS.done=1
- SSOT refs: test_requirements.scenarios.SC_BASIC

### RTL-0142: Keep RTL observable for scenario SC_CARRY

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_CARRY
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_CARRY.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_CARRY; name=Carry propagation; expected=SUM_RESULT=0x00000001, COUT_RESULT=1, STATUS.overflow=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_CARRY
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: SUM_RESULT=0x00000001, COUT_RESULT=1, STATUS.overflow=1
- SSOT refs: test_requirements.scenarios.SC_CARRY

### RTL-0143: Keep RTL observable for scenario SC_APB_ERR

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_APB_ERR
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_APB_ERR.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_APB_ERR; name=APB out-of-bounds; expected=pslverr=1, prdata=0, no register change.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_APB_ERR
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: pslverr=1, prdata=0, no register change
- SSOT refs: test_requirements.scenarios.SC_APB_ERR

### RTL-0144: Keep RTL observable for scenario SC_HOLD_MODE

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_HOLD_MODE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_HOLD_MODE.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_HOLD_MODE; name=Hold mode operation; expected=Output registers hold previous result; new operands do not affect sum until next start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_HOLD_MODE
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: Output registers hold previous result; new operands do not affect sum until next start
- SSOT refs: test_requirements.scenarios.SC_HOLD_MODE

### RTL-0145: Keep RTL observable for scenario SC_CLR_DONE

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_CLR_DONE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_CLR_DONE.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_CLR_DONE; name=Clear done flag; expected=STATUS.done transitions 1->0 on next cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_CLR_DONE
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: STATUS.done transitions 1->0 on next cycle
- SSOT refs: test_requirements.scenarios.SC_CLR_DONE

### RTL-0146: Keep RTL observable for scenario SC_RESET

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_RESET
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_RESET.
Owner: adder_kogge_stone in rtl/adder_kogge_stone.sv via test_requirements.
SSOT item context: id=SC_RESET; name=Reset behavior; expected=All registers reset to 0; STATUS.busy=0, STATUS.done=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_RESET
  - Primary implementation evidence is in rtl/adder_kogge_stone.sv
  - Downstream checker compares RTL-observed behavior against expected result: All registers reset to 0; STATUS.busy=0, STATUS.done=0
- SSOT refs: test_requirements.scenarios.SC_RESET
