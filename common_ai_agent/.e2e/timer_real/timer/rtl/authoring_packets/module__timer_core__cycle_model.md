# RTL Authoring Packet: module__timer_core__cycle_model

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
- Task count: 19
- Required tasks: 19

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, dataflow.count_path, dataflow.irq_path, decomposition, features, fsm, function_model, function_model.state_variables, function_model.state_variables.count_q, function_model.state_variables.enable_q, function_model.state_variables.load_q, function_model.transactions.FM_DISABLED_HOLD
- Module slice: 2/8 section=cycle_model task_limit=48
- Slice rule: Owner module timer_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_core.pclk <= pclk (integration.connections[13])
  - timer_core.presetn <= presetn (integration.connections[14])
  - timer_core.load_q <= load_q (integration.connections[15])
  - timer_core.enable_q <= enable_q (integration.connections[16])
  - timer_core.count_q <= count_q (integration.connections[17])
  - timer_core.irq <= irq (integration.connections[18])

## Tasks

### RTL-0141: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0142: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0143: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0144: Implement handshake rule: pready

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pready.
Owner: timer_core in rtl/timer_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=pready; expr=psel == 1 and penable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pready
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.handshake_rules.pready RTL expression implements SSOT expression psel == 1 and penable == 1
  - cycle_model.handshake_rules.pready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pready

### RTL-0145: Implement handshake rule: pslverr

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pslverr
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pslverr.
Owner: timer_core in rtl/timer_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=pslverr; expr=psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pslverr
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.handshake_rules.pslverr RTL expression implements SSOT expression psel == 1 and penable == 1 and (paddr != 0 and paddr != 4 and paddr != 8)
  - cycle_model.handshake_rules.pslverr appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pslverr

### RTL-0146: Implement handshake rule: prdata

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.prdata
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.prdata.
Owner: timer_core in rtl/timer_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=prdata; expr=psel == 1 and penable == 1 and pwrite == 0 and paddr == 8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.prdata
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.handshake_rules.prdata RTL expression implements SSOT expression psel == 1 and penable == 1 and pwrite == 0 and paddr == 8
  - cycle_model.handshake_rules.prdata appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.prdata

### RTL-0147: Implement handshake rule: irq

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.irq
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.irq.
Owner: timer_core in rtl/timer_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=irq; expr=enable_q == 1 and count_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.irq
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.handshake_rules.irq RTL expression implements SSOT expression enable_q == 1 and count_q == 0
  - cycle_model.handshake_rules.irq appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.irq

### RTL-0148: Implement pipeline stage: RESET_RELEASED_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RESET_RELEASED_IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RESET_RELEASED_IDLE.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=RESET_RELEASED_IDLE; action=After reset deassertion, hold count_q=0, enable_q=0, irq=0 until APB write or enable tick.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RESET_RELEASED_IDLE
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.RESET_RELEASED_IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.RESET_RELEASED_IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RESET_RELEASED_IDLE

### RTL-0149: Implement pipeline stage: APB_ACCESS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.APB_ACCESS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.APB_ACCESS.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=APB_ACCESS; action=Decode LOAD, CTRL, STATUS, or unmapped address during APB access phase.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.APB_ACCESS
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.APB_ACCESS timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.APB_ACCESS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.APB_ACCESS

### RTL-0150: Implement pipeline stage: TICK_DECREMENT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TICK_DECREMENT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TICK_DECREMENT.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=TICK_DECREMENT; action=If enabled and count_q is nonzero, decrement count_q by one and keep irq low.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TICK_DECREMENT
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.TICK_DECREMENT timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.TICK_DECREMENT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TICK_DECREMENT

### RTL-0151: Implement pipeline stage: TICK_RELOAD_IRQ

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TICK_RELOAD_IRQ
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TICK_RELOAD_IRQ.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=TICK_RELOAD_IRQ; action=If enabled and count_q is zero, assert irq for this cycle and reload count_q from LOAD.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TICK_RELOAD_IRQ
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.TICK_RELOAD_IRQ timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.TICK_RELOAD_IRQ appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TICK_RELOAD_IRQ

### RTL-0152: Implement pipeline stage: DISABLED_HOLD

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.DISABLED_HOLD
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.DISABLED_HOLD.
Owner: timer_core in rtl/timer_core.sv via cycle_model.pipeline.
SSOT item context: stage=DISABLED_HOLD; action=If disabled, hold count_q and deassert irq.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.DISABLED_HOLD
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.pipeline.DISABLED_HOLD timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.DISABLED_HOLD appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.DISABLED_HOLD

### RTL-0153: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: timer_core in rtl/timer_core.sv via cycle_model.ordering.
SSOT item context: value=APB writes update LOAD or CTRL on the accepted access edge..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0154: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: timer_core in rtl/timer_core.sv via cycle_model.ordering.
SSOT item context: value=A CTRL write with ENABLE=0 prevents subsequent decrement/reload ticks and holds count_q..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0155: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: timer_core in rtl/timer_core.sv via cycle_model.ordering.
SSOT item context: value=STATUS read observes the current count_q value for the access cycle and has no read side effects..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0156: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: timer_core in rtl/timer_core.sv via cycle_model.ordering.
SSOT item context: value=irq assertion and count_q reload occur on the same timer tick when enable_q == 1 and count_q == 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0157: Implement ordering rule: ordering_rule_4

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_4
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_4.
Owner: timer_core in rtl/timer_core.sv via cycle_model.ordering.
SSOT item context: value=irq deasserts on the cycle following a reload event unless another reload condition is again true..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_4
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.ordering.ordering_rule_4 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_4

### RTL-0158: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=No APB wait states are introduced by the timer; pready follows accepted access phase..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0159: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: timer_core in rtl/timer_core.sv via cycle_model.
SSOT item context: value=STATUS read, irq pulse, and internal count_q are the primary scoreboard observation points..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
