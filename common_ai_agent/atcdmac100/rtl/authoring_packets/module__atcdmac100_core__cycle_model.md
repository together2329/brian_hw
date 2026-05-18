# RTL Authoring Packet: module__atcdmac100_core__cycle_model

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 20
- Required tasks: 20

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, decomposition, decomposition.owners, decomposition.source_refs, error_handling, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM_AHB_READ, function_model.transactions.FM_AHB_WRITE, function_model.transactions.FM_ARBITRATE, function_model.transactions.FM_COMPLETE, function_model.transactions.FM_ERROR_ABORT, function_model.transactions.FM_HANDSHAKE_ACK
- Module slice: 7/17 section=cycle_model task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0252: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=hclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0253: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=hresetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0254: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=AHB slave register access is zero-wait; DMA data movement issues read/write beats while hgrant_mst and hready_mst are....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0255: Implement handshake rule: handshake_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.handshake_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.handshake_rule_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=AHB slave access samples when hsel && hreadyin && htrans[1]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.handshake_rule_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.handshake_rules.handshake_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.handshake_rule_0

### RTL-0256: Implement handshake rule: handshake_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.handshake_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.handshake_rule_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=AHB master transfer completes when hgrant_mst && hready_mst && htrans_mst[1]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.handshake_rule_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.handshake_rules.handshake_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.handshake_rule_1

### RTL-0257: Implement handshake rule: handshake_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.handshake_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.handshake_rule_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=dma_ack is asserted after SrcBurstSize transfers for an enabled hardware request pair and is deasserted after dma_req....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.handshake_rule_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.handshake_rules.handshake_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.handshake_rule_2

### RTL-0258: Implement pipeline stage: pipeline_stage_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.pipeline_stage_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.pipeline_stage_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=IDLE selects a ready channel by priority/round-robin..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.pipeline_stage_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.pipeline.pipeline_stage_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.pipeline_stage_0

### RTL-0259: Implement pipeline stage: pipeline_stage_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.pipeline_stage_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.pipeline_stage_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=READ issues AHB read and captures hrdata_mst..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.pipeline_stage_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.pipeline.pipeline_stage_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.pipeline_stage_1

### RTL-0260: Implement pipeline stage: pipeline_stage_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.pipeline_stage_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.pipeline_stage_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=WRITE issues AHB write and advances counters..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.pipeline_stage_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.pipeline.pipeline_stage_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.pipeline_stage_2

### RTL-0261: Implement pipeline stage: pipeline_stage_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.pipeline_stage_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.pipeline_stage_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=DONE/ERROR updates status and interrupt..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.pipeline_stage_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.pipeline.pipeline_stage_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.pipeline_stage_3

### RTL-0262: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=Only one channel is actively serviced at a time..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0263: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=Same-priority channels are visited in round-robin order..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0264: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=A write beat uses data captured from the preceding read beat..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0265: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=Chain descriptor preload happens after head transfer completion when ChnLLPointer is nonzero..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0266: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=active_ch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0267: Implement observability signal: observability_signal_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=busy.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_1

### RTL-0268: Implement observability signal: observability_signal_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=htrans_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_2

### RTL-0269: Implement observability signal: observability_signal_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=hbusreq_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_3

### RTL-0270: Implement observability signal: observability_signal_4

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_4
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_4.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=dma_ack.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_4
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_4 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_4

### RTL-0271: Implement observability signal: observability_signal_5

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_5
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_5.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via cycle_model.
SSOT item context: value=dma_int.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_5
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - cycle_model.observability.observability_signal_5 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_5
