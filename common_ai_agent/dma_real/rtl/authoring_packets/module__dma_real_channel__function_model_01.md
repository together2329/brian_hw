# RTL Authoring Packet: module__dma_real_channel__function_model_01

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0081: Implement transaction FM_DMA_START

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMA_START
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMA_START.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_START

### RTL-0082: Implement precondition for FM_DMA_START: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_START.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.preconditions.precondition_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: value=presetn and hresetn are deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_START.preconditions.precondition_0

### RTL-0083: Implement precondition for FM_DMA_START: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_START.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.preconditions.precondition_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: value=dma_en_q == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.preconditions.precondition_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_START.preconditions.precondition_1

### RTL-0084: Implement precondition for FM_DMA_START: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_START.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.preconditions.precondition_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: value=ch_busy_q[ch_id] == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.preconditions.precondition_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_START.preconditions.precondition_2

### RTL-0085: Implement output for FM_DMA_START: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_START.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.outputs.output_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_busy", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.outputs.output_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.outputs.output_0

### RTL-0086: Implement output for FM_DMA_START: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_START.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.outputs.output_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_error", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.outputs.output_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.outputs.output_1

### RTL-0087: Implement output for FM_DMA_START: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_START.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.outputs.output_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_err_code", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.outputs.output_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.outputs.output_2

### RTL-0088: Implement output rule for FM_DMA_START: ch_busy_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_START.output_rules.ch_busy_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.output_rules.ch_busy_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: name=ch_busy_next; port=ch_busy; expr=1 if (dma_en_q and not ch_busy_q[ch_id] and length > 0 and (src_addr % 4 == 0) and (dst_addr % 4 == 0)) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.output_rules.ch_busy_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - ch_busy_next width matches SSOT value 1
  - ch_busy_next RTL expression implements SSOT expression 1 if (dma_en_q and not ch_busy_q[ch_id] and length > 0 and (src_addr % 4 == 0) and (dst_addr % 4 == 0)) else 0
  - DUT port ch_busy is the implementation/observation point for ch_busy_next
  - ch_busy_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_START.output_rules.ch_busy_next

### RTL-0089: Implement output rule for FM_DMA_START: ch_error_flag

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_START.output_rules.ch_error_flag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.output_rules.ch_error_flag.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: name=ch_error_flag; port=ch_error; expr=1 if (length == 0 or src_addr % 4 != 0 or dst_addr % 4 != 0) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.output_rules.ch_error_flag
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - ch_error_flag width matches SSOT value 1
  - ch_error_flag RTL expression implements SSOT expression 1 if (length == 0 or src_addr % 4 != 0 or dst_addr % 4 != 0) else 0
  - DUT port ch_error is the implementation/observation point for ch_error_flag
  - ch_error_flag is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_START.output_rules.ch_error_flag

### RTL-0090: Implement output rule for FM_DMA_START: ch_err_code_val

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_START.output_rules.ch_err_code_val
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.output_rules.ch_err_code_val.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: name=ch_err_code_val; port=ch_err_code; expr=2 if (length == 0) else 1 if (src_addr % 4 != 0 or dst_addr % 4 != 0) else 0; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.output_rules.ch_err_code_val
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - ch_err_code_val width matches SSOT value 3
  - ch_err_code_val RTL expression implements SSOT expression 2 if (length == 0) else 1 if (src_addr % 4 != 0 or dst_addr % 4 != 0) else 0
  - DUT port ch_err_code is the implementation/observation point for ch_err_code_val
  - ch_err_code_val is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_START.output_rules.ch_err_code_val

### RTL-0091: Implement side effect for FM_DMA_START: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_remaining_q[ch_id] set to length on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_0

### RTL-0092: Implement side effect for FM_DMA_START: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_src_addr_q[ch_id] set to src_addr on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_1

### RTL-0093: Implement side effect for FM_DMA_START: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_dst_addr_q[ch_id] set to dst_addr on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_2

### RTL-0094: Implement side effect for FM_DMA_START: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["ch_stride_q[ch_id] set to stride on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_3

### RTL-0095: Implement side effect for FM_DMA_START: side_effect_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["perf_cycles_q[ch_id] reset to 0 on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_4

### RTL-0096: Implement side effect for FM_DMA_START: side_effect_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_5
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.side_effects.side_effect_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["perf_words_q[ch_id] reset to 0 on valid start", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.side_effects.side_effect_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.side_effects.side_effect_5

### RTL-0097: Implement error case for FM_DMA_START: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_START.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.error_cases.error_case_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["zero length (length == 0, error code 2)", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.error_cases.error_case_0

### RTL-0098: Implement error case for FM_DMA_START: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_START.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.error_cases.error_case_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["misaligned source address (src_addr % 4 != 0, error code 1)", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.error_cases.error_case_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.error_cases.error_case_1

### RTL-0099: Implement error case for FM_DMA_START: error_case_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_START.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.error_cases.error_case_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["misaligned destination address (dst_addr % 4 != 0, error code 1)", "ch_id", "src_addr", "dst_addr", "length", "stri....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.error_cases.error_case_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.error_cases.error_case_2

### RTL-0100: Implement error case for FM_DMA_START: error_case_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_START.error_cases.error_case_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_START.error_cases.error_case_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_START.
SSOT item context: id=FM_DMA_START; name=dma_start; port=["ch_busy", "ch_error", "ch_err_code"]; signal=["start while busy (ignored, preserves state)", "ch_id", "src_addr", "dst_addr", "length", "stride"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_START.error_cases.error_case_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_error", "ch_err_code"] is the implementation/observation point for dma_start
- SSOT refs: function_model.transactions.FM_DMA_START.error_cases.error_case_3

### RTL-0101: Implement transaction FM_DMA_STEP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMA_STEP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMA_STEP.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_STEP

### RTL-0102: Implement precondition for FM_DMA_STEP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_STEP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.preconditions.precondition_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: value=ch_busy_q[ch_id] == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_STEP.preconditions.precondition_0

### RTL-0103: Implement precondition for FM_DMA_STEP: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_STEP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.preconditions.precondition_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: value=arbiter has granted bus to ch_id.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_STEP.preconditions.precondition_1

### RTL-0104: Implement output for FM_DMA_STEP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_STEP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.outputs.output_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["ch_busy", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.outputs.output_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.outputs.output_0

### RTL-0105: Implement output for FM_DMA_STEP: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_STEP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.outputs.output_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["ch_done", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.outputs.output_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.outputs.output_1

### RTL-0106: Implement output rule for FM_DMA_STEP: busy_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_STEP.output_rules.busy_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.output_rules.busy_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=busy_next; port=ch_busy; expr=1 if (ch_remaining_q[ch_id] > burst_len) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.output_rules.busy_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - busy_next width matches SSOT value 1
  - busy_next RTL expression implements SSOT expression 1 if (ch_remaining_q[ch_id] > burst_len) else 0
  - DUT port ch_busy is the implementation/observation point for busy_next
  - busy_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_STEP.output_rules.busy_next

### RTL-0107: Implement output rule for FM_DMA_STEP: done_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_STEP.output_rules.done_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.output_rules.done_pulse.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=done_pulse; port=ch_done; expr=1 if (ch_remaining_q[ch_id] <= burst_len and ch_remaining_q[ch_id] > 0) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.output_rules.done_pulse
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - done_pulse width matches SSOT value 1
  - done_pulse RTL expression implements SSOT expression 1 if (ch_remaining_q[ch_id] <= burst_len and ch_remaining_q[ch_id] > 0) else 0
  - DUT port ch_done is the implementation/observation point for done_pulse
  - done_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_STEP.output_rules.done_pulse

### RTL-0108: Implement state update for FM_DMA_STEP: remaining_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DMA_STEP.state_updates.remaining_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.state_updates.remaining_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=remaining_next; expr=ch_remaining_q[ch_id] - burst_len if ch_remaining_q[ch_id] > burst_len else 0; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.state_updates.remaining_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - remaining_next width matches SSOT value 32
  - remaining_next RTL expression implements SSOT expression ch_remaining_q[ch_id] - burst_len if ch_remaining_q[ch_id] > burst_len else 0
  - remaining_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DMA_STEP.state_updates.remaining_next

### RTL-0109: Implement state update for FM_DMA_STEP: src_addr_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DMA_STEP.state_updates.src_addr_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.state_updates.src_addr_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=src_addr_next; expr=ch_src_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.state_updates.src_addr_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - src_addr_next width matches SSOT value ADDR_WIDTH
  - src_addr_next RTL expression implements SSOT expression ch_src_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]
  - src_addr_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DMA_STEP.state_updates.src_addr_next

### RTL-0110: Implement state update for FM_DMA_STEP: dst_addr_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DMA_STEP.state_updates.dst_addr_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.state_updates.dst_addr_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=dst_addr_next; expr=ch_dst_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]; width=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.state_updates.dst_addr_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - dst_addr_next width matches SSOT value ADDR_WIDTH
  - dst_addr_next RTL expression implements SSOT expression ch_dst_addr_q[ch_id] + burst_len * ch_stride_q[ch_id]
  - dst_addr_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DMA_STEP.state_updates.dst_addr_next

### RTL-0111: Implement state update for FM_DMA_STEP: perf_words_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DMA_STEP.state_updates.perf_words_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.state_updates.perf_words_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=perf_words_next; expr=perf_words_q[ch_id] + burst_len; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.state_updates.perf_words_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - perf_words_next width matches SSOT value 32
  - perf_words_next RTL expression implements SSOT expression perf_words_q[ch_id] + burst_len
  - perf_words_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DMA_STEP.state_updates.perf_words_next

### RTL-0112: Implement state update for FM_DMA_STEP: perf_cycles_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DMA_STEP.state_updates.perf_cycles_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.state_updates.perf_cycles_next.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: name=perf_cycles_next; expr=perf_cycles_q[ch_id] + burst_len + 4; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.state_updates.perf_cycles_next
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - perf_cycles_next width matches SSOT value 32
  - perf_cycles_next RTL expression implements SSOT expression perf_cycles_q[ch_id] + burst_len + 4
  - perf_cycles_next updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DMA_STEP.state_updates.perf_cycles_next

### RTL-0113: Implement side effect for FM_DMA_STEP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["ch_remaining_q decrements by burst_len", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_0

### RTL-0114: Implement side effect for FM_DMA_STEP: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["ch_src_addr_q increments by burst_len * ch_stride_q[ch_id]", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_1

### RTL-0115: Implement side effect for FM_DMA_STEP: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["ch_dst_addr_q increments by burst_len * ch_stride_q[ch_id]", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_2

### RTL-0116: Implement side effect for FM_DMA_STEP: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["perf_words_q increments by burst_len", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_3

### RTL-0117: Implement side effect for FM_DMA_STEP: side_effect_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["perf_cycles_q increments by burst_len plus pipeline overhead", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_4

### RTL-0118: Implement side effect for FM_DMA_STEP: side_effect_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_5
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["done pulses on terminal step", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.side_effects.side_effect_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.side_effects.side_effect_5

### RTL-0119: Implement error case for FM_DMA_STEP: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_STEP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.error_cases.error_case_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["bus error during AHB transfer (hresp == ERROR, code 3)", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.error_cases.error_case_0

### RTL-0120: Implement error case for FM_DMA_STEP: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMA_STEP.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_STEP.error_cases.error_case_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_STEP.
SSOT item context: id=FM_DMA_STEP; name=dma_step; port=["ch_busy", "ch_done"]; signal=["timeout waiting for hready (code 4)", "ch_id", "burst_len"]; state=["remaining_next", "src_addr_next", "dst_addr_next", "perf_words_next", "perf_cycles_next"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_STEP.error_cases.error_case_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done"] is the implementation/observation point for dma_step
- SSOT refs: function_model.transactions.FM_DMA_STEP.error_cases.error_case_1

### RTL-0121: Implement transaction FM_DMA_COMPLETE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMA_COMPLETE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE

### RTL-0122: Implement precondition for FM_DMA_COMPLETE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: value=ch_remaining_q[ch_id] == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_0

### RTL-0123: Implement precondition for FM_DMA_COMPLETE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: value=ch_busy_q[ch_id] == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.preconditions.precondition_1

### RTL-0124: Implement output for FM_DMA_COMPLETE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["ch_busy", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.outputs.output_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.outputs.output_0

### RTL-0125: Implement output for FM_DMA_COMPLETE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["ch_done", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.outputs.output_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.outputs.output_1

### RTL-0126: Implement output for FM_DMA_COMPLETE: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.outputs.output_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: id=FM_DMA_COMPLETE; name=dma_complete; port=["ch_busy", "ch_done", "irq"]; signal=["irq", "ch_id"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.outputs.output_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - DUT port ["ch_busy", "ch_done", "irq"] is the implementation/observation point for dma_complete
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.outputs.output_2

### RTL-0127: Implement output rule for FM_DMA_COMPLETE: busy_clear

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.busy_clear
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.busy_clear.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: name=busy_clear; port=ch_busy; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.output_rules.busy_clear
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - busy_clear width matches SSOT value 1
  - busy_clear RTL expression implements SSOT expression 0
  - DUT port ch_busy is the implementation/observation point for busy_clear
  - busy_clear is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.output_rules.busy_clear

### RTL-0128: Implement output rule for FM_DMA_COMPLETE: done_assert

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.done_assert
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMA_COMPLETE.output_rules.done_assert.
Owner: dma_real_channel in rtl/dma_real_channel.sv via function_model.transactions.FM_DMA_COMPLETE.
SSOT item context: name=done_assert; port=ch_done; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMA_COMPLETE.output_rules.done_assert
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - done_assert width matches SSOT value 1
  - done_assert RTL expression implements SSOT expression 1
  - DUT port ch_done is the implementation/observation point for done_assert
  - done_assert is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_DMA_COMPLETE.output_rules.done_assert
