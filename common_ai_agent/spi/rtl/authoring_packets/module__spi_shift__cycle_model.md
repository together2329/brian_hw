# RTL Authoring Packet: module__spi_shift__cycle_model

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
- Task count: 7
- Required tasks: 7

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.launch_gate, cycle_model.ordering, cycle_model.pipeline, cycle_model.pipeline.S1_LAUNCH_CHECK, cycle_model.pipeline.S2_ASSERT_CS, cycle_model.pipeline.S3_SHIFT, cycle_model.pipeline.S4_SAMPLE, cycle_model.pipeline.S5_COMPLETE, dataflow, dataflow.control_path, features, features.APB-programmed frame transfer, features.Programmable SPI mode and bit order, fsm, fsm.channel_level
- Module slice: 2/6 section=cycle_model task_limit=48
- Slice rule: Owner module spi_shift is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0121: Implement handshake rule: launch_gate

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.launch_gate
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.launch_gate.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.handshake_rules.launch_gate.
SSOT item context: signal=launch_gate.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.launch_gate
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.handshake_rules.launch_gate appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.launch_gate

### RTL-0125: Implement pipeline stage: S1_LAUNCH_CHECK

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_LAUNCH_CHECK
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_LAUNCH_CHECK.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.pipeline.S1_LAUNCH_CHECK.
SSOT item context: stage=S1_LAUNCH_CHECK; action=Evaluate launch preconditions and latch frame context; cycle=t+0..t+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_LAUNCH_CHECK
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.pipeline.S1_LAUNCH_CHECK timing uses SSOT cycle/latency t+0..t+1
  - cycle_model.pipeline.S1_LAUNCH_CHECK appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_LAUNCH_CHECK

### RTL-0126: Implement pipeline stage: S2_ASSERT_CS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_ASSERT_CS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_ASSERT_CS.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.pipeline.S2_ASSERT_CS.
SSOT item context: stage=S2_ASSERT_CS; action=Drive selected chip select active-low; cycle=next.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_ASSERT_CS
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.pipeline.S2_ASSERT_CS timing uses SSOT cycle/latency next
  - cycle_model.pipeline.S2_ASSERT_CS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_ASSERT_CS

### RTL-0127: Implement pipeline stage: S3_SHIFT

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_SHIFT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_SHIFT.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.pipeline.S3_SHIFT.
SSOT item context: stage=S3_SHIFT; action=Generate sclk_o edges and launch MOSI bits; cycle=repeating.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_SHIFT
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.pipeline.S3_SHIFT timing uses SSOT cycle/latency repeating
  - cycle_model.pipeline.S3_SHIFT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_SHIFT

### RTL-0130: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.ordering.
SSOT item context: value=For each frame, TX dequeue precedes first MOSI launch edge..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0131: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.ordering.
SSOT item context: value=Final RX sample precedes done event and interrupt pending update for completion..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0132: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: spi_shift in rtl/spi_shift.sv via cycle_model.ordering.
SSOT item context: value=INT_CLEAR W1C effects apply after the write transfer edge and before next irq_o observation edge..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/spi_shift.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2
