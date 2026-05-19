# RTL Authoring Packet: module__dma_scratch_orch_live_20260519b__io_list

- Kind: module
- Owner module: dma_scratch_orch_live_20260519b
- Owner file: rtl/dma_scratch_orch_live_20260519b.sv
- Task count: 23
- Required tasks: 23

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 2/15 section=io_list task_limit=48
- Slice rule: Owner module dma_scratch_orch_live_20260519b is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 21

## Tasks

### RTL-0055: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0056: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0057: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.clock_reset.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.clock_reset.ports.clk.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.clock_reset.ports.clk
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.interfaces.clock_reset.ports.clk

### RTL-0058: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.clock_reset.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.clock_reset.ports.rst_n.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.clock_reset.ports.rst_n
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.interfaces.clock_reset.ports.rst_n

### RTL-0059: Implement and connect port csr_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_valid width matches SSOT value 1
  - csr_valid port direction remains input
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_valid

### RTL-0060: Implement and connect port csr_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_ready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_ready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_ready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_ready width matches SSOT value 1
  - csr_ready port direction remains output
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_ready

### RTL-0061: Implement and connect port csr_write

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_write
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_write.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_write; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_write
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_write width matches SSOT value 1
  - csr_write port direction remains input
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_write

### RTL-0062: Implement and connect port csr_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_addr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_addr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_addr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_addr width matches SSOT value ADDR_WIDTH
  - csr_addr port direction remains input
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_addr

### RTL-0063: Implement and connect port csr_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_wdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_wdata; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_wdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_wdata width matches SSOT value DATA_WIDTH
  - csr_wdata port direction remains input
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_wdata

### RTL-0064: Implement and connect port csr_wstrb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_wstrb.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_wstrb; width=DATA_WIDTH/8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_wstrb
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_wstrb width matches SSOT value DATA_WIDTH/8
  - csr_wstrb port direction remains input
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_wstrb

### RTL-0065: Implement and connect port csr_rvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_rvalid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_rvalid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_rvalid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_rvalid width matches SSOT value 1
  - csr_rvalid port direction remains output
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_rvalid

### RTL-0066: Implement and connect port csr_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_rdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_rdata; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_rdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_rdata width matches SSOT value DATA_WIDTH
  - csr_rdata port direction remains output
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_rdata

### RTL-0067: Implement and connect port csr_error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.csr_slave.ports.csr_error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_slave.ports.csr_error.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=csr_error; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_slave.ports.csr_error
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - csr_error width matches SSOT value 1
  - csr_error port direction remains output
- SSOT refs: io_list.interfaces.csr_slave.ports.csr_error

### RTL-0068: Implement and connect port mem_req_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_valid width matches SSOT value 1
  - mem_req_valid port direction remains output
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_valid

### RTL-0069: Implement and connect port mem_req_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_ready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_ready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_ready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_ready width matches SSOT value 1
  - mem_req_ready port direction remains input
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_ready

### RTL-0070: Implement and connect port mem_req_write

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_write
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_write.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_write; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_write
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_write width matches SSOT value 1
  - mem_req_write port direction remains output
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_write

### RTL-0071: Implement and connect port mem_req_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_addr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_addr; width=ADDR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_addr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_addr width matches SSOT value ADDR_WIDTH
  - mem_req_addr port direction remains output
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_addr

### RTL-0072: Implement and connect port mem_req_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_wdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_wdata; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_wdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_wdata width matches SSOT value DATA_WIDTH
  - mem_req_wdata port direction remains output
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_wdata

### RTL-0073: Implement and connect port mem_req_wstrb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_req_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_req_wstrb.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_req_wstrb; width=DATA_WIDTH/8; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_req_wstrb
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_req_wstrb width matches SSOT value DATA_WIDTH/8
  - mem_req_wstrb port direction remains output
- SSOT refs: io_list.interfaces.mem_master.ports.mem_req_wstrb

### RTL-0074: Implement and connect port mem_rsp_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_rsp_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_rsp_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_rsp_valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_rsp_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_rsp_valid width matches SSOT value 1
  - mem_rsp_valid port direction remains input
- SSOT refs: io_list.interfaces.mem_master.ports.mem_rsp_valid

### RTL-0075: Implement and connect port mem_rsp_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_rsp_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_rsp_rdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_rsp_rdata; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_rsp_rdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_rsp_rdata width matches SSOT value DATA_WIDTH
  - mem_rsp_rdata port direction remains input
- SSOT refs: io_list.interfaces.mem_master.ports.mem_rsp_rdata

### RTL-0076: Implement and connect port mem_rsp_error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.mem_master.ports.mem_rsp_error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.mem_master.ports.mem_rsp_error.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=mem_rsp_error; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.mem_master.ports.mem_rsp_error
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - mem_rsp_error width matches SSOT value 1
  - mem_rsp_error port direction remains input
- SSOT refs: io_list.interfaces.mem_master.ports.mem_rsp_error

### RTL-0077: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.irq.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=irq; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.irq
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - irq width matches SSOT value 1
  - irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.irq
