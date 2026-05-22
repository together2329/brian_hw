# RTL Authoring Packet: module__atcdmac100_core__io_list

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 29
- Required tasks: 29

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
- Owner refs: cycle_model, dataflow, decomposition, decomposition.owners, decomposition.source_refs, error_handling, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM_AHB_READ, function_model.transactions.FM_AHB_WRITE, function_model.transactions.FM_ARBITRATE, function_model.transactions.FM_COMPLETE, function_model.transactions.FM_ERROR_ABORT, function_model.transactions.FM_HANDSHAKE_ACK
- Module slice: 1/17 section=io_list task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0028: Implement and connect port hclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.hclk_domain.ports.hclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.hclk_domain.ports.hclk.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.hclk_domain.ports.hclk
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hclk width matches SSOT value 1
  - hclk port direction remains input
- SSOT refs: io_list.clock_domains.hclk_domain.ports.hclk

### RTL-0029: Implement and connect port hresetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.hresetn.ports.hresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.hresetn.ports.hresetn.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hresetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.hresetn.ports.hresetn
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresetn width matches SSOT value 1
  - hresetn port direction remains input
- SSOT refs: io_list.resets.hresetn.ports.hresetn

### RTL-0030: Implement and connect port dma_int

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_handshake.ports.dma_int
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_handshake.ports.dma_int.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=dma_int; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_handshake.ports.dma_int
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int width matches SSOT value 1
  - dma_int port direction remains output
- SSOT refs: io_list.interfaces.dma_handshake.ports.dma_int

### RTL-0031: Implement and connect port dma_req

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_handshake.ports.dma_req
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_handshake.ports.dma_req.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=dma_req; width=REQ_ACK_NUM; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_handshake.ports.dma_req
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_req width matches SSOT value REQ_ACK_NUM
  - dma_req port direction remains input
- SSOT refs: io_list.interfaces.dma_handshake.ports.dma_req

### RTL-0032: Implement and connect port dma_ack

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.dma_handshake.ports.dma_ack
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_handshake.ports.dma_ack.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=dma_ack; width=REQ_ACK_NUM; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_handshake.ports.dma_ack
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_ack width matches SSOT value REQ_ACK_NUM
  - dma_ack port direction remains output
- SSOT refs: io_list.interfaces.dma_handshake.ports.dma_ack

### RTL-0033: Implement and connect port haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.haddr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=haddr; width=ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.haddr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - haddr width matches SSOT value ADDR_WIDTH
  - haddr port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.haddr

### RTL-0034: Implement and connect port htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.htrans.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=htrans; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.htrans
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans width matches SSOT value 2
  - htrans port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.htrans

### RTL-0035: Implement and connect port hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hwrite.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hwrite; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hwrite
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwrite width matches SSOT value 1
  - hwrite port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hwrite

### RTL-0036: Implement and connect port hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hsize.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hsize; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hsize
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hsize width matches SSOT value 3
  - hsize port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hsize

### RTL-0037: Implement and connect port hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hburst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hburst; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hburst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hburst width matches SSOT value 3
  - hburst port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hburst

### RTL-0038: Implement and connect port hwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hwdata.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hwdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hwdata
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwdata width matches SSOT value 32
  - hwdata port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hwdata

### RTL-0039: Implement and connect port hsel

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hsel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hsel.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hsel; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hsel
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hsel width matches SSOT value 1
  - hsel port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hsel

### RTL-0040: Implement and connect port hreadyin

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hreadyin
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hreadyin.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hreadyin; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hreadyin
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hreadyin width matches SSOT value 1
  - hreadyin port direction remains input
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hreadyin

### RTL-0041: Implement and connect port hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hrdata.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hrdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hrdata
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hrdata width matches SSOT value 32
  - hrdata port direction remains output
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hrdata

### RTL-0042: Implement and connect port hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hresp.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hresp; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hresp
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresp width matches SSOT value 2
  - hresp port direction remains output
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hresp

### RTL-0043: Implement and connect port hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_slave_regs.ports.hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_slave_regs.ports.hready.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_slave_regs.ports.hready
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hready width matches SSOT value 1
  - hready port direction remains output
- SSOT refs: io_list.interfaces.ahb_slave_regs.ports.hready

### RTL-0044: Implement and connect port haddr_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.haddr_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.haddr_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=haddr_mst; width=ADDR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.haddr_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - haddr_mst width matches SSOT value ADDR_WIDTH
  - haddr_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.haddr_mst

### RTL-0045: Implement and connect port htrans_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.htrans_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.htrans_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=htrans_mst; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.htrans_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_mst width matches SSOT value 2
  - htrans_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.htrans_mst

### RTL-0046: Implement and connect port hwrite_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hwrite_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hwrite_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hwrite_mst; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hwrite_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwrite_mst width matches SSOT value 1
  - hwrite_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hwrite_mst

### RTL-0047: Implement and connect port hsize_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hsize_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hsize_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hsize_mst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hsize_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hsize_mst width matches SSOT value 3
  - hsize_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hsize_mst

### RTL-0048: Implement and connect port hprot_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hprot_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hprot_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hprot_mst; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hprot_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hprot_mst width matches SSOT value 4
  - hprot_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hprot_mst

### RTL-0049: Implement and connect port hlock_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hlock_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hlock_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hlock_mst; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hlock_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hlock_mst width matches SSOT value 1
  - hlock_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hlock_mst

### RTL-0050: Implement and connect port hburst_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hburst_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hburst_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hburst_mst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hburst_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hburst_mst width matches SSOT value 3
  - hburst_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hburst_mst

### RTL-0051: Implement and connect port hwdata_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hwdata_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hwdata_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hwdata_mst; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hwdata_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hwdata_mst width matches SSOT value 32
  - hwdata_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hwdata_mst

### RTL-0052: Implement and connect port hrdata_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hrdata_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hrdata_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hrdata_mst; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hrdata_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hrdata_mst width matches SSOT value 32
  - hrdata_mst port direction remains input
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hrdata_mst

### RTL-0053: Implement and connect port hresp_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hresp_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hresp_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hresp_mst; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hresp_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresp_mst width matches SSOT value 2
  - hresp_mst port direction remains input
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hresp_mst

### RTL-0054: Implement and connect port hready_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hready_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hready_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hready_mst; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hready_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hready_mst width matches SSOT value 1
  - hready_mst port direction remains input
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hready_mst

### RTL-0055: Implement and connect port hbusreq_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hbusreq_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hbusreq_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hbusreq_mst; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hbusreq_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hbusreq_mst width matches SSOT value 1
  - hbusreq_mst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hbusreq_mst

### RTL-0056: Implement and connect port hgrant_mst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master_dma.ports.hgrant_mst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master_dma.ports.hgrant_mst.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via io_list.
SSOT item context: name=hgrant_mst; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master_dma.ports.hgrant_mst
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hgrant_mst width matches SSOT value 1
  - hgrant_mst port direction remains input
- SSOT refs: io_list.interfaces.ahb_master_dma.ports.hgrant_mst
