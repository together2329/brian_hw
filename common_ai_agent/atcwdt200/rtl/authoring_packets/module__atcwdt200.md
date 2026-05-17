# RTL Authoring Packet: module__atcwdt200

- Kind: module
- Owner module: atcwdt200
- Owner file: rtl/atcwdt200.sv
- Task count: 42
- Required tasks: 42

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: filelist, integration, integration.connections, io_list, io_list.interfaces, top_module
- SSOT connection contracts:
  - atcwdt200_regs.pclk <= pclk (integration.connections[0])
  - atcwdt200_regs.presetn <= presetn (integration.connections[1])
  - atcwdt200_core.pclk <= pclk (integration.connections[2])
  - atcwdt200_core.presetn <= presetn (integration.connections[3])
  - atcwdt200_sync.pclk <= pclk (integration.connections[4])
  - atcwdt200_sync.presetn <= presetn (integration.connections[5])
- SSOT top IO contracts: 12

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_module.
SSOT item context: value=atcwdt200.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: io_list

### RTL-0165: Implement feature apb_register_access

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.apb_register_access
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.apb_register_access.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=apb_register_access; output=prdata, CR state, SR state, restart pulse..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.apb_register_access
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: features.apb_register_access

### RTL-0166: Implement feature watchdog_timeout

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.watchdog_timeout
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.watchdog_timeout.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=watchdog_timeout; output=wdt_int, wdt_rst, SR.INTZERO..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.watchdog_timeout
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: features.watchdog_timeout

### RTL-0167: Implement feature restart_and_pause

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.restart_and_pause
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.restart_and_pause.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=restart_and_pause; output=Counter/state update only; no APB read side effect..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.restart_and_pause
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: features.restart_and_pause

### RTL-0179: Implement security item watchdog_reset_control

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.watchdog_reset_control
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.watchdog_reset_control.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=watchdog_reset_control.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.watchdog_reset_control
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: security.assets.watchdog_reset_control

### RTL-0180: Implement security item watchdog_disable_control

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.watchdog_disable_control
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.watchdog_disable_control.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=watchdog_disable_control.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.watchdog_disable_control
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: security.assets.watchdog_disable_control

### RTL-0181: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.
SSOT item context: name=external_modules; value=[{"name": "nds_sync_l2l", "policy": "replaced_by_local_manifest_sync", "source": "imported flist references external ....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0182: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.
SSOT item context: name=external_clocks; value=["pclk", "extclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0183: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.
SSOT item context: name=external_resets; value=["presetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0184: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0185: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0186: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0187: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0188: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0189: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: atcwdt200 in rtl/atcwdt200.sv via integration.connections.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0190: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: value=No inferred latches..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0191: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: value=Single pclk sequential domain after synchronizers..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0192: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: value=Generated RTL must be clean-room from SSOT behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0193: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0194: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0195: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=frequency_mhz_min; value=50.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0021: Implement parameter COUNTER_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.COUNTER_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.COUNTER_WIDTH.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=COUNTER_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.COUNTER_WIDTH
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: parameters.COUNTER_WIDTH

### RTL-0022: Implement parameter INT_TIME_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.INT_TIME_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.INT_TIME_WIDTH.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=INT_TIME_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.INT_TIME_WIDTH
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: parameters.INT_TIME_WIDTH

### RTL-0023: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: parameters.APB_ADDR_WIDTH

### RTL-0024: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/atcwdt200.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0027: Implement and connect port psel

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.psel.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.psel
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_control.ports.psel

### RTL-0028: Implement and connect port penable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.penable.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.penable
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_control.ports.penable

### RTL-0029: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.paddr.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=paddr; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.paddr
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - paddr width matches SSOT value 3
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_control.ports.paddr

### RTL-0030: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.pwrite.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.pwrite
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_control.ports.pwrite

### RTL-0031: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.pwdata.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.pwdata
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_control.ports.pwdata

### RTL-0032: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_control.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_control.ports.prdata.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_control.ports.prdata
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_control.ports.prdata

### RTL-0033: Implement and connect port extclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.watchdog_sideband.ports.extclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.watchdog_sideband.ports.extclk.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=extclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.watchdog_sideband.ports.extclk
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - extclk width matches SSOT value 1
  - extclk port direction remains input
- SSOT refs: io_list.interfaces.watchdog_sideband.ports.extclk

### RTL-0034: Implement and connect port wdt_pause

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.watchdog_sideband.ports.wdt_pause
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.watchdog_sideband.ports.wdt_pause.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=wdt_pause; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.watchdog_sideband.ports.wdt_pause
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - wdt_pause width matches SSOT value 1
  - wdt_pause port direction remains input
- SSOT refs: io_list.interfaces.watchdog_sideband.ports.wdt_pause

### RTL-0035: Implement and connect port wdt_int

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.watchdog_sideband.ports.wdt_int
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.watchdog_sideband.ports.wdt_int.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=wdt_int; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.watchdog_sideband.ports.wdt_int
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - wdt_int width matches SSOT value 1
  - wdt_int port direction remains output
- SSOT refs: io_list.interfaces.watchdog_sideband.ports.wdt_int

### RTL-0036: Implement and connect port wdt_rst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.watchdog_sideband.ports.wdt_rst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.watchdog_sideband.ports.wdt_rst.
Owner: atcwdt200 in rtl/atcwdt200.sv via io_list.interfaces.
SSOT item context: name=wdt_rst; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.watchdog_sideband.ports.wdt_rst
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - wdt_rst width matches SSOT value 1
  - wdt_rst port direction remains output
- SSOT refs: io_list.interfaces.watchdog_sideband.ports.wdt_rst

### RTL-0199: Keep RTL observable for scenario reset_defaults

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.reset_defaults
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.reset_defaults.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=reset_defaults; name=Reset defaults; expected=CR, SR, REG_WEN, COUNTER, and STATE reset to declared values; outputs deassert..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.reset_defaults
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: CR, SR, REG_WEN, COUNTER, and STATE reset to declared values; outputs deassert.
- SSOT refs: test_requirements.scenarios.reset_defaults

### RTL-0200: Keep RTL observable for scenario apb_register_access

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.apb_register_access
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.apb_register_access.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=apb_register_access; name=APB register read/write; expected=Register readback follows register map and protected write policy..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.apb_register_access
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: Register readback follows register map and protected write policy.
- SSOT refs: test_requirements.scenarios.apb_register_access

### RTL-0201: Keep RTL observable for scenario restart_command

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.restart_command
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.restart_command.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=restart_command; name=Restart command; expected=COUNTER clears and STATE returns to ST_INTTIME..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.restart_command
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: COUNTER clears and STATE returns to ST_INTTIME.
- SSOT refs: test_requirements.scenarios.restart_command

### RTL-0202: Keep RTL observable for scenario interrupt_timeout

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.interrupt_timeout
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.interrupt_timeout.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=interrupt_timeout; name=Interrupt timeout; expected=SR.INTZERO sets and wdt_int asserts when timeout is reached..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.interrupt_timeout
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: SR.INTZERO sets and wdt_int asserts when timeout is reached.
- SSOT refs: test_requirements.scenarios.interrupt_timeout

### RTL-0203: Keep RTL observable for scenario reset_timeout

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.reset_timeout
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.reset_timeout.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=reset_timeout; name=Reset timeout; expected=wdt_rst asserts and CR.EN clears on reset timeout..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.reset_timeout
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: wdt_rst asserts and CR.EN clears on reset timeout.
- SSOT refs: test_requirements.scenarios.reset_timeout

### RTL-0204: Keep RTL observable for scenario pause_and_extclk

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.pause_and_extclk
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.pause_and_extclk.
Owner: atcwdt200 in rtl/atcwdt200.sv via top_fallback.
SSOT item context: id=pause_and_extclk; name=Pause and external clock behavior; expected=Counter advances only on approved ticks while pause is deasserted..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.pause_and_extclk
  - Primary implementation evidence is in rtl/atcwdt200.sv
  - Downstream checker compares RTL-observed behavior against expected result: Counter advances only on approved ticks while pause is deasserted.
- SSOT refs: test_requirements.scenarios.pause_and_extclk
