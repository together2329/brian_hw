# RTL Authoring Packet: module__priority_enc_core

- Kind: module
- Owner module: priority_enc_core
- Owner file: rtl/priority_enc_core.sv
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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, function_model, function_model.state_updates, function_model.transactions
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=4
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 21 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - priority_enc_core.PCLK <= PCLK (observed_named_port_map)
  - priority_enc_core.PRESETn <= PRESETn (observed_named_port_map)
  - priority_enc_core.data_in <= data_in (observed_named_port_map)
  - priority_enc_core.enable_i <= ctrl_enable (observed_named_port_map)
  - priority_enc_core.index_out <= core_index (observed_named_port_map)
  - priority_enc_core.mask_i <= mask (observed_named_port_map)
  - priority_enc_core.valid_out <= core_valid (observed_named_port_map)

## Tasks

### RTL-0028: Implement priority encoder datapath

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Combinational priority encoder tree finding highest set bit of masked data_in. Registered outputs index_out and valid_out, gated by CTRL.enable.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: priority_enc_core in rtl/priority_enc_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Core implements function_model.state_updates.index and valid
  - 1-cycle registered latency verified in sim
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.state_updates
- SSOT refs: cycle_model.pipeline, function_model.state_updates, workflow_todos.rtl-gen[1]

### RTL-0047: Implement RTL state owner for FL state enable

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.enable.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: name=enable; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.enable
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - enable reset behavior matches SSOT value 1
- SSOT refs: function_model.state_variables.enable

### RTL-0048: Implement RTL state owner for FL state mask

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.mask
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.mask.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: name=mask; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.mask
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - mask reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.mask

### RTL-0049: Implement RTL state owner for FL state index

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.index
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.index.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: name=index; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.index
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - index reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.index

### RTL-0050: Implement RTL state owner for FL state valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.valid
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.valid.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: name=valid; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.valid
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - valid reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.valid

### RTL-0051: Implement transaction FM_ENCODE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ENCODE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ENCODE.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: id=FM_ENCODE; name=priority_encode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.transactions.FM_ENCODE

### RTL-0052: Implement precondition for FM_ENCODE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ENCODE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.preconditions.precondition_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: value=CTRL.enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.transactions.FM_ENCODE.preconditions.precondition_0

### RTL-0053: Implement input for FM_ENCODE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ENCODE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.inputs.input_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: value=data_in[N-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.inputs.input_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.transactions.FM_ENCODE.inputs.input_0

### RTL-0054: Implement output for FM_ENCODE: index_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ENCODE.outputs.index_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.outputs.index_out.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: name=index_out; port=index_out; expr=priority_index(data_in & ~MASK.mask); width=INDEX_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.outputs.index_out
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - index_out width matches SSOT value INDEX_WIDTH
  - index_out RTL expression implements SSOT expression priority_index(data_in & ~MASK.mask)
  - DUT port index_out is the implementation/observation point for index_out
- SSOT refs: function_model.transactions.FM_ENCODE.outputs.index_out

### RTL-0055: Implement output for FM_ENCODE: valid_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ENCODE.outputs.valid_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.outputs.valid_out.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: name=valid_out; port=valid_out; expr=|(data_in & ~MASK.mask); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.outputs.valid_out
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - valid_out width matches SSOT value 1
  - valid_out RTL expression implements SSOT expression |(data_in & ~MASK.mask)
  - DUT port valid_out is the implementation/observation point for valid_out
- SSOT refs: function_model.transactions.FM_ENCODE.outputs.valid_out

### RTL-0056: Implement output rule for FM_ENCODE: index_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ENCODE.output_rules.index_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.output_rules.index_out.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: name=index_out; port=index_out; expr=for i=N-1 downto 0: if ((data_in[i] & ~mask[i]) == 1) return i; return 0; width=INDEX_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.output_rules.index_out
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - index_out width matches SSOT value INDEX_WIDTH
  - index_out RTL expression implements SSOT expression for i=N-1 downto 0: if ((data_in[i] & ~mask[i]) == 1) return i; return 0
  - DUT port index_out is the implementation/observation point for index_out
  - index_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ENCODE.output_rules.index_out

### RTL-0057: Implement output rule for FM_ENCODE: valid_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ENCODE.output_rules.valid_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.output_rules.valid_out.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: name=valid_out; port=valid_out; expr=|(data_in & ~mask); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.output_rules.valid_out
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - valid_out width matches SSOT value 1
  - valid_out RTL expression implements SSOT expression |(data_in & ~mask)
  - DUT port valid_out is the implementation/observation point for valid_out
  - valid_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ENCODE.output_rules.valid_out

### RTL-0058: Implement side effect for FM_ENCODE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ENCODE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.side_effects.side_effect_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: value=STATUS.index updates to current index_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.transactions.FM_ENCODE.side_effects.side_effect_0

### RTL-0059: Implement side effect for FM_ENCODE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ENCODE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.side_effects.side_effect_1.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: value=STATUS.valid updates to current valid_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.transactions.FM_ENCODE.side_effects.side_effect_1

### RTL-0060: Implement error case for FM_ENCODE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ENCODE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.error_cases.error_case_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: condition=PADDR accesses undefined register offset.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - function_model.transactions.FM_ENCODE.error_cases.error_case_0 condition is implemented as RTL control logic: PADDR accesses undefined register offset
- SSOT refs: function_model.transactions.FM_ENCODE.error_cases.error_case_0

### RTL-0061: Implement error case for FM_ENCODE: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ENCODE.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ENCODE.error_cases.error_case_1.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.transactions.
SSOT item context: condition=Write to read-only STATUS field.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ENCODE.error_cases.error_case_1
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - function_model.transactions.FM_ENCODE.error_cases.error_case_1 condition is implemented as RTL control logic: Write to read-only STATUS field
- SSOT refs: function_model.transactions.FM_ENCODE.error_cases.error_case_1

### RTL-0062: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: value=When enable==0, index_out and valid_out are both 0 regardless of inputs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0063: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: priority_enc_core in rtl/priority_enc_core.sv via function_model.
SSOT item context: value=When multiple inputs are asserted, index_out always reflects the highest-numbered (highest-priority) bit..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0064: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0065: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0066: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0067: Implement handshake rule: apb_csr

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.apb_csr
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.apb_csr.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: signal=apb_csr.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.apb_csr
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.handshake_rules.apb_csr appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.apb_csr

### RTL-0068: Implement pipeline stage: S0_COMB

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_COMB
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_COMB.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.pipeline.
SSOT item context: stage=S0_COMB; action=Combinational priority encode: masked_data = data_in & ~MASK; find highest set bit; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_COMB
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.pipeline.S0_COMB timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_COMB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_COMB

### RTL-0069: Implement pipeline stage: S1_REG

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_REG
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_REG.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.pipeline.
SSOT item context: stage=S1_REG; action=Register index_out and valid_out on PCLK rising edge when CTRL.enable==1; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_REG
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.pipeline.S1_REG timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_REG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_REG

### RTL-0070: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: value=Output register update occurs on PCLK rising edge after combinational priority logic settles..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0071: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: value=APB register writes take effect on the PCLK cycle after PENABLE handshake completes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0072: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: value=No backpressure on priority inputs; outputs are always valid or zero..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0073: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: priority_enc_core in rtl/priority_enc_core.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to cycle_model pipeline stages S0_COMB and S1_REG..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/priority_enc_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0100: Prove module priority_enc_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.priority_enc_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.priority_enc_core.module_equivalence.
Owner: priority_enc_core in rtl/priority_enc_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.priority_enc_core.module_equivalence
  - Primary implementation evidence is in rtl/priority_enc_core.sv
- SSOT refs: sub_modules.priority_enc_core.module_equivalence
