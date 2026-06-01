# RTL Authoring Packet: module__mctp_assembler_scratch_sram_arbiter

- Kind: module
- Owner module: mctp_assembler_scratch_sram_arbiter
- Owner file: rtl/mctp_assembler_scratch_sram_arbiter.sv
- Task count: 17
- Required tasks: 17

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.arbitration, io_list, io_list.interfaces.sram_read_port, io_list.interfaces.sram_write_port, memory

## Tasks

### RTL-0300: Implement handshake rule: sram_ready_valid

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sram_ready_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sram_ready_valid.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via cycle_model.
SSOT item context: name=sram_ready_valid; signal=sram_wr_valid/sram_wr_ready/sram_rd_req_valid/sram_rd_req_ready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sram_ready_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_ready_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sram_ready_valid

### RTL-0310: Implement ordering rule: descriptor_after_sram_flush

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.descriptor_after_sram_flush
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.descriptor_after_sram_flush.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via cycle_model.
SSOT item context: name=descriptor_after_sram_flush.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.descriptor_after_sram_flush
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - descriptor_after_sram_flush appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.descriptor_after_sram_flush

### RTL-0315: Implement arbitration rule: name

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.arbitration
- Source ref: cycle_model.arbitration.name
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.arbitration.name.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via cycle_model.arbitration.
SSOT item context: name=name; value=sram_write_priority.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.arbitration.name
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - name appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.arbitration.name

### RTL-0316: Implement arbitration rule: policy

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.arbitration
- Source ref: cycle_model.arbitration.policy
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.arbitration.policy.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via cycle_model.arbitration.
SSOT item context: name=policy; value=assembly SRAM writes win over firmware SRAM reads; reads are retried after write acceptance..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.arbitration.policy
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - policy appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.arbitration.policy

### RTL-0427: Prove module mctp_assembler_scratch_sram_arbiter is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_sram_arbiter.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_sram_arbiter.module_equivalence.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_sram_arbiter.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_sram_arbiter.module_equivalence

### RTL-0087: Implement and connect port sram_wr_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write_port.ports.sram_wr_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write_port.ports.sram_wr_valid.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_write_port.
SSOT item context: name=sram_wr_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write_port.ports.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_wr_valid width matches SSOT value 1
  - sram_wr_valid port direction remains output
- SSOT refs: io_list.interfaces.sram_write_port.ports.sram_wr_valid

### RTL-0088: Implement and connect port sram_wr_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write_port.ports.sram_wr_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write_port.ports.sram_wr_ready.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_write_port.
SSOT item context: name=sram_wr_ready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write_port.ports.sram_wr_ready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_wr_ready width matches SSOT value 1
  - sram_wr_ready port direction remains input
- SSOT refs: io_list.interfaces.sram_write_port.ports.sram_wr_ready

### RTL-0089: Implement and connect port sram_wr_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write_port.ports.sram_wr_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write_port.ports.sram_wr_addr.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_write_port.
SSOT item context: name=sram_wr_addr; width=SRAM_ADDR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write_port.ports.sram_wr_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_wr_addr width matches SSOT value SRAM_ADDR_WIDTH
  - sram_wr_addr port direction remains output
- SSOT refs: io_list.interfaces.sram_write_port.ports.sram_wr_addr

### RTL-0090: Implement and connect port sram_wr_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write_port.ports.sram_wr_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write_port.ports.sram_wr_data.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_write_port.
SSOT item context: name=sram_wr_data; width=SRAM_DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write_port.ports.sram_wr_data
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_wr_data width matches SSOT value SRAM_DATA_WIDTH
  - sram_wr_data port direction remains output
- SSOT refs: io_list.interfaces.sram_write_port.ports.sram_wr_data

### RTL-0091: Implement and connect port sram_wr_strb

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_write_port.ports.sram_wr_strb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_write_port.ports.sram_wr_strb.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_write_port.
SSOT item context: name=sram_wr_strb; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_write_port.ports.sram_wr_strb
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_wr_strb width matches SSOT value 32
  - sram_wr_strb port direction remains output
- SSOT refs: io_list.interfaces.sram_write_port.ports.sram_wr_strb

### RTL-0092: Implement and connect port sram_rd_req_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_valid.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_req_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_req_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_req_valid width matches SSOT value 1
  - sram_rd_req_valid port direction remains output
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_req_valid

### RTL-0093: Implement and connect port sram_rd_req_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_ready.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_req_ready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_req_ready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_req_ready width matches SSOT value 1
  - sram_rd_req_ready port direction remains input
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_req_ready

### RTL-0094: Implement and connect port sram_rd_req_addr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_addr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_req_addr.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_req_addr; width=SRAM_ADDR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_req_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_req_addr width matches SSOT value SRAM_ADDR_WIDTH
  - sram_rd_req_addr port direction remains output
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_req_addr

### RTL-0095: Implement and connect port sram_rd_rsp_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_valid.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_rsp_valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_rsp_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_rsp_valid width matches SSOT value 1
  - sram_rd_rsp_valid port direction remains input
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_valid

### RTL-0096: Implement and connect port sram_rd_rsp_ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_ready.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_rsp_ready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_rsp_ready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_rsp_ready width matches SSOT value 1
  - sram_rd_rsp_ready port direction remains output
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_ready

### RTL-0097: Implement and connect port sram_rd_rsp_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_data.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_rsp_data; width=SRAM_DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_rsp_data
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_rsp_data width matches SSOT value SRAM_DATA_WIDTH
  - sram_rd_rsp_data port direction remains input
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_data

### RTL-0098: Implement and connect port sram_rd_rsp_error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_error.
Owner: mctp_assembler_scratch_sram_arbiter in rtl/mctp_assembler_scratch_sram_arbiter.sv via io_list.interfaces.sram_read_port.
SSOT item context: name=sram_rd_rsp_error; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.sram_read_port.ports.sram_rd_rsp_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_sram_arbiter.sv
  - sram_rd_rsp_error width matches SSOT value 1
  - sram_rd_rsp_error port direction remains input
- SSOT refs: io_list.interfaces.sram_read_port.ports.sram_rd_rsp_error
