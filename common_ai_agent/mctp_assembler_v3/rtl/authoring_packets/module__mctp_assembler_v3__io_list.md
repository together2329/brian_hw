# RTL Authoring Packet: module__mctp_assembler_v3__io_list

- Kind: module
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 22
- Required tasks: 22

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 22
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, function_model, function_model.transactions, integration, integration.connections, io_list, io_list.interfaces, top_module
- Module slice: 2/9 section=io_list task_limit=48
- Slice rule: Owner module mctp_assembler_v3 is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])
- SSOT top IO contracts: 51

## Tasks

### RTL-0081: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=paddr; width=16; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - paddr width matches SSOT value 16
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0082: Implement and connect port psel

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0083: Implement and connect port penable

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0084: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0085: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0086: Implement and connect port pstrb

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pstrb.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=pstrb; width=4; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pstrb
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - pstrb width matches SSOT value 4
  - pstrb port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pstrb

### RTL-0087: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0088: Implement and connect port pready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pready.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pready
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pready

### RTL-0089: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pslverr.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pslverr
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pslverr

### RTL-0090: Implement and connect port sram_wr_valid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write.ports.sram_wr_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write.ports.sram_wr_valid.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_wr_valid; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write.ports.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_wr_valid width matches SSOT value 1
  - sram_wr_valid port direction remains output
- SSOT refs: io_list.interfaces.sram_write.ports.sram_wr_valid

### RTL-0091: Implement and connect port sram_wr_ready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write.ports.sram_wr_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write.ports.sram_wr_ready.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_wr_ready; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write.ports.sram_wr_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_wr_ready width matches SSOT value 1
  - sram_wr_ready port direction remains input
- SSOT refs: io_list.interfaces.sram_write.ports.sram_wr_ready

### RTL-0092: Implement and connect port sram_wr_addr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write.ports.sram_wr_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write.ports.sram_wr_addr.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_wr_addr; width=16; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write.ports.sram_wr_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_wr_addr width matches SSOT value 16
  - sram_wr_addr port direction remains output
- SSOT refs: io_list.interfaces.sram_write.ports.sram_wr_addr

### RTL-0093: Implement and connect port sram_wr_data

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write.ports.sram_wr_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write.ports.sram_wr_data.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_wr_data; width=256; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write.ports.sram_wr_data
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_wr_data width matches SSOT value 256
  - sram_wr_data port direction remains output
- SSOT refs: io_list.interfaces.sram_write.ports.sram_wr_data

### RTL-0094: Implement and connect port sram_wr_strb

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write.ports.sram_wr_strb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write.ports.sram_wr_strb.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_wr_strb; width=32; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write.ports.sram_wr_strb
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_wr_strb width matches SSOT value 32
  - sram_wr_strb port direction remains output
- SSOT refs: io_list.interfaces.sram_write.ports.sram_wr_strb

### RTL-0095: Implement and connect port sram_rd_req_valid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_req_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_req_valid.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_req_valid; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_req_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_req_valid width matches SSOT value 1
  - sram_rd_req_valid port direction remains output
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_req_valid

### RTL-0096: Implement and connect port sram_rd_req_ready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_req_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_req_ready.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_req_ready; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_req_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_req_ready width matches SSOT value 1
  - sram_rd_req_ready port direction remains input
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_req_ready

### RTL-0097: Implement and connect port sram_rd_req_addr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_req_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_req_addr.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_req_addr; width=16; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_req_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_req_addr width matches SSOT value 16
  - sram_rd_req_addr port direction remains output
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_req_addr

### RTL-0098: Implement and connect port sram_rd_rsp_valid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_valid.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_rsp_valid; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_rsp_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_rsp_valid width matches SSOT value 1
  - sram_rd_rsp_valid port direction remains input
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_rsp_valid

### RTL-0099: Implement and connect port sram_rd_rsp_ready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_ready.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_rsp_ready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_rsp_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_rsp_ready width matches SSOT value 1
  - sram_rd_rsp_ready port direction remains output
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_rsp_ready

### RTL-0100: Implement and connect port sram_rd_rsp_data

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_data.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_rsp_data; width=256; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_rsp_data
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_rsp_data width matches SSOT value 256
  - sram_rd_rsp_data port direction remains input
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_rsp_data

### RTL-0101: Implement and connect port sram_rd_rsp_error

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read.ports.sram_rd_rsp_error.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=sram_rd_rsp_error; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read.ports.sram_rd_rsp_error
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - sram_rd_rsp_error width matches SSOT value 1
  - sram_rd_rsp_error port direction remains input
- SSOT refs: io_list.interfaces.sram_read.ports.sram_rd_rsp_error

### RTL-0102: Implement and connect port irq

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.irq.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via io_list.interfaces.
SSOT item context: name=irq; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.irq
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - irq width matches SSOT value 1
  - irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.irq
