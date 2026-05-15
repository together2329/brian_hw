# RTL Authoring Packet: module__clkdiv_core__cycle_model

- Kind: module
- Owner module: clkdiv_core
- Owner file: rtl/clkdiv_core.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 18
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow, dataflow.clock_path, dataflow.control_path, fsm, fsm.divider_fsm, function_model, function_model.state_variables, function_model.transactions.FM_DIVIDE
- Module slice: 2/5 section=cycle_model task_limit=48
- Slice rule: Owner module clkdiv_core is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - clkdiv_core.clk_i <= clk_i (sub_modules[1].connections[0])
  - clkdiv_core.rst_ni <= rst_ni (sub_modules[1].connections[1])
  - clkdiv_core.enable_i <= enable (sub_modules[1].connections[2])
  - clkdiv_core.divisor_i <= active_divisor (sub_modules[1].connections[3])
  - clkdiv_core.clk_o <= clk_o (sub_modules[1].connections[4])
  - clkdiv_core.locked_o <= locked_o (sub_modules[1].connections[5])
  - clkdiv_core.terminal_event_o <= terminal_event (sub_modules[1].connections[6])
  - clkdiv_core.clk_i <= clk_i (integration.connections[11])
  - clkdiv_core.rst_ni <= rst_ni (integration.connections[12])
  - clkdiv_core.enable_i <= enable (integration.connections[13])
  - clkdiv_core.divisor_i <= active_divisor (integration.connections[14])
  - clkdiv_core.clk_o <= clk_o (integration.connections[15])

## Tasks

### RTL-0077: Implement cycle-model clock

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=clk_i.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0078: Implement cycle-model reset

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0079: Implement cycle-model latency

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0080: Implement handshake rule: pready

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pready.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=pready.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pready
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.handshake_rules.pready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pready

### RTL-0081: Implement handshake rule: pslverr

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pslverr
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pslverr.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=pslverr.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pslverr
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.handshake_rules.pslverr appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pslverr

### RTL-0082: Implement handshake rule: prdata

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.prdata
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.prdata.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=prdata.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.prdata
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.handshake_rules.prdata appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.prdata

### RTL-0083: Implement handshake rule: clk_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.clk_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.clk_o.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=clk_o.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.clk_o
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.handshake_rules.clk_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.clk_o

### RTL-0084: Implement handshake rule: irq_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.irq_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.irq_o.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.handshake_rules.
SSOT item context: signal=irq_o.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.irq_o
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.handshake_rules.irq_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.irq_o

### RTL-0085: Implement pipeline stage: S0_APB_SETUP

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_APB_SETUP
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_APB_SETUP.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.pipeline.
SSOT item context: stage=S0_APB_SETUP; action=Capture paddr/pwrite context when psel=1 and penable=0.; cycle=0.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_APB_SETUP
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.pipeline.S0_APB_SETUP timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_APB_SETUP appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_APB_SETUP

### RTL-0086: Implement pipeline stage: S1_APB_ACCESS

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_APB_ACCESS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_APB_ACCESS.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.pipeline.
SSOT item context: stage=S1_APB_ACCESS; action=Complete APB read/write; update CTRL/DIVISOR/INTCLR effects.; cycle=1.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_APB_ACCESS
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.pipeline.S1_APB_ACCESS timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S1_APB_ACCESS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_APB_ACCESS

### RTL-0087: Implement pipeline stage: S2_COUNT

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_COUNT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_COUNT.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.pipeline.
SSOT item context: stage=S2_COUNT; action=Increment counter while counter < active_divisor-1.; cycle=each enabled clk_i edge.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_COUNT
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.pipeline.S2_COUNT timing uses SSOT cycle/latency each enabled clk_i edge
  - cycle_model.pipeline.S2_COUNT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_COUNT

### RTL-0088: Implement pipeline stage: S3_TERMINAL

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_TERMINAL
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_TERMINAL.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.pipeline.
SSOT item context: stage=S3_TERMINAL; action=Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending.; cycle=terminal edge.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_TERMINAL
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.pipeline.S3_TERMINAL timing uses SSOT cycle/latency terminal edge
  - cycle_model.pipeline.S3_TERMINAL appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_TERMINAL

### RTL-0089: Implement pipeline stage: S4_DISABLE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_DISABLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_DISABLE.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.pipeline.
SSOT item context: stage=S4_DISABLE; action=Force counter and clk_o low and clear locked.; cycle=first edge after enable=0.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_DISABLE
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.pipeline.S4_DISABLE timing uses SSOT cycle/latency first edge after enable=0
  - cycle_model.pipeline.S4_DISABLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_DISABLE

### RTL-0090: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=APB DIVISOR writes update pending_divisor before the next core reload boundary..
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0091: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=active_divisor changes only in S3_TERMINAL or reset..
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0092: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=INTCLR.clear_irq write clears irq_pending no later than the completing APB access edge..
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0093: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=No backpressure exists on divided_clock outputs; APB baseline has no wait states..
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0094: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to S2_COUNT/S3_TERMINAL and a test_requirements scenario..
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
