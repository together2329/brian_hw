# RTL Authoring Packet: module__gpio_input_sampler

- Kind: module
- Owner module: gpio_input_sampler
- Owner file: rtl/gpio_input_sampler.sv
- Task count: 5
- Required tasks: 5

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
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.S2_SAMPLE_INPUTS, function_model, function_model.transactions.FM2_SAMPLE_INPUTS, registers, registers.register_list.DIN_Q
- SSOT connection contracts:
  - gpio_input_sampler.clk <= clk (integration.connections[6])
  - gpio_input_sampler.rst_n <= rst_n (integration.connections[7])
  - gpio_input_sampler.pad_in <= pad_in (integration.connections[8])
  - gpio_input_sampler.dir_q <= dir_q (integration.connections[9])
  - gpio_input_sampler.din_q <= din_q (integration.connections[10])

## Tasks

### RTL-0021: Implement direction-masked input sampling

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Update din_q only on input-configured bits at rising edge
SSOT ref: workflow_todos.rtl-gen[1].
Owner: gpio_input_sampler in rtl/gpio_input_sampler.sv via workflow_todos.owner.
SSOT item context: id=RTL_GPIO_SAMPLER.
- Current reason: Owner RTL file is missing: rtl/gpio_input_sampler.sv.
- Criteria:
  - din_q[i] samples pad_in[i] when dir_q[i]==0
  - din_q[i] holds when dir_q[i]==1
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/gpio_input_sampler.sv
  - Semantic source_refs covered: cycle_model.pipeline.S2_SAMPLE_INPUTS, function_model.transactions.FM2_SAMPLE_INPUTS
- SSOT refs: cycle_model.pipeline.S2_SAMPLE_INPUTS, function_model.transactions.FM2_SAMPLE_INPUTS, workflow_todos.rtl-gen[1]

### RTL-0089: Implement pipeline stage: S2_SAMPLE_INPUTS

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_SAMPLE_INPUTS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_SAMPLE_INPUTS.
Owner: gpio_input_sampler in rtl/gpio_input_sampler.sv via cycle_model.pipeline.S2_SAMPLE_INPUTS.
SSOT item context: stage=S2_SAMPLE_INPUTS; action=Sample pad_in into din_q only for dir_q=0 bits; cycle=N.
- Current reason: Owner RTL file is missing: rtl/gpio_input_sampler.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_SAMPLE_INPUTS
  - Primary implementation evidence is in rtl/gpio_input_sampler.sv
  - cycle_model.pipeline.S2_SAMPLE_INPUTS timing uses SSOT cycle/latency N
  - cycle_model.pipeline.S2_SAMPLE_INPUTS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_SAMPLE_INPUTS

### RTL-0099: Implement CSR/register DIN_Q

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DIN_Q
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DIN_Q.
Owner: gpio_input_sampler in rtl/gpio_input_sampler.sv via registers.register_list.DIN_Q.
SSOT item context: name=DIN_Q; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/gpio_input_sampler.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DIN_Q
  - Primary implementation evidence is in rtl/gpio_input_sampler.sv
  - DIN_Q width matches SSOT value 32
  - DIN_Q reset behavior matches SSOT value 0
  - DIN_Q access policy ro is implemented without read/write shortcuts
  - DIN_Q decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.DIN_Q

### RTL-0100: Implement field DIN_Q.din

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DIN_Q.fields.din
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIN_Q.fields.din.
Owner: gpio_input_sampler in rtl/gpio_input_sampler.sv via registers.register_list.DIN_Q.
SSOT item context: name=din; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/gpio_input_sampler.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIN_Q.fields.din
  - Primary implementation evidence is in rtl/gpio_input_sampler.sv
  - din reset behavior matches SSOT value 0
  - din access policy ro is implemented without read/write shortcuts
  - din readback returns implemented RTL state when readable
  - din write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIN_Q.fields.din

### RTL-0133: Prove module gpio_input_sampler is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.gpio_input_sampler.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.gpio_input_sampler.module_equivalence.
Owner: gpio_input_sampler in rtl/gpio_input_sampler.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/gpio_input_sampler.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.gpio_input_sampler.module_equivalence
  - Primary implementation evidence is in rtl/gpio_input_sampler.sv
- SSOT refs: sub_modules.gpio_input_sampler.module_equivalence
