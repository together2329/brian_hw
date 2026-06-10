# RTL Authoring Packet: module__fifo_sync_cx1__cycle_model

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 10
- Required tasks: 10

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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 6/11 section=cycle_model task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0066: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0067: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: value=rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0068: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: value=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0069: Implement handshake rule: wr_en_full

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.wr_en_full
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.wr_en_full.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via top_level_handshake_rule.
SSOT item context: name=wr_en_full; signal=wr_en; condition=wr_data sampled when wr_en is high and full is low..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.wr_en_full
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - wr_en_full condition is implemented as RTL control logic: wr_data sampled when wr_en is high and full is low.
  - wr_en_full appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.wr_en_full

### RTL-0070: Implement handshake rule: rd_en_empty

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.rd_en_empty
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.rd_en_empty.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via top_level_handshake_rule.
SSOT item context: name=rd_en_empty; signal=rd_en; condition=rd_ptr advanced when rd_en is high and empty is low..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.rd_en_empty
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_en_empty condition is implemented as RTL control logic: rd_ptr advanced when rd_en is high and empty is low.
  - rd_en_empty appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.rd_en_empty

### RTL-0071: Implement handshake rule: reset_clear

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.reset_clear
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.reset_clear.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via top_level_handshake_rule.
SSOT item context: name=reset_clear; signal=rst_n; condition=rst_n low clears count, wr_ptr, rd_ptr to 0 synchronously..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.reset_clear
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - reset_clear condition is implemented as RTL control logic: rst_n low clears count, wr_ptr, rd_ptr to 0 synchronously.
  - reset_clear appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.reset_clear

### RTL-0072: Implement pipeline stage: WRITE_WR_EN

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.WRITE_WR_EN
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.WRITE_WR_EN.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.pipeline.
SSOT item context: stage=WRITE_WR_EN; action=Accept wr_data when wr_en and not full.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.WRITE_WR_EN
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.pipeline.WRITE_WR_EN timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.WRITE_WR_EN appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.WRITE_WR_EN

### RTL-0073: Implement pipeline stage: READ_RD_EN

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.READ_RD_EN
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.READ_RD_EN.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.pipeline.
SSOT item context: stage=READ_RD_EN; action=Advance rd_ptr when rd_en and not empty.; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.READ_RD_EN
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.pipeline.READ_RD_EN timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.READ_RD_EN appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.READ_RD_EN

### RTL-0074: Implement pipeline stage: COUNT_FULL_EMPTY

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.COUNT_FULL_EMPTY
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.COUNT_FULL_EMPTY.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.pipeline.
SSOT item context: stage=COUNT_FULL_EMPTY; action=Update count, full and empty flags.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.COUNT_FULL_EMPTY
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.pipeline.COUNT_FULL_EMPTY timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.COUNT_FULL_EMPTY appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.COUNT_FULL_EMPTY

### RTL-0075: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: value=Simultaneous write and read (bypass) is allowed when !full && !empty..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0
