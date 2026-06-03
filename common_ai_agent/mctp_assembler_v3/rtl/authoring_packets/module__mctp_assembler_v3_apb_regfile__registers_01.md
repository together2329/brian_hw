# RTL Authoring Packet: module__mctp_assembler_v3_apb_regfile__registers_01

- Kind: module
- Owner module: mctp_assembler_v3_apb_regfile
- Owner file: rtl/mctp_assembler_v3_apb_regfile.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: decomposition, error_handling, features, function_model.state_variables, interrupts, registers, registers.register_list
- Module slice: 2/7 section=registers task_limit=48
- Slice rule: Owner module mctp_assembler_v3_apb_regfile is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])

## Tasks

### RTL-0314: Implement CSR/register CONTROL

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CONTROL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CONTROL.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=CONTROL; width=32; reset=0; access=rw; offset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CONTROL
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - CONTROL width matches SSOT value 32
  - CONTROL reset behavior matches SSOT value 0
  - CONTROL access policy rw is implemented without read/write shortcuts
  - CONTROL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CONTROL

### RTL-0315: Implement field CONTROL.enable

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.enable.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.enable
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.enable

### RTL-0316: Implement field CONTROL.drop_when_disabled

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.drop_when_disabled
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.drop_when_disabled.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=drop_when_disabled; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.drop_when_disabled
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - drop_when_disabled reset behavior matches SSOT value 0
  - drop_when_disabled access policy rw is implemented without read/write shortcuts
  - drop_when_disabled readback returns implemented RTL state when readable
  - drop_when_disabled write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.drop_when_disabled

### RTL-0317: Implement field CONTROL.soft_reset

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.soft_reset
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.soft_reset.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=soft_reset; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.soft_reset
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - soft_reset reset behavior matches SSOT value 0
  - soft_reset access policy rw is implemented without read/write shortcuts
  - soft_reset readback returns implemented RTL state when readable
  - soft_reset write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.soft_reset

### RTL-0318: Implement field CONTROL.dest_filter_enable

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.dest_filter_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.dest_filter_enable.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=dest_filter_enable; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.dest_filter_enable
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - dest_filter_enable reset behavior matches SSOT value 0
  - dest_filter_enable access policy rw is implemented without read/write shortcuts
  - dest_filter_enable readback returns implemented RTL state when readable
  - dest_filter_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.dest_filter_enable

### RTL-0319: Implement field CONTROL.accept_broadcast_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.accept_broadcast_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.accept_broadcast_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=accept_broadcast_eid; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.accept_broadcast_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - accept_broadcast_eid reset behavior matches SSOT value 0
  - accept_broadcast_eid access policy rw is implemented without read/write shortcuts
  - accept_broadcast_eid readback returns implemented RTL state when readable
  - accept_broadcast_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.accept_broadcast_eid

### RTL-0320: Implement field CONTROL.accept_null_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.accept_null_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.accept_null_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=accept_null_eid; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.accept_null_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - accept_null_eid reset behavior matches SSOT value 0
  - accept_null_eid access policy rw is implemented without read/write shortcuts
  - accept_null_eid readback returns implemented RTL state when readable
  - accept_null_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.accept_null_eid

### RTL-0321: Implement field CONTROL.raw_sram_debug_read_enable

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.raw_sram_debug_read_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.raw_sram_debug_read_enable.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=raw_sram_debug_read_enable; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.raw_sram_debug_read_enable
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - raw_sram_debug_read_enable reset behavior matches SSOT value 0
  - raw_sram_debug_read_enable access policy rw is implemented without read/write shortcuts
  - raw_sram_debug_read_enable readback returns implemented RTL state when readable
  - raw_sram_debug_read_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.raw_sram_debug_read_enable

### RTL-0322: Implement field CONTROL.descriptor_pop

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.descriptor_pop
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.descriptor_pop.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=descriptor_pop; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.descriptor_pop
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_pop reset behavior matches SSOT value 0
  - descriptor_pop access policy rw is implemented without read/write shortcuts
  - descriptor_pop readback returns implemented RTL state when readable
  - descriptor_pop write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.descriptor_pop

### RTL-0323: Implement field CONTROL.counter_clear

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.counter_clear
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.counter_clear.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=counter_clear; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.counter_clear
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - counter_clear reset behavior matches SSOT value 0
  - counter_clear access policy rw is implemented without read/write shortcuts
  - counter_clear readback returns implemented RTL state when readable
  - counter_clear write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.counter_clear

### RTL-0324: Implement field CONTROL.local_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.local_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.local_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=local_eid; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.local_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - local_eid reset behavior matches SSOT value 0
  - local_eid access policy rw is implemented without read/write shortcuts
  - local_eid readback returns implemented RTL state when readable
  - local_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.local_eid

### RTL-0325: Implement field CONTROL.debug_context_select

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.debug_context_select
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.debug_context_select.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=debug_context_select; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.debug_context_select
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - debug_context_select reset behavior matches SSOT value 0
  - debug_context_select access policy rw is implemented without read/write shortcuts
  - debug_context_select readback returns implemented RTL state when readable
  - debug_context_select write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.debug_context_select

### RTL-0326: Implement CSR/register CFG_TU

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CFG_TU
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CFG_TU.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=CFG_TU; width=32; reset=268435520; access=rw; offset=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CFG_TU
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - CFG_TU width matches SSOT value 32
  - CFG_TU reset behavior matches SSOT value 268435520
  - CFG_TU access policy rw is implemented without read/write shortcuts
  - CFG_TU decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.CFG_TU

### RTL-0327: Implement field CFG_TU.transmission_unit_bytes

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CFG_TU.fields.transmission_unit_bytes
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CFG_TU.fields.transmission_unit_bytes.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=transmission_unit_bytes; reset=64; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CFG_TU.fields.transmission_unit_bytes
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - transmission_unit_bytes reset behavior matches SSOT value 64
  - transmission_unit_bytes access policy rw is implemented without read/write shortcuts
  - transmission_unit_bytes readback returns implemented RTL state when readable
  - transmission_unit_bytes write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CFG_TU.fields.transmission_unit_bytes

### RTL-0328: Implement field CFG_TU.max_message_bytes

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CFG_TU.fields.max_message_bytes
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CFG_TU.fields.max_message_bytes.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=max_message_bytes; reset=4096; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CFG_TU.fields.max_message_bytes
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - max_message_bytes reset behavior matches SSOT value 4096
  - max_message_bytes access policy rw is implemented without read/write shortcuts
  - max_message_bytes readback returns implemented RTL state when readable
  - max_message_bytes write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CFG_TU.fields.max_message_bytes

### RTL-0329: Implement CSR/register CFG_TIMEOUT

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CFG_TIMEOUT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CFG_TIMEOUT.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=CFG_TIMEOUT; width=32; reset=0; access=rw; offset=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CFG_TIMEOUT
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - CFG_TIMEOUT width matches SSOT value 32
  - CFG_TIMEOUT reset behavior matches SSOT value 0
  - CFG_TIMEOUT access policy rw is implemented without read/write shortcuts
  - CFG_TIMEOUT decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.CFG_TIMEOUT

### RTL-0330: Implement field CFG_TIMEOUT.assembly_timeout_cycles

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CFG_TIMEOUT.fields.assembly_timeout_cycles
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CFG_TIMEOUT.fields.assembly_timeout_cycles.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=assembly_timeout_cycles; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CFG_TIMEOUT.fields.assembly_timeout_cycles
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - assembly_timeout_cycles reset behavior matches SSOT value 0
  - assembly_timeout_cycles access policy rw is implemented without read/write shortcuts
  - assembly_timeout_cycles readback returns implemented RTL state when readable
  - assembly_timeout_cycles write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CFG_TIMEOUT.fields.assembly_timeout_cycles

### RTL-0331: Implement CSR/register SRAM_BASE

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.SRAM_BASE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SRAM_BASE.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=SRAM_BASE; width=32; reset=0; access=rw; offset=12.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SRAM_BASE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - SRAM_BASE width matches SSOT value 32
  - SRAM_BASE reset behavior matches SSOT value 0
  - SRAM_BASE access policy rw is implemented without read/write shortcuts
  - SRAM_BASE decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.SRAM_BASE

### RTL-0332: Implement field SRAM_BASE.sram_base

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.SRAM_BASE.fields.sram_base
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SRAM_BASE.fields.sram_base.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_base; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SRAM_BASE.fields.sram_base
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_base reset behavior matches SSOT value 0
  - sram_base access policy rw is implemented without read/write shortcuts
  - sram_base readback returns implemented RTL state when readable
  - sram_base write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SRAM_BASE.fields.sram_base

### RTL-0333: Implement CSR/register SRAM_LIMIT

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.SRAM_LIMIT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SRAM_LIMIT.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=SRAM_LIMIT; width=32; reset=65535; access=rw; offset=16.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SRAM_LIMIT
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - SRAM_LIMIT width matches SSOT value 32
  - SRAM_LIMIT reset behavior matches SSOT value 65535
  - SRAM_LIMIT access policy rw is implemented without read/write shortcuts
  - SRAM_LIMIT decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.SRAM_LIMIT

### RTL-0334: Implement field SRAM_LIMIT.sram_limit

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.SRAM_LIMIT.fields.sram_limit
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SRAM_LIMIT.fields.sram_limit.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_limit; reset=65535; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SRAM_LIMIT.fields.sram_limit
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_limit reset behavior matches SSOT value 65535
  - sram_limit access policy rw is implemented without read/write shortcuts
  - sram_limit readback returns implemented RTL state when readable
  - sram_limit write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SRAM_LIMIT.fields.sram_limit

### RTL-0335: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.STATUS

### RTL-0336: Implement field STATUS.ingress_busy

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.ingress_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.ingress_busy.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ingress_busy; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.ingress_busy
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ingress_busy reset behavior matches SSOT value 0
  - ingress_busy access policy ro is implemented without read/write shortcuts
  - ingress_busy readback returns implemented RTL state when readable
  - ingress_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.ingress_busy

### RTL-0337: Implement field STATUS.axi_read_busy

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.axi_read_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.axi_read_busy.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=axi_read_busy; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.axi_read_busy
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - axi_read_busy reset behavior matches SSOT value 0
  - axi_read_busy access policy ro is implemented without read/write shortcuts
  - axi_read_busy readback returns implemented RTL state when readable
  - axi_read_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.axi_read_busy

### RTL-0338: Implement field STATUS.sram_write_busy

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.sram_write_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.sram_write_busy.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_write_busy; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.sram_write_busy
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_write_busy reset behavior matches SSOT value 0
  - sram_write_busy access policy ro is implemented without read/write shortcuts
  - sram_write_busy readback returns implemented RTL state when readable
  - sram_write_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.sram_write_busy

### RTL-0339: Implement field STATUS.sram_read_busy

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.sram_read_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.sram_read_busy.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_read_busy; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.sram_read_busy
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_read_busy reset behavior matches SSOT value 0
  - sram_read_busy access policy ro is implemented without read/write shortcuts
  - sram_read_busy readback returns implemented RTL state when readable
  - sram_read_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.sram_read_busy

### RTL-0340: Implement field STATUS.descriptor_available

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.descriptor_available
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.descriptor_available.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=descriptor_available; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.descriptor_available
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_available reset behavior matches SSOT value 0
  - descriptor_available access policy ro is implemented without read/write shortcuts
  - descriptor_available readback returns implemented RTL state when readable
  - descriptor_available write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.descriptor_available

### RTL-0341: Implement field STATUS.descriptor_queue_full

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.descriptor_queue_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.descriptor_queue_full.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=descriptor_queue_full; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.descriptor_queue_full
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_queue_full reset behavior matches SSOT value 0
  - descriptor_queue_full access policy ro is implemented without read/write shortcuts
  - descriptor_queue_full readback returns implemented RTL state when readable
  - descriptor_queue_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.descriptor_queue_full

### RTL-0342: Implement field STATUS.context_active_any

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.context_active_any
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.context_active_any.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=context_active_any; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.context_active_any
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - context_active_any reset behavior matches SSOT value 0
  - context_active_any access policy ro is implemented without read/write shortcuts
  - context_active_any readback returns implemented RTL state when readable
  - context_active_any write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.context_active_any

### RTL-0343: Implement field STATUS.context_error_any

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.context_error_any
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.context_error_any.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=context_error_any; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.context_error_any
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - context_error_any reset behavior matches SSOT value 0
  - context_error_any access policy ro is implemented without read/write shortcuts
  - context_error_any readback returns implemented RTL state when readable
  - context_error_any write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.context_error_any

### RTL-0344: Implement field STATUS.packet_drop_seen

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.packet_drop_seen
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.packet_drop_seen.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=packet_drop_seen; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.packet_drop_seen
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - packet_drop_seen reset behavior matches SSOT value 0
  - packet_drop_seen access policy ro is implemented without read/write shortcuts
  - packet_drop_seen readback returns implemented RTL state when readable
  - packet_drop_seen write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.packet_drop_seen

### RTL-0345: Implement field STATUS.assembly_drop_seen

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.assembly_drop_seen
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.assembly_drop_seen.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=assembly_drop_seen; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.assembly_drop_seen
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - assembly_drop_seen reset behavior matches SSOT value 0
  - assembly_drop_seen access policy ro is implemented without read/write shortcuts
  - assembly_drop_seen readback returns implemented RTL state when readable
  - assembly_drop_seen write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.assembly_drop_seen

### RTL-0346: Implement field STATUS.active_context_count

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.active_context_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.active_context_count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=active_context_count; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - active_context_count reset behavior matches SSOT value 0
  - active_context_count access policy ro is implemented without read/write shortcuts
  - active_context_count readback returns implemented RTL state when readable
  - active_context_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.active_context_count

### RTL-0347: Implement field STATUS.last_drop_class

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.last_drop_class
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.last_drop_class.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=last_drop_class; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.last_drop_class
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - last_drop_class reset behavior matches SSOT value 0
  - last_drop_class access policy ro is implemented without read/write shortcuts
  - last_drop_class readback returns implemented RTL state when readable
  - last_drop_class write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.last_drop_class

### RTL-0348: Implement field STATUS.last_drop_reason

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.last_drop_reason
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.last_drop_reason.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=last_drop_reason; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - last_drop_reason reset behavior matches SSOT value 0
  - last_drop_reason access policy ro is implemented without read/write shortcuts
  - last_drop_reason readback returns implemented RTL state when readable
  - last_drop_reason write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.last_drop_reason

### RTL-0349: Implement field STATUS.last_error_context_id

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.last_error_context_id
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.last_error_context_id.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=last_error_context_id; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.last_error_context_id
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - last_error_context_id reset behavior matches SSOT value 0
  - last_error_context_id access policy ro is implemented without read/write shortcuts
  - last_error_context_id readback returns implemented RTL state when readable
  - last_error_context_id write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.last_error_context_id

### RTL-0350: Implement CSR/register CTX_STATE

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CTX_STATE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTX_STATE.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=CTX_STATE; width=32; reset=0; access=ro; offset=1024.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTX_STATE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - CTX_STATE width matches SSOT value 32
  - CTX_STATE reset behavior matches SSOT value 0
  - CTX_STATE access policy ro is implemented without read/write shortcuts
  - CTX_STATE decode uses SSOT address/offset 1024
- SSOT refs: registers.register_list.CTX_STATE

### RTL-0351: Implement field CTX_STATE.ctx_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_state reset behavior matches SSOT value 0
  - ctx_state access policy ro is implemented without read/write shortcuts
  - ctx_state readback returns implemented RTL state when readable
  - ctx_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_state

### RTL-0352: Implement field CTX_STATE.ctx_valid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_valid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_valid; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_valid reset behavior matches SSOT value 0
  - ctx_valid access policy ro is implemented without read/write shortcuts
  - ctx_valid readback returns implemented RTL state when readable
  - ctx_valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_valid

### RTL-0353: Implement field CTX_STATE.ctx_error

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_error.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_error; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_error
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_error reset behavior matches SSOT value 0
  - ctx_error access policy ro is implemented without read/write shortcuts
  - ctx_error readback returns implemented RTL state when readable
  - ctx_error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_error

### RTL-0354: Implement field CTX_STATE.ctx_source_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_source_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_source_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_source_eid; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_source_eid reset behavior matches SSOT value 0
  - ctx_source_eid access policy ro is implemented without read/write shortcuts
  - ctx_source_eid readback returns implemented RTL state when readable
  - ctx_source_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_source_eid

### RTL-0355: Implement field CTX_STATE.ctx_message_tag

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_message_tag
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_message_tag.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_message_tag; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_message_tag reset behavior matches SSOT value 0
  - ctx_message_tag access policy ro is implemented without read/write shortcuts
  - ctx_message_tag readback returns implemented RTL state when readable
  - ctx_message_tag write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_message_tag

### RTL-0356: Implement field CTX_STATE.ctx_tag_owner

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_tag_owner
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_tag_owner.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_tag_owner; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_tag_owner reset behavior matches SSOT value 0
  - ctx_tag_owner access policy ro is implemented without read/write shortcuts
  - ctx_tag_owner readback returns implemented RTL state when readable
  - ctx_tag_owner write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_tag_owner

### RTL-0357: Implement field CTX_STATE.ctx_expected_seq

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_expected_seq
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_expected_seq.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_expected_seq; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_expected_seq reset behavior matches SSOT value 0
  - ctx_expected_seq access policy ro is implemented without read/write shortcuts
  - ctx_expected_seq readback returns implemented RTL state when readable
  - ctx_expected_seq write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_expected_seq

### RTL-0358: Implement field CTX_STATE.ctx_last_seq

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_last_seq
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_last_seq.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_last_seq; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_last_seq reset behavior matches SSOT value 0
  - ctx_last_seq access policy ro is implemented without read/write shortcuts
  - ctx_last_seq readback returns implemented RTL state when readable
  - ctx_last_seq write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_last_seq

### RTL-0359: Implement field CTX_STATE.ctx_message_type

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_message_type
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_message_type.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_message_type; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_message_type
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_message_type reset behavior matches SSOT value 0
  - ctx_message_type access policy ro is implemented without read/write shortcuts
  - ctx_message_type readback returns implemented RTL state when readable
  - ctx_message_type write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_message_type

### RTL-0360: Implement field CTX_STATE.ctx_last_drop_reason

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CTX_STATE.fields.ctx_last_drop_reason
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTX_STATE.fields.ctx_last_drop_reason.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_last_drop_reason; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTX_STATE.fields.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - ctx_last_drop_reason reset behavior matches SSOT value 0
  - ctx_last_drop_reason access policy ro is implemented without read/write shortcuts
  - ctx_last_drop_reason readback returns implemented RTL state when readable
  - ctx_last_drop_reason write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTX_STATE.fields.ctx_last_drop_reason

### RTL-0361: Implement CSR/register INTR_RAW_STATUS

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTR_RAW_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTR_RAW_STATUS.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=INTR_RAW_STATUS; width=32; reset=0; access=ro; offset=256.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTR_RAW_STATUS
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - INTR_RAW_STATUS width matches SSOT value 32
  - INTR_RAW_STATUS reset behavior matches SSOT value 0
  - INTR_RAW_STATUS access policy ro is implemented without read/write shortcuts
  - INTR_RAW_STATUS decode uses SSOT address/offset 256
- SSOT refs: registers.register_list.INTR_RAW_STATUS
