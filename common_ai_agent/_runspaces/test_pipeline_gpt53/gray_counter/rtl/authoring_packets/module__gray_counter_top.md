# RTL Authoring Packet: module__gray_counter_top

- Kind: module
- Owner module: gray_counter_top
- Owner file: rtl/gray_counter.sv
- Task count: 27
- Required tasks: 27

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: integration, integration.connections, io_list, io_list.interfaces, io_list.interfaces.control, io_list.interfaces.status

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: gray_counter_top in rtl/gray_counter.sv via semantic_terms:top.
SSOT item context: value=gray_counter.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: io_list

### RTL-0121: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Correct state transition semantics.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: security.assets.asset_0

### RTL-0122: Implement security item asset_1

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Deterministic reset/clear behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: security.assets.asset_1

### RTL-0123: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Accurate done pulse used for downstream checks.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: security.assets.asset_2

### RTL-0124: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.
SSOT item context: value=Single clean synchronous clock source.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0125: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.
SSOT item context: value=Asynchronous active-low reset source meeting timing assumptions.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0126: Implement integration item dependencie_2

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_2
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_2.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.
SSOT item context: value=Upstream stimulus driver for enable/clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_2
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: integration.dependencies.dependencie_2

### RTL-0127: Implement integration item soc_clk_or_tb_clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.soc_clk_or_tb_clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.soc_clk_or_tb_clk.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=clk; signal=soc_clk_or_tb_clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.soc_clk_or_tb_clk
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port clk is the implementation/observation point for clk
- SSOT refs: integration.connections.soc_clk_or_tb_clk

### RTL-0128: Implement integration item soc_rst_n_or_tb_rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.soc_rst_n_or_tb_rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.soc_rst_n_or_tb_rst_n.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=rst_n; signal=soc_rst_n_or_tb_rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.soc_rst_n_or_tb_rst_n
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port rst_n is the implementation/observation point for rst_n
- SSOT refs: integration.connections.soc_rst_n_or_tb_rst_n

### RTL-0129: Implement integration item control_enable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.control_enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.control_enable.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=enable; signal=control_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.control_enable
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port enable is the implementation/observation point for enable
- SSOT refs: integration.connections.control_enable

### RTL-0130: Implement integration item control_clear

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.control_clear
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.control_clear.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=clear; signal=control_clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.control_clear
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port clear is the implementation/observation point for clear
- SSOT refs: integration.connections.control_clear

### RTL-0131: Implement integration item observed_gray_value

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.observed_gray_value
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.observed_gray_value.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=gray_value; signal=observed_gray_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.observed_gray_value
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port gray_value is the implementation/observation point for gray_value
- SSOT refs: integration.connections.observed_gray_value

### RTL-0132: Implement integration item observed_bin_value

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.observed_bin_value
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.observed_bin_value.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=bin_value; signal=observed_bin_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.observed_bin_value
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port bin_value is the implementation/observation point for bin_value
- SSOT refs: integration.connections.observed_bin_value

### RTL-0133: Implement integration item observed_done

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.observed_done
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.observed_done.
Owner: gray_counter_top in rtl/gray_counter.sv via integration.connections.
SSOT item context: port=done; signal=observed_done.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.observed_done
  - Primary implementation evidence is in rtl/gray_counter.sv
  - DUT port done is the implementation/observation point for done
- SSOT refs: integration.connections.observed_done

### RTL-0134: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Primary clock constraint from timing.target_clocks.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0135: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Asynchronous reset path treated per library reset semantics.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0136: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: value=Honor WIDTH parameterization without hardcoded constants.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0021: Implement parameter WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.WIDTH.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: name=WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.WIDTH
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: parameters.WIDTH

### RTL-0022: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: gray_counter_top in rtl/gray_counter.sv via top_fallback.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/gray_counter.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0023: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/gray_counter.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0024: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/gray_counter.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0025: Implement and connect port enable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control.ports.enable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control.ports.enable.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.interfaces.control.
SSOT item context: name=enable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control.ports.enable
  - Primary implementation evidence is in rtl/gray_counter.sv
  - enable width matches SSOT value 1
  - enable port direction remains input
- SSOT refs: io_list.interfaces.control.ports.enable

### RTL-0026: Implement and connect port clear

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.control.ports.clear
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.control.ports.clear.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.interfaces.control.
SSOT item context: name=clear; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.control.ports.clear
  - Primary implementation evidence is in rtl/gray_counter.sv
  - clear width matches SSOT value 1
  - clear port direction remains input
- SSOT refs: io_list.interfaces.control.ports.clear

### RTL-0027: Implement and connect port gray_value

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status.ports.gray_value
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status.ports.gray_value.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.interfaces.status.
SSOT item context: name=gray_value; width=WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status.ports.gray_value
  - Primary implementation evidence is in rtl/gray_counter.sv
  - gray_value width matches SSOT value WIDTH
  - gray_value port direction remains output
- SSOT refs: io_list.interfaces.status.ports.gray_value

### RTL-0028: Implement and connect port bin_value

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status.ports.bin_value
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status.ports.bin_value.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.interfaces.status.
SSOT item context: name=bin_value; width=WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status.ports.bin_value
  - Primary implementation evidence is in rtl/gray_counter.sv
  - bin_value width matches SSOT value WIDTH
  - bin_value port direction remains output
- SSOT refs: io_list.interfaces.status.ports.bin_value

### RTL-0029: Implement and connect port done

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status.ports.done
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status.ports.done.
Owner: gray_counter_top in rtl/gray_counter.sv via io_list.interfaces.status.
SSOT item context: name=done; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status.ports.done
  - Primary implementation evidence is in rtl/gray_counter.sv
  - done width matches SSOT value 1
  - done port direction remains output
- SSOT refs: io_list.interfaces.status.ports.done
