# RTL Authoring Packet: module__mctp_assembler_v3_axi_wr_ingress__cycle_model

- Kind: module
- Owner module: mctp_assembler_v3_axi_wr_ingress
- Owner file: rtl/mctp_assembler_v3_axi_wr_ingress.sv
- Task count: 16
- Required tasks: 16

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 16
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, function_model, function_model.transactions.FM_INGEST_TLP, io_list, io_list.interfaces.axi_wr_slave, test_requirements
- Module slice: 3/5 section=cycle_model task_limit=48
- Slice rule: Owner module mctp_assembler_v3_axi_wr_ingress is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])

## Tasks

### RTL-0292: Implement cycle-model clock

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=axi_aclk.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0293: Implement cycle-model reset

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0294: Implement cycle-model latency

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0295: Implement handshake rule: s_axi_awready/s_axi_wready

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.s_axi_awready_s_axi_wready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.s_axi_awready_s_axi_wready.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=s_axi_awready/s_axi_wready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.s_axi_awready_s_axi_wready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.s_axi_awready_s_axi_wready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.s_axi_awready_s_axi_wready

### RTL-0296: Implement handshake rule: s_axi_bvalid

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.s_axi_bvalid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.s_axi_bvalid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=s_axi_bvalid.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.s_axi_bvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.s_axi_bvalid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.s_axi_bvalid

### RTL-0297: Implement handshake rule: sram_wr_valid

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sram_wr_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sram_wr_valid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=sram_wr_valid.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.sram_wr_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sram_wr_valid

### RTL-0298: Implement handshake rule: sram_rd_req_valid

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sram_rd_req_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sram_rd_req_valid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=sram_rd_req_valid.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sram_rd_req_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.sram_rd_req_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sram_rd_req_valid

### RTL-0299: Implement handshake rule: s_axi_rvalid/s_axi_rlast

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=s_axi_rvalid/s_axi_rlast.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast

### RTL-0300: Implement handshake rule: apb pready

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.apb_pready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.apb_pready.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=apb pready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.apb_pready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.apb_pready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.apb_pready

### RTL-0307: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=descriptor_publish must occur only after the final SRAM payload write/flush for the message is accepted..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0308: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=AXI read response is not issued before the corresponding SRAM read response..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0309: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=Interrupt status updates occur on the rising edge the terminal event is recorded (after CDC into pclk for status bits)..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0310: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=sram_wr_ready deassertion stalls payload writes without dropping accepted bytes unless timeout/overflow occurs..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0311: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=SRAM write traffic for assembly has priority over firmware AXI read traffic on a shared port..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0312: Implement backpressure rule: backpressure_rule_2

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_2.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=AXI read backpressure must not corrupt ongoing assembly writes; each context owns its own partial-word state..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.backpressure.backpressure_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_2

### RTL-0313: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0
