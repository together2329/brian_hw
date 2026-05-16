# RTL Authoring Packet: module__rv32i_min

- Kind: module
- Owner module: rv32i_min
- Owner file: rtl/rv32i_min.sv
- Task count: 11
- Required tasks: 11

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: integration, integration.connections, io_list
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])
  - rv32i_min_memwb.d_addr <= d_addr (integration.connections[3])
  - rv32i_min_memwb.d_wdata <= d_wdata (integration.connections[4])
  - rv32i_min_memwb.d_rdata <= d_rdata (integration.connections[5])
  - rv32i_min_memwb.d_we <= d_we (integration.connections[6])
  - rv32i_min_memwb.d_be <= d_be (integration.connections[7])
  - rv32i_min_memwb.d_valid <= d_valid (integration.connections[8])
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])
- SSOT top IO contracts: 24

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=rv32i_min.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: io_list

### RTL-0153: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=Architectural register state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: security.assets.asset_0

### RTL-0154: Implement security item asset_1

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=Program counter control flow integrity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: security.assets.asset_1

### RTL-0155: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=Load/store data correctness.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: security.assets.asset_2

### RTL-0168: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=Single clock clk with async active-low reset rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0169: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=No inferred latches.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0170: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: value=Preserve explicit three-stage pipeline boundaries.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0024: Implement parameter XLEN

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.XLEN
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.XLEN.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: name=XLEN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.XLEN
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: parameters.XLEN

### RTL-0025: Implement parameter RESET_PC

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_PC
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_PC.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: name=RESET_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_PC
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: parameters.RESET_PC

### RTL-0026: Implement parameter INST_ALIGN

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.INST_ALIGN
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.INST_ALIGN.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
SSOT item context: name=INST_ALIGN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.INST_ALIGN
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: parameters.INST_ALIGN
