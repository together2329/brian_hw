# RTL Authoring Packet: module__atciic100_ctrl__function_model_02

- Kind: module
- Owner module: atciic100_ctrl
- Owner file: rtl/atciic100_ctrl.v
- Task count: 48
- Required tasks: 48

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, fsm, fsm.iic_phase, function_model, function_model.transactions
- Module slice: 2/7 section=function_model task_limit=48
- Slice rule: Owner module atciic100_ctrl is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])

## Tasks

### RTL-0101: Implement precondition for FM5: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=master==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_0

### RTL-0102: Implement precondition for FM5: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=trans==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_1

### RTL-0103: Implement precondition for FM5: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=cmd==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_2

### RTL-0104: Implement input for FM5: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM5.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=addr.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.inputs.input_0

### RTL-0105: Implement output for FM5: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=SCL/SDA signals driven for Start->Addr->Data->Stop.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.outputs.output_0

### RTL-0106: Implement output for FM5: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Data pushed to FIFO.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.outputs.output_1

### RTL-0107: Implement side effect for FM5: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=datacnt decrements.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_0

### RTL-0108: Implement side effect for FM5: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=ByteRecv interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_1

### RTL-0109: Implement side effect for FM5: side_effect_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=FIFO status updates.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_2

### RTL-0110: Implement error case for FM5: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM5.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=Slave NACK on address.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM5.error_cases.error_case_0 condition is implemented as RTL control logic: Slave NACK on address
- SSOT refs: function_model.transactions.FM5.error_cases.error_case_0

### RTL-0111: Implement transaction FM6

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM6
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM6.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM6; name=slave_send.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM6
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6

### RTL-0112: Implement precondition for FM6: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=master==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_0

### RTL-0113: Implement precondition for FM6: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=trans==1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_1

### RTL-0114: Implement precondition for FM6: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=addr matched.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_2

### RTL-0115: Implement input for FM6: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM6.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_clk.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.inputs.input_0

### RTL-0116: Implement input for FM6: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM6.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.inputs.input_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_data.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.inputs.input_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.inputs.input_1

### RTL-0117: Implement output for FM6: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Data from FIFO shifted out.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.outputs.output_0

### RTL-0118: Implement side effect for FM6: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=ByteTrans interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_0

### RTL-0119: Implement error case for FM6: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM6.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=FIFO Empty.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM6.error_cases.error_case_0 condition is implemented as RTL control logic: FIFO Empty
- SSOT refs: function_model.transactions.FM6.error_cases.error_case_0

### RTL-0120: Implement transaction FM7

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM7
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM7.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM7; name=slave_recv.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM7
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7

### RTL-0121: Implement precondition for FM7: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM7.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=master==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.preconditions.precondition_0

### RTL-0122: Implement precondition for FM7: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM7.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=trans==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.preconditions.precondition_1

### RTL-0123: Implement precondition for FM7: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM7.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.preconditions.precondition_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=addr matched.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.preconditions.precondition_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.preconditions.precondition_2

### RTL-0124: Implement input for FM7: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM7.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_clk.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.inputs.input_0

### RTL-0125: Implement input for FM7: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM7.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.inputs.input_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_data.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.inputs.input_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.inputs.input_1

### RTL-0126: Implement output for FM7: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM7.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Data pushed to FIFO.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.outputs.output_0

### RTL-0127: Implement side effect for FM7: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM7.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=ByteRecv interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM7.side_effects.side_effect_0

### RTL-0128: Implement error case for FM7: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM7.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=FIFO Full.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM7.error_cases.error_case_0 condition is implemented as RTL control logic: FIFO Full
- SSOT refs: function_model.transactions.FM7.error_cases.error_case_0

### RTL-0129: Implement transaction FM8

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM8
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM8.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM8; name=general_call.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM8
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8

### RTL-0130: Implement precondition for FM8: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM8.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=master==0.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.preconditions.precondition_0

### RTL-0131: Implement precondition for FM8: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM8.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Address byte == 0x00.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.preconditions.precondition_1

### RTL-0132: Implement input for FM8: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM8.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_clk.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.inputs.input_0

### RTL-0133: Implement input for FM8: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM8.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.inputs.input_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=bus_data.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.inputs.input_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.inputs.input_1

### RTL-0134: Implement output for FM8: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM8.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=ACK response.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.outputs.output_0

### RTL-0135: Implement output for FM8: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM8.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.outputs.output_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=int_st.GenCall = 1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.outputs.output_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.outputs.output_1

### RTL-0136: Implement side effect for FM8: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM8.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=AddrHit interrupt.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM8.side_effects.side_effect_0

### RTL-0137: Implement error case for FM8: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM8.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=Controller disabled (IICEn=0).
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM8.error_cases.error_case_0 condition is implemented as RTL control logic: Controller disabled (IICEn=0)
- SSOT refs: function_model.transactions.FM8.error_cases.error_case_0

### RTL-0138: Implement transaction FM9

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM9
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM9.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: id=FM9; name=dma_request.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM9
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9

### RTL-0139: Implement precondition for FM9: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM9.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.preconditions.precondition_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=setup.DMAEn == 1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9.preconditions.precondition_0

### RTL-0140: Implement precondition for FM9: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM9.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.preconditions.precondition_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=(trans==1 && fifo_count > 0) || (trans==0 && fifo_count < FIFO_DEPTH).
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.preconditions.precondition_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9.preconditions.precondition_1

### RTL-0141: Implement input for FM9: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM9.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.inputs.input_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=DMA Enable.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.inputs.input_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9.inputs.input_0

### RTL-0142: Implement output for FM9: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM9.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.outputs.output_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=i2c_req = 1.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.outputs.output_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9.outputs.output_0

### RTL-0143: Implement side effect for FM9: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM9.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.side_effects.side_effect_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=DMA transfers data between FIFO and memory via external DMA controller.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.transactions.FM9.side_effects.side_effect_0

### RTL-0144: Implement error case for FM9: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM9.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.error_cases.error_case_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: condition=DMA acknowledge timeout.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - function_model.transactions.FM9.error_cases.error_case_0 condition is implemented as RTL control logic: DMA acknowledge timeout
- SSOT refs: function_model.transactions.FM9.error_cases.error_case_0

### RTL-0145: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=FIFO count never exceeds FIFO_DEPTH parameter..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_0

### RTL-0146: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Phase transitions follow IDLE->START->ADDR->DAT->STOP strictly, unless ArbLose occurs..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_1

### RTL-0147: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=Arbitration Lost (ArbLose) terminates transmission immediately and releases bus..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_2

### RTL-0148: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=i2c_int is asserted if and only if (int_st & int_en) != 0..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_3
