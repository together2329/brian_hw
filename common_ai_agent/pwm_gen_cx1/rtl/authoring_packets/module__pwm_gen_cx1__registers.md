# RTL Authoring Packet: module__pwm_gen_cx1__registers

- Kind: module
- Owner module: pwm_gen_cx1
- Owner file: rtl/pwm_gen_cx1.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: function_model, function_model.transactions, function_model.transactions.FM_TICK, function_model.transactions.FM_WRITE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 8/18 section=registers task_limit=48
- Slice rule: Owner module pwm_gen_cx1 is split into 18 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0062: Implement CSR/register DUTY

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DUTY
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DUTY.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via registers.register_list.
SSOT item context: name=DUTY; width=8; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DUTY
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - DUTY width matches SSOT value 8
  - DUTY reset behavior matches SSOT value 0
  - DUTY access policy rw is implemented without read/write shortcuts
  - DUTY decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.DUTY

### RTL-0063: Implement field DUTY.duty

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DUTY.fields.duty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DUTY.fields.duty.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via registers.register_list.
SSOT item context: name=duty; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DUTY.fields.duty
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
  - duty reset behavior matches SSOT value 0
  - duty access policy rw is implemented without read/write shortcuts
  - duty readback returns implemented RTL state when readable
  - duty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DUTY.fields.duty
