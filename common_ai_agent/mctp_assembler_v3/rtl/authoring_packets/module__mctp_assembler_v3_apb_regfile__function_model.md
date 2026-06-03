# RTL Authoring Packet: module__mctp_assembler_v3_apb_regfile__function_model

- Kind: module
- Owner module: mctp_assembler_v3_apb_regfile
- Owner file: rtl/mctp_assembler_v3_apb_regfile.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 17
- Human-locked open tasks: 0
- Owner refs: decomposition, error_handling, features, function_model.state_variables, interrupts, registers, registers.register_list
- Module slice: 1/7 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_v3_apb_regfile is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])

## Tasks

### RTL-0103: Implement RTL state owner for FL state context_table

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.context_table
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.context_table.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=context_table; reset=IDLE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.context_table
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - context_table reset behavior matches SSOT value IDLE
- SSOT refs: function_model.state_variables.context_table

### RTL-0104: Implement RTL state owner for FL state descriptor_queue

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.descriptor_queue
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.descriptor_queue.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=descriptor_queue; reset=empty.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.descriptor_queue
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_queue reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.descriptor_queue

### RTL-0105: Implement RTL state owner for FL state sram_alloc_ptr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sram_alloc_ptr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sram_alloc_ptr.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=sram_alloc_ptr; reset=sram_base.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sram_alloc_ptr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_alloc_ptr reset behavior matches SSOT value sram_base
- SSOT refs: function_model.state_variables.sram_alloc_ptr

### RTL-0106: Implement RTL state owner for FL state counters

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.counters
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.counters.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=counters; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.counters
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - counters reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.counters

### RTL-0107: Implement RTL state owner for FL state last_drop_class

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.last_drop_class
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.last_drop_class.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=last_drop_class; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.last_drop_class
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - last_drop_class reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.last_drop_class

### RTL-0108: Implement RTL state owner for FL state tlp_seen_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tlp_seen_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tlp_seen_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=tlp_seen_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tlp_seen_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - tlp_seen_count width matches SSOT value 32
  - tlp_seen_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.tlp_seen_count

### RTL-0109: Implement RTL state owner for FL state tlp_accepted_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tlp_accepted_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tlp_accepted_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=tlp_accepted_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tlp_accepted_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - tlp_accepted_count width matches SSOT value 32
  - tlp_accepted_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.tlp_accepted_count

### RTL-0110: Implement RTL state owner for FL state active_context_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.active_context_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.active_context_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=active_context_count; width=5; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - active_context_count width matches SSOT value 5
  - active_context_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.active_context_count

### RTL-0111: Implement RTL state owner for FL state ctx_payload_byte_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_byte_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_byte_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_byte_count; width=13; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_payload_byte_count width matches SSOT value 13
  - ctx_payload_byte_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_byte_count

### RTL-0112: Implement RTL state owner for FL state ctx_expected_seq

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_expected_seq
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_expected_seq.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_expected_seq; width=2; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_expected_seq width matches SSOT value 2
  - ctx_expected_seq reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_expected_seq

### RTL-0113: Implement RTL state owner for FL state ctx_payload_base_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_base_addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_base_addr.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_base_addr; width=16; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_payload_base_addr width matches SSOT value 16
  - ctx_payload_base_addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_base_addr

### RTL-0114: Implement RTL state owner for FL state ctx_payload_next_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_payload_next_addr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_payload_next_addr.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_payload_next_addr; width=16; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_payload_next_addr width matches SSOT value 16
  - ctx_payload_next_addr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_payload_next_addr

### RTL-0115: Implement RTL state owner for FL state ctx_partial_next_lane

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctx_partial_next_lane
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctx_partial_next_lane.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=ctx_partial_next_lane; width=5; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_partial_next_lane width matches SSOT value 5
  - ctx_partial_next_lane reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctx_partial_next_lane

### RTL-0116: Implement RTL state owner for FL state payload_bytes_written_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.payload_bytes_written_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.payload_bytes_written_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=payload_bytes_written_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.payload_bytes_written_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - payload_bytes_written_count width matches SSOT value 32
  - payload_bytes_written_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.payload_bytes_written_count

### RTL-0117: Implement RTL state owner for FL state message_completed_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.message_completed_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.message_completed_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=message_completed_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.message_completed_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - message_completed_count width matches SSOT value 32
  - message_completed_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.message_completed_count

### RTL-0118: Implement RTL state owner for FL state fw_axi_read_beat_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fw_axi_read_beat_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fw_axi_read_beat_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=fw_axi_read_beat_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fw_axi_read_beat_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - fw_axi_read_beat_count width matches SSOT value 32
  - fw_axi_read_beat_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fw_axi_read_beat_count

### RTL-0119: Implement RTL state owner for FL state fw_axi_read_error_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fw_axi_read_error_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fw_axi_read_error_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=fw_axi_read_error_count; width=32; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fw_axi_read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - fw_axi_read_error_count width matches SSOT value 32
  - fw_axi_read_error_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fw_axi_read_error_count
