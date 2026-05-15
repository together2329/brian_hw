# RTL Authoring Packet: module__arm_m0_min_ex

- Kind: module
- Owner module: arm_m0_min_ex
- Owner file: rtl/arm_m0_min_ex.sv
- Task count: 31
- Required tasks: 31

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
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, error_handling, error_handling.error_sources, function_model, function_model.transactions.TX_DECODE_EXEC, function_model.transactions.TX_LOAD_STORE, io_list, io_list.interfaces.ahb_d_master
- SSOT connection contracts:
  - arm_m0_min_ex.d_haddr <= d_haddr (integration.connections[5])
  - arm_m0_min_ex.d_htrans <= d_htrans (integration.connections[6])
  - arm_m0_min_ex.d_hwrite <= d_hwrite (integration.connections[7])
  - arm_m0_min_ex.d_hwdata <= d_hwdata (integration.connections[8])
  - arm_m0_min_ex.d_hready <= d_hready (integration.connections[9])
  - arm_m0_min_ex.d_hrdata <= d_hrdata (integration.connections[10])
  - arm_m0_min_ex.d_hresp <= d_hresp (integration.connections[11])

## Tasks

### RTL-0027: Implement IF/ID/EX pipeline control and stalls

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate cycle_model pipeline, ordering, and backpressure rules into concrete stage-valid/stall logic.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_PIPELINE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Program-order commit is preserved
  - IF stall on i_hready low and MEM stall on d_hready low are correct
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - Semantic source_refs covered: cycle_model.backpressure, cycle_model.ordering, cycle_model.pipeline
- SSOT refs: cycle_model.backpressure, cycle_model.ordering, cycle_model.pipeline, workflow_todos.rtl-gen[0]

### RTL-0029: Implement bus-error fault-halt behavior

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Detect i_hresp/d_hresp errors on completed transfers and latch FAULT_HALT until reset.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FAULT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - No retire after FAULT_HALT entry
  - Reset exits FAULT_HALT
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - Semantic source_refs covered: error_handling.error_sources, fsm.core, function_model.invariants
- SSOT refs: error_handling.error_sources, fsm.core, function_model.invariants, workflow_todos.rtl-gen[2]

### RTL-0073: Implement transaction TX_LOAD_STORE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.TX_LOAD_STORE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.TX_LOAD_STORE.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: id=TX_LOAD_STORE; name=single_transfer_memory_access.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE

### RTL-0074: Implement precondition for TX_LOAD_STORE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=fault_halt == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_0

### RTL-0075: Implement precondition for TX_LOAD_STORE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_1.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=decoded opcode is LDR or STR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.preconditions.precondition_1

### RTL-0076: Implement input for TX_LOAD_STORE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.TX_LOAD_STORE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.inputs.input_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=base register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.inputs.input_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.inputs.input_0

### RTL-0077: Implement input for TX_LOAD_STORE: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.TX_LOAD_STORE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.inputs.input_1.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=immediate offset.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.inputs.input_1
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.inputs.input_1

### RTL-0078: Implement input for TX_LOAD_STORE: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.TX_LOAD_STORE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.inputs.input_2.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=store data for STR or bus read data for LDR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.inputs.input_2
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.inputs.input_2

### RTL-0079: Implement output for TX_LOAD_STORE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.TX_LOAD_STORE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.outputs.output_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=LDR updates destination register with returned word.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.outputs.output_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.outputs.output_0

### RTL-0080: Implement output for TX_LOAD_STORE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.TX_LOAD_STORE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.outputs.output_1.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=STR commits one data write on bus.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.outputs.output_1
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.outputs.output_1

### RTL-0081: Implement output rule for TX_LOAD_STORE: d_haddr_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.TX_LOAD_STORE.output_rules.d_haddr_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.output_rules.d_haddr_rule.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: name=d_haddr_rule; port=d_haddr; expr=base + imm; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.output_rules.d_haddr_rule
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_haddr_rule width matches SSOT value 32
  - d_haddr_rule RTL expression implements SSOT expression base + imm
  - DUT port d_haddr is the implementation/observation point for d_haddr_rule
  - d_haddr_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.TX_LOAD_STORE.output_rules.d_haddr_rule

### RTL-0082: Implement output rule for TX_LOAD_STORE: d_hwrite_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.TX_LOAD_STORE.output_rules.d_hwrite_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.output_rules.d_hwrite_rule.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: name=d_hwrite_rule; port=d_hwrite; expr=(1) if (is_store) else (0); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.output_rules.d_hwrite_rule
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hwrite_rule width matches SSOT value 1
  - d_hwrite_rule RTL expression implements SSOT expression (1) if (is_store) else (0)
  - DUT port d_hwrite is the implementation/observation point for d_hwrite_rule
  - d_hwrite_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.TX_LOAD_STORE.output_rules.d_hwrite_rule

### RTL-0083: Implement side effect for TX_LOAD_STORE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.TX_LOAD_STORE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.side_effects.side_effect_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: value=pc advances after transfer completion.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: function_model.transactions.TX_LOAD_STORE.side_effects.side_effect_0

### RTL-0084: Implement error case for TX_LOAD_STORE: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.TX_LOAD_STORE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_LOAD_STORE.error_cases.error_case_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via function_model.transactions.TX_LOAD_STORE.
SSOT item context: condition=data bus response ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_LOAD_STORE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - function_model.transactions.TX_LOAD_STORE.error_cases.error_case_0 condition is implemented as RTL control logic: data bus response ERROR
- SSOT refs: function_model.transactions.TX_LOAD_STORE.error_cases.error_case_0

### RTL-0090: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via cycle_model.latency.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0096: Implement pipeline stage: EX

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.EX
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.EX.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via cycle_model.pipeline.
SSOT item context: stage=EX; action=Execute/branch/load-store and commit results; cycle=n+2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.EX
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - cycle_model.pipeline.EX timing uses SSOT cycle/latency n+2
  - cycle_model.pipeline.EX appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.EX

### RTL-0097: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via cycle_model.ordering.
SSOT item context: value=Program-order retirement: instruction i commits before i+1..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0098: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via cycle_model.ordering.
SSOT item context: value=Branch redirection affects subsequent fetch only after branch evaluation reaches commit boundary..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0120: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via error_handling.
SSOT item context: value=Only synchronous reset clears fault_halt.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0144: Prove module arm_m0_min_ex is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.arm_m0_min_ex.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arm_m0_min_ex.module_equivalence.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arm_m0_min_ex.module_equivalence
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
- SSOT refs: sub_modules.arm_m0_min_ex.module_equivalence

### RTL-0045: Implement and connect port d_haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_haddr.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_haddr; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_haddr
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_haddr width matches SSOT value 32
  - d_haddr port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_haddr

### RTL-0046: Implement and connect port d_htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_htrans.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_htrans; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_htrans
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_htrans width matches SSOT value 2
  - d_htrans port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_htrans

### RTL-0047: Implement and connect port d_hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hwrite.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hwrite; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hwrite
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hwrite width matches SSOT value 1
  - d_hwrite port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hwrite

### RTL-0048: Implement and connect port d_hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hsize.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hsize; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hsize
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hsize width matches SSOT value 3
  - d_hsize port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hsize

### RTL-0049: Implement and connect port d_hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hburst.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hburst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hburst
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hburst width matches SSOT value 3
  - d_hburst port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hburst

### RTL-0050: Implement and connect port d_hprot

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hprot
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hprot.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hprot; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hprot
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hprot width matches SSOT value 4
  - d_hprot port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hprot

### RTL-0051: Implement and connect port d_hmastlock

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hmastlock
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hmastlock.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hmastlock; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hmastlock
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hmastlock width matches SSOT value 1
  - d_hmastlock port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hmastlock

### RTL-0052: Implement and connect port d_hwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hwdata.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hwdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hwdata
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hwdata width matches SSOT value 32
  - d_hwdata port direction remains output
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hwdata

### RTL-0053: Implement and connect port d_hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hready.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hready
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hready width matches SSOT value 1
  - d_hready port direction remains input
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hready

### RTL-0054: Implement and connect port d_hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hrdata.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hrdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hrdata
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hrdata width matches SSOT value 32
  - d_hrdata port direction remains input
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hrdata

### RTL-0055: Implement and connect port d_hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_d_master.ports.d_hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_d_master.ports.d_hresp.
Owner: arm_m0_min_ex in rtl/arm_m0_min_ex.sv via io_list.interfaces.ahb_d_master.
SSOT item context: name=d_hresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_d_master.ports.d_hresp
  - Primary implementation evidence is in rtl/arm_m0_min_ex.sv
  - d_hresp width matches SSOT value 1
  - d_hresp port direction remains input
- SSOT refs: io_list.interfaces.ahb_d_master.ports.d_hresp
