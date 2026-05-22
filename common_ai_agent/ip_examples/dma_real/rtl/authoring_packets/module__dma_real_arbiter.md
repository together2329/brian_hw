# RTL Authoring Packet: module__dma_real_arbiter

- Kind: module
- Owner module: dma_real_arbiter
- Owner file: rtl/dma_real_arbiter.sv
- Task count: 28
- Required tasks: 28

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, dataflow.ordering.ordering_1, dataflow.sequence.sequence_2, function_model, function_model.transactions.FM_ARB_GRANT

## Tasks

### RTL-0022: Implement round-robin arbiter in hclk domain

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: dma_real_arbiter accepts request from each active channel and grants bus to next channel in round-robin order. Starvation-free.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.performance.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - round-robin pointer advances after each grant
  - only one channel granted at a time
  - idle channels not considered
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - Semantic source_refs covered: cycle_model.performance, function_model.transactions.FM_ARB_GRANT
- SSOT refs: cycle_model.performance, function_model.transactions.FM_ARB_GRANT, workflow_todos.rtl-gen[2]

### RTL-0024: Implement full AHB-Lite master protocol engine

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: dma_real_ahb_master drives full AHB-Lite protocol: haddr, htrans, hsize, hburst (INCR4/8/16 + WRAP4/8/16), hprot, hmaster, hmastlock, hwdata. 2-bit hresp handles OKAY/ERROR/RETRY/SPLIT. 1KB boundary detection splits burst.
SSOT ref: workflow_todos.rtl-gen[4].
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - address phase and data phase timing correct
  - NONSEQ for first beat, SEQ for subsequent
  - hburst INCR and WRAP modes encoded correctly
  - hprot default 0011, hmaster set to channel ID
  - hresp=ERROR aborts, hresp=RETRY re-requests
  - 1KB boundary detection triggers new NONSEQ
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - Semantic source_refs covered: cycle_model.handshake_rules, cycle_model.pipeline, io_list.interfaces.ahb_master
- SSOT refs: cycle_model.handshake_rules, cycle_model.pipeline, io_list.interfaces.ahb_master, workflow_todos.rtl-gen[4]

### RTL-0149: Implement transaction FM_ARB_GRANT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ARB_GRANT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ARB_GRANT.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: id=FM_ARB_GRANT; name=arb_grant.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
- SSOT refs: function_model.transactions.FM_ARB_GRANT

### RTL-0150: Implement precondition for FM_ARB_GRANT: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ARB_GRANT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.preconditions.precondition_0.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: value=at least one channel is requesting bus access.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
- SSOT refs: function_model.transactions.FM_ARB_GRANT.preconditions.precondition_0

### RTL-0151: Implement output for FM_ARB_GRANT: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ARB_GRANT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.outputs.output_0.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: id=FM_ARB_GRANT; name=arb_grant; port=["arb_grant"]; signal=["arb_grant", "requester_mask"]; state=["arb_ptr_update"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.outputs.output_0
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - DUT port ["arb_grant"] is the implementation/observation point for arb_grant
- SSOT refs: function_model.transactions.FM_ARB_GRANT.outputs.output_0

### RTL-0152: Implement output rule for FM_ARB_GRANT: grant_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ARB_GRANT.output_rules.grant_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.output_rules.grant_next.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: name=grant_next; port=arb_grant; expr=(arb_ptr_q + 1) % N_CHANNELS if requester_mask[arb_ptr_q] == 0 else arb_ptr_q; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.output_rules.grant_next
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - grant_next width matches SSOT value 3
  - grant_next RTL expression implements SSOT expression (arb_ptr_q + 1) % N_CHANNELS if requester_mask[arb_ptr_q] == 0 else arb_ptr_q
  - DUT port arb_grant is the implementation/observation point for grant_next
  - grant_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ARB_GRANT.output_rules.grant_next

### RTL-0153: Implement state update for FM_ARB_GRANT: arb_ptr_update

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ARB_GRANT.state_updates.arb_ptr_update
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.state_updates.arb_ptr_update.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: name=arb_ptr_update; expr=(grant_ch + 1) % N_CHANNELS; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.state_updates.arb_ptr_update
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - arb_ptr_update width matches SSOT value 3
  - arb_ptr_update RTL expression implements SSOT expression (grant_ch + 1) % N_CHANNELS
  - arb_ptr_update updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ARB_GRANT.state_updates.arb_ptr_update

### RTL-0154: Implement side effect for FM_ARB_GRANT: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_0.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: id=FM_ARB_GRANT; name=arb_grant; port=["arb_grant"]; signal=["arb_ptr_q updated to next channel after grant", "requester_mask"]; state=["arb_ptr_update"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - DUT port ["arb_grant"] is the implementation/observation point for arb_grant
- SSOT refs: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_0

### RTL-0155: Implement side effect for FM_ARB_GRANT: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_1.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via function_model.transactions.FM_ARB_GRANT.
SSOT item context: id=FM_ARB_GRANT; name=arb_grant; port=["arb_grant"]; signal=["granted channel gains AHB bus access", "requester_mask"]; state=["arb_ptr_update"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - DUT port ["arb_grant"] is the implementation/observation point for arb_grant
- SSOT refs: function_model.transactions.FM_ARB_GRANT.side_effects.side_effect_1

### RTL-0164: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=hclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0165: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=hresetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0166: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0167: Implement handshake rule: apb_access

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.apb_access
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.apb_access.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
SSOT item context: name=apb_access.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.apb_access
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - apb_access appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.apb_access

### RTL-0168: Implement handshake rule: cdc_config

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.cdc_config
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.cdc_config.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
SSOT item context: name=cdc_config.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.cdc_config
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cdc_config appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.cdc_config

### RTL-0173: Implement handshake rule: arb_grant_rule

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.arb_grant_rule
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.arb_grant_rule.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
SSOT item context: name=arb_grant_rule.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.arb_grant_rule
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - arb_grant_rule appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.arb_grant_rule

### RTL-0174: Implement handshake rule: start_accept

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.start_accept
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.start_accept.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
SSOT item context: name=start_accept.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.start_accept
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - start_accept appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.start_accept

### RTL-0175: Implement handshake rule: timeout_rule

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.timeout_rule
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.timeout_rule.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.handshake_rules.
SSOT item context: name=timeout_rule.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.timeout_rule
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - timeout_rule appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.timeout_rule

### RTL-0184: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=Configuration (APB pclk) must cross CDC before hclk channel FSM reads it..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0185: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=Read burst completion must precede write burst for same data..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0186: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=Address update (UPDATE) must precede next burst request..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0187: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=Transfer completion (DONE) precedes done pulse observation..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0188: Implement ordering rule: ordering_rule_4

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_4
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_4.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=1KB boundary crossing recalculates burst parameters before next address phase..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_4
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.ordering.ordering_rule_4 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_4

### RTL-0189: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=New starts blocked while channel busy..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0190: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=AHB transfers stall when hready is low..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0191: Implement backpressure rule: backpressure_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_2.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=Arbiter queues requests when bus is occupied..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_2
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.backpressure.backpressure_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_2

### RTL-0192: Implement backpressure rule: backpressure_rule_3

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_3.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=FIFO almost_full back-pressures read burst..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_3
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.backpressure.backpressure_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_3

### RTL-0193: Implement backpressure rule: backpressure_rule_4

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_4
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_4.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via cycle_model.
SSOT item context: value=CDC FIFO full back-pressures APB writes (pslverr or pready deassert)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_4
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
  - cycle_model.backpressure.backpressure_rule_4 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_4

### RTL-0377: Prove module dma_real_arbiter is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.dma_real_arbiter.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.dma_real_arbiter.module_equivalence.
Owner: dma_real_arbiter in rtl/dma_real_arbiter.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.dma_real_arbiter.module_equivalence
  - Primary implementation evidence is in rtl/dma_real_arbiter.sv
- SSOT refs: sub_modules.dma_real_arbiter.module_equivalence
