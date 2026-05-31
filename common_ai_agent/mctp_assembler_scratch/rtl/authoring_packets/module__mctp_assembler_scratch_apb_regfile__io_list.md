# RTL Authoring Packet: module__mctp_assembler_scratch_apb_regfile__io_list

- Kind: module
- Owner module: mctp_assembler_scratch_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_apb_regfile.sv
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 1/9 section=io_list task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0078: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=paddr; width=16; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - paddr width matches SSOT value 16
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0079: Implement and connect port psel

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0080: Implement and connect port penable

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0081: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0082: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0083: Implement and connect port pstrb

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pstrb.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pstrb; width=4; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pstrb
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - pstrb width matches SSOT value 4
  - pstrb port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pstrb

### RTL-0084: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0085: Implement and connect port pready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pready.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pready

### RTL-0086: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pslverr.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pslverr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pslverr
