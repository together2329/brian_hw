# RTL Authoring Packet: module__fifo_sync_cx1__function_model

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 30
- Required tasks: 30

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 5/11 section=function_model task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0036: Implement RTL state owner for FL state count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.count.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.state_variables.
SSOT item context: name=count; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.count
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - count width matches SSOT value 4
  - count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.count

### RTL-0037: Implement RTL state owner for FL state wr_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.wr_ptr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.wr_ptr.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.state_variables.
SSOT item context: name=wr_ptr; width=3; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - wr_ptr width matches SSOT value 3
  - wr_ptr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.wr_ptr

### RTL-0038: Implement RTL state owner for FL state rd_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rd_ptr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rd_ptr.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.state_variables.
SSOT item context: name=rd_ptr; width=3; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_ptr width matches SSOT value 3
  - rd_ptr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rd_ptr

### RTL-0039: Implement RTL state owner for FL state head_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.head_data
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.head_data.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.state_variables.
SSOT item context: name=head_data; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.head_data
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - head_data width matches SSOT value 8
  - head_data reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.head_data

### RTL-0040: Implement transaction FM_WRITE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_WRITE.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: id=FM_WRITE; name=write_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_WRITE
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE

### RTL-0041: Implement precondition for FM_WRITE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.preconditions.precondition_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=rst_n is deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.preconditions.precondition_0

### RTL-0042: Implement precondition for FM_WRITE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WRITE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.preconditions.precondition_1.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=wr_en is high.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.preconditions.precondition_1

### RTL-0043: Implement precondition for FM_WRITE: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_WRITE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.preconditions.precondition_2.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=full is low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.preconditions.precondition_2

### RTL-0044: Implement output for FM_WRITE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.outputs.output_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.outputs.output_0

### RTL-0045: Implement output for FM_WRITE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_WRITE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.outputs.output_1.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: value=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_WRITE.outputs.output_1

### RTL-0046: Implement output rule for FM_WRITE: full

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_WRITE.output_rules.full
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.output_rules.full.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=full; port=full; expr=(count + 1) == 8; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.output_rules.full
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - full width matches SSOT value 1
  - full RTL expression implements SSOT expression (count + 1) == 8
  - DUT port full is the implementation/observation point for full
  - full is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_WRITE.output_rules.full

### RTL-0047: Implement output rule for FM_WRITE: empty

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_WRITE.output_rules.empty
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.output_rules.empty.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=empty; port=empty; expr=(count + 1) == 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.output_rules.empty
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - empty width matches SSOT value 1
  - empty RTL expression implements SSOT expression (count + 1) == 0
  - DUT port empty is the implementation/observation point for empty
  - empty is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_WRITE.output_rules.empty

### RTL-0048: Implement state update for FM_WRITE: count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WRITE.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.state_updates.count.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=count; expr=count + 1; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - count width matches SSOT value 4
  - count RTL expression implements SSOT expression count + 1
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WRITE.state_updates.count

### RTL-0049: Implement state update for FM_WRITE: wr_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WRITE.state_updates.wr_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.state_updates.wr_ptr.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=wr_ptr; expr=(wr_ptr + 1) % 8; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.state_updates.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - wr_ptr width matches SSOT value 3
  - wr_ptr RTL expression implements SSOT expression (wr_ptr + 1) % 8
  - wr_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WRITE.state_updates.wr_ptr

### RTL-0050: Implement state update for FM_WRITE: head_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_WRITE.state_updates.head_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_WRITE.state_updates.head_data.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_WRITE.
SSOT item context: name=head_data; expr=wr_data if count == 0 else head_data; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_WRITE.state_updates.head_data
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - head_data width matches SSOT value 8
  - head_data RTL expression implements SSOT expression wr_data if count == 0 else head_data
  - head_data updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_WRITE.state_updates.head_data

### RTL-0051: Implement transaction FM_READ

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_READ.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: id=FM_READ; name=read_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_READ
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ

### RTL-0052: Implement precondition for FM_READ: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.preconditions.precondition_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=rst_n is deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.preconditions.precondition_0

### RTL-0053: Implement precondition for FM_READ: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_READ.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.preconditions.precondition_1.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=rd_en is high.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.preconditions.precondition_1
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.preconditions.precondition_1

### RTL-0054: Implement precondition for FM_READ: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_READ.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.preconditions.precondition_2.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=empty is low.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.preconditions.precondition_2
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.preconditions.precondition_2

### RTL-0055: Implement output for FM_READ: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.outputs.output_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=rd_data.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.outputs.output_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.outputs.output_0

### RTL-0056: Implement output for FM_READ: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_READ.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.outputs.output_1.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.outputs.output_1
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.outputs.output_1

### RTL-0057: Implement output for FM_READ: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_READ.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.outputs.output_2.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: value=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.outputs.output_2
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: function_model.transactions.FM_READ.outputs.output_2

### RTL-0058: Implement output rule for FM_READ: rd_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_READ.output_rules.rd_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.output_rules.rd_data.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: name=rd_data; port=rd_data; expr=head_data; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.output_rules.rd_data
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_data width matches SSOT value 8
  - rd_data RTL expression implements SSOT expression head_data
  - DUT port rd_data is the implementation/observation point for rd_data
  - rd_data is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_READ.output_rules.rd_data

### RTL-0059: Implement output rule for FM_READ: full

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_READ.output_rules.full
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.output_rules.full.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: name=full; port=full; expr=(count - 1) == 8; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.output_rules.full
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - full width matches SSOT value 1
  - full RTL expression implements SSOT expression (count - 1) == 8
  - DUT port full is the implementation/observation point for full
  - full is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_READ.output_rules.full

### RTL-0060: Implement output rule for FM_READ: empty

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_READ.output_rules.empty
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.output_rules.empty.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: name=empty; port=empty; expr=(count - 1) == 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.output_rules.empty
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - empty width matches SSOT value 1
  - empty RTL expression implements SSOT expression (count - 1) == 0
  - DUT port empty is the implementation/observation point for empty
  - empty is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_READ.output_rules.empty

### RTL-0061: Implement state update for FM_READ: count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_READ.state_updates.count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.state_updates.count.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: name=count; expr=count - 1; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.state_updates.count
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - count width matches SSOT value 4
  - count RTL expression implements SSOT expression count - 1
  - count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_READ.state_updates.count

### RTL-0062: Implement state update for FM_READ: rd_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_READ.state_updates.rd_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_READ.state_updates.rd_ptr.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.transactions.FM_READ.
SSOT item context: name=rd_ptr; expr=(rd_ptr + 1) % 8; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_READ.state_updates.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_ptr width matches SSOT value 3
  - rd_ptr RTL expression implements SSOT expression (rd_ptr + 1) % 8
  - rd_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_READ.state_updates.rd_ptr

### RTL-0063: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.
SSOT item context: port=["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]; signal=count is always in [0, 8].; state=["count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - DUT port ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"] is the implementation/observation point for ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0064: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.
SSOT item context: port=["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]; signal=full is equivalent to count == 8.; state=["count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - DUT port ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"] is the implementation/observation point for ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0065: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via function_model.
SSOT item context: port=["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]; signal=empty is equivalent to count == 0.; state=["count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - DUT port ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"] is the implementation/observation point for ["wr_data", "wr_en", "full", "empty", "rd_en", "rd_data", "full", "empty"]
- SSOT refs: function_model.invariants.invariant_2
