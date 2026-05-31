# RTL Authoring Packet: module__mctp_assembler_scratch_apb_regfile__function_model_01

- Kind: module
- Owner module: mctp_assembler_scratch_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_apb_regfile.sv
- Task count: 48
- Required tasks: 48

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
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0104: Implement RTL state owner for FL state enable_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.enable_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.enable_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=enable_reg; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.enable_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - enable_reg width matches SSOT value 1
  - enable_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.enable_reg

### RTL-0105: Implement RTL state owner for FL state drop_mode_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.drop_mode_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.drop_mode_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=drop_mode_reg; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.drop_mode_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - drop_mode_reg width matches SSOT value 1
  - drop_mode_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.drop_mode_reg

### RTL-0106: Implement RTL state owner for FL state raw_debug_read_enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.raw_debug_read_enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.raw_debug_read_enable.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=raw_debug_read_enable; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.raw_debug_read_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - raw_debug_read_enable width matches SSOT value 1
  - raw_debug_read_enable reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.raw_debug_read_enable

### RTL-0107: Implement RTL state owner for FL state active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.active_context_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.active_context_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=active_context_count; width=5; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - active_context_count width matches SSOT value 5
  - active_context_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.active_context_count

### RTL-0108: Implement RTL state owner for FL state descriptor_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.descriptor_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.descriptor_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=descriptor_count; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.descriptor_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - descriptor_count width matches SSOT value 4
  - descriptor_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.descriptor_count

### RTL-0109: Implement RTL state owner for FL state payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.payload_byte_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.payload_byte_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=payload_byte_count; width=13; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - payload_byte_count width matches SSOT value 13
  - payload_byte_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.payload_byte_count

### RTL-0110: Implement RTL state owner for FL state collected_tlp_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.collected_tlp_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.collected_tlp_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=collected_tlp_count; width=16; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.collected_tlp_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - collected_tlp_count width matches SSOT value 16
  - collected_tlp_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.collected_tlp_count

### RTL-0111: Implement RTL state owner for FL state packet_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.packet_drop_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.packet_drop_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=packet_drop_count; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.packet_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - packet_drop_count width matches SSOT value 32
  - packet_drop_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.packet_drop_count

### RTL-0112: Implement RTL state owner for FL state assembly_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.assembly_drop_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.assembly_drop_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=assembly_drop_count; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.assembly_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - assembly_drop_count width matches SSOT value 32
  - assembly_drop_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.assembly_drop_count

### RTL-0113: Implement RTL state owner for FL state read_error_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.read_error_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.read_error_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=read_error_count; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - read_error_count width matches SSOT value 32
  - read_error_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.read_error_count

### RTL-0114: Implement RTL state owner for FL state ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_state.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_state; width=2; reset=STATE_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_state width matches SSOT value 2
  - ctx_state reset behavior matches SSOT value STATE_IDLE
- SSOT refs: function_model.state_variables.ctx_state

### RTL-0115: Implement RTL state owner for FL state ctx_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_valid
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_valid.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_valid; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_valid width matches SSOT value 1
  - ctx_valid reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_valid

### RTL-0116: Implement RTL state owner for FL state ctx_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_error
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_error.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_error; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_error width matches SSOT value 1
  - ctx_error reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_error

### RTL-0117: Implement RTL state owner for FL state ctx_source_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_source_eid
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_source_eid.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_source_eid; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_source_eid width matches SSOT value 8
  - ctx_source_eid reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_source_eid

### RTL-0118: Implement RTL state owner for FL state ctx_destination_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_destination_eid
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_destination_eid.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_destination_eid; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_destination_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_destination_eid width matches SSOT value 8
  - ctx_destination_eid reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_destination_eid

### RTL-0119: Implement RTL state owner for FL state ctx_tag_owner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_tag_owner
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_tag_owner.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_tag_owner; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_tag_owner width matches SSOT value 1
  - ctx_tag_owner reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_tag_owner

### RTL-0120: Implement RTL state owner for FL state ctx_message_tag

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_message_tag
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_message_tag.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_message_tag; width=3; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_message_tag width matches SSOT value 3
  - ctx_message_tag reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_message_tag

### RTL-0121: Implement RTL state owner for FL state ctx_message_type

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_message_type
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_message_type.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_message_type; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_message_type
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_message_type width matches SSOT value 8
  - ctx_message_type reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_message_type

### RTL-0122: Implement RTL state owner for FL state ctx_expected_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_expected_seq
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_expected_seq.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_expected_seq; width=2; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_expected_seq width matches SSOT value 2
  - ctx_expected_seq reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_expected_seq

### RTL-0123: Implement RTL state owner for FL state ctx_last_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_last_seq
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_last_seq.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_last_seq; width=2; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_last_seq width matches SSOT value 2
  - ctx_last_seq reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_last_seq

### RTL-0124: Implement RTL state owner for FL state ctx_payload_base_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_base_addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_base_addr.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_base_addr; width=SRAM_ADDR_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_payload_base_addr width matches SSOT value SRAM_ADDR_WIDTH
  - ctx_payload_base_addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_base_addr

### RTL-0125: Implement RTL state owner for FL state ctx_payload_next_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_next_addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_next_addr.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_next_addr; width=SRAM_ADDR_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_payload_next_addr width matches SSOT value SRAM_ADDR_WIDTH
  - ctx_payload_next_addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_next_addr

### RTL-0126: Implement RTL state owner for FL state ctx_payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_byte_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_byte_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_byte_count; width=13; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_payload_byte_count width matches SSOT value 13
  - ctx_payload_byte_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_byte_count

### RTL-0127: Implement RTL state owner for FL state ctx_transmission_unit_bytes

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_transmission_unit_bytes
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_transmission_unit_bytes.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_transmission_unit_bytes; width=13; reset=BASELINE_MTU_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_transmission_unit_bytes
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_transmission_unit_bytes width matches SSOT value 13
  - ctx_transmission_unit_bytes reset behavior matches SSOT value BASELINE_MTU_BYTES
- SSOT refs: function_model.state_variables.ctx_transmission_unit_bytes

### RTL-0128: Implement RTL state owner for FL state ctx_timeout_age

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_timeout_age
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_timeout_age.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_timeout_age; width=TIMEOUT_COUNTER_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_timeout_age
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_timeout_age width matches SSOT value TIMEOUT_COUNTER_WIDTH
  - ctx_timeout_age reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_timeout_age

### RTL-0129: Implement RTL state owner for FL state ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_last_drop_reason
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_last_drop_reason; width=8; reset=DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_last_drop_reason width matches SSOT value 8
  - ctx_last_drop_reason reset behavior matches SSOT value DROP_NONE
- SSOT refs: function_model.state_variables.ctx_last_drop_reason

### RTL-0130: Implement RTL state owner for FL state ctx_partial_word_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_partial_word_addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_partial_word_addr.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_partial_word_addr; width=SRAM_ADDR_WIDTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_partial_word_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_partial_word_addr width matches SSOT value SRAM_ADDR_WIDTH
  - ctx_partial_word_addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_partial_word_addr

### RTL-0131: Implement RTL state owner for FL state ctx_partial_word_strobe

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_partial_word_strobe
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_partial_word_strobe.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_partial_word_strobe; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_partial_word_strobe
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_partial_word_strobe width matches SSOT value 32
  - ctx_partial_word_strobe reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_partial_word_strobe

### RTL-0132: Implement RTL state owner for FL state ctx_partial_word_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_partial_word_valid
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_partial_word_valid.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_partial_word_valid; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_partial_word_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_partial_word_valid width matches SSOT value 1
  - ctx_partial_word_valid reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_partial_word_valid

### RTL-0133: Implement RTL state owner for FL state ctx_partial_next_lane

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_partial_next_lane
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_partial_next_lane.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_partial_next_lane; width=5; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_partial_next_lane width matches SSOT value 5
  - ctx_partial_next_lane reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_partial_next_lane

### RTL-0243: Implement transaction FM_ASSEMBLY_DROP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: id=FM_ASSEMBLY_DROP; name=Assembly drop without descriptor publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP

### RTL-0244: Implement precondition for FM_ASSEMBLY_DROP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.preconditions.precondition_0.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: value=assembly_drop_reason != DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.preconditions.precondition_0

### RTL-0245: Implement output for FM_ASSEMBLY_DROP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_0.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: value=debug_drop_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_0

### RTL-0246: Implement output for FM_ASSEMBLY_DROP: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_1.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: value=interrupt.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.output_1

### RTL-0247: Implement output for FM_ASSEMBLY_DROP: interrupt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.interrupt.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=interrupt; port=irq; expr=assembly_drop_reason != DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.interrupt
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - interrupt RTL expression implements SSOT expression assembly_drop_reason != DROP_NONE
  - DUT port irq is the implementation/observation point for interrupt
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.interrupt

### RTL-0248: Implement output for FM_ASSEMBLY_DROP: assembly_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.assembly_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.assembly_drop_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: state=assembly_drop_count; expr=assembly_drop_count + (assembly_drop_reason != DROP_NONE).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.assembly_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_ASSEMBLY_DROP.outputs.assembly_drop_count RTL expression implements SSOT expression assembly_drop_count + (assembly_drop_reason != DROP_NONE)
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.assembly_drop_count

### RTL-0249: Implement output for FM_ASSEMBLY_DROP: ctx_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_error.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: state=ctx_error; expr=assembly_drop_reason != DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_error RTL expression implements SSOT expression assembly_drop_reason != DROP_NONE
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_error

### RTL-0250: Implement output for FM_ASSEMBLY_DROP: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_state.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: state=ctx_state; expr=STATE_ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_state RTL expression implements SSOT expression STATE_ERROR
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_state

### RTL-0251: Implement output for FM_ASSEMBLY_DROP: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: state=ctx_last_drop_reason; expr=assembly_drop_reason.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_last_drop_reason RTL expression implements SSOT expression assembly_drop_reason
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.outputs.ctx_last_drop_reason

### RTL-0252: Implement output rule for FM_ASSEMBLY_DROP: debug_drop_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.debug_drop_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.debug_drop_pulse.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=debug_drop_pulse; port=debug_drop_pulse; expr=assembly_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.output_rules.debug_drop_pulse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - debug_drop_pulse width matches SSOT value 1
  - debug_drop_pulse RTL expression implements SSOT expression assembly_drop_reason != DROP_NONE
  - DUT port debug_drop_pulse is the implementation/observation point for debug_drop_pulse
  - debug_drop_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.debug_drop_pulse

### RTL-0253: Implement output rule for FM_ASSEMBLY_DROP: interrupt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.interrupt.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=interrupt; port=irq; expr=assembly_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.output_rules.interrupt
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - interrupt width matches SSOT value 1
  - interrupt RTL expression implements SSOT expression assembly_drop_reason != DROP_NONE
  - DUT port irq is the implementation/observation point for interrupt
  - interrupt is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.output_rules.interrupt

### RTL-0254: Implement state update for FM_ASSEMBLY_DROP: assembly_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.assembly_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.assembly_drop_count.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=assembly_drop_count; expr=assembly_drop_count + (assembly_drop_reason != DROP_NONE); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.state_updates.assembly_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - assembly_drop_count width matches SSOT value 32
  - assembly_drop_count RTL expression implements SSOT expression assembly_drop_count + (assembly_drop_reason != DROP_NONE)
  - assembly_drop_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.assembly_drop_count

### RTL-0255: Implement state update for FM_ASSEMBLY_DROP: ctx_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_error.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=ctx_error; expr=assembly_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_error width matches SSOT value 1
  - ctx_error RTL expression implements SSOT expression assembly_drop_reason != DROP_NONE
  - ctx_error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_error

### RTL-0256: Implement state update for FM_ASSEMBLY_DROP: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_state.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=ctx_state; expr=STATE_ERROR; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_state width matches SSOT value 2
  - ctx_state RTL expression implements SSOT expression STATE_ERROR
  - ctx_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_state

### RTL-0257: Implement state update for FM_ASSEMBLY_DROP: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: name=ctx_last_drop_reason; expr=assembly_drop_reason; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - ctx_last_drop_reason width matches SSOT value 8
  - ctx_last_drop_reason RTL expression implements SSOT expression assembly_drop_reason
  - ctx_last_drop_reason updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.state_updates.ctx_last_drop_reason

### RTL-0258: Implement error case for FM_ASSEMBLY_DROP: AD_MESSAGE_OVERFLOW

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_MESSAGE_OVERFLOW
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_MESSAGE_OVERFLOW.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: id=FM_ASSEMBLY_DROP; name=Assembly drop without descriptor publish; port=["debug_drop_pulse", "irq"]; signal=[{"action": "no_sram_write_and_enter_error_state", "condition": "assembly_drop_reason == 22", "id": "AD_MESSAGE_OVERF...; state=["assembly_drop_count", "ctx_error", "ctx_state", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_MESSAGE_OVERFLOW
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - DUT port ["debug_drop_pulse", "irq"] is the implementation/observation point for Assembly drop without descriptor publish
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_MESSAGE_OVERFLOW

### RTL-0259: Implement error case for FM_ASSEMBLY_DROP: AD_SRAM_OVERFLOW

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_SRAM_OVERFLOW
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_SRAM_OVERFLOW.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: id=FM_ASSEMBLY_DROP; name=Assembly drop without descriptor publish; port=["debug_drop_pulse", "irq"]; signal=[{"action": "no_sram_write_and_enter_error_state", "condition": "assembly_drop_reason == 23", "id": "AD_SRAM_OVERFLOW...; state=["assembly_drop_count", "ctx_error", "ctx_state", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_SRAM_OVERFLOW
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - DUT port ["debug_drop_pulse", "irq"] is the implementation/observation point for Assembly drop without descriptor publish
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_SRAM_OVERFLOW

### RTL-0260: Implement error case for FM_ASSEMBLY_DROP: AD_TIMEOUT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_TIMEOUT
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_TIMEOUT.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_ASSEMBLY_DROP.
SSOT item context: id=FM_ASSEMBLY_DROP; name=Assembly drop without descriptor publish; port=["debug_drop_pulse", "irq"]; signal=[{"action": "clear_context_after_counting_drop", "condition": "assembly_drop_reason == 25", "id": "AD_TIMEOUT"}, "ass...; state=["assembly_drop_count", "ctx_error", "ctx_state", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_TIMEOUT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - DUT port ["debug_drop_pulse", "irq"] is the implementation/observation point for Assembly drop without descriptor publish
- SSOT refs: function_model.transactions.FM_ASSEMBLY_DROP.error_cases.AD_TIMEOUT
