# RTL Authoring Packet: module__rv32i_min_if__cycle_model

- Kind: module
- Owner module: rv32i_min_if
- Owner file: rtl/rv32i_min_if.sv
- Task count: 12
- Required tasks: 12

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, function_model, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, io_list, io_list.interfaces.instr_bus
- Module slice: 3/6 section=cycle_model task_limit=48
- Slice rule: Owner module rv32i_min_if is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])

## Tasks

### RTL-0123: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0124: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0125: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0126: Implement handshake rule: i_valid

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.i_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.i_valid.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=i_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.i_valid
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.handshake_rules.i_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.i_valid

### RTL-0127: Implement handshake rule: d_valid

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.d_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.d_valid.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=d_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.d_valid
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.handshake_rules.d_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.d_valid

### RTL-0128: Implement handshake rule: d_we

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.d_we
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.d_we.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=d_we.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.d_we
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.handshake_rules.d_we appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.d_we

### RTL-0129: Implement handshake rule: excpt_o

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.excpt_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.excpt_o.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=excpt_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.excpt_o
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.handshake_rules.excpt_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.excpt_o

### RTL-0130: Implement pipeline stage: IF

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.IF
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.IF.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.pipeline.
SSOT item context: stage=IF; action=Drive i_addr from pc and sample i_rdata; cycle=t.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.IF
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.pipeline.IF timing uses SSOT cycle/latency t
  - cycle_model.pipeline.IF appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.IF

### RTL-0131: Implement pipeline stage: ID_EX

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.ID_EX
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.ID_EX.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.pipeline.
SSOT item context: stage=ID_EX; action=Decode and compute ALU or branch or target or effective address; cycle=t+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.ID_EX
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.pipeline.ID_EX timing uses SSOT cycle/latency t+1
  - cycle_model.pipeline.ID_EX appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.ID_EX

### RTL-0132: Implement pipeline stage: MEM_WB

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.MEM_WB
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.MEM_WB.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.pipeline.
SSOT item context: stage=MEM_WB; action=Perform load/store signaling and writeback and retire; cycle=t+2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.MEM_WB
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.pipeline.MEM_WB timing uses SSOT cycle/latency t+2
  - cycle_model.pipeline.MEM_WB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.MEM_WB

### RTL-0136: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.
SSOT item context: value=No explicit ready channels; interfaces are sampled synchronously each cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0137: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to IF or ID_EX or MEM_WB stage.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
