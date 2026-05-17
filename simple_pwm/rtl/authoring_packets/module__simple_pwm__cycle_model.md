# RTL Authoring Packet: module__simple_pwm__cycle_model

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 6/14 section=cycle_model task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0057: Implement cycle-model clock

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0058: Implement cycle-model reset

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0059: Implement cycle-model latency

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0060: Implement handshake rule: pwm_out

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pwm_out
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: signal=pwm_out.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.handshake_rules.pwm_out appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pwm_out

### RTL-0061: Implement pipeline stage: S0_COUNTER_UPDATE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_COUNTER_UPDATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_COUNTER_UPDATE.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: stage=S0_COUNTER_UPDATE; action=Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0; cycle=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_COUNTER_UPDATE
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.pipeline.S0_COUNTER_UPDATE timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S0_COUNTER_UPDATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_COUNTER_UPDATE

### RTL-0062: Implement pipeline stage: S1_COMPARE_OUTPUT

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_COMPARE_OUTPUT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_COMPARE_OUTPUT.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: stage=S1_COMPARE_OUTPUT; action=Compare counter with duty_cycle; drive pwm_out accordingly; cycle=1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_COMPARE_OUTPUT
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.pipeline.S1_COMPARE_OUTPUT timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_COMPARE_OUTPUT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_COMPARE_OUTPUT

### RTL-0063: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: value=Counter update and output comparison occur in the same clock cycle..
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0064: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: value=counter value is observable via internal state.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0065: Implement observability signal: observability_signal_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_1.
Owner: simple_pwm in rtl/simple_pwm.sv via cycle_model.
SSOT item context: value=pwm_out is the primary observable output.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - cycle_model.observability.observability_signal_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_1
