# RTL Authoring Packet: module__mctp_assembler_scratch_v5_apb_regfile__registers_01

- Kind: module
- Owner module: mctp_assembler_scratch_v5_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_v5_apb_regfile.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 4/9 section=registers task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_v5_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0317: Implement CSR/register GLOBAL_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.GLOBAL_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.GLOBAL_CTRL.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=GLOBAL_CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - GLOBAL_CTRL width matches SSOT value 32
  - GLOBAL_CTRL reset behavior matches SSOT value 0
  - GLOBAL_CTRL access policy rw is implemented without read/write shortcuts
  - GLOBAL_CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.GLOBAL_CTRL

### RTL-0318: Implement field GLOBAL_CTRL.enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.enable

### RTL-0319: Implement field GLOBAL_CTRL.drop_mode

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.drop_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.drop_mode.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=drop_mode; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.drop_mode
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - drop_mode reset behavior matches SSOT value 0
  - drop_mode access policy rw is implemented without read/write shortcuts
  - drop_mode readback returns implemented RTL state when readable
  - drop_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.drop_mode

### RTL-0320: Implement field GLOBAL_CTRL.raw_debug_read_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.raw_debug_read_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.raw_debug_read_enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=raw_debug_read_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.raw_debug_read_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - raw_debug_read_enable reset behavior matches SSOT value 0
  - raw_debug_read_enable access policy rw is implemented without read/write shortcuts
  - raw_debug_read_enable readback returns implemented RTL state when readable
  - raw_debug_read_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.raw_debug_read_enable

### RTL-0321: Implement field GLOBAL_CTRL.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.reserved

### RTL-0322: Implement CSR/register GLOBAL_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.GLOBAL_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.GLOBAL_STATUS.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=GLOBAL_STATUS; width=32; reset=0; access=ro; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.GLOBAL_STATUS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - GLOBAL_STATUS width matches SSOT value 32
  - GLOBAL_STATUS reset behavior matches SSOT value 0
  - GLOBAL_STATUS access policy ro is implemented without read/write shortcuts
  - GLOBAL_STATUS decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.GLOBAL_STATUS

### RTL-0323: Implement field GLOBAL_STATUS.active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_STATUS.fields.active_context_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_STATUS.fields.active_context_count.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=active_context_count; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_STATUS.fields.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - active_context_count reset behavior matches SSOT value 0
  - active_context_count access policy ro is implemented without read/write shortcuts
  - active_context_count readback returns implemented RTL state when readable
  - active_context_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_STATUS.fields.active_context_count

### RTL-0324: Implement field GLOBAL_STATUS.descriptor_count

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_STATUS.fields.descriptor_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_STATUS.fields.descriptor_count.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=descriptor_count; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_STATUS.fields.descriptor_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - descriptor_count reset behavior matches SSOT value 0
  - descriptor_count access policy ro is implemented without read/write shortcuts
  - descriptor_count readback returns implemented RTL state when readable
  - descriptor_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_STATUS.fields.descriptor_count

### RTL-0325: Implement field GLOBAL_STATUS.any_error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_STATUS.fields.any_error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_STATUS.fields.any_error.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=any_error; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_STATUS.fields.any_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - any_error reset behavior matches SSOT value 0
  - any_error access policy ro is implemented without read/write shortcuts
  - any_error readback returns implemented RTL state when readable
  - any_error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_STATUS.fields.any_error

### RTL-0326: Implement field GLOBAL_STATUS.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_STATUS.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_STATUS.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_STATUS.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_STATUS.fields.reserved

### RTL-0327: Implement CSR/register IRQ_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.IRQ_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.IRQ_STATUS.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=IRQ_STATUS; width=32; reset=0; access=rw1c; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - IRQ_STATUS width matches SSOT value 32
  - IRQ_STATUS reset behavior matches SSOT value 0
  - IRQ_STATUS access policy rw1c is implemented without read/write shortcuts
  - IRQ_STATUS decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.IRQ_STATUS

### RTL-0328: Implement field IRQ_STATUS.desc_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_STATUS.fields.desc_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_STATUS.fields.desc_pending.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=desc_pending; reset=0; access=rw1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS.fields.desc_pending
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - desc_pending reset behavior matches SSOT value 0
  - desc_pending access policy rw1c is implemented without read/write shortcuts
  - desc_pending readback returns implemented RTL state when readable
  - desc_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_STATUS.fields.desc_pending

### RTL-0329: Implement field IRQ_STATUS.packet_drop_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_STATUS.fields.packet_drop_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_STATUS.fields.packet_drop_pending.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=packet_drop_pending; reset=0; access=rw1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS.fields.packet_drop_pending
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - packet_drop_pending reset behavior matches SSOT value 0
  - packet_drop_pending access policy rw1c is implemented without read/write shortcuts
  - packet_drop_pending readback returns implemented RTL state when readable
  - packet_drop_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_STATUS.fields.packet_drop_pending

### RTL-0330: Implement field IRQ_STATUS.assembly_drop_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_STATUS.fields.assembly_drop_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_STATUS.fields.assembly_drop_pending.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=assembly_drop_pending; reset=0; access=rw1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS.fields.assembly_drop_pending
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - assembly_drop_pending reset behavior matches SSOT value 0
  - assembly_drop_pending access policy rw1c is implemented without read/write shortcuts
  - assembly_drop_pending readback returns implemented RTL state when readable
  - assembly_drop_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_STATUS.fields.assembly_drop_pending

### RTL-0331: Implement field IRQ_STATUS.read_error_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_STATUS.fields.read_error_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_STATUS.fields.read_error_pending.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=read_error_pending; reset=0; access=rw1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS.fields.read_error_pending
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - read_error_pending reset behavior matches SSOT value 0
  - read_error_pending access policy rw1c is implemented without read/write shortcuts
  - read_error_pending readback returns implemented RTL state when readable
  - read_error_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_STATUS.fields.read_error_pending

### RTL-0332: Implement field IRQ_STATUS.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_STATUS.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_STATUS.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_STATUS.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_STATUS.fields.reserved

### RTL-0333: Implement CSR/register IRQ_ENABLE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.IRQ_ENABLE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.IRQ_ENABLE.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=IRQ_ENABLE; width=32; reset=0; access=rw; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - IRQ_ENABLE width matches SSOT value 32
  - IRQ_ENABLE reset behavior matches SSOT value 0
  - IRQ_ENABLE access policy rw is implemented without read/write shortcuts
  - IRQ_ENABLE decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.IRQ_ENABLE

### RTL-0334: Implement field IRQ_ENABLE.desc_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_ENABLE.fields.desc_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_ENABLE.fields.desc_enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=desc_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE.fields.desc_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - desc_enable reset behavior matches SSOT value 0
  - desc_enable access policy rw is implemented without read/write shortcuts
  - desc_enable readback returns implemented RTL state when readable
  - desc_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_ENABLE.fields.desc_enable

### RTL-0335: Implement field IRQ_ENABLE.packet_drop_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_ENABLE.fields.packet_drop_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_ENABLE.fields.packet_drop_enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=packet_drop_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE.fields.packet_drop_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - packet_drop_enable reset behavior matches SSOT value 0
  - packet_drop_enable access policy rw is implemented without read/write shortcuts
  - packet_drop_enable readback returns implemented RTL state when readable
  - packet_drop_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_ENABLE.fields.packet_drop_enable

### RTL-0336: Implement field IRQ_ENABLE.assembly_drop_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_ENABLE.fields.assembly_drop_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_ENABLE.fields.assembly_drop_enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=assembly_drop_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE.fields.assembly_drop_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - assembly_drop_enable reset behavior matches SSOT value 0
  - assembly_drop_enable access policy rw is implemented without read/write shortcuts
  - assembly_drop_enable readback returns implemented RTL state when readable
  - assembly_drop_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_ENABLE.fields.assembly_drop_enable

### RTL-0337: Implement field IRQ_ENABLE.read_error_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_ENABLE.fields.read_error_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_ENABLE.fields.read_error_enable.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=read_error_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE.fields.read_error_enable
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - read_error_enable reset behavior matches SSOT value 0
  - read_error_enable access policy rw is implemented without read/write shortcuts
  - read_error_enable readback returns implemented RTL state when readable
  - read_error_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_ENABLE.fields.read_error_enable

### RTL-0338: Implement field IRQ_ENABLE.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.IRQ_ENABLE.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IRQ_ENABLE.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IRQ_ENABLE.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IRQ_ENABLE.fields.reserved

### RTL-0339: Implement CSR/register PACKET_DROP_COUNT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.PACKET_DROP_COUNT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PACKET_DROP_COUNT.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=PACKET_DROP_COUNT; width=32; reset=0; access=ro; offset=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PACKET_DROP_COUNT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - PACKET_DROP_COUNT width matches SSOT value 32
  - PACKET_DROP_COUNT reset behavior matches SSOT value 0
  - PACKET_DROP_COUNT access policy ro is implemented without read/write shortcuts
  - PACKET_DROP_COUNT decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.PACKET_DROP_COUNT

### RTL-0340: Implement field PACKET_DROP_COUNT.value

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.PACKET_DROP_COUNT.fields.value
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PACKET_DROP_COUNT.fields.value.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=value; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PACKET_DROP_COUNT.fields.value
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - value reset behavior matches SSOT value 0
  - value access policy ro is implemented without read/write shortcuts
  - value readback returns implemented RTL state when readable
  - value write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PACKET_DROP_COUNT.fields.value

### RTL-0341: Implement CSR/register ASSEMBLY_DROP_COUNT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.ASSEMBLY_DROP_COUNT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ASSEMBLY_DROP_COUNT.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=ASSEMBLY_DROP_COUNT; width=32; reset=0; access=ro; offset=36.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ASSEMBLY_DROP_COUNT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - ASSEMBLY_DROP_COUNT width matches SSOT value 32
  - ASSEMBLY_DROP_COUNT reset behavior matches SSOT value 0
  - ASSEMBLY_DROP_COUNT access policy ro is implemented without read/write shortcuts
  - ASSEMBLY_DROP_COUNT decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.ASSEMBLY_DROP_COUNT

### RTL-0342: Implement field ASSEMBLY_DROP_COUNT.value

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.ASSEMBLY_DROP_COUNT.fields.value
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ASSEMBLY_DROP_COUNT.fields.value.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=value; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ASSEMBLY_DROP_COUNT.fields.value
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - value reset behavior matches SSOT value 0
  - value access policy ro is implemented without read/write shortcuts
  - value readback returns implemented RTL state when readable
  - value write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ASSEMBLY_DROP_COUNT.fields.value

### RTL-0343: Implement CSR/register SRAM_BASE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SRAM_BASE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SRAM_BASE.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=SRAM_BASE; width=32; reset=0; access=rw; offset=48.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SRAM_BASE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - SRAM_BASE width matches SSOT value 32
  - SRAM_BASE reset behavior matches SSOT value 0
  - SRAM_BASE access policy rw is implemented without read/write shortcuts
  - SRAM_BASE decode uses SSOT address/offset 48
- SSOT refs: registers.register_list.SRAM_BASE

### RTL-0344: Implement field SRAM_BASE.base_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SRAM_BASE.fields.base_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SRAM_BASE.fields.base_addr.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=base_addr; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SRAM_BASE.fields.base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - base_addr reset behavior matches SSOT value 0
  - base_addr access policy rw is implemented without read/write shortcuts
  - base_addr readback returns implemented RTL state when readable
  - base_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SRAM_BASE.fields.base_addr

### RTL-0345: Implement CSR/register SRAM_LIMIT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SRAM_LIMIT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SRAM_LIMIT.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=SRAM_LIMIT; width=32; reset=65536; access=rw; offset=52.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SRAM_LIMIT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - SRAM_LIMIT width matches SSOT value 32
  - SRAM_LIMIT reset behavior matches SSOT value 65536
  - SRAM_LIMIT access policy rw is implemented without read/write shortcuts
  - SRAM_LIMIT decode uses SSOT address/offset 52
- SSOT refs: registers.register_list.SRAM_LIMIT

### RTL-0346: Implement field SRAM_LIMIT.limit_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SRAM_LIMIT.fields.limit_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SRAM_LIMIT.fields.limit_addr.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=limit_addr; reset=65536; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SRAM_LIMIT.fields.limit_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - limit_addr reset behavior matches SSOT value 65536
  - limit_addr access policy rw is implemented without read/write shortcuts
  - limit_addr readback returns implemented RTL state when readable
  - limit_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SRAM_LIMIT.fields.limit_addr

### RTL-0347: Implement CSR/register Q_STATE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.Q_STATE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.Q_STATE.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=Q_STATE; width=32; reset=0; access=ro; offset=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.Q_STATE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - Q_STATE width matches SSOT value 32
  - Q_STATE reset behavior matches SSOT value 0
  - Q_STATE access policy ro is implemented without read/write shortcuts
  - Q_STATE decode uses SSOT address/offset 256
- SSOT refs: registers.register_list.Q_STATE

### RTL-0348: Implement field Q_STATE.ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_STATE.fields.ctx_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_STATE.fields.ctx_state.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_state; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_STATE.fields.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - ctx_state reset behavior matches SSOT value 0
  - ctx_state access policy ro is implemented without read/write shortcuts
  - ctx_state readback returns implemented RTL state when readable
  - ctx_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_STATE.fields.ctx_state

### RTL-0349: Implement field Q_STATE.ctx_valid

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_STATE.fields.ctx_valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_STATE.fields.ctx_valid.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_valid; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_STATE.fields.ctx_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - ctx_valid reset behavior matches SSOT value 0
  - ctx_valid access policy ro is implemented without read/write shortcuts
  - ctx_valid readback returns implemented RTL state when readable
  - ctx_valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_STATE.fields.ctx_valid

### RTL-0350: Implement field Q_STATE.ctx_error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_STATE.fields.ctx_error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_STATE.fields.ctx_error.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_error; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_STATE.fields.ctx_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - ctx_error reset behavior matches SSOT value 0
  - ctx_error access policy ro is implemented without read/write shortcuts
  - ctx_error readback returns implemented RTL state when readable
  - ctx_error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_STATE.fields.ctx_error

### RTL-0351: Implement field Q_STATE.ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_STATE.fields.ctx_last_drop_reason
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_STATE.fields.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=ctx_last_drop_reason; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_STATE.fields.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - ctx_last_drop_reason reset behavior matches SSOT value 0
  - ctx_last_drop_reason access policy ro is implemented without read/write shortcuts
  - ctx_last_drop_reason readback returns implemented RTL state when readable
  - ctx_last_drop_reason write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_STATE.fields.ctx_last_drop_reason

### RTL-0352: Implement field Q_STATE.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_STATE.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_STATE.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_STATE.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_STATE.fields.reserved

### RTL-0353: Implement CSR/register Q_KEY

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.Q_KEY
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.Q_KEY.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=Q_KEY; width=32; reset=0; access=ro; offset=260.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.Q_KEY
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - Q_KEY width matches SSOT value 32
  - Q_KEY reset behavior matches SSOT value 0
  - Q_KEY access policy ro is implemented without read/write shortcuts
  - Q_KEY decode uses SSOT address/offset 260
- SSOT refs: registers.register_list.Q_KEY

### RTL-0354: Implement field Q_KEY.source_eid

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.source_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.source_eid.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=source_eid; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - source_eid reset behavior matches SSOT value 0
  - source_eid access policy ro is implemented without read/write shortcuts
  - source_eid readback returns implemented RTL state when readable
  - source_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.source_eid

### RTL-0355: Implement field Q_KEY.destination_eid

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.destination_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.destination_eid.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=destination_eid; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.destination_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - destination_eid reset behavior matches SSOT value 0
  - destination_eid access policy ro is implemented without read/write shortcuts
  - destination_eid readback returns implemented RTL state when readable
  - destination_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.destination_eid

### RTL-0356: Implement field Q_KEY.tag_owner

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.tag_owner
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.tag_owner.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=tag_owner; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - tag_owner reset behavior matches SSOT value 0
  - tag_owner access policy ro is implemented without read/write shortcuts
  - tag_owner readback returns implemented RTL state when readable
  - tag_owner write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.tag_owner

### RTL-0357: Implement field Q_KEY.message_tag

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.message_tag
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.message_tag.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=message_tag; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - message_tag reset behavior matches SSOT value 0
  - message_tag access policy ro is implemented without read/write shortcuts
  - message_tag readback returns implemented RTL state when readable
  - message_tag write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.message_tag

### RTL-0358: Implement field Q_KEY.message_type

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.message_type
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.message_type.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=message_type; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.message_type
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - message_type reset behavior matches SSOT value 0
  - message_type access policy ro is implemented without read/write shortcuts
  - message_type readback returns implemented RTL state when readable
  - message_type write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.message_type

### RTL-0359: Implement field Q_KEY.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_KEY.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_KEY.fields.reserved.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_KEY.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_KEY.fields.reserved

### RTL-0360: Implement CSR/register Q_PAYLOAD_BASE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.Q_PAYLOAD_BASE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.Q_PAYLOAD_BASE.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=Q_PAYLOAD_BASE; width=32; reset=0; access=ro; offset=264.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_BASE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - Q_PAYLOAD_BASE width matches SSOT value 32
  - Q_PAYLOAD_BASE reset behavior matches SSOT value 0
  - Q_PAYLOAD_BASE access policy ro is implemented without read/write shortcuts
  - Q_PAYLOAD_BASE decode uses SSOT address/offset 264
- SSOT refs: registers.register_list.Q_PAYLOAD_BASE

### RTL-0361: Implement field Q_PAYLOAD_BASE.payload_base_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_PAYLOAD_BASE.fields.payload_base_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_PAYLOAD_BASE.fields.payload_base_addr.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=payload_base_addr; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_BASE.fields.payload_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - payload_base_addr reset behavior matches SSOT value 0
  - payload_base_addr access policy ro is implemented without read/write shortcuts
  - payload_base_addr readback returns implemented RTL state when readable
  - payload_base_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_PAYLOAD_BASE.fields.payload_base_addr

### RTL-0362: Implement CSR/register Q_PAYLOAD_COUNT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.Q_PAYLOAD_COUNT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.Q_PAYLOAD_COUNT.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=Q_PAYLOAD_COUNT; width=32; reset=0; access=ro; offset=268.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_COUNT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - Q_PAYLOAD_COUNT width matches SSOT value 32
  - Q_PAYLOAD_COUNT reset behavior matches SSOT value 0
  - Q_PAYLOAD_COUNT access policy ro is implemented without read/write shortcuts
  - Q_PAYLOAD_COUNT decode uses SSOT address/offset 268
- SSOT refs: registers.register_list.Q_PAYLOAD_COUNT

### RTL-0363: Implement field Q_PAYLOAD_COUNT.payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_PAYLOAD_COUNT.fields.payload_byte_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_PAYLOAD_COUNT.fields.payload_byte_count.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=payload_byte_count; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_COUNT.fields.payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - payload_byte_count reset behavior matches SSOT value 0
  - payload_byte_count access policy ro is implemented without read/write shortcuts
  - payload_byte_count readback returns implemented RTL state when readable
  - payload_byte_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_PAYLOAD_COUNT.fields.payload_byte_count

### RTL-0364: Implement field Q_PAYLOAD_COUNT.partial_next_lane

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_next_lane
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_next_lane.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via registers.register_list.
SSOT item context: name=partial_next_lane; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_COUNT.fields.partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
  - partial_next_lane reset behavior matches SSOT value 0
  - partial_next_lane access policy ro is implemented without read/write shortcuts
  - partial_next_lane readback returns implemented RTL state when readable
  - partial_next_lane write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_next_lane
