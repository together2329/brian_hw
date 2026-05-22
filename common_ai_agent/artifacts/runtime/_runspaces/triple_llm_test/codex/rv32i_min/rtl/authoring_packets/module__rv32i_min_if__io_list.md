# RTL Authoring Packet: module__rv32i_min_if__io_list

- Kind: module
- Owner module: rv32i_min_if
- Owner file: rtl/rv32i_min_if.sv
- Task count: 24
- Required tasks: 24

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, function_model, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, io_list, io_list.interfaces.instr_bus
- Module slice: 1/6 section=io_list task_limit=48
- Slice rule: Owner module rv32i_min_if is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])

## Tasks

### RTL-0027: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0028: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0029: Implement and connect port i_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.i_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.i_addr.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=i_addr; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.i_addr
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - i_addr width matches SSOT value 32
  - i_addr port direction remains output
- SSOT refs: io_list.interfaces.instr_bus.ports.i_addr

### RTL-0030: Implement and connect port i_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.i_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.i_rdata.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=i_rdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.i_rdata
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - i_rdata width matches SSOT value 32
  - i_rdata port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.i_rdata

### RTL-0031: Implement and connect port i_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.i_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.i_valid.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=i_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.i_valid
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - i_valid width matches SSOT value 1
  - i_valid port direction remains output
- SSOT refs: io_list.interfaces.instr_bus.ports.i_valid

### RTL-0032: Implement and connect port alu_result

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.alu_result
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.alu_result.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=alu_result; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.alu_result
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - alu_result width matches SSOT value 1
  - alu_result port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.alu_result

### RTL-0033: Implement and connect port branch_imm

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.branch_imm
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.branch_imm.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=branch_imm; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.branch_imm
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - branch_imm width matches SSOT value 1
  - branch_imm port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.branch_imm

### RTL-0034: Implement and connect port branch_taken

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.branch_taken
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.branch_taken.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=branch_taken; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.branch_taken
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - branch_taken width matches SSOT value 1
  - branch_taken port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.branch_taken

### RTL-0035: Implement and connect port illegal_shamt

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.illegal_shamt
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.illegal_shamt.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=illegal_shamt; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.illegal_shamt
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - illegal_shamt width matches SSOT value 1
  - illegal_shamt port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.illegal_shamt

### RTL-0036: Implement and connect port imm

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.imm
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.imm.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=imm; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.imm
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - imm width matches SSOT value 1
  - imm port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.imm

### RTL-0037: Implement and connect port is_ebreak

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.is_ebreak
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.is_ebreak.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=is_ebreak; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.is_ebreak
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - is_ebreak width matches SSOT value 1
  - is_ebreak port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.is_ebreak

### RTL-0038: Implement and connect port is_ecall

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.is_ecall
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.is_ecall.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=is_ecall; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.is_ecall
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - is_ecall width matches SSOT value 1
  - is_ecall port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.is_ecall

### RTL-0039: Implement and connect port is_jalr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.is_jalr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.is_jalr.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=is_jalr; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.is_jalr
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - is_jalr width matches SSOT value 1
  - is_jalr port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.is_jalr

### RTL-0040: Implement and connect port is_store

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.is_store
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.is_store.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=is_store; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.is_store
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - is_store width matches SSOT value 1
  - is_store port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.is_store

### RTL-0041: Implement and connect port load_data_ext

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.load_data_ext
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.load_data_ext.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=load_data_ext; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.load_data_ext
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - load_data_ext width matches SSOT value 1
  - load_data_ext port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.load_data_ext

### RTL-0042: Implement and connect port misaligned_access

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.misaligned_access
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.misaligned_access.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=misaligned_access; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.misaligned_access
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - misaligned_access width matches SSOT value 1
  - misaligned_access port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.misaligned_access

### RTL-0043: Implement and connect port rs1

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.instr_bus.ports.rs1
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.instr_bus.ports.rs1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.interfaces.instr_bus.
SSOT item context: name=rs1; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.instr_bus.ports.rs1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - rs1 width matches SSOT value 1
  - rs1 port direction remains input
- SSOT refs: io_list.interfaces.instr_bus.ports.rs1

### RTL-0044: Implement and connect port d_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_addr.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_addr; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_addr
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_addr width matches SSOT value 32
  - d_addr port direction remains output
- SSOT refs: io_list.interfaces.data_bus.ports.d_addr

### RTL-0045: Implement and connect port d_wdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_wdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_wdata.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_wdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_wdata
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_wdata width matches SSOT value 32
  - d_wdata port direction remains output
- SSOT refs: io_list.interfaces.data_bus.ports.d_wdata

### RTL-0046: Implement and connect port d_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_rdata.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_rdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_rdata
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_rdata width matches SSOT value 32
  - d_rdata port direction remains input
- SSOT refs: io_list.interfaces.data_bus.ports.d_rdata

### RTL-0047: Implement and connect port d_we

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_we
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_we.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_we; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_we
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_we width matches SSOT value 1
  - d_we port direction remains output
- SSOT refs: io_list.interfaces.data_bus.ports.d_we

### RTL-0048: Implement and connect port d_be

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_be
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_be.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_be; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_be
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_be width matches SSOT value 4
  - d_be port direction remains output
- SSOT refs: io_list.interfaces.data_bus.ports.d_be

### RTL-0049: Implement and connect port d_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_bus.ports.d_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_bus.ports.d_valid.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=d_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_bus.ports.d_valid
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - d_valid width matches SSOT value 1
  - d_valid port direction remains output
- SSOT refs: io_list.interfaces.data_bus.ports.d_valid

### RTL-0050: Implement and connect port excpt_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.exception.ports.excpt_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.exception.ports.excpt_o.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via io_list.
SSOT item context: name=excpt_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.exception.ports.excpt_o
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - excpt_o width matches SSOT value 1
  - excpt_o port direction remains output
- SSOT refs: io_list.interfaces.exception.ports.excpt_o
