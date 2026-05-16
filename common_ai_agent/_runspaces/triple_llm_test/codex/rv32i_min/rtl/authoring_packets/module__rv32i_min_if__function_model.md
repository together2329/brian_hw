# RTL Authoring Packet: module__rv32i_min_if__function_model

- Kind: module
- Owner module: rv32i_min_if
- Owner file: rtl/rv32i_min_if.sv
- Task count: 35
- Required tasks: 35

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, function_model, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, io_list, io_list.interfaces.instr_bus
- Module slice: 2/6 section=function_model task_limit=48
- Slice rule: Owner module rv32i_min_if is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])

## Tasks

### RTL-0054: Implement transaction FM_FETCH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FETCH
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FETCH.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: id=FM_FETCH; name=fetch_and_default_advance.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FETCH
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH

### RTL-0055: Implement precondition for FM_FETCH: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FETCH.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.preconditions.precondition_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=pc % 4 == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.preconditions.precondition_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.preconditions.precondition_0

### RTL-0056: Implement input for FM_FETCH: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FETCH.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.inputs.input_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=pc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.inputs.input_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.inputs.input_0

### RTL-0057: Implement input for FM_FETCH: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FETCH.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.inputs.input_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=i_rdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.inputs.input_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.inputs.input_1

### RTL-0058: Implement output for FM_FETCH: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FETCH.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.outputs.output_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=decoded instruction fields available to execute stage.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.outputs.output_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.outputs.output_0

### RTL-0059: Implement output for FM_FETCH: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FETCH.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.outputs.output_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=default next_pc equals pc plus 4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.outputs.output_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.outputs.output_1

### RTL-0060: Implement state update for FM_FETCH: next_pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FETCH.state_updates.next_pc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.state_updates.next_pc.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: name=next_pc; expr=pc + 4; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.state_updates.next_pc
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - next_pc width matches SSOT value 32
  - next_pc RTL expression implements SSOT expression pc + 4
  - next_pc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FETCH.state_updates.next_pc

### RTL-0061: Implement side effect for FM_FETCH: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FETCH.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FETCH.side_effects.side_effect_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_FETCH.
SSOT item context: value=pc advances by 4 when no control transfer or fault blocks retirement.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FETCH.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_FETCH.side_effects.side_effect_0

### RTL-0073: Implement transaction FM_BRANCH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_BRANCH
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_BRANCH.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: id=FM_BRANCH; name=conditional_branches.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH

### RTL-0074: Implement precondition for FM_BRANCH: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_BRANCH.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.preconditions.precondition_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=is_branch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.preconditions.precondition_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.preconditions.precondition_0

### RTL-0075: Implement input for FM_BRANCH: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_BRANCH.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.inputs.input_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=pc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.inputs.input_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.inputs.input_0

### RTL-0076: Implement input for FM_BRANCH: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_BRANCH.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.inputs.input_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=branch_taken.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.inputs.input_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.inputs.input_1

### RTL-0077: Implement input for FM_BRANCH: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_BRANCH.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.inputs.input_2.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=branch_imm.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.inputs.input_2
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.inputs.input_2

### RTL-0078: Implement output for FM_BRANCH: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_BRANCH.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.outputs.output_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=pc becomes branch target if taken else pc plus 4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.outputs.output_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.outputs.output_0

### RTL-0079: Implement state update for FM_BRANCH: next_pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_BRANCH.state_updates.next_pc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.state_updates.next_pc.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: name=next_pc; expr=(pc + branch_imm) if branch_taken else (pc + 4); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.state_updates.next_pc
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - next_pc width matches SSOT value 32
  - next_pc RTL expression implements SSOT expression (pc + branch_imm) if branch_taken else (pc + 4)
  - next_pc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_BRANCH.state_updates.next_pc

### RTL-0080: Implement side effect for FM_BRANCH: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_BRANCH.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BRANCH.side_effects.side_effect_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_BRANCH.
SSOT item context: value=no register writeback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BRANCH.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_BRANCH.side_effects.side_effect_0

### RTL-0081: Implement transaction FM_JUMP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_JUMP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_JUMP.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: id=FM_JUMP; name=jal_and_jalr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_JUMP
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP

### RTL-0082: Implement precondition for FM_JUMP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_JUMP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.preconditions.precondition_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=is_jump.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.preconditions.precondition_0

### RTL-0083: Implement input for FM_JUMP: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_JUMP.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.inputs.input_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=pc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.inputs.input_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.inputs.input_0

### RTL-0084: Implement input for FM_JUMP: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_JUMP.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.inputs.input_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=rs1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.inputs.input_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.inputs.input_1

### RTL-0085: Implement input for FM_JUMP: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_JUMP.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.inputs.input_2.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=imm.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.inputs.input_2
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.inputs.input_2

### RTL-0086: Implement input for FM_JUMP: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_JUMP.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.inputs.input_3.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=is_jalr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.inputs.input_3
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.inputs.input_3

### RTL-0087: Implement output for FM_JUMP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_JUMP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.outputs.output_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=link register gets old pc plus 4 when rd != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.outputs.output_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.outputs.output_0

### RTL-0088: Implement output for FM_JUMP: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_JUMP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.outputs.output_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=jump target selected by JAL or JALR rule.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.outputs.output_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.outputs.output_1

### RTL-0089: Implement state update for FM_JUMP: next_pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_JUMP.state_updates.next_pc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.state_updates.next_pc.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: name=next_pc; expr=((rs1 + imm) & ~1) if is_jalr else (pc + imm); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.state_updates.next_pc
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - next_pc width matches SSOT value 32
  - next_pc RTL expression implements SSOT expression ((rs1 + imm) & ~1) if is_jalr else (pc + imm)
  - next_pc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_JUMP.state_updates.next_pc

### RTL-0090: Implement side effect for FM_JUMP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_JUMP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_JUMP.side_effects.side_effect_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_JUMP.
SSOT item context: value=pc redirected to computed target.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_JUMP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_JUMP.side_effects.side_effect_0

### RTL-0111: Implement transaction FM_SYSTEM

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_SYSTEM
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_SYSTEM.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: id=FM_SYSTEM; name=fence_ecall_ebreak.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM

### RTL-0112: Implement precondition for FM_SYSTEM: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_SYSTEM.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.preconditions.precondition_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=is_system.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.preconditions.precondition_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.preconditions.precondition_0

### RTL-0113: Implement input for FM_SYSTEM: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_SYSTEM.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.inputs.input_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=is_fence.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.inputs.input_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.inputs.input_0

### RTL-0114: Implement input for FM_SYSTEM: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_SYSTEM.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.inputs.input_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=is_ecall.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.inputs.input_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.inputs.input_1

### RTL-0115: Implement input for FM_SYSTEM: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_SYSTEM.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.inputs.input_2.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=is_ebreak.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.inputs.input_2
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.inputs.input_2

### RTL-0116: Implement output for FM_SYSTEM: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SYSTEM.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.outputs.output_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=FENCE inserts one bubble.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.outputs.output_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.outputs.output_0

### RTL-0117: Implement output for FM_SYSTEM: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SYSTEM.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.outputs.output_1.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=ECALL and EBREAK pulse excpt_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.outputs.output_1
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.outputs.output_1

### RTL-0118: Implement output rule for FM_SYSTEM: exception_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_SYSTEM.output_rules.exception_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.output_rules.exception_pulse.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: name=exception_pulse; port=excpt_o; expr=1 if (is_ecall or is_ebreak or illegal_shamt or misaligned_access) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.output_rules.exception_pulse
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - exception_pulse width matches SSOT value 1
  - exception_pulse RTL expression implements SSOT expression 1 if (is_ecall or is_ebreak or illegal_shamt or misaligned_access) else 0
  - DUT port excpt_o is the implementation/observation point for exception_pulse
  - exception_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_SYSTEM.output_rules.exception_pulse

### RTL-0119: Implement side effect for FM_SYSTEM: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_SYSTEM.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SYSTEM.side_effects.side_effect_0.
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via function_model.transactions.FM_SYSTEM.
SSOT item context: value=ECALL and EBREAK advance pc by 4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SYSTEM.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
- SSOT refs: function_model.transactions.FM_SYSTEM.side_effects.side_effect_0
