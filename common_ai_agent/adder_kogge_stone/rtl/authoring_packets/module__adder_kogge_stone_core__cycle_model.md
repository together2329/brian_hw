# RTL Authoring Packet: module__adder_kogge_stone_core__cycle_model

- Kind: module
- Owner module: adder_kogge_stone_core
- Owner file: rtl/adder_kogge_stone_core.sv
- Task count: 14
- Required tasks: 14

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
- Owner refs: cycle_model, cycle_model.pipeline, features, features.ks_addition, fsm, fsm.adder_fsm, function_model, function_model.state_updates, function_model.transactions, function_model.transactions.FM_ADD
- Module slice: 2/6 section=cycle_model task_limit=48
- Slice rule: Owner module adder_kogge_stone_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0075: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0076: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0077: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0078: Implement handshake rule: psel/penable

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.psel_penable
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.psel_penable.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: signal=psel/penable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.psel_penable
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.handshake_rules.psel_penable appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.psel_penable

### RTL-0079: Implement handshake rule: pready

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pready.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pready
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.handshake_rules.pready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pready

### RTL-0080: Implement handshake rule: pslverr

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pslverr
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pslverr.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: signal=pslverr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pslverr
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.handshake_rules.pslverr appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pslverr

### RTL-0081: Implement pipeline stage: S_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S_IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S_IDLE.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.pipeline.
SSOT item context: stage=S_IDLE; action=Wait for CONTROL.start or hold_mode=0 with valid shadow registers.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S_IDLE
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.pipeline.S_IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S_IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S_IDLE

### RTL-0082: Implement pipeline stage: S_COMPUTE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S_COMPUTE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S_COMPUTE.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.pipeline.
SSOT item context: stage=S_COMPUTE; action=Combinational Kogge-Stone prefix tree evaluates propagate/generate and produces sum/carry.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S_COMPUTE
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.pipeline.S_COMPUTE timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S_COMPUTE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S_COMPUTE

### RTL-0083: Implement pipeline stage: S_CAPTURE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S_CAPTURE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S_CAPTURE.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.pipeline.
SSOT item context: stage=S_CAPTURE; action=On posedge PCLK, output registers capture sum and carry; STATUS updates to done=1, busy=0.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S_CAPTURE
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.pipeline.S_CAPTURE timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S_CAPTURE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S_CAPTURE

### RTL-0084: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=APB write to A_DATA/B_DATA/CIN updates shadow before start is sampled..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0085: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=APB write to CONTROL.start must be visible in the same cycle as the APB completes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0086: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=Output register update occurs only on posedge PCLK..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0087: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=No backpressure on adder datapath; APB interface is zero-wait-state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0088: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
