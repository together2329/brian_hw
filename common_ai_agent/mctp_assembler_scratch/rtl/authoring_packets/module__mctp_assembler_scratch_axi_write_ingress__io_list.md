# RTL Authoring Packet: module__mctp_assembler_scratch_axi_write_ingress__io_list

- Kind: module
- Owner module: mctp_assembler_scratch_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_axi_write_ingress.sv
- Task count: 23
- Required tasks: 23

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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 1/6 section=io_list task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_axi_write_ingress is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0049: Implement and connect port axi_aclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.axi_aclk.ports.axi_aclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.axi_aclk.ports.axi_aclk.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=axi_aclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.axi_aclk.ports.axi_aclk
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - axi_aclk width matches SSOT value 1
  - axi_aclk port direction remains input
- SSOT refs: io_list.clock_domains.axi_aclk.ports.axi_aclk

### RTL-0050: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0051: Implement and connect port axi_aresetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.axi_aresetn.ports.axi_aresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.axi_aresetn.ports.axi_aresetn.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=axi_aresetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.axi_aresetn.ports.axi_aresetn
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - axi_aresetn width matches SSOT value 1
  - axi_aresetn port direction remains input
- SSOT refs: io_list.resets.axi_aresetn.ports.axi_aresetn

### RTL-0052: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.presetn
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.presetn

### RTL-0053: Implement and connect port m_axi_awaddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awaddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awaddr.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awaddr; width=AXI_ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awaddr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awaddr width matches SSOT value AXI_ADDR_WIDTH
  - m_axi_awaddr port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awaddr

### RTL-0054: Implement and connect port m_axi_awlen

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awlen
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awlen.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awlen; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awlen
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awlen width matches SSOT value 8
  - m_axi_awlen port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awlen

### RTL-0055: Implement and connect port m_axi_awsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awsize.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awsize; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awsize
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awsize width matches SSOT value 3
  - m_axi_awsize port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awsize

### RTL-0056: Implement and connect port m_axi_awburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awburst.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awburst; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awburst
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awburst width matches SSOT value 2
  - m_axi_awburst port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awburst

### RTL-0057: Implement and connect port m_axi_awvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awvalid.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awvalid width matches SSOT value 1
  - m_axi_awvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awvalid

### RTL-0058: Implement and connect port m_axi_awready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_awready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_awready.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_awready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_awready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_awready width matches SSOT value 1
  - m_axi_awready port direction remains output
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_awready

### RTL-0059: Implement and connect port m_axi_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_wdata.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_wdata; width=AXI_DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_wdata
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_wdata width matches SSOT value AXI_DATA_WIDTH
  - m_axi_wdata port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_wdata

### RTL-0060: Implement and connect port m_axi_wstrb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_wstrb.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_wstrb; width=AXI_STRB_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_wstrb
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_wstrb width matches SSOT value AXI_STRB_WIDTH
  - m_axi_wstrb port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_wstrb

### RTL-0061: Implement and connect port m_axi_wlast

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_wlast
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_wlast.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_wlast; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_wlast
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_wlast width matches SSOT value 1
  - m_axi_wlast port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_wlast

### RTL-0062: Implement and connect port m_axi_wvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_wvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_wvalid.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_wvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_wvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_wvalid width matches SSOT value 1
  - m_axi_wvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_wvalid

### RTL-0063: Implement and connect port m_axi_wready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_wready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_wready.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_wready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_wready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_wready width matches SSOT value 1
  - m_axi_wready port direction remains output
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_wready

### RTL-0064: Implement and connect port m_axi_bresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_bresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_bresp.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_bresp; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_bresp
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_bresp width matches SSOT value 2
  - m_axi_bresp port direction remains output
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_bresp

### RTL-0065: Implement and connect port m_axi_bvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_bvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_bvalid.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_bvalid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_bvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_bvalid width matches SSOT value 1
  - m_axi_bvalid port direction remains output
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_bvalid

### RTL-0066: Implement and connect port m_axi_bready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_write_slave.ports.m_axi_bready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_write_slave.ports.m_axi_bready.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.interfaces.axi_write_slave.
SSOT item context: name=m_axi_bready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_write_slave.ports.m_axi_bready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - m_axi_bready width matches SSOT value 1
  - m_axi_bready port direction remains input
- SSOT refs: io_list.interfaces.axi_write_slave.ports.m_axi_bready

### RTL-0099: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_and_debug.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_and_debug.ports.irq.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=irq; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_and_debug.ports.irq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - irq width matches SSOT value 1
  - irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt_and_debug.ports.irq

### RTL-0100: Implement and connect port debug_context_id

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_and_debug.ports.debug_context_id
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_and_debug.ports.debug_context_id.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=debug_context_id; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_and_debug.ports.debug_context_id
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - debug_context_id width matches SSOT value 4
  - debug_context_id port direction remains output
- SSOT refs: io_list.interfaces.interrupt_and_debug.ports.debug_context_id

### RTL-0101: Implement and connect port debug_context_key

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_and_debug.ports.debug_context_key
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_and_debug.ports.debug_context_key.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=debug_context_key; width=18; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_and_debug.ports.debug_context_key
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - debug_context_key width matches SSOT value 18
  - debug_context_key port direction remains output
- SSOT refs: io_list.interfaces.interrupt_and_debug.ports.debug_context_key

### RTL-0102: Implement and connect port debug_drop_pulse

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_and_debug.ports.debug_drop_pulse
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_and_debug.ports.debug_drop_pulse.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=debug_drop_pulse; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_and_debug.ports.debug_drop_pulse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - debug_drop_pulse width matches SSOT value 1
  - debug_drop_pulse port direction remains output
- SSOT refs: io_list.interfaces.interrupt_and_debug.ports.debug_drop_pulse

### RTL-0103: Implement and connect port debug_vdm_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt_and_debug.ports.debug_vdm_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt_and_debug.ports.debug_vdm_valid.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via io_list.
SSOT item context: name=debug_vdm_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt_and_debug.ports.debug_vdm_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - debug_vdm_valid width matches SSOT value 1
  - debug_vdm_valid port direction remains output
- SSOT refs: io_list.interfaces.interrupt_and_debug.ports.debug_vdm_valid
