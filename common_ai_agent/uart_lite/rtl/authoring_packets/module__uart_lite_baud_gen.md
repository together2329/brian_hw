# RTL Authoring Packet: module__uart_lite_baud_gen

- Kind: module
- Owner module: uart_lite_baud_gen
- Owner file: rtl/uart_lite_baud_gen.sv
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
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.baud_generation, parameters, parameters.OVERSAMPLE

## Tasks

### RTL-0029: Implement baud-rate generator with OVERSAMPLE counter

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Counter increments every PCLK. Baud tick pulse when oversample_counter==0 and baud_div_counter reaches (baud_div * OVERSAMPLE - 1). Separate oversample counter 0..15 for RX centre-sampling.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_BAUD_GEN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Baud tick is single PCLK cycle wide
  - Baud tick period = baud_div * OVERSAMPLE PCLK cycles
  - RX oversample counter resets on each baud tick
  - Baud_div==0 disables baud tick generation
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - Semantic source_refs covered: cycle_model.baud_generation
- SSOT refs: cycle_model.baud_generation, workflow_todos.rtl-gen[2]

### RTL-0110: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0111: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0112: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0113: Implement handshake rule: PREADY

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PREADY
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PREADY.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: signal=PREADY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PREADY
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.handshake_rules.PREADY appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PREADY

### RTL-0114: Implement handshake rule: PSLVERR

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.PSLVERR
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.PSLVERR.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: signal=PSLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.PSLVERR
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.handshake_rules.PSLVERR appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.PSLVERR

### RTL-0115: Implement handshake rule: txd_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.txd_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.txd_o.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: signal=txd_o.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.txd_o
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.handshake_rules.txd_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.txd_o

### RTL-0116: Implement handshake rule: irq_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.irq_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.irq_o.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: signal=irq_o.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.irq_o
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.handshake_rules.irq_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.irq_o

### RTL-0117: Implement pipeline stage: APB_DECODE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.APB_DECODE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.APB_DECODE.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=APB_DECODE; action=APB setup/access phase — decode address, mux read data, capture write data; cycle=0..1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.APB_DECODE
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.APB_DECODE timing uses SSOT cycle/latency 0..1
  - cycle_model.pipeline.APB_DECODE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.APB_DECODE

### RTL-0118: Implement pipeline stage: TX_ARBITRATE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_ARBITRATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_ARBITRATE.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=TX_ARBITRATE; action=TX FSM checks FIFO not empty, baud tick present, break not active; pops byte from FIFO; cycle=N.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_ARBITRATE
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.TX_ARBITRATE timing uses SSOT cycle/latency N
  - cycle_model.pipeline.TX_ARBITRATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_ARBITRATE

### RTL-0119: Implement pipeline stage: TX_SHIFT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_SHIFT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_SHIFT.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=TX_SHIFT; action=TX FSM shifts out start/data/parity/stop bits on successive baud ticks; cycle=N+1 .. N+frame_len.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_SHIFT
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.TX_SHIFT timing uses SSOT cycle/latency N+1 .. N+frame_len
  - cycle_model.pipeline.TX_SHIFT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_SHIFT

### RTL-0120: Implement pipeline stage: RX_SYNC

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_SYNC
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_SYNC.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=RX_SYNC; action=2-FF synchronizer captures rxd_i; falling-edge detector output; cycle=M .. M+1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_SYNC
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.RX_SYNC timing uses SSOT cycle/latency M .. M+1
  - cycle_model.pipeline.RX_SYNC appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_SYNC

### RTL-0121: Implement pipeline stage: RX_SAMPLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_SAMPLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_SAMPLE.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=RX_SAMPLE; action=RX FSM center-samples start/data/parity/stop at oversample count 7 per baud period; cycle=M+2 .. M+2+frame_len.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_SAMPLE
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.RX_SAMPLE timing uses SSOT cycle/latency M+2 .. M+2+frame_len
  - cycle_model.pipeline.RX_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_SAMPLE

### RTL-0122: Implement pipeline stage: RX_COMMIT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.RX_COMMIT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.RX_COMMIT.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=RX_COMMIT; action=RX FSM pushes assembled byte to RX FIFO or flags error; updates counters; cycle=M+2+frame_len+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.RX_COMMIT
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.RX_COMMIT timing uses SSOT cycle/latency M+2+frame_len+1
  - cycle_model.pipeline.RX_COMMIT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.RX_COMMIT

### RTL-0123: Implement pipeline stage: INT_UPDATE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.INT_UPDATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.INT_UPDATE.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: stage=INT_UPDATE; action=Sticky status/pending bits set on same cycle as error detection; irq_o updates combinatorially or next cycle; cycle=same cycle as event.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.INT_UPDATE
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.pipeline.INT_UPDATE timing uses SSOT cycle/latency same cycle as event
  - cycle_model.pipeline.INT_UPDATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.INT_UPDATE

### RTL-0124: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=TX FSM and RX FSM operate in parallel; no ordering dependency except loopback where TX output → RX input..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0125: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=APB reads to any register return current values combinatorially or after 1 wait state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0126: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=W1C clear takes effect in the same cycle as APB write access phase completion..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0127: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=TX FIFO: APB writes to TXDATA ignored when FIFO full (tx_full=1). TX FSM stalls when FIFO empty..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0128: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=RX FIFO: RX FSM discards new byte when RX FIFO full (rx_full=1), sets rx_overrun..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0129: Implement backpressure rule: backpressure_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_2.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=APB: PREADY deassertion (wait states) stalls the APB access phase only..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_2
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.backpressure.backpressure_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_2

### RTL-0130: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0259: Prove module uart_lite_baud_gen is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_baud_gen.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_baud_gen.module_equivalence.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_baud_gen.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: sub_modules.uart_lite_baud_gen.module_equivalence

### RTL-0035: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0036: Implement parameter FIFO_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.FIFO_DEPTH.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.FIFO_DEPTH
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.FIFO_DEPTH

### RTL-0037: Implement parameter OVERSAMPLE

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.OVERSAMPLE
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.OVERSAMPLE.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=OVERSAMPLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.OVERSAMPLE
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.OVERSAMPLE

### RTL-0038: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.APB_ADDR_WIDTH

### RTL-0039: Implement parameter APB_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_DATA_WIDTH.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=APB_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_DATA_WIDTH
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.APB_DATA_WIDTH

### RTL-0040: Implement parameter PCLK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.PCLK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PCLK_FREQ_MHZ.
Owner: uart_lite_baud_gen in rtl/uart_lite_baud_gen.sv via parameters.
SSOT item context: name=PCLK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PCLK_FREQ_MHZ
  - Primary implementation evidence is in rtl/uart_lite_baud_gen.sv
- SSOT refs: parameters.PCLK_FREQ_MHZ
