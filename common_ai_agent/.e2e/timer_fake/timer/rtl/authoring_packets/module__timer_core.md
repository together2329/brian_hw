# RTL Authoring Packet: module__timer_core

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
- Task count: 40
- Required tasks: 40

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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, decomposition, features, fsm, fsm.control, function_model, function_model.invariants, function_model.state_variables, function_model.transactions, function_model.transactions.FM_PRIMARY, registers, registers.architectural_state.accepted_count
- SSOT connection contracts:
  - timer_core.clk <= clk (integration.connections[0])
  - timer_core.rst_n <= rst_n (integration.connections[1])
  - timer_core.valid <= valid (integration.connections[2])
  - timer_core.data_in <= data_in (integration.connections[3])
  - timer_core.ready <= ready (integration.connections[4])
  - timer_core.result <= result (integration.connections[5])
  - timer_core.result_valid <= result_valid (integration.connections[6])

## Tasks

### RTL-0020: Implement rule_double from the SSOT function and cycle model

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Capture accepted data_in, produce result=data_in*2 at the declared cycle latency, and expose enough DUT evidence for FL-vs-RTL comparison.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: timer_core in rtl/timer_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_RULE_DOUBLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL updates only on the declared valid/ready acceptance event
  - RTL observed result equals FunctionalModel.apply for RULE_DOUBLE
  - DUT-only compile/lint and rtl_todo_plan audit pass after the final edit
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/timer_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.transactions.RULE_DOUBLE
- SSOT refs: cycle_model.pipeline, function_model.transactions.RULE_DOUBLE, workflow_todos.rtl-gen[0]

### RTL-0030: Implement RTL state owner for FL state accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.accepted_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.accepted_count.
Owner: timer_core in rtl/timer_core.sv via function_model.state_variables.
SSOT item context: name=accepted_count; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.accepted_count
  - Primary implementation evidence is in rtl/timer_core.sv
  - accepted_count width matches SSOT value 8
  - accepted_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.accepted_count

### RTL-0031: Implement transaction FM_PRIMARY

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PRIMARY
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PRIMARY.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: id=FM_PRIMARY; name=primary_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: function_model.transactions.FM_PRIMARY

### RTL-0032: Implement precondition for FM_PRIMARY: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_0.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=rst_n is deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.preconditions.precondition_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.preconditions.precondition_0

### RTL-0033: Implement precondition for FM_PRIMARY: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.preconditions.precondition_1.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=valid is high.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.preconditions.precondition_1
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.preconditions.precondition_1

### RTL-0034: Implement output for FM_PRIMARY: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_0.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: value=result.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_0

### RTL-0035: Implement output for FM_PRIMARY: accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.accepted_count.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: state=accepted_count; expr=accepted_count + 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.accepted_count
  - Primary implementation evidence is in rtl/timer_core.sv
  - function_model.transactions.FM_PRIMARY.outputs.accepted_count RTL expression implements SSOT expression accepted_count + 1
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.accepted_count

### RTL-0036: Implement output rule for FM_PRIMARY: result

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.result
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.result.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: name=result; port=result; expr=value * 2; width=9.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.result
  - Primary implementation evidence is in rtl/timer_core.sv
  - result width matches SSOT value 9
  - result RTL expression implements SSOT expression value * 2
  - DUT port result is the implementation/observation point for result
  - result is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.result

### RTL-0037: Implement state update for FM_PRIMARY: accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PRIMARY.state_updates.accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.state_updates.accepted_count.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: name=accepted_count; expr=accepted_count + 1; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.state_updates.accepted_count
  - Primary implementation evidence is in rtl/timer_core.sv
  - accepted_count width matches SSOT value 8
  - accepted_count RTL expression implements SSOT expression accepted_count + 1
  - accepted_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PRIMARY.state_updates.accepted_count

### RTL-0038: Implement side effect for FM_PRIMARY: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0.
Owner: timer_core in rtl/timer_core.sv via function_model.transactions.FM_PRIMARY.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["result"]; signal=["accepted_count increments on each sampled transaction", "value"]; state=["accepted_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - DUT port ["result"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0

### RTL-0039: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: timer_core in rtl/timer_core.sv via function_model.invariants.
SSOT item context: port=["value", "result"]; signal=No result is produced before reset is released..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - DUT port ["value", "result"] is the implementation/observation point for ["value", "result"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0040: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: timer_core in rtl/timer_core.sv via function_model.invariants.
SSOT item context: port=["value", "result"]; signal=Each accepted valid transaction produces exactly one result_valid observation.; state=["accepted_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/timer_core.sv
  - DUT port ["value", "result"] is the implementation/observation point for ["value", "result"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0041: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: timer_core in rtl/timer_core.sv via function_model.invariants.
SSOT item context: port=["value", "result"]; signal=The result value is derived only from the sampled input transaction..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/timer_core.sv
  - DUT port ["value", "result"] is the implementation/observation point for ["value", "result"]
- SSOT refs: function_model.invariants.invariant_2

### RTL-0042: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0043: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0044: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0045: Implement handshake rule: valid_sample

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.valid_sample
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.valid_sample.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: name=valid_sample.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.valid_sample
  - Primary implementation evidence is in rtl/timer_core.sv
  - valid_sample appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.valid_sample

### RTL-0046: Implement pipeline stage: S0_SAMPLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_SAMPLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_SAMPLE.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=S0_SAMPLE; action=Sample data_in when valid is high.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_SAMPLE
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.S0_SAMPLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_SAMPLE

### RTL-0047: Implement pipeline stage: S1_RESULT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_RESULT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_RESULT.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=S1_RESULT; action=Drive result and result_valid for the sampled value.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_RESULT
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.S1_RESULT timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_RESULT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_RESULT

### RTL-0048: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=Transactions are observed in the same order they are sampled..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0049: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=Reset clears pending valid output before any new transaction is accepted..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0050: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=ready remains asserted in this one-deep sample rule IP..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0051: Implement architectural state accepted_count

- Priority: high
- Required: True
- Status: pass
- Category: registers.architectural_state
- Source ref: registers.architectural_state.accepted_count
- Detail: Architectural state listed outside the register map still needs RTL storage and reset/update ownership.
SSOT ref: registers.architectural_state.accepted_count.
Owner: timer_core in rtl/timer_core.sv via registers.architectural_state.accepted_count.
SSOT item context: name=accepted_count; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State storage is present in RTL
  - Reset/update behavior matches SSOT
  - State is observable if required by registers/debug/coverage
  - Traceability keeps source_ref registers.architectural_state.accepted_count
  - Primary implementation evidence is in rtl/timer_core.sv
  - accepted_count reset behavior matches SSOT value 0
- SSOT refs: registers.architectural_state.accepted_count

### RTL-0052: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: timer_core in rtl/timer_core.sv via fsm.control.
SSOT item context: value=S0_SAMPLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0053: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: timer_core in rtl/timer_core.sv via fsm.control.
SSOT item context: value=S1_RESULT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0054: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: timer_core in rtl/timer_core.sv via fsm.control.
SSOT item context: from=S0_SAMPLE; to=S1_RESULT; condition=valid; action=Latch input value..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: valid
  - fsm.control.transitions.transition_0 transition path S0_SAMPLE -> S1_RESULT is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0055: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: timer_core in rtl/timer_core.sv via fsm.control.
SSOT item context: from=S1_RESULT; to=S0_SAMPLE; condition=next cycle; action=Emit result_valid..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: next cycle
  - fsm.control.transitions.transition_1 transition path S1_RESULT -> S0_SAMPLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0056: Implement feature double_value

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.double_value
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.double_value.
Owner: timer_core in rtl/timer_core.sv via features.
SSOT item context: name=double_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.double_value
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: features.double_value

### RTL-0057: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: timer_core in rtl/timer_core.sv via dataflow.sequence.
SSOT item context: value=Sample data_in when valid is asserted after reset release..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0058: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: timer_core in rtl/timer_core.sv via dataflow.sequence.
SSOT item context: value=Compute result as sampled value multiplied by two..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0059: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: timer_core in rtl/timer_core.sv via dataflow.sequence.
SSOT item context: value=Present result and result_valid on the next observable cycle..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0060: Implement dataflow ordering: ordering_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_0.
Owner: timer_core in rtl/timer_core.sv via dataflow.ordering.
SSOT item context: value=accepted request precedes result observation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: dataflow.ordering.ordering_0

### RTL-0079: Prove module timer_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.timer_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.timer_core.module_equivalence.
Owner: timer_core in rtl/timer_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.timer_core.module_equivalence
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: sub_modules.timer_core.module_equivalence

### RTL-0080: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC01; name=reset contract; expected=Architectural state, status, outputs, and debug observability match function_model reset outputs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Architectural state, status, outputs, and debug observability match function_model reset outputs.
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0081: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC02; name=primary approved behavior; expected=Externally observable result/status/side effects match the function_model primary transaction..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Externally observable result/status/side effects match the function_model primary transaction.
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0082: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC03; name=cycle handshake and backpressure; expected=Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
- SSOT refs: test_requirements.scenarios.SC03

### RTL-0083: Keep RTL observable for scenario SC04

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC04
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC04.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC04; name=error and recovery policy; expected=Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC04
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
- SSOT refs: test_requirements.scenarios.SC04

### RTL-0084: Keep RTL observable for scenario SC05

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC05
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC05.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC05; name=debug and trace observability; expected=Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC05
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
- SSOT refs: test_requirements.scenarios.SC05

### RTL-0085: Keep RTL observable for scenario SC06

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC06
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC06.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=SC06; name=function_model transaction FM_PRIMARY; expected=Outputs and side effects match `FM_PRIMARY` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC06
  - Primary implementation evidence is in rtl/timer_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_PRIMARY` exactly.
- SSOT refs: test_requirements.scenarios.SC06

### RTL-0086: Provide RTL evidence for coverage bin FCOV_RULE_DOUBLE

- Priority: normal
- Required: True
- Status: pass
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE.
Owner: timer_core in rtl/timer_core.sv via test_requirements.
SSOT item context: id=FCOV_RULE_DOUBLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
  - Primary implementation evidence is in rtl/timer_core.sv
  - FCOV_RULE_DOUBLE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
