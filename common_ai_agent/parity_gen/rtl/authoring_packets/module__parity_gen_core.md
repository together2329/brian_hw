# RTL Authoring Packet: module__parity_gen_core

- Kind: module
- Owner module: parity_gen_core
- Owner file: rtl/parity_gen_core.sv
- Task count: 29
- Required tasks: 29

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
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, features, function_model, function_model.transactions
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=2
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 23 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - parity_gen_core.PCLK <= PCLK (observed_named_port_map)
  - parity_gen_core.PRESETn <= PRESETn (observed_named_port_map)
  - parity_gen_core.check_enable <= check_enable (observed_named_port_map)
  - parity_gen_core.data_in <= data_in (observed_named_port_map)
  - parity_gen_core.enable <= enable (observed_named_port_map)
  - parity_gen_core.expected_parity <= expected_parity (observed_named_port_map)
  - parity_gen_core.parity_error <= parity_error (observed_named_port_map)
  - parity_gen_core.parity_mismatch_comb <= parity_mismatch_comb (observed_named_port_map)

## Tasks

### RTL-0027: Implement parity generation and checking datapath

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model transactions FM_GEN and FM_CHK, cycle_model timing, and ownership refs into RTL state/datapath/control logic in parity_gen_core.sv.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: parity_gen_core in rtl/parity_gen_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is present in parity_gen_core.sv
  - FunctionalModel expected result and RTL observed result can be compared for FM_GEN and FM_CHK
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.transactions
- SSOT refs: cycle_model.pipeline, function_model.transactions, workflow_todos.rtl-gen[0]

### RTL-0045: Implement RTL state owner for FL state control

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.control
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.control.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.
SSOT item context: name=control; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.control
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - control reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.control

### RTL-0046: Implement RTL state owner for FL state status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.
SSOT item context: name=status; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status

### RTL-0047: Implement transaction FM_GEN

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_GEN
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_GEN.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: id=FM_GEN; name=parity_generate.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_GEN
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_GEN

### RTL-0048: Implement precondition for FM_GEN: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_GEN.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_GEN.preconditions.precondition_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=control.enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_GEN.preconditions.precondition_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_GEN.preconditions.precondition_0

### RTL-0049: Implement input for FM_GEN: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_GEN.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_GEN.inputs.input_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=data_in[DATA_WIDTH-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_GEN.inputs.input_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_GEN.inputs.input_0

### RTL-0050: Implement output for FM_GEN: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_GEN.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_GEN.outputs.output_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=parity_out == XOR reduction of data_in.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_GEN.outputs.output_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_GEN.outputs.output_0

### RTL-0051: Implement transaction FM_CHK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_CHK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_CHK.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: id=FM_CHK; name=parity_check.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_CHK
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK

### RTL-0052: Implement precondition for FM_CHK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CHK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CHK.preconditions.precondition_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=control.check_enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CHK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK.preconditions.precondition_0

### RTL-0053: Implement input for FM_CHK: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CHK.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CHK.inputs.input_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=data_in[DATA_WIDTH-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CHK.inputs.input_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK.inputs.input_0

### RTL-0054: Implement input for FM_CHK: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CHK.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CHK.inputs.input_1.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=control.expected_parity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CHK.inputs.input_1
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK.inputs.input_1

### RTL-0055: Implement output for FM_CHK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CHK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CHK.outputs.output_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=parity_error == (XOR reduction of data_in) XOR control.expected_parity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CHK.outputs.output_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK.outputs.output_0

### RTL-0056: Implement side effect for FM_CHK: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CHK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CHK.side_effects.side_effect_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.transactions.
SSOT item context: value=status.parity_err_sticky set if parity_error == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CHK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.transactions.FM_CHK.side_effects.side_effect_0

### RTL-0057: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.
SSOT item context: value=parity_out is strictly a function of data_in and control.enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0058: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: parity_gen_core in rtl/parity_gen_core.sv via function_model.
SSOT item context: value=parity_error is strictly a function of data_in, control.expected_parity, and control.check_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0059: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0060: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0061: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.latency.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0062: Implement handshake rule: PSEL/PENABLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PSEL_PENABLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PSEL_PENABLE.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: signal=PSEL/PENABLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PSEL_PENABLE
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.handshake_rules.PSEL_PENABLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PSEL_PENABLE

### RTL-0063: Implement handshake rule: data_in

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.data_in
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.data_in.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: signal=data_in.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.data_in
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.handshake_rules.data_in appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.data_in

### RTL-0064: Implement pipeline stage: S0_SAMPLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_SAMPLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_SAMPLE.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: stage=S0_SAMPLE; action=Sample data_in and control register state; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_SAMPLE
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.pipeline.S0_SAMPLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_SAMPLE

### RTL-0065: Implement pipeline stage: S1_OUTPUT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_OUTPUT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_OUTPUT.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: stage=S1_OUTPUT; action=Drive parity_out and parity_error registered outputs; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_OUTPUT
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.pipeline.S1_OUTPUT timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_OUTPUT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_OUTPUT

### RTL-0066: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: value=Registered outputs parity_out and parity_error reflect data_in sampled in the previous cycle..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0067: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: value=None for data_in (always-on sampling). APB slave accepts every transfer with zero wait states..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0068: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: parity_gen_core in rtl/parity_gen_core.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/parity_gen_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0077: Implement feature Parity Generation

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Parity_Generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Parity_Generation.
Owner: parity_gen_core in rtl/parity_gen_core.sv via features.
SSOT item context: name=Parity Generation; output=parity_out single bit.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Parity_Generation
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: features.Parity_Generation

### RTL-0078: Implement feature Parity Checking

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Parity_Checking
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Parity_Checking.
Owner: parity_gen_core in rtl/parity_gen_core.sv via features.
SSOT item context: name=Parity Checking; output=parity_error single bit.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Parity_Checking
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: features.Parity_Checking

### RTL-0079: Implement feature APB-lite Configuration

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.APB_lite_Configuration
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.APB_lite_Configuration.
Owner: parity_gen_core in rtl/parity_gen_core.sv via features.
SSOT item context: name=APB-lite Configuration; output=Updated configuration registers.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.APB_lite_Configuration
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: features.APB_lite_Configuration

### RTL-0086: Prove module parity_gen_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.parity_gen_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.parity_gen_core.module_equivalence.
Owner: parity_gen_core in rtl/parity_gen_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.parity_gen_core.module_equivalence
  - Primary implementation evidence is in rtl/parity_gen_core.sv
- SSOT refs: sub_modules.parity_gen_core.module_equivalence
