# RTL Authoring Packet: module__dma_real_channel__function_model_02

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 3/9 section=function_model task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0129: Implement output rule for FM_DMA_COMPLETE: irq_assert

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.irq_assert
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.irq_assert.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: name=irq_assert; port=irq; expr=1 if (int_enable_q[ch_id]) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.output_rules.irq_assert
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - irq_assert width matches SSOT value 1
  - irq_assert RTL expression implements SSOT expression 1 if (int_enable_q[ch_id]) else 0
  - DUT port irq is the implementation/observation point for irq_assert
  - irq_assert is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.output_rules.irq_assert

### RTL-0130: Implement side effect for FM_DMA_COMPLETE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["ch_done_q[ch_id] set to 1", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_0

### RTL-0131: Implement side effect for FM_DMA_COMPLETE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["ch_busy_q[ch_id] cleared", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_1

### RTL-0132: Implement side effect for FM_DMA_COMPLETE: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["IRQ asserted if enabled", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.side_effects.side_effect_2

### RTL-0133: Implement transaction FM_DMA_ERROR

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMA_ERROR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMA_ERROR.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_ERROR

### RTL-0134: Implement precondition for FM_DMA_ERROR: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_ERROR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.preconditions.precondition_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: value=error condition detected (alignment, zero-length, bus error, timeout, or FIFO overflow).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_ERROR.preconditions.precondition_0

### RTL-0135: Implement output for FM_DMA_ERROR: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_ERROR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.outputs.output_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["ch_error", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.outputs.output_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.outputs.output_0

### RTL-0136: Implement output for FM_DMA_ERROR: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_ERROR.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.outputs.output_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["ch_err_code", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.outputs.output_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.outputs.output_1

### RTL-0137: Implement output for FM_DMA_ERROR: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_ERROR.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.outputs.output_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["irq", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.outputs.output_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.outputs.output_2

### RTL-0138: Implement output rule for FM_DMA_ERROR: error_assert

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_ERROR.output_rules.error_assert
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.output_rules.error_assert.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: name=error_assert; port=ch_error; expr=1; width=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.output_rules.error_assert
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - error_assert width matches SSOT value 1
  - error_assert RTL expression implements SSOT expression 1
  - DUT port ch_error is the implementation/observation point for error_assert
  - error_assert is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_ERROR.output_rules.error_assert

### RTL-0139: Implement output rule for FM_DMA_ERROR: error_code_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_ERROR.output_rules.error_code_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.output_rules.error_code_out.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: name=error_code_out; port=ch_err_code; expr=error_code; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.output_rules.error_code_out
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - error_code_out width matches SSOT value 3
  - error_code_out RTL expression implements SSOT expression error_code
  - DUT port ch_err_code is the implementation/observation point for error_code_out
  - error_code_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_ERROR.output_rules.error_code_out

### RTL-0140: Implement output rule for FM_DMA_ERROR: irq_error

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_ERROR.output_rules.irq_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.output_rules.irq_error.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: name=irq_error; port=irq; expr=1 if (int_enable_q[ch_id]) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.output_rules.irq_error
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - irq_error width matches SSOT value 1
  - irq_error RTL expression implements SSOT expression 1 if (int_enable_q[ch_id]) else 0
  - DUT port irq is the implementation/observation point for irq_error
  - irq_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_ERROR.output_rules.irq_error

### RTL-0141: Implement side effect for FM_DMA_ERROR: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["ch_error_q[ch_id] set to 1", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_0

### RTL-0142: Implement side effect for FM_DMA_ERROR: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["ch_busy_q[ch_id] cleared", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_1

### RTL-0143: Implement side effect for FM_DMA_ERROR: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["Error code latched in status register", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.side_effects.side_effect_2

### RTL-0144: Implement error case for FM_DMA_ERROR: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["alignment error (code 1)", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_0

### RTL-0145: Implement error case for FM_DMA_ERROR: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["zero length (code 2)", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.error_cases.error_case_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_1

### RTL-0146: Implement error case for FM_DMA_ERROR: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["bus error (code 3)", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.error_cases.error_case_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_2

### RTL-0147: Implement error case for FM_DMA_ERROR: error_case_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["timeout (code 4)", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.error_cases.error_case_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_3

### RTL-0148: Implement error case for FM_DMA_ERROR: error_case_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_ERROR.
SSOT item context: id=FM_DMA_ERROR; name=dma_error; port=["ch_error", "ch_err_code", "irq"]; signal=["FIFO overflow (code 5)", "ch_id", "error_code"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_ERROR.error_cases.error_case_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_error", "ch_err_code", "irq"] is the implementation/observation point for dma_error
- SSOT refs: function_model.transactions.FM_DMA_ERROR.error_cases.error_case_4

### RTL-0156: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...; signal=ch_busy and ch_done are not asserted together for the same channel.; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q", "int_enab....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...
- SSOT refs: function_model.invariants.invariant_0

### RTL-0157: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...; signal=ch_error is asserted only for invalid requests, bus errors, timeouts, or FIFO overflows.; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q", "timeout_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...
- SSOT refs: function_model.invariants.invariant_1

### RTL-0158: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...; signal=ch_remaining_q never underflows below zero.; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...
- SSOT refs: function_model.invariants.invariant_2

### RTL-0159: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...; signal=irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch].; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q", "dma_en_q....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...
- SSOT refs: function_model.invariants.invariant_3

### RTL-0160: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "ch_busy", "ch_d...; signal=irq_combined reflects OR of all per-channel irq outputs.; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q", "int_enab....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "ch_busy", "ch_d... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "ch_busy", "ch_d...
- SSOT refs: function_model.invariants.invariant_4

### RTL-0161: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...; signal=Each FIFO operates as circular buffer with gray-code synchronized pointers across clock domains..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "ch_id", "burst_len", "ch...
- SSOT refs: function_model.invariants.invariant_5

### RTL-0162: Preserve FL invariant invariant_6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_6
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_6.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["requester_mask", "arb_grant"]; signal=htrans transitions IDLE only when no channel has an active grant.; state=["ch_busy_q", "ch_done_q", "ch_error_q", "ch_remaining_q", "ch_src_addr_q", "ch_dst_addr_q", "ch_stride_q", "int_enab....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_6
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["requester_mask", "arb_grant"] is the implementation/observation point for ["requester_mask", "arb_grant"]
- SSOT refs: function_model.invariants.invariant_6

### RTL-0163: Preserve FL invariant invariant_7

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_7
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_7.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.invariants.
SSOT item context: port=["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "requester_mask", "arb_gr...; signal=Performance counters saturate at 32'hFFFFFFFF and do not wrap..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_7
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "requester_mask", "arb_gr... is the implementation/observation point for ["ch_id", "src_addr", "dst_addr", "length", "stride", "ch_busy", "ch_error", "ch_err_code", "requester_mask", "arb_gr...
- SSOT refs: function_model.invariants.invariant_7
