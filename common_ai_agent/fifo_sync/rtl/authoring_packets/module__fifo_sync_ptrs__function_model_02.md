# RTL Authoring Packet: module__fifo_sync_ptrs__function_model_02

- Kind: module
- Owner module: fifo_sync_ptrs
- Owner file: rtl/fifo_sync_ptrs.sv
- Task count: 48
- Required tasks: 48

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, decomposition.units.pointer_control, fsm.ptr_fsm, function_model, function_model.state_variables, function_model.state_variables.count, function_model.state_variables.rd_ptr, function_model.state_variables.wr_ptr
- Module slice: 2/6 section=function_model task_limit=48
- Slice rule: Owner module fifo_sync_ptrs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0109: Implement output rule for FM3: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.count_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count_o; port=count_o; expr=count; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression count
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3.output_rules.count_o

### RTL-0110: Implement state update for FM3: mem[wr_ptr]

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.mem_wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.mem_wr_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=mem[wr_ptr]; expr=wr_data_i; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.mem_wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - mem[wr_ptr] reset behavior matches SSOT value 0
  - mem[wr_ptr] RTL expression implements SSOT expression wr_data_i
  - mem[wr_ptr] updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.mem_wr_ptr

### RTL-0111: Implement state update for FM3: wr_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.wr_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=wr_ptr; expr=(wr_ptr + 1) % DEPTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - wr_ptr reset behavior matches SSOT value 0
  - wr_ptr RTL expression implements SSOT expression (wr_ptr + 1) % DEPTH
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.wr_ptr

### RTL-0112: Implement state update for FM3: rd_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.rd_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=rd_ptr; expr=(rd_ptr + 1) % DEPTH; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - rd_ptr reset behavior matches SSOT value 0
  - rd_ptr RTL expression implements SSOT expression (rd_ptr + 1) % DEPTH
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.rd_ptr

### RTL-0113: Implement state update for FM3: count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.count.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count; expr=count; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression count
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.count

### RTL-0114: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count is unchanged because push and pop cancel.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0115: Implement transaction FM4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: id=FM4; name=overflow_reject.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4

### RTL-0116: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=wr_en_i == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0117: Implement precondition for FM4: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=full_o == 1 (count == DEPTH).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_1

### RTL-0118: Implement output for FM4: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=full_o = 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_0

### RTL-0119: Implement output for FM4: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count_o = DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_1

### RTL-0120: Implement output rule for FM4: full_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4.output_rules.full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.output_rules.full_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=full_o; port=full_o; expr=1; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - full_o width matches SSOT value 1
  - full_o RTL expression implements SSOT expression 1
  - DUT port full_o is the implementation/observation point for full_o
  - full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4.output_rules.full_o

### RTL-0121: Implement output rule for FM4: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.output_rules.count_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count_o; port=count_o; expr=DEPTH; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression DEPTH
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4.output_rules.count_o

### RTL-0122: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Write rejected silently; no data corruption.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0123: Implement transaction FM5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM5
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM5.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: id=FM5; name=underflow_reject.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM5
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5

### RTL-0124: Implement precondition for FM5: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=rd_en_i == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_0

### RTL-0125: Implement precondition for FM5: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=empty_o == 1 (count == 0).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_1

### RTL-0126: Implement output for FM5: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=empty_o = 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_0

### RTL-0127: Implement output for FM5: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=rd_data_o = previous_value_or_zero.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_1

### RTL-0128: Implement output for FM5: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count_o = 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_2

### RTL-0129: Implement output rule for FM5: empty_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.empty_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=empty_o; port=empty_o; expr=1; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - empty_o width matches SSOT value 1
  - empty_o RTL expression implements SSOT expression 1
  - DUT port empty_o is the implementation/observation point for empty_o
  - empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM5.output_rules.empty_o

### RTL-0130: Implement output rule for FM5: rd_data_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.rd_data_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.rd_data_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=rd_data_o; port=rd_data_o; expr=previous_value_or_zero; width=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.rd_data_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - rd_data_o width matches SSOT value DATA_WIDTH
  - rd_data_o RTL expression implements SSOT expression previous_value_or_zero
  - DUT port rd_data_o is the implementation/observation point for rd_data_o
  - rd_data_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM5.output_rules.rd_data_o

### RTL-0131: Implement output rule for FM5: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.count_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count_o; port=count_o; expr=0; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression 0
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM5.output_rules.count_o

### RTL-0132: Implement side effect for FM5: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Read rejected silently; rd_data_o holds previous value (not guaranteed).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_0

### RTL-0133: Implement transaction FM6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM6
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM6.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: id=FM6; name=flush.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM6
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6

### RTL-0134: Implement precondition for FM6: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=flush_i == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_0

### RTL-0135: Implement output for FM6: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=empty_o = 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_0

### RTL-0136: Implement output for FM6: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=full_o = 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_1

### RTL-0137: Implement output for FM6: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=almost_full_o = 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_2

### RTL-0138: Implement output for FM6: output_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=almost_empty_o = 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_3

### RTL-0139: Implement output for FM6: output_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count_o = 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_4

### RTL-0140: Implement output rule for FM6: empty_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.empty_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=empty_o; port=empty_o; expr=1; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - empty_o width matches SSOT value 1
  - empty_o RTL expression implements SSOT expression 1
  - DUT port empty_o is the implementation/observation point for empty_o
  - empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.empty_o

### RTL-0141: Implement output rule for FM6: full_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.full_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=full_o; port=full_o; expr=0; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - full_o width matches SSOT value 1
  - full_o RTL expression implements SSOT expression 0
  - DUT port full_o is the implementation/observation point for full_o
  - full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.full_o

### RTL-0142: Implement output rule for FM6: almost_full_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.almost_full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.almost_full_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=almost_full_o; port=almost_full_o; expr=0; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.almost_full_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - almost_full_o width matches SSOT value 1
  - almost_full_o RTL expression implements SSOT expression 0
  - DUT port almost_full_o is the implementation/observation point for almost_full_o
  - almost_full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.almost_full_o

### RTL-0143: Implement output rule for FM6: almost_empty_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.almost_empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.almost_empty_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=almost_empty_o; port=almost_empty_o; expr=1; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.almost_empty_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - almost_empty_o width matches SSOT value 1
  - almost_empty_o RTL expression implements SSOT expression 1
  - DUT port almost_empty_o is the implementation/observation point for almost_empty_o
  - almost_empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.almost_empty_o

### RTL-0144: Implement output rule for FM6: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.count_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count_o; port=count_o; expr=0; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression 0
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.count_o

### RTL-0145: Implement state update for FM6: wr_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.wr_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=wr_ptr; expr=0; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - wr_ptr reset behavior matches SSOT value 0
  - wr_ptr RTL expression implements SSOT expression 0
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.wr_ptr

### RTL-0146: Implement state update for FM6: rd_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.rd_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=rd_ptr; expr=0; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - rd_ptr reset behavior matches SSOT value 0
  - rd_ptr RTL expression implements SSOT expression 0
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.rd_ptr

### RTL-0147: Implement state update for FM6: count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.count.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: name=count; expr=0; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression 0
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.count

### RTL-0148: Implement side effect for FM6: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=All FIFO entries invalidated; memory contents become undefined.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_0

### RTL-0149: Implement side effect for FM6: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Flush takes precedence over concurrent push/pop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_1

### RTL-0150: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count is always in range [0, DEPTH]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0151: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=full_o == 1 if and only if count == DEPTH..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0152: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=empty_o == 1 if and only if count == 0..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0153: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=wr_ptr and rd_ptr are always in range [0, DEPTH-1]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0154: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=No read data changes unless rd_en_i is accepted or flush occurs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_4

### RTL-0155: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Simultaneous push/pop leaves count unchanged..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_5

### RTL-0156: Preserve FL invariant invariant_6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_6
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_6.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Overflow and underflow are silently rejected with no state corruption..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_6
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_6
