# RTL Authoring Packet: module__uart_lite_tx__cycle_model

- Kind: module
- Owner module: uart_lite_tx
- Owner file: rtl/uart_lite_tx.sv
- Task count: 16
- Required tasks: 16

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
- Owner refs: cycle_model, cycle_model.pipeline, cycle_model.pipeline[TX_DATA], cycle_model.pipeline[TX_IDLE], cycle_model.pipeline[TX_PARITY], cycle_model.pipeline[TX_START], cycle_model.pipeline[TX_STOP1], cycle_model.pipeline[TX_STOP2], fsm, fsm.tx_fsm, function_model, function_model.transactions.FM_TX_BYTE
- Module slice: 2/5 section=cycle_model task_limit=48
- Slice rule: Owner module uart_lite_tx is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0115: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0116: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0117: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0122: Implement pipeline stage: TX_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_IDLE.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_IDLE; action=Wait for TX FIFO not empty; assert tx_active=false; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_IDLE
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.TX_IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_IDLE

### RTL-0123: Implement pipeline stage: TX_START

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_START
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_START.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_START; action=Drive tx=0 for one baud tick period; assert tx_active; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_START
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_START timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.TX_START appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_START

### RTL-0124: Implement pipeline stage: TX_DATA

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_DATA
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_DATA.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_DATA; action=Shift LSB of tx_shift_reg to tx each baud tick; repeat DATA_WIDTH times. tx_shift_reg loaded from TX FIFO on entry.; cycle=2..1+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_DATA
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_DATA timing uses SSOT cycle/latency 2..1+DATA_WIDTH
  - cycle_model.pipeline.TX_DATA appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_DATA

### RTL-0125: Implement pipeline stage: TX_PARITY

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_PARITY
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_PARITY.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_PARITY; action=Drive computed parity bit to tx for one baud tick (present only if parity_en=1); cycle=2+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_PARITY
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_PARITY timing uses SSOT cycle/latency 2+DATA_WIDTH
  - cycle_model.pipeline.TX_PARITY appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_PARITY

### RTL-0126: Implement pipeline stage: TX_STOP1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_STOP1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_STOP1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_STOP1; action=Drive tx=1 for one baud tick; cycle=3+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_STOP1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_STOP1 timing uses SSOT cycle/latency 3+DATA_WIDTH
  - cycle_model.pipeline.TX_STOP1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_STOP1

### RTL-0127: Implement pipeline stage: TX_STOP2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.TX_STOP2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.TX_STOP2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.pipeline.
SSOT item context: stage=TX_STOP2; action=Drive tx=1 for one baud tick (present only if stop_bits=1); cycle=4+DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.TX_STOP2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.pipeline.TX_STOP2 timing uses SSOT cycle/latency 4+DATA_WIDTH
  - cycle_model.pipeline.TX_STOP2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.TX_STOP2

### RTL-0135: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=TX FSM does not start a new frame until the current frame completes (no pipelining across bytes)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0136: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=RX FSM does not start a new frame until the current frame completes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0137: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=Interrupt pending bits update on the same PCLK edge as the condition (FIFO threshold crossing, error detection, frame....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0138: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=TX backpressure: TX FSM waits in TX_IDLE when TX FIFO is empty..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0139: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=RX backpressure: If RX FIFO is full when a new byte would be pushed, overrun_err is set and the byte is discarded; RX....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0140: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model TX or RX stage..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0141: Implement observability signal: observability_signal_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via cycle_model.
SSOT item context: value=Baud tick, oversample counter, TX/RX shift registers, and FIFO pointers are observable in waveform..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - cycle_model.observability.observability_signal_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_1
