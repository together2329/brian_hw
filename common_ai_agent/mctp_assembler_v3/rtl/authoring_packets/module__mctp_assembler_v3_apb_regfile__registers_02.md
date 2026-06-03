# RTL Authoring Packet: module__mctp_assembler_v3_apb_regfile__registers_02

- Kind: module
- Owner module: mctp_assembler_v3_apb_regfile
- Owner file: rtl/mctp_assembler_v3_apb_regfile.sv
- Task count: 25
- Required tasks: 25

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
- LLM-actionable open tasks: 25
- Human-locked open tasks: 0
- Owner refs: decomposition, error_handling, features, function_model.state_variables, interrupts, registers, registers.register_list
- Module slice: 3/7 section=registers task_limit=48
- Slice rule: Owner module mctp_assembler_v3_apb_regfile is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])

## Tasks

### RTL-0362: Implement field INTR_RAW_STATUS.raw

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTR_RAW_STATUS.fields.raw
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTR_RAW_STATUS.fields.raw.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=raw; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTR_RAW_STATUS.fields.raw
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - raw reset behavior matches SSOT value 0
  - raw access policy ro is implemented without read/write shortcuts
  - raw readback returns implemented RTL state when readable
  - raw write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTR_RAW_STATUS.fields.raw

### RTL-0363: Implement CSR/register INTR_ENABLE

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTR_ENABLE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTR_ENABLE.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=INTR_ENABLE; width=32; reset=0; access=rw; offset=260.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTR_ENABLE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - INTR_ENABLE width matches SSOT value 32
  - INTR_ENABLE reset behavior matches SSOT value 0
  - INTR_ENABLE access policy rw is implemented without read/write shortcuts
  - INTR_ENABLE decode uses SSOT address/offset 260
- SSOT refs: registers.register_list.INTR_ENABLE

### RTL-0364: Implement field INTR_ENABLE.enable

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTR_ENABLE.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTR_ENABLE.fields.enable.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTR_ENABLE.fields.enable
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTR_ENABLE.fields.enable

### RTL-0365: Implement CSR/register INTR_STATUS

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTR_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTR_STATUS.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=INTR_STATUS; width=32; reset=0; access=ro; offset=264.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTR_STATUS
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - INTR_STATUS width matches SSOT value 32
  - INTR_STATUS reset behavior matches SSOT value 0
  - INTR_STATUS access policy ro is implemented without read/write shortcuts
  - INTR_STATUS decode uses SSOT address/offset 264
- SSOT refs: registers.register_list.INTR_STATUS

### RTL-0366: Implement field INTR_STATUS.status

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTR_STATUS.fields.status
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTR_STATUS.fields.status.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=status; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTR_STATUS.fields.status
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - status reset behavior matches SSOT value 0
  - status access policy ro is implemented without read/write shortcuts
  - status readback returns implemented RTL state when readable
  - status write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTR_STATUS.fields.status

### RTL-0367: Implement CSR/register INTR_CLEAR

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.INTR_CLEAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTR_CLEAR.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=INTR_CLEAR; width=32; reset=0; access=rw; offset=268.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTR_CLEAR
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - INTR_CLEAR width matches SSOT value 32
  - INTR_CLEAR reset behavior matches SSOT value 0
  - INTR_CLEAR access policy rw is implemented without read/write shortcuts
  - INTR_CLEAR decode uses SSOT address/offset 268
- SSOT refs: registers.register_list.INTR_CLEAR

### RTL-0368: Implement field INTR_CLEAR.clear

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.INTR_CLEAR.fields.clear
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTR_CLEAR.fields.clear.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=clear; reset=0; access=w1c.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTR_CLEAR.fields.clear
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - clear reset behavior matches SSOT value 0
  - clear access policy w1c is implemented without read/write shortcuts
  - clear readback returns implemented RTL state when readable
  - clear write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTR_CLEAR.fields.clear

### RTL-0369: Implement CSR/register CNT_TLP_SEEN

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.CNT_TLP_SEEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CNT_TLP_SEEN.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=CNT_TLP_SEEN; width=32; reset=0; access=ro; offset=512.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CNT_TLP_SEEN
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - CNT_TLP_SEEN width matches SSOT value 32
  - CNT_TLP_SEEN reset behavior matches SSOT value 0
  - CNT_TLP_SEEN access policy ro is implemented without read/write shortcuts
  - CNT_TLP_SEEN decode uses SSOT address/offset 512
- SSOT refs: registers.register_list.CNT_TLP_SEEN

### RTL-0370: Implement field CNT_TLP_SEEN.count

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.CNT_TLP_SEEN.fields.count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CNT_TLP_SEEN.fields.count.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=count; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CNT_TLP_SEEN.fields.count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - count reset behavior matches SSOT value 0
  - count access policy ro is implemented without read/write shortcuts
  - count readback returns implemented RTL state when readable
  - count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CNT_TLP_SEEN.fields.count

### RTL-0371: Implement CSR/register DESC_VALID

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.DESC_VALID
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DESC_VALID.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=DESC_VALID; width=32; reset=0; access=ro; offset=768.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DESC_VALID
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - DESC_VALID width matches SSOT value 32
  - DESC_VALID reset behavior matches SSOT value 0
  - DESC_VALID access policy ro is implemented without read/write shortcuts
  - DESC_VALID decode uses SSOT address/offset 768
- SSOT refs: registers.register_list.DESC_VALID

### RTL-0372: Implement field DESC_VALID.descriptor_valid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.descriptor_valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.descriptor_valid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=descriptor_valid; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.descriptor_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_valid reset behavior matches SSOT value 0
  - descriptor_valid access policy ro is implemented without read/write shortcuts
  - descriptor_valid readback returns implemented RTL state when readable
  - descriptor_valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.descriptor_valid

### RTL-0373: Implement field DESC_VALID.completion_status

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.completion_status
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.completion_status.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=completion_status; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.completion_status
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - completion_status reset behavior matches SSOT value 0
  - completion_status access policy ro is implemented without read/write shortcuts
  - completion_status readback returns implemented RTL state when readable
  - completion_status write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.completion_status

### RTL-0374: Implement field DESC_VALID.source_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.source_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.source_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=source_eid; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - source_eid reset behavior matches SSOT value 0
  - source_eid access policy ro is implemented without read/write shortcuts
  - source_eid readback returns implemented RTL state when readable
  - source_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.source_eid

### RTL-0375: Implement field DESC_VALID.destination_eid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.destination_eid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.destination_eid.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=destination_eid; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.destination_eid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - destination_eid reset behavior matches SSOT value 0
  - destination_eid access policy ro is implemented without read/write shortcuts
  - destination_eid readback returns implemented RTL state when readable
  - destination_eid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.destination_eid

### RTL-0376: Implement field DESC_VALID.message_tag

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.message_tag
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.message_tag.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=message_tag; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - message_tag reset behavior matches SSOT value 0
  - message_tag access policy ro is implemented without read/write shortcuts
  - message_tag readback returns implemented RTL state when readable
  - message_tag write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.message_tag

### RTL-0377: Implement field DESC_VALID.tag_owner

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.tag_owner
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.tag_owner.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=tag_owner; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - tag_owner reset behavior matches SSOT value 0
  - tag_owner access policy ro is implemented without read/write shortcuts
  - tag_owner readback returns implemented RTL state when readable
  - tag_owner write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.tag_owner

### RTL-0378: Implement field DESC_VALID.message_type

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.message_type
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.message_type.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=message_type; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.message_type
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - message_type reset behavior matches SSOT value 0
  - message_type access policy ro is implemented without read/write shortcuts
  - message_type readback returns implemented RTL state when readable
  - message_type write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.message_type

### RTL-0379: Implement field DESC_VALID.context_id

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.context_id
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.context_id.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=context_id; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.context_id
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - context_id reset behavior matches SSOT value 0
  - context_id access policy ro is implemented without read/write shortcuts
  - context_id readback returns implemented RTL state when readable
  - context_id write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.context_id

### RTL-0380: Implement CSR/register DEBUG_CTX

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.DEBUG_CTX
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG_CTX.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=DEBUG_CTX; width=32; reset=0; access=ro; offset=896.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - DEBUG_CTX width matches SSOT value 32
  - DEBUG_CTX reset behavior matches SSOT value 0
  - DEBUG_CTX access policy ro is implemented without read/write shortcuts
  - DEBUG_CTX decode uses SSOT address/offset 896
- SSOT refs: registers.register_list.DEBUG_CTX

### RTL-0381: Implement field DEBUG_CTX.parser_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.parser_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.parser_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=parser_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.parser_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - parser_state reset behavior matches SSOT value 0
  - parser_state access policy ro is implemented without read/write shortcuts
  - parser_state readback returns implemented RTL state when readable
  - parser_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.parser_state

### RTL-0382: Implement field DEBUG_CTX.axi_wr_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.axi_wr_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.axi_wr_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=axi_wr_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.axi_wr_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - axi_wr_state reset behavior matches SSOT value 0
  - axi_wr_state access policy ro is implemented without read/write shortcuts
  - axi_wr_state readback returns implemented RTL state when readable
  - axi_wr_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.axi_wr_state

### RTL-0383: Implement field DEBUG_CTX.axi_rd_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.axi_rd_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.axi_rd_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=axi_rd_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.axi_rd_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - axi_rd_state reset behavior matches SSOT value 0
  - axi_rd_state access policy ro is implemented without read/write shortcuts
  - axi_rd_state readback returns implemented RTL state when readable
  - axi_rd_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.axi_rd_state

### RTL-0384: Implement field DEBUG_CTX.sram_pack_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.sram_pack_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.sram_pack_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_pack_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.sram_pack_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_pack_state reset behavior matches SSOT value 0
  - sram_pack_state access policy ro is implemented without read/write shortcuts
  - sram_pack_state readback returns implemented RTL state when readable
  - sram_pack_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.sram_pack_state

### RTL-0385: Implement field DEBUG_CTX.sram_read_state

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.sram_read_state
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.sram_read_state.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=sram_read_state; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.sram_read_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_read_state reset behavior matches SSOT value 0
  - sram_read_state access policy ro is implemented without read/write shortcuts
  - sram_read_state readback returns implemented RTL state when readable
  - sram_read_state write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.sram_read_state

### RTL-0386: Implement field DEBUG_CTX.selected_ctx

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.DEBUG_CTX.fields.selected_ctx
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_CTX.fields.selected_ctx.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=selected_ctx; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_CTX.fields.selected_ctx
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - selected_ctx reset behavior matches SSOT value 0
  - selected_ctx access policy ro is implemented without read/write shortcuts
  - selected_ctx readback returns implemented RTL state when readable
  - selected_ctx write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_CTX.fields.selected_ctx
