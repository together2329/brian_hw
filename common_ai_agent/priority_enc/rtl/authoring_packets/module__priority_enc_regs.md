# RTL Authoring Packet: module__priority_enc_regs

- Kind: module
- Owner module: priority_enc_regs
- Owner file: rtl/priority_enc_regs.sv
- Task count: 12
- Required tasks: 12

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: registers, registers.register_list
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=4
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 23 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - priority_enc_regs.PADDR <= PADDR (observed_named_port_map)
  - priority_enc_regs.PCLK <= PCLK (observed_named_port_map)
  - priority_enc_regs.PENABLE <= PENABLE (observed_named_port_map)
  - priority_enc_regs.PRDATA <= PRDATA (observed_named_port_map)
  - priority_enc_regs.PREADY <= PREADY (observed_named_port_map)
  - priority_enc_regs.PRESETn <= PRESETn (observed_named_port_map)
  - priority_enc_regs.PSEL <= PSEL (observed_named_port_map)
  - priority_enc_regs.PSLVERR <= PSLVERR (observed_named_port_map)

## Tasks

### RTL-0027: Implement APB-lite register block

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Decode APB addresses 0x000/0x004/0x008; implement CTRL, MASK, STATUS registers with declared fields and reset values. PREADY tied high. PSLVERR on bad addr.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Register block compiles and passes APB protocol assertions
  - All register reset values match SSOT
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - Semantic source_refs covered: cycle_model.handshake_rules, registers.register_list
- SSOT refs: cycle_model.handshake_rules, registers.register_list, workflow_todos.rtl-gen[0]

### RTL-0074: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=CTRL; width=32; reset=1; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 1
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0075: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=enable; reset=1; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - enable reset behavior matches SSOT value 1
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0076: Implement field CTRL.rsvd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.rsvd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.rsvd.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=rsvd; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.rsvd
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - rsvd reset behavior matches SSOT value 0
  - rsvd access policy ro is implemented without read/write shortcuts
  - rsvd readback returns implemented RTL state when readable
  - rsvd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.rsvd

### RTL-0077: Implement CSR/register MASK

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.MASK
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.MASK.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=MASK; width=32; reset=0; access=rw; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.MASK
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - MASK width matches SSOT value 32
  - MASK reset behavior matches SSOT value 0
  - MASK access policy rw is implemented without read/write shortcuts
  - MASK decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.MASK

### RTL-0078: Implement field MASK.mask

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.MASK.fields.mask
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.MASK.fields.mask.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=mask; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.MASK.fields.mask
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - mask reset behavior matches SSOT value 0
  - mask access policy rw is implemented without read/write shortcuts
  - mask readback returns implemented RTL state when readable
  - mask write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.MASK.fields.mask

### RTL-0079: Implement field MASK.rsvd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.MASK.fields.rsvd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.MASK.fields.rsvd.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=rsvd; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.MASK.fields.rsvd
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - rsvd reset behavior matches SSOT value 0
  - rsvd access policy ro is implemented without read/write shortcuts
  - rsvd readback returns implemented RTL state when readable
  - rsvd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.MASK.fields.rsvd

### RTL-0080: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0081: Implement field STATUS.index

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.index
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.index.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=index; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.index
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - index reset behavior matches SSOT value 0
  - index access policy ro is implemented without read/write shortcuts
  - index readback returns implemented RTL state when readable
  - index write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.index

### RTL-0082: Implement field STATUS.valid

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.valid.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=valid; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.valid
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - valid reset behavior matches SSOT value 0
  - valid access policy ro is implemented without read/write shortcuts
  - valid readback returns implemented RTL state when readable
  - valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.valid

### RTL-0083: Implement field STATUS.rsvd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rsvd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rsvd.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via registers.register_list.
SSOT item context: name=rsvd; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rsvd
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
  - rsvd reset behavior matches SSOT value 0
  - rsvd access policy ro is implemented without read/write shortcuts
  - rsvd readback returns implemented RTL state when readable
  - rsvd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rsvd

### RTL-0099: Prove module priority_enc_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.priority_enc_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.priority_enc_regs.module_equivalence.
Owner: priority_enc_regs in rtl/priority_enc_regs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.priority_enc_regs.module_equivalence
  - Primary implementation evidence is in rtl/priority_enc_regs.sv
- SSOT refs: sub_modules.priority_enc_regs.module_equivalence
