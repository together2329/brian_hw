# RTL Authoring Packet: module__dma_scratch_ui_live_20260519a__io_list

- Kind: module
- Owner module: dma_scratch_ui_live_20260519a
- Owner file: rtl/dma_scratch_ui_live_20260519a.sv
- Task count: 36
- Required tasks: 36

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 2/15 section=io_list task_limit=48
- Slice rule: Owner module dma_scratch_ui_live_20260519a is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 36

## Tasks

### RTL-0064: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0065: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0066: Implement and connect port s_axil_awaddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_awaddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_awaddr.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_awaddr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_awaddr
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_awaddr width matches SSOT value ADDR_WIDTH
  - s_axil_awaddr port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_awaddr

### RTL-0067: Implement and connect port s_axil_awvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_awvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_awvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_awvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_awvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_awvalid width matches SSOT value 1
  - s_axil_awvalid port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_awvalid

### RTL-0068: Implement and connect port s_axil_awready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_awready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_awready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_awready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_awready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_awready width matches SSOT value 1
  - s_axil_awready port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_awready

### RTL-0069: Implement and connect port s_axil_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_wdata.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_wdata; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_wdata
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_wdata width matches SSOT value DATA_WIDTH
  - s_axil_wdata port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_wdata

### RTL-0070: Implement and connect port s_axil_wstrb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_wstrb.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_wstrb; width=DATA_WIDTH/8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_wstrb
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_wstrb width matches SSOT value DATA_WIDTH/8
  - s_axil_wstrb port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_wstrb

### RTL-0071: Implement and connect port s_axil_wvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_wvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_wvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_wvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_wvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_wvalid width matches SSOT value 1
  - s_axil_wvalid port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_wvalid

### RTL-0072: Implement and connect port s_axil_wready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_wready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_wready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_wready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_wready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_wready width matches SSOT value 1
  - s_axil_wready port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_wready

### RTL-0073: Implement and connect port s_axil_bresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_bresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_bresp.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_bresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_bresp
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_bresp width matches SSOT value 1
  - s_axil_bresp port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_bresp

### RTL-0074: Implement and connect port s_axil_bvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_bvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_bvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_bvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_bvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_bvalid width matches SSOT value 1
  - s_axil_bvalid port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_bvalid

### RTL-0075: Implement and connect port s_axil_bready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_bready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_bready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_bready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_bready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_bready width matches SSOT value 1
  - s_axil_bready port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_bready

### RTL-0076: Implement and connect port s_axil_araddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_araddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_araddr.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_araddr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_araddr
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_araddr width matches SSOT value ADDR_WIDTH
  - s_axil_araddr port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_araddr

### RTL-0077: Implement and connect port s_axil_arvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_arvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_arvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_arvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_arvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_arvalid width matches SSOT value 1
  - s_axil_arvalid port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_arvalid

### RTL-0078: Implement and connect port s_axil_arready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_arready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_arready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_arready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_arready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_arready width matches SSOT value 1
  - s_axil_arready port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_arready

### RTL-0079: Implement and connect port s_axil_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_rdata.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_rdata; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_rdata
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_rdata width matches SSOT value DATA_WIDTH
  - s_axil_rdata port direction remains output
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_rdata

### RTL-0080: Implement and connect port s_axil_rresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_rresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_rresp.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_rresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_rresp
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_rresp width matches SSOT value 1
  - s_axil_rresp port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_rresp

### RTL-0081: Implement and connect port s_axil_rvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_rvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_rvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_rvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_rvalid width matches SSOT value 1
  - s_axil_rvalid port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_rvalid

### RTL-0082: Implement and connect port s_axil_rready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axil_ctrl.ports.s_axil_rready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axil_ctrl.ports.s_axil_rready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=s_axil_rready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axil_ctrl.ports.s_axil_rready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - s_axil_rready width matches SSOT value 1
  - s_axil_rready port direction remains input
- SSOT refs: io_list.interfaces.axil_ctrl.ports.s_axil_rready

### RTL-0083: Implement and connect port m_axi_araddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_araddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_araddr.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_araddr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_araddr
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_araddr width matches SSOT value ADDR_WIDTH
  - m_axi_araddr port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_araddr

### RTL-0084: Implement and connect port m_axi_arvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_arvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_arvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_arvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_arvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_arvalid width matches SSOT value 1
  - m_axi_arvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_arvalid

### RTL-0085: Implement and connect port m_axi_arready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_arready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_arready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_arready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_arready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_arready width matches SSOT value 1
  - m_axi_arready port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_arready

### RTL-0086: Implement and connect port m_axi_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_rdata.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_rdata; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_rdata
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_rdata width matches SSOT value DATA_WIDTH
  - m_axi_rdata port direction remains output
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_rdata

### RTL-0087: Implement and connect port m_axi_rresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_rresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_rresp.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_rresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_rresp
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_rresp width matches SSOT value 1
  - m_axi_rresp port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_rresp

### RTL-0088: Implement and connect port m_axi_rvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_rvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_rvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_rvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_rvalid width matches SSOT value 1
  - m_axi_rvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_rvalid

### RTL-0089: Implement and connect port m_axi_rready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_rready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_rready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_rready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_rready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_rready width matches SSOT value 1
  - m_axi_rready port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_rready

### RTL-0090: Implement and connect port m_axi_awaddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_awaddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_awaddr.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_awaddr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_awaddr
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_awaddr width matches SSOT value ADDR_WIDTH
  - m_axi_awaddr port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_awaddr

### RTL-0091: Implement and connect port m_axi_awvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_awvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_awvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_awvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_awvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_awvalid width matches SSOT value 1
  - m_axi_awvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_awvalid

### RTL-0092: Implement and connect port m_axi_awready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_awready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_awready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_awready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_awready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_awready width matches SSOT value 1
  - m_axi_awready port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_awready

### RTL-0093: Implement and connect port m_axi_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_wdata.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_wdata; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_wdata
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_wdata width matches SSOT value DATA_WIDTH
  - m_axi_wdata port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_wdata

### RTL-0094: Implement and connect port m_axi_wstrb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_wstrb.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_wstrb; width=DATA_WIDTH/8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_wstrb
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_wstrb width matches SSOT value DATA_WIDTH/8
  - m_axi_wstrb port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_wstrb

### RTL-0095: Implement and connect port m_axi_wvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_wvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_wvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_wvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_wvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_wvalid width matches SSOT value 1
  - m_axi_wvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_wvalid

### RTL-0096: Implement and connect port m_axi_wready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_wready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_wready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_wready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_wready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_wready width matches SSOT value 1
  - m_axi_wready port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_wready

### RTL-0097: Implement and connect port m_axi_bresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_bresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_bresp.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_bresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_bresp
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_bresp width matches SSOT value 1
  - m_axi_bresp port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_bresp

### RTL-0098: Implement and connect port m_axi_bvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_bvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_bvalid.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_bvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_bvalid
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_bvalid width matches SSOT value 1
  - m_axi_bvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_bvalid

### RTL-0099: Implement and connect port m_axi_bready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_mem.ports.m_axi_bready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_mem.ports.m_axi_bready.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via io_list.
SSOT item context: name=m_axi_bready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_mem.ports.m_axi_bready
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - m_axi_bready width matches SSOT value 1
  - m_axi_bready port direction remains input
- SSOT refs: io_list.interfaces.axi_mem.ports.m_axi_bready
