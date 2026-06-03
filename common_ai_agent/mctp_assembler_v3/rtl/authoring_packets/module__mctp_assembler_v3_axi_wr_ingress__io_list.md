# RTL Authoring Packet: module__mctp_assembler_v3_axi_wr_ingress__io_list

- Kind: module
- Owner module: mctp_assembler_v3_axi_wr_ingress
- Owner file: rtl/mctp_assembler_v3_axi_wr_ingress.sv
- Task count: 18
- Required tasks: 18

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
- LLM-actionable open tasks: 18
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, function_model, function_model.transactions.FM_INGEST_TLP, io_list, io_list.interfaces.axi_wr_slave, test_requirements
- Module slice: 1/5 section=io_list task_limit=48
- Slice rule: Owner module mctp_assembler_v3_axi_wr_ingress is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])

## Tasks

### RTL-0052: Implement and connect port axi_aclk

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.clock_domains.axi_aclk.ports.axi_aclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.axi_aclk.ports.axi_aclk.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.
SSOT item context: name=axi_aclk; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.axi_aclk.ports.axi_aclk
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - axi_aclk width matches SSOT value 1
  - axi_aclk port direction remains input
- SSOT refs: io_list.clock_domains.axi_aclk.ports.axi_aclk

### RTL-0053: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0054: Implement and connect port axi_aresetn

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.resets.axi_aresetn.ports.axi_aresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.axi_aresetn.ports.axi_aresetn.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.
SSOT item context: name=axi_aresetn; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.axi_aresetn.ports.axi_aresetn
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - axi_aresetn width matches SSOT value 1
  - axi_aresetn port direction remains input
- SSOT refs: io_list.resets.axi_aresetn.ports.axi_aresetn

### RTL-0055: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.presetn
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.presetn

### RTL-0056: Implement and connect port s_axi_awaddr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awaddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awaddr.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awaddr; width=16; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awaddr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awaddr width matches SSOT value 16
  - s_axi_awaddr port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awaddr

### RTL-0057: Implement and connect port s_axi_awlen

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awlen
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awlen.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awlen; width=8; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awlen
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awlen width matches SSOT value 8
  - s_axi_awlen port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awlen

### RTL-0058: Implement and connect port s_axi_awsize

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awsize.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awsize; width=3; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awsize
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awsize width matches SSOT value 3
  - s_axi_awsize port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awsize

### RTL-0059: Implement and connect port s_axi_awburst

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awburst.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awburst; width=2; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awburst
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awburst width matches SSOT value 2
  - s_axi_awburst port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awburst

### RTL-0060: Implement and connect port s_axi_awvalid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awvalid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awvalid; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awvalid width matches SSOT value 1
  - s_axi_awvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awvalid

### RTL-0061: Implement and connect port s_axi_awready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_awready.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_awready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_awready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_awready width matches SSOT value 1
  - s_axi_awready port direction remains output
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_awready

### RTL-0062: Implement and connect port s_axi_wdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wdata.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_wdata; width=256; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_wdata
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_wdata width matches SSOT value 256
  - s_axi_wdata port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_wdata

### RTL-0063: Implement and connect port s_axi_wstrb

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wstrb.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_wstrb; width=32; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_wstrb
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_wstrb width matches SSOT value 32
  - s_axi_wstrb port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_wstrb

### RTL-0064: Implement and connect port s_axi_wlast

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wlast
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wlast.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_wlast; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_wlast
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_wlast width matches SSOT value 1
  - s_axi_wlast port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_wlast

### RTL-0065: Implement and connect port s_axi_wvalid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wvalid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_wvalid; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_wvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_wvalid width matches SSOT value 1
  - s_axi_wvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_wvalid

### RTL-0066: Implement and connect port s_axi_wready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_wready.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_wready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_wready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_wready width matches SSOT value 1
  - s_axi_wready port direction remains output
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_wready

### RTL-0067: Implement and connect port s_axi_bresp

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bresp.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_bresp; width=2; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_bresp
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_bresp width matches SSOT value 2
  - s_axi_bresp port direction remains output
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_bresp

### RTL-0068: Implement and connect port s_axi_bvalid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bvalid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_bvalid; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_bvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_bvalid width matches SSOT value 1
  - s_axi_bvalid port direction remains output
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_bvalid

### RTL-0069: Implement and connect port s_axi_bready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_wr_slave.ports.s_axi_bready.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via io_list.interfaces.axi_wr_slave.
SSOT item context: name=s_axi_bready; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_wr_slave.ports.s_axi_bready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - s_axi_bready width matches SSOT value 1
  - s_axi_bready port direction remains input
- SSOT refs: io_list.interfaces.axi_wr_slave.ports.s_axi_bready
