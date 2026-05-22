# RTL Authoring Packet: module__gpio

- Kind: module
- Owner module: gpio
- Owner file: rtl/gpio.sv
- Task count: 26
- Required tasks: 26

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
- LLM-actionable open tasks: 25
- Human-locked open tasks: 0
- Owner refs: integration, integration.connections, rtl_contract
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])
  - gpio_input_sampler.clk <= clk (integration.connections[6])
  - gpio_input_sampler.rst_n <= rst_n (integration.connections[7])
  - gpio_input_sampler.pad_in <= pad_in (integration.connections[8])
  - gpio_input_sampler.dir_q <= dir_q (integration.connections[9])
  - gpio_input_sampler.din_q <= din_q (integration.connections[10])
  - gpio_pad_logic.dir_q <= dir_q (integration.connections[11])
- SSOT top IO contracts: 10

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: gpio in rtl/gpio.sv via top_fallback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: open
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=gpio.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: io_list

### RTL-0109: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=Assert rst_n low to restore deterministic zero state.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0110: Implement security item asset_0

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=Correct direction gating to avoid unintended output drive.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: security.assets.asset_0

### RTL-0111: Implement security item asset_1

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=Integrity of sampled input state din_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: security.assets.asset_1

### RTL-0112: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: gpio in rtl/gpio.sv via integration.
SSOT item context: value=pad_ring interface for pad_in/oe_o/pad_o.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0113: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: gpio in rtl/gpio.sv via integration.
SSOT item context: value=clock/reset distribution for clk/rst_n.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0114: Implement integration item clk

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=clk; signal=clk.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port clk is the implementation/observation point for clk
- SSOT refs: integration.connections.clk

### RTL-0115: Implement integration item rst_n

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_n.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=rst_n; signal=rst_n.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_n
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port rst_n is the implementation/observation point for rst_n
- SSOT refs: integration.connections.rst_n

### RTL-0116: Implement integration item dir_in

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dir_in
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dir_in.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dir_in; signal=dir_in.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dir_in
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dir_in is the implementation/observation point for dir_in
- SSOT refs: integration.connections.dir_in

### RTL-0117: Implement integration item dout_in

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dout_in
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dout_in.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dout_in; signal=dout_in.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dout_in
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dout_in is the implementation/observation point for dout_in
- SSOT refs: integration.connections.dout_in

### RTL-0118: Implement integration item dir_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dir_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dir_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dir_q; signal=dir_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dir_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dir_q is the implementation/observation point for dir_q
- SSOT refs: integration.connections.dir_q

### RTL-0119: Implement integration item dout_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dout_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dout_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dout_q; signal=dout_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dout_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dout_q is the implementation/observation point for dout_q
- SSOT refs: integration.connections.dout_q

### RTL-0120: Implement integration item clk

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=clk; signal=clk.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port clk is the implementation/observation point for clk
- SSOT refs: integration.connections.clk

### RTL-0121: Implement integration item rst_n

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_n.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=rst_n; signal=rst_n.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_n
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port rst_n is the implementation/observation point for rst_n
- SSOT refs: integration.connections.rst_n

### RTL-0122: Implement integration item pad_in

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pad_in
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pad_in.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=pad_in; signal=pad_in.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pad_in
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port pad_in is the implementation/observation point for pad_in
- SSOT refs: integration.connections.pad_in

### RTL-0123: Implement integration item dir_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dir_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dir_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dir_q; signal=dir_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dir_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dir_q is the implementation/observation point for dir_q
- SSOT refs: integration.connections.dir_q

### RTL-0124: Implement integration item din_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.din_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.din_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=din_q; signal=din_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.din_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port din_q is the implementation/observation point for din_q
- SSOT refs: integration.connections.din_q

### RTL-0125: Implement integration item dir_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dir_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dir_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dir_q; signal=dir_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dir_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dir_q is the implementation/observation point for dir_q
- SSOT refs: integration.connections.dir_q

### RTL-0126: Implement integration item dout_q

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.dout_q
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dout_q.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=dout_q; signal=dout_q.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dout_q
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port dout_q is the implementation/observation point for dout_q
- SSOT refs: integration.connections.dout_q

### RTL-0127: Implement integration item oe_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.oe_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.oe_o.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=oe_o; signal=oe_o.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.oe_o
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port oe_o is the implementation/observation point for oe_o
- SSOT refs: integration.connections.oe_o

### RTL-0128: Implement integration item pad_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pad_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pad_o.
Owner: gpio in rtl/gpio.sv via integration.connections.
SSOT item context: port=pad_o; signal=pad_o.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pad_o
  - Primary implementation evidence is in rtl/gpio.sv
  - DUT port pad_o is the implementation/observation point for pad_o
- SSOT refs: integration.connections.pad_o

### RTL-0129: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=Single clock constraint on clk.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0130: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=Reset recovery/removal constraints for rst_n.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0131: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: value=WIDTH >= 1.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0023: Implement parameter WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.WIDTH.
Owner: gpio in rtl/gpio.sv via top_fallback.
SSOT item context: name=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.WIDTH
  - Primary implementation evidence is in rtl/gpio.sv
- SSOT refs: parameters.WIDTH
