# RTL Authoring Packet: module__fifo_sync_flags__function_model_01

- Kind: module
- Owner module: fifo_sync_flags
- Owner file: rtl/fifo_sync_flags.sv
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
- LLM-actionable open tasks: 22
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, decomposition.units.flag_generation, function_model, function_model.transactions, function_model.transactions.output_rules
- Module slice: 1/4 section=function_model task_limit=48
- Slice rule: Owner module fifo_sync_flags is split into 4 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
  - fifo_sync_flags.almost_empty_o <= almost_empty_o (integration.connections[12])

## Tasks

### RTL-0065: Implement transaction FM1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM1; name=push.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0066: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=wr_en_i == 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0067: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o == 0 (count < DEPTH).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0068: Implement precondition for FM1: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=flush_i == 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_2

### RTL-0069: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=wr_data_i[DATA_WIDTH-1:0].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0070: Implement output for FM1: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o = (count + 1 - pop_accepted) == DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_0

### RTL-0071: Implement output for FM1: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=almost_full_o = (count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_1

### RTL-0072: Implement output for FM1: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = count + 1 - pop_accepted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_2

### RTL-0073: Implement output rule for FM1: full_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.full_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=full_o; port=full_o; expr=(count + 1 - pop_accepted) == DEPTH; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - full_o width matches SSOT value 1
  - full_o RTL expression implements SSOT expression (count + 1 - pop_accepted) == DEPTH
  - DUT port full_o is the implementation/observation point for full_o
  - full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.full_o

### RTL-0074: Implement output rule for FM1: almost_full_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.almost_full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.almost_full_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=almost_full_o; port=almost_full_o; expr=(count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.almost_full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - almost_full_o width matches SSOT value 1
  - almost_full_o RTL expression implements SSOT expression (count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD
  - DUT port almost_full_o is the implementation/observation point for almost_full_o
  - almost_full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.almost_full_o

### RTL-0075: Implement output rule for FM1: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=count + 1 - pop_accepted; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression count + 1 - pop_accepted
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.count_o

### RTL-0076: Implement state update for FM1: mem[wr_ptr]

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.mem_wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.mem_wr_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=mem[wr_ptr]; expr=wr_data_i; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.mem_wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - mem[wr_ptr] reset behavior matches SSOT value 0
  - mem[wr_ptr] RTL expression implements SSOT expression wr_data_i
  - mem[wr_ptr] updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.mem_wr_ptr

### RTL-0077: Implement state update for FM1: wr_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.wr_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=wr_ptr; expr=(wr_ptr + 1) % DEPTH; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - wr_ptr reset behavior matches SSOT value 0
  - wr_ptr RTL expression implements SSOT expression (wr_ptr + 1) % DEPTH
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.wr_ptr

### RTL-0078: Implement state update for FM1: count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.count.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count; expr=count + 1 - pop_accepted; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression count + 1 - pop_accepted
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.count

### RTL-0079: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=Architectural state updated per output_rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0080: Implement transaction FM2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM2; name=pop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0081: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=rd_en_i == 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0082: Implement precondition for FM2: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o == 0 (count > 0).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_1

### RTL-0083: Implement precondition for FM2: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=flush_i == 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_2

### RTL-0084: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=mem[rd_ptr].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0085: Implement output for FM2: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=rd_data_o = mem[rd_ptr].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_0

### RTL-0086: Implement output for FM2: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o = (count - 1 + push_accepted) == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_1

### RTL-0087: Implement output for FM2: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=almost_empty_o = (count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_2

### RTL-0088: Implement output for FM2: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_3.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = count - 1 + push_accepted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_3
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_3

### RTL-0089: Implement output rule for FM2: rd_data_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.rd_data_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.rd_data_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_data_o; port=rd_data_o; expr=mem[rd_ptr]; width=DATA_WIDTH.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.rd_data_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_data_o width matches SSOT value DATA_WIDTH
  - rd_data_o RTL expression implements SSOT expression mem[rd_ptr]
  - DUT port rd_data_o is the implementation/observation point for rd_data_o
  - rd_data_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.rd_data_o

### RTL-0090: Implement output rule for FM2: empty_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.empty_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=empty_o; port=empty_o; expr=(count - 1 + push_accepted) == 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - empty_o width matches SSOT value 1
  - empty_o RTL expression implements SSOT expression (count - 1 + push_accepted) == 0
  - DUT port empty_o is the implementation/observation point for empty_o
  - empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.empty_o

### RTL-0091: Implement output rule for FM2: almost_empty_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.almost_empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.almost_empty_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=almost_empty_o; port=almost_empty_o; expr=(count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.almost_empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - almost_empty_o width matches SSOT value 1
  - almost_empty_o RTL expression implements SSOT expression (count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD
  - DUT port almost_empty_o is the implementation/observation point for almost_empty_o
  - almost_empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.almost_empty_o

### RTL-0092: Implement output rule for FM2: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=count - 1 + push_accepted; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression count - 1 + push_accepted
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.count_o

### RTL-0093: Implement state update for FM2: rd_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.rd_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_ptr; expr=(rd_ptr + 1) % DEPTH; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_ptr reset behavior matches SSOT value 0
  - rd_ptr RTL expression implements SSOT expression (rd_ptr + 1) % DEPTH
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.rd_ptr

### RTL-0094: Implement state update for FM2: count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.count.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count; expr=count - 1 + push_accepted; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression count - 1 + push_accepted
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.count

### RTL-0095: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=Popped entry storage is invalidated (no read-again guarantee).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0096: Implement transaction FM3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM3; name=simultaneous_push_pop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3

### RTL-0097: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=wr_en_i == 1 and rd_en_i == 1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0098: Implement precondition for FM3: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o == 0 and empty_o == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_1

### RTL-0099: Implement precondition for FM3: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=flush_i == 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_2

### RTL-0100: Implement input for FM3: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=wr_data_i[DATA_WIDTH-1:0].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.inputs.input_0

### RTL-0101: Implement input for FM3: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=mem[rd_ptr].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.inputs.input_1

### RTL-0102: Implement output for FM3: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=rd_data_o = mem[rd_ptr].
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_0

### RTL-0103: Implement output for FM3: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o = count == DEPTH - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_1

### RTL-0104: Implement output for FM3: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o = count == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_2

### RTL-0105: Implement output for FM3: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM3.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.outputs.output_3.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = count.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.outputs.output_3
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.outputs.output_3

### RTL-0106: Implement output rule for FM3: rd_data_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.rd_data_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.rd_data_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_data_o; port=rd_data_o; expr=mem[rd_ptr]; width=DATA_WIDTH.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.rd_data_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_data_o width matches SSOT value DATA_WIDTH
  - rd_data_o RTL expression implements SSOT expression mem[rd_ptr]
  - DUT port rd_data_o is the implementation/observation point for rd_data_o
  - rd_data_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3.output_rules.rd_data_o

### RTL-0107: Implement output rule for FM3: full_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.full_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=full_o; port=full_o; expr=count == DEPTH - 1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - full_o width matches SSOT value 1
  - full_o RTL expression implements SSOT expression count == DEPTH - 1
  - DUT port full_o is the implementation/observation point for full_o
  - full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3.output_rules.full_o

### RTL-0108: Implement output rule for FM3: empty_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.empty_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=empty_o; port=empty_o; expr=count == 1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - empty_o width matches SSOT value 1
  - empty_o RTL expression implements SSOT expression count == 1
  - DUT port empty_o is the implementation/observation point for empty_o
  - empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3.output_rules.empty_o

### RTL-0109: Implement output rule for FM3: count_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=count; width=$clog2(DEPTH+1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
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
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=mem[wr_ptr]; expr=wr_data_i; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.mem_wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - mem[wr_ptr] reset behavior matches SSOT value 0
  - mem[wr_ptr] RTL expression implements SSOT expression wr_data_i
  - mem[wr_ptr] updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.mem_wr_ptr

### RTL-0111: Implement state update for FM3: wr_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.wr_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=wr_ptr; expr=(wr_ptr + 1) % DEPTH; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - wr_ptr reset behavior matches SSOT value 0
  - wr_ptr RTL expression implements SSOT expression (wr_ptr + 1) % DEPTH
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.wr_ptr

### RTL-0112: Implement state update for FM3: rd_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.rd_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_ptr; expr=(rd_ptr + 1) % DEPTH; reset=0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_ptr reset behavior matches SSOT value 0
  - rd_ptr RTL expression implements SSOT expression (rd_ptr + 1) % DEPTH
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.rd_ptr
