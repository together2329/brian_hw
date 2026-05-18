# RTL Authoring Packet: module__dma_scratch_orch_live_20260519b__io_list

- Kind: module
- Owner module: dma_scratch_orch_live_20260519b
- Owner file: rtl/dma_scratch_orch_live_20260519b.sv
- Task count: 25
- Required tasks: 25

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 2/15 section=io_list task_limit=48
- Slice rule: Owner module dma_scratch_orch_live_20260519b is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 23

## Tasks

### RTL-0054: Implement and connect port clk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0055: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0056: Implement and connect port clk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.clock_reset.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.clock_reset.ports.clk.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.clock_reset.ports.clk
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.interfaces.clock_reset.ports.clk

### RTL-0057: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.clock_reset.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.clock_reset.ports.rst_n.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.clock_reset.ports.rst_n
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.interfaces.clock_reset.ports.rst_n

### RTL-0058: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.paddr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=paddr; width=ADDR_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.paddr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - paddr width matches SSOT value ADDR_WIDTH
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.paddr

### RTL-0059: Implement and connect port psel

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.psel.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.psel
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.psel

### RTL-0060: Implement and connect port penable

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.penable.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.penable
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.penable

### RTL-0061: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.pwrite.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.pwrite
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.pwrite

### RTL-0062: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.pwdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=pwdata; width=DATA_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.pwdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - pwdata width matches SSOT value DATA_WIDTH
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.pwdata

### RTL-0063: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.prdata.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=prdata; width=DATA_WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.prdata
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - prdata width matches SSOT value DATA_WIDTH
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.prdata

### RTL-0064: Implement and connect port pready

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.pready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.pready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.pready

### RTL-0065: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.csr_apb_lite.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.csr_apb_lite.ports.pslverr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.csr_apb_lite.ports.pslverr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.csr_apb_lite.ports.pslverr

### RTL-0066: Implement and connect port rd_addr_valid

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_addr.ports.rd_addr_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_addr.ports.rd_addr_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_addr_valid; width=ADDR_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_addr.ports.rd_addr_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_addr_valid width matches SSOT value ADDR_WIDTH
  - rd_addr_valid port direction remains input
- SSOT refs: io_list.interfaces.dma_read_addr.ports.rd_addr_valid

### RTL-0067: Implement and connect port rd_addr_ready

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_addr.ports.rd_addr_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_addr.ports.rd_addr_ready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_addr_ready; width=ADDR_WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_addr.ports.rd_addr_ready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_addr_ready width matches SSOT value ADDR_WIDTH
  - rd_addr_ready port direction remains output
- SSOT refs: io_list.interfaces.dma_read_addr.ports.rd_addr_ready

### RTL-0068: Implement and connect port rd_addr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_addr.ports.rd_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_addr.ports.rd_addr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_addr; width=ADDR_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_addr.ports.rd_addr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_addr width matches SSOT value ADDR_WIDTH
  - rd_addr port direction remains input
- SSOT refs: io_list.interfaces.dma_read_addr.ports.rd_addr

### RTL-0069: Implement and connect port rd_data_valid

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_data.ports.rd_data_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_data.ports.rd_data_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_data_valid; width=DATA_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_data.ports.rd_data_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_data_valid width matches SSOT value DATA_WIDTH
  - rd_data_valid port direction remains input
- SSOT refs: io_list.interfaces.dma_read_data.ports.rd_data_valid

### RTL-0070: Implement and connect port rd_data_ready

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_data.ports.rd_data_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_data.ports.rd_data_ready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_data_ready; width=DATA_WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_data.ports.rd_data_ready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_data_ready width matches SSOT value DATA_WIDTH
  - rd_data_ready port direction remains output
- SSOT refs: io_list.interfaces.dma_read_data.ports.rd_data_ready

### RTL-0071: Implement and connect port rd_data

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_data.ports.rd_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_data.ports.rd_data.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_data; width=DATA_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_data.ports.rd_data
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_data width matches SSOT value DATA_WIDTH
  - rd_data port direction remains input
- SSOT refs: io_list.interfaces.dma_read_data.ports.rd_data

### RTL-0072: Implement and connect port rd_resp

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_read_data.ports.rd_resp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_read_data.ports.rd_resp.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=rd_resp; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_read_data.ports.rd_resp
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - rd_resp width matches SSOT value 1
  - rd_resp port direction remains input
- SSOT refs: io_list.interfaces.dma_read_data.ports.rd_resp

### RTL-0073: Implement and connect port wr_data_valid

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_write_data.ports.wr_data_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_write_data.ports.wr_data_valid.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=wr_data_valid; width=DATA_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_write_data.ports.wr_data_valid
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - wr_data_valid width matches SSOT value DATA_WIDTH
  - wr_data_valid port direction remains input
- SSOT refs: io_list.interfaces.dma_write_data.ports.wr_data_valid

### RTL-0074: Implement and connect port wr_data_ready

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_write_data.ports.wr_data_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_write_data.ports.wr_data_ready.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=wr_data_ready; width=DATA_WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_write_data.ports.wr_data_ready
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - wr_data_ready width matches SSOT value DATA_WIDTH
  - wr_data_ready port direction remains output
- SSOT refs: io_list.interfaces.dma_write_data.ports.wr_data_ready

### RTL-0075: Implement and connect port wr_addr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_write_data.ports.wr_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_write_data.ports.wr_addr.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=wr_addr; width=ADDR_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_write_data.ports.wr_addr
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - wr_addr width matches SSOT value ADDR_WIDTH
  - wr_addr port direction remains input
- SSOT refs: io_list.interfaces.dma_write_data.ports.wr_addr

### RTL-0076: Implement and connect port wr_data

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_write_data.ports.wr_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_write_data.ports.wr_data.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=wr_data; width=DATA_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_write_data.ports.wr_data
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - wr_data width matches SSOT value DATA_WIDTH
  - wr_data port direction remains input
- SSOT refs: io_list.interfaces.dma_write_data.ports.wr_data

### RTL-0077: Implement and connect port wr_strb

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_write_data.ports.wr_strb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_write_data.ports.wr_strb.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=wr_strb; width=DATA_WIDTH/8; direction=input.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_write_data.ports.wr_strb
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - wr_strb width matches SSOT value DATA_WIDTH/8
  - wr_strb port direction remains input
- SSOT refs: io_list.interfaces.dma_write_data.ports.wr_strb

### RTL-0078: Implement and connect port irq

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.status_irq.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status_irq.ports.irq.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via io_list.
SSOT item context: name=irq; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/dma_scratch_orch_live_20260519b.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status_irq.ports.irq
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - irq width matches SSOT value 1
  - irq port direction remains output
- SSOT refs: io_list.interfaces.status_irq.ports.irq
