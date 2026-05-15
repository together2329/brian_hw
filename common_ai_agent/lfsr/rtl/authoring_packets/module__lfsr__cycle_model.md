# RTL Authoring Packet: module__lfsr__cycle_model

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 10
- Required tasks: 10

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
- LLM-actionable open tasks: 10
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 6/13 section=cycle_model task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0073: Implement cycle-model clock

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0074: Implement cycle-model reset

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0075: Implement cycle-model latency

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0076: Implement handshake rule: PSEL/PENABLE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PSEL_PENABLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PSEL_PENABLE.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: signal=PSEL/PENABLE.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PSEL_PENABLE
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.handshake_rules.PSEL_PENABLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PSEL_PENABLE

### RTL-0077: Implement pipeline stage: S0_IDLE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_IDLE.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: stage=S0_IDLE; action=Hold state; sample APB decode and enable; cycle=0.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_IDLE
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.pipeline.S0_IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_IDLE

### RTL-0078: Implement pipeline stage: S1_STEP

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_STEP
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_STEP.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: stage=S1_STEP; action=Compute next LFSR state if enabled; update prbs_out/prbs_bit/prbs_valid; cycle=1.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_STEP
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.pipeline.S1_STEP timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_STEP appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_STEP

### RTL-0079: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: value=APB write to SEED takes effect on the same cycle as the completing PREADY..
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0080: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: value=LFSR state update occurs on the rising edge after enable is sampled high..
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0081: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: value=No backpressure on PRBS output; downstream must sample prbs_out/prbs_bit on appropriate cycles..
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0082: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: lfsr in rtl/lfsr.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/lfsr.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
