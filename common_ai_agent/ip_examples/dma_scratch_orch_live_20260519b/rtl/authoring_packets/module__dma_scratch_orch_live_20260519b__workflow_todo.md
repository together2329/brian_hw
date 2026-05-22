# RTL Authoring Packet: module__dma_scratch_orch_live_20260519b__workflow_todo

- Kind: module
- Owner module: dma_scratch_orch_live_20260519b
- Owner file: rtl/dma_scratch_orch_live_20260519b.sv
- Task count: 32
- Required tasks: 32

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 14/15 section=workflow_todo task_limit=48
- Slice rule: Owner module dma_scratch_orch_live_20260519b is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 21

## Tasks

### RTL-0020: Implement the complete SSOT RTL contract without fixed-template fallback behavior

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Use the current SSOT as the only source for ports, parameters, function_model, cycle_model, registers, dataflow, error/security/debug behavior, decomposition ownership, and quality gates.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPLEMENT_SSOT_CONTRACT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Generated RTL drives only SSOT-approved externally visible behavior
  - No placeholder heartbeat, tie-off, alive-only, or comment-only implementation is used as evidence
  - derive_rtl_todos.py --audit-rtl reports every required TODO as pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, top_module
- SSOT refs: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, top_module, workflow_todos.rtl-gen[0]

### RTL-0021: Implement or account for SSOT module slice `dma_scratch_orch_live_20260519b_behavior_contract`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Conceptual owner for SSOT function-model behavior implemented by the generated RTL.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_DMA_SCRATCH_ORCH_LIVE_20260519B_BEHAVIOR_CONTRACT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3, function_model.transactions.FM4, test_requirements
- SSOT refs: cycle_model, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1, function_model.transactions.FM2, function_model.transactions.FM3, function_model.transactions.FM4, test_requirements, workflow_todos.rtl-gen[1]

### RTL-0022: Implement or account for SSOT module slice `dma_scratch_orch_live_20260519b`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Top-level integration module matching SSOT top_module
SSOT ref: workflow_todos.rtl-gen[2].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_DMA_SCRATCH_ORCH_LIVE_20260519B.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: dataflow, decomposition, integration, io_list, top_module
- SSOT refs: dataflow, decomposition, integration, io_list, top_module, workflow_todos.rtl-gen[2]

### RTL-0023: Implement FunctionalModel transaction `FM1` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Preconditions: Feature trigger is asserted under legal configuration. Outputs: Architectural output matches feature definition; name=irq; description=Auto-injected benign observable rule so the function_model has at least one scoreboard-visible out...; description=Repair marker making this transaction machine-checkable; ssot-gen should r.... Side effects: Architectural state updates according to FSM/control policy. Error cases: condition=Downstream protocol response is non-OKAY or invalid.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions.FM1, function_model.transactions[0]
- SSOT refs: function_model.transactions.FM1, function_model.transactions[0], workflow_todos.rtl-gen[3]

### RTL-0024: Drive output rule `irq` from FunctionalModel expression

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: Expression: 0
SSOT ref: workflow_todos.rtl-gen[4].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_OUTPUT_RULE_IRQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL output `irq` follows the SSOT expression
  - Expression inputs are mapped through rtl_contract.input_map or declared ports
  - FL-vs-RTL scoreboard can compare this observable without changing SSOT
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions[0].output_rules[0]
- SSOT refs: function_model.transactions[0].output_rules[0], workflow_todos.rtl-gen[4]

### RTL-0025: Implement state update `fm1_observed` from FunctionalModel expression

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[5]
- Detail: Expression: 1
SSOT ref: workflow_todos.rtl-gen[5].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_STATE_UPDATE_FM1_OBSERVED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL updates the state only on the approved sample condition
  - Reset value and width match function_model.state_variables
  - Debug/status visibility remains consistent with SSOT traceability
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[5]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions[0].state_updates[0]
- SSOT refs: function_model.transactions[0].state_updates[0], workflow_todos.rtl-gen[5]

### RTL-0026: Implement FunctionalModel transaction `FM2` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[6]
- Detail: Preconditions: Feature trigger is asserted under legal configuration. Outputs: Architectural output matches feature definition; description=Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectu.... Side effects: Architectural state updates according to FSM/control policy. Error cases: condition=Downstream protocol response is non-OKAY or invalid.
SSOT ref: workflow_todos.rtl-gen[6].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[6]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions.FM2, function_model.transactions[1]
- SSOT refs: function_model.transactions.FM2, function_model.transactions[1], workflow_todos.rtl-gen[6]

### RTL-0027: Implement state update `fm2_observed` from FunctionalModel expression

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[7]
- Detail: Expression: 1
SSOT ref: workflow_todos.rtl-gen[7].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_STATE_UPDATE_FM2_OBSERVED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL updates the state only on the approved sample condition
  - Reset value and width match function_model.state_variables
  - Debug/status visibility remains consistent with SSOT traceability
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[7]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions[1].state_updates[0]
- SSOT refs: function_model.transactions[1].state_updates[0], workflow_todos.rtl-gen[7]

### RTL-0028: Implement FunctionalModel transaction `FM3` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[8]
- Detail: Preconditions: Feature trigger is asserted under legal configuration. Outputs: Architectural output matches feature definition; description=Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectu.... Side effects: Architectural state updates according to FSM/control policy. Error cases: condition=Downstream protocol response is non-OKAY or invalid.
SSOT ref: workflow_todos.rtl-gen[8].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[8]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions.FM3, function_model.transactions[2]
- SSOT refs: function_model.transactions.FM3, function_model.transactions[2], workflow_todos.rtl-gen[8]

### RTL-0029: Implement state update `fm3_observed` from FunctionalModel expression

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[9]
- Detail: Expression: 1
SSOT ref: workflow_todos.rtl-gen[9].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_STATE_UPDATE_FM3_OBSERVED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL updates the state only on the approved sample condition
  - Reset value and width match function_model.state_variables
  - Debug/status visibility remains consistent with SSOT traceability
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[9]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions[2].state_updates[0]
- SSOT refs: function_model.transactions[2].state_updates[0], workflow_todos.rtl-gen[9]

### RTL-0030: Implement FunctionalModel transaction `FM4` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[10]
- Detail: Preconditions: Feature trigger is asserted under legal configuration. Outputs: Architectural output matches feature definition; description=Repair marker making this transaction machine-checkable; ssot-gen should replace with IP-specific architectu.... Side effects: Architectural state updates according to FSM/control policy. Error cases: condition=Downstream protocol response is non-OKAY or invalid.
SSOT ref: workflow_todos.rtl-gen[10].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[10]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions.FM4, function_model.transactions[3]
- SSOT refs: function_model.transactions.FM4, function_model.transactions[3], workflow_todos.rtl-gen[10]

### RTL-0031: Implement state update `fm4_observed` from FunctionalModel expression

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[11]
- Detail: Expression: 1
SSOT ref: workflow_todos.rtl-gen[11].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_STATE_UPDATE_FM4_OBSERVED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL updates the state only on the approved sample condition
  - Reset value and width match function_model.state_variables
  - Debug/status visibility remains consistent with SSOT traceability
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[11]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: function_model.transactions[3].state_updates[0]
- SSOT refs: function_model.transactions[3].state_updates[0], workflow_todos.rtl-gen[11]

### RTL-0032: Implement cycle_model handshake rule 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[12]
- Detail: rule=csr_valid payload remains stable until csr_ready is sampled asserted on csr_slave.
SSOT ref: workflow_todos.rtl-gen[12].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_handshake_rules_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[12]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.handshake_rules[0]
- SSOT refs: cycle_model.handshake_rules[0], workflow_todos.rtl-gen[12]

### RTL-0033: Implement cycle_model handshake rule 1

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[13]
- Detail: rule=mem_req_valid payload remains stable until mem_req_ready is sampled asserted on mem_master.
SSOT ref: workflow_todos.rtl-gen[13].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_handshake_rules_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[13]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.handshake_rules[1]
- SSOT refs: cycle_model.handshake_rules[1], workflow_todos.rtl-gen[13]

### RTL-0034: Implement cycle_model pipeline stage 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[14]
- Detail: action=Accept legal request/command/packet/control work under declared handshake rules.
SSOT ref: workflow_todos.rtl-gen[14].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[14]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.pipeline[0]
- SSOT refs: cycle_model.pipeline[0], workflow_todos.rtl-gen[14]

### RTL-0035: Implement cycle_model pipeline stage 1

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[15]
- Detail: action=Evaluate function_model transaction and update only declared state.
SSOT ref: workflow_todos.rtl-gen[15].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[15]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.pipeline[1]
- SSOT refs: cycle_model.pipeline[1], workflow_todos.rtl-gen[15]

### RTL-0036: Implement cycle_model pipeline stage 2

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[16]
- Detail: action=Publish response/status/output/debug event and hold it stable until accepted.
SSOT ref: workflow_todos.rtl-gen[16].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[16]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.pipeline[2]
- SSOT refs: cycle_model.pipeline[2], workflow_todos.rtl-gen[16]

### RTL-0037: Implement cycle_model ordering rule 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[17]
- Detail: Accepted requests update architectural state only on clock edges.
SSOT ref: workflow_todos.rtl-gen[17].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_ordering_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[17]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.ordering[0]
- SSOT refs: cycle_model.ordering[0], workflow_todos.rtl-gen[17]

### RTL-0038: Implement cycle_model ordering rule 1

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[18]
- Detail: Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.
SSOT ref: workflow_todos.rtl-gen[18].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_ordering_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[18]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.ordering[1]
- SSOT refs: cycle_model.ordering[1], workflow_todos.rtl-gen[18]

### RTL-0039: Implement cycle_model ordering rule 2

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[19]
- Detail: Backpressure stalls the active handshake stage without corrupting stored state.
SSOT ref: workflow_todos.rtl-gen[19].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_ordering_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[19]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.ordering[2]
- SSOT refs: cycle_model.ordering[2], workflow_todos.rtl-gen[19]

### RTL-0040: Implement cycle_model ordering rule 3

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[20]
- Detail: Read/dataflow stages must precede dependent write/output stages where declared in dataflow.
SSOT ref: workflow_todos.rtl-gen[20].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_ordering_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[20]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.ordering[3]
- SSOT refs: cycle_model.ordering[3], workflow_todos.rtl-gen[20]

### RTL-0041: Implement cycle_model backpressure rule 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[21]
- Detail: Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable.
SSOT ref: workflow_todos.rtl-gen[21].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_backpressure_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[21]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: cycle_model.backpressure[0]
- SSOT refs: cycle_model.backpressure[0], workflow_todos.rtl-gen[21]

### RTL-0051: Close all rtl_gate.rtl_gen quality-gate TODOs with fresh evidence

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[31]
- Detail: Run dynamic TODO audit, DUT compile, DUT-only lint, and static traceability checks after the final RTL edit. The gate TODOs are pass/fail work items, not summary prose.
SSOT ref: workflow_todos.rtl-gen[31].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_CLOSE_GATE_TODOS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - SSOT authority, workflow TODO format, owner traceability, static RTL evidence, compile, lint, and closure gate TODOs pass
  - rtl_compile.json and lint/dut_lint.json are fresh and clean
  - open_required_todos is zero
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[31]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: generation_flow, quality_gates.rtl, quality_gates.rtl_gen, workflow_todos.rtl-gen
- SSOT refs: generation_flow, quality_gates.rtl, quality_gates.rtl_gen, workflow_todos.rtl-gen, workflow_todos.rtl-gen[31]

### RTL-0042: Expose RTL behavior needed by SSOT scenario `SC01`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[22]
- Detail: Stimulus: Assert and release the declared reset while all external interfaces remain idle.. Expected: Architectural state, status, outputs, and debug observability match function_model reset outputs..
SSOT ref: workflow_todos.rtl-gen[22].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC01.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[22]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[0]
- SSOT refs: test_requirements.scenarios[0], workflow_todos.rtl-gen[22]

### RTL-0043: Expose RTL behavior needed by SSOT scenario `SC02`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[23]
- Detail: Stimulus: Drive a legal request, transaction, command, packet, or CSR operation from function_model primary preconditions.. Expected: Externally observable result/status/side effects match the function_model primary transaction..
SSOT ref: workflow_todos.rtl-gen[23].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC02.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[23]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[1]
- SSOT refs: test_requirements.scenarios[1], workflow_todos.rtl-gen[23]

### RTL-0044: Expose RTL behavior needed by SSOT scenario `SC03`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[24]
- Detail: Stimulus: Apply legal stalls or delayed handshakes on every declared cycle_model interface phase.. Expected: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..
SSOT ref: workflow_todos.rtl-gen[24].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC03.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[24]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[2]
- SSOT refs: test_requirements.scenarios[2], workflow_todos.rtl-gen[24]

### RTL-0045: Expose RTL behavior needed by SSOT scenario `SC04`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[25]
- Detail: Stimulus: Inject each declared error_handling.error_sources condition where the interface can represent it.. Expected: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..
SSOT ref: workflow_todos.rtl-gen[25].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC04.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[25]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[3]
- SSOT refs: test_requirements.scenarios[3], workflow_todos.rtl-gen[25]

### RTL-0046: Expose RTL behavior needed by SSOT scenario `SC05`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[26]
- Detail: Stimulus: Run nominal and error flows while sampling every debug_observability waveform/status/trace point.. Expected: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..
SSOT ref: workflow_todos.rtl-gen[26].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC05.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[26]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[4]
- SSOT refs: test_requirements.scenarios[4], workflow_todos.rtl-gen[26]

### RTL-0047: Expose RTL behavior needed by SSOT scenario `SC06`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[27]
- Detail: Stimulus: Drive preconditions for function_model transaction `FM1`.. Expected: Outputs and side effects match `FM1` exactly..
SSOT ref: workflow_todos.rtl-gen[27].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC06.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[27]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[5]
- SSOT refs: test_requirements.scenarios[5], workflow_todos.rtl-gen[27]

### RTL-0048: Expose RTL behavior needed by SSOT scenario `SC07`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[28]
- Detail: Stimulus: Drive preconditions for function_model transaction `FM2`.. Expected: Outputs and side effects match `FM2` exactly..
SSOT ref: workflow_todos.rtl-gen[28].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC07.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[28]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[6]
- SSOT refs: test_requirements.scenarios[6], workflow_todos.rtl-gen[28]

### RTL-0049: Expose RTL behavior needed by SSOT scenario `SC08`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[29]
- Detail: Stimulus: Drive preconditions for function_model transaction `FM3`.. Expected: Outputs and side effects match `FM3` exactly..
SSOT ref: workflow_todos.rtl-gen[29].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC08.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[29]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[7]
- SSOT refs: test_requirements.scenarios[7], workflow_todos.rtl-gen[29]

### RTL-0050: Expose RTL behavior needed by SSOT scenario `SC09`

- Priority: normal
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[30]
- Detail: Stimulus: Drive preconditions for function_model transaction `FM4`.. Expected: Outputs and side effects match `FM4` exactly..
SSOT ref: workflow_todos.rtl-gen[30].
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via workflow_todos.owner.
SSOT item context: id=RTL_SCENARIO_SUPPORT_SC09.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL has observable behavior for the scenario checker without weakening expected results
  - Scenario coverage can be closed by tb-gen using function_model/cycle_model
  - If behavior is unsupported, rtl-gen emits a precise SSOT question instead of a fake pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[30]
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - Semantic source_refs covered: test_requirements.scenarios[8]
- SSOT refs: test_requirements.scenarios[8], workflow_todos.rtl-gen[30]
