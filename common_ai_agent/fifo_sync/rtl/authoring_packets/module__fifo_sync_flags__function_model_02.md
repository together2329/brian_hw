# RTL Authoring Packet: module__fifo_sync_flags__function_model_02

- Kind: module
- Owner module: fifo_sync_flags
- Owner file: rtl/fifo_sync_flags.sv
- Task count: 37
- Required tasks: 37

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
- LLM-actionable open tasks: 37
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, function_model, function_model.transactions, function_model.transactions.output_rules
- Module slice: 2/4 section=function_model task_limit=48
- Slice rule: Owner module fifo_sync_flags is split into 4 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
  - fifo_sync_flags.almost_empty_o <= almost_empty_o (integration.connections[12])

## Tasks

### RTL-0113: Implement state update for FM3: count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.count.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count; expr=count; reset=0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression count
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.count

### RTL-0114: Implement side effect for FM3: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.side_effects.side_effect_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count is unchanged because push and pop cancel.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM3.side_effects.side_effect_0

### RTL-0115: Implement transaction FM4

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM4; name=overflow_reject.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4

### RTL-0116: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=wr_en_i == 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0117: Implement precondition for FM4: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o == 1 (count == DEPTH).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_1

### RTL-0118: Implement output for FM4: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o = 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_0

### RTL-0119: Implement output for FM4: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = DEPTH.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_1

### RTL-0120: Implement output rule for FM4: full_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4.output_rules.full_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.output_rules.full_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=full_o; port=full_o; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - full_o width matches SSOT value 1
  - full_o RTL expression implements SSOT expression 1
  - DUT port full_o is the implementation/observation point for full_o
  - full_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4.output_rules.full_o

### RTL-0121: Implement output rule for FM4: count_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=DEPTH; width=$clog2(DEPTH+1).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression DEPTH
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4.output_rules.count_o

### RTL-0122: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=Write rejected silently; no data corruption.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0123: Implement transaction FM5

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM5
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM5.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM5; name=underflow_reject.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM5
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5

### RTL-0124: Implement precondition for FM5: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=rd_en_i == 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_0

### RTL-0125: Implement precondition for FM5: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o == 1 (count == 0).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_1

### RTL-0126: Implement output for FM5: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o = 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_0

### RTL-0127: Implement output for FM5: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=rd_data_o = previous_value_or_zero.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_1

### RTL-0128: Implement output for FM5: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = 0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_2

### RTL-0129: Implement output rule for FM5: empty_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.empty_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=empty_o; port=empty_o; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - empty_o width matches SSOT value 1
  - empty_o RTL expression implements SSOT expression 1
  - DUT port empty_o is the implementation/observation point for empty_o
  - empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM5.output_rules.empty_o

### RTL-0130: Implement output rule for FM5: rd_data_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.rd_data_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.rd_data_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_data_o; port=rd_data_o; expr=previous_value_or_zero; width=DATA_WIDTH.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.rd_data_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_data_o width matches SSOT value DATA_WIDTH
  - rd_data_o RTL expression implements SSOT expression previous_value_or_zero
  - DUT port rd_data_o is the implementation/observation point for rd_data_o
  - rd_data_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM5.output_rules.rd_data_o

### RTL-0131: Implement output rule for FM5: count_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM5.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=0; width=$clog2(DEPTH+1).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
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
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=Read rejected silently; rd_data_o holds previous value (not guaranteed).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_0

### RTL-0133: Implement transaction FM6

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM6
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM6.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: id=FM6; name=flush.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM6
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6

### RTL-0134: Implement precondition for FM6: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=flush_i == 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_0

### RTL-0135: Implement output for FM6: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=empty_o = 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_0

### RTL-0136: Implement output for FM6: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=full_o = 0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_1

### RTL-0137: Implement output for FM6: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_2.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=almost_full_o = 0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_2

### RTL-0138: Implement output for FM6: output_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_3.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=almost_empty_o = 1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_3
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_3

### RTL-0139: Implement output for FM6: output_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_4.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=count_o = 0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_4
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_4

### RTL-0140: Implement output rule for FM6: empty_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.empty_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.empty_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=empty_o; port=empty_o; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
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
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=full_o; port=full_o; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
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
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=almost_full_o; port=almost_full_o; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.almost_full_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
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
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=almost_empty_o; port=almost_empty_o; expr=1; width=1.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.almost_empty_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - almost_empty_o width matches SSOT value 1
  - almost_empty_o RTL expression implements SSOT expression 1
  - DUT port almost_empty_o is the implementation/observation point for almost_empty_o
  - almost_empty_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.almost_empty_o

### RTL-0144: Implement output rule for FM6: count_o

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM6.output_rules.count_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.output_rules.count_o.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count_o; port=count_o; expr=0; width=$clog2(DEPTH+1).
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.output_rules.count_o
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count_o width matches SSOT value $clog2(DEPTH+1)
  - count_o RTL expression implements SSOT expression 0
  - DUT port count_o is the implementation/observation point for count_o
  - count_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM6.output_rules.count_o

### RTL-0145: Implement state update for FM6: wr_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.wr_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=wr_ptr; expr=0; reset=0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - wr_ptr reset behavior matches SSOT value 0
  - wr_ptr RTL expression implements SSOT expression 0
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.wr_ptr

### RTL-0146: Implement state update for FM6: rd_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.rd_ptr.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=rd_ptr; expr=0; reset=0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - rd_ptr reset behavior matches SSOT value 0
  - rd_ptr RTL expression implements SSOT expression 0
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.rd_ptr

### RTL-0147: Implement state update for FM6: count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM6.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.state_updates.count.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: name=count; expr=0; reset=0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
  - count reset behavior matches SSOT value 0
  - count RTL expression implements SSOT expression 0
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM6.state_updates.count

### RTL-0148: Implement side effect for FM6: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_0.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=All FIFO entries invalidated; memory contents become undefined.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_0

### RTL-0149: Implement side effect for FM6: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_1.
Owner: fifo_sync_flags in rtl/fifo_sync_flags.sv via function_model.transactions.
SSOT item context: value=Flush takes precedence over concurrent push/pop.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_flags.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/fifo_sync_flags.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_1
