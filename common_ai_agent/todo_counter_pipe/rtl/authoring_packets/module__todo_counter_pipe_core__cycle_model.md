# RTL Authoring Packet: module__todo_counter_pipe_core__cycle_model

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
- Task count: 18
- Required tasks: 18

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 4/8 section=cycle_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0160: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=core_clk (primary behavioral clock).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0161: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0162: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0165: Implement handshake rule: event_i

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.event_i
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.event_i.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: signal=event_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.event_i
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.handshake_rules.event_i appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.event_i

### RTL-0168: Implement pipeline stage: S1_CDC_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_CDC_CTRL
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_CDC_CTRL.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: stage=S1_CDC_CTRL; action=2-stage synchronizer: CTRL fields (enable, up_down, mode, clear pulse, load pulse), LOAD value cross bus→core; cycle=0..4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_CDC_CTRL
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.pipeline.S1_CDC_CTRL timing uses SSOT cycle/latency 0..4
  - cycle_model.pipeline.S1_CDC_CTRL appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_CDC_CTRL

### RTL-0169: Implement pipeline stage: S2_COUNT_EVAL

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_COUNT_EVAL
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_COUNT_EVAL.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: stage=S2_COUNT_EVAL; action=Sample event_i; if enable && event_i rising edge, evaluate prio (clear>load>count), arithmetic, saturate/wrap, termin...; cycle=0..N.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_COUNT_EVAL
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.pipeline.S2_COUNT_EVAL timing uses SSOT cycle/latency 0..N
  - cycle_model.pipeline.S2_COUNT_EVAL appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_COUNT_EVAL

### RTL-0170: Implement pipeline stage: S3_CDC_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_CDC_STATUS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_CDC_STATUS.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: stage=S3_CDC_STATUS; action=2-stage synchronizer: cnt_value, overflow, underflow, tc_pending, ovf_pending, unf_pending, dbg_cycle_count cross cor...; cycle=0..5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_CDC_STATUS
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.pipeline.S3_CDC_STATUS timing uses SSOT cycle/latency 0..5
  - cycle_model.pipeline.S3_CDC_STATUS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_CDC_STATUS

### RTL-0172: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=clear and load CDC pulses must be edge-detected in core domain (single-cycle pulse after synchronization)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0173: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=A write to CTRL.clear or CTRL.load followed by a write to CTRL.enable in the same or subsequent bus_clk cycle must gu....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0174: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=Interrupt status updates (INTSTAT, STATUS) occur in bus_clk domain after CDC convergence; counter_irq follows in the ....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0175: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=dbg_cycle_count is free-running on core_clk and visible through CDC on bus_clk; no synchronization to event_i..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0176: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=No backpressure on APB: zero-wait-state response always..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0177: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=No backpressure on event_i: every rising edge while enable=1 produces a count; no flow control..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0178: Implement backpressure rule: backpressure_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=CDC pipeline is fixed-depth; no credit-based or ready/valid flow control between domains..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.backpressure.backpressure_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_2

### RTL-0179: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0180: Implement observability signal: observability_signal_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=S2_COUNT_EVAL covers FM1-FM9 count/clear/load/terminal/overflow/underflow logic..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.observability.observability_signal_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_1

### RTL-0181: Implement observability signal: observability_signal_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=S4_STATUS_UPDATE covers FM10 interrupt clear logic..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.observability.observability_signal_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_2

### RTL-0182: Implement observability signal: observability_signal_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via cycle_model.
SSOT item context: value=dbg_cycle_count provides cycle-level observability independent of event activity..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - cycle_model.observability.observability_signal_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_3
