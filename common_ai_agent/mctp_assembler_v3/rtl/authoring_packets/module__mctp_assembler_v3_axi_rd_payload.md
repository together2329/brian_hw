# RTL Authoring Packet: module__mctp_assembler_v3_axi_rd_payload

- Kind: module
- Owner module: mctp_assembler_v3_axi_rd_payload
- Owner file: rtl/mctp_assembler_v3_axi_rd_payload.sv
- Task count: 47
- Required tasks: 47

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: fsm, fsm.axi_read_fsm, function_model, function_model.transactions.FM_AXI_READ, io_list, io_list.interfaces.axi_rd_slave
- SSOT target scale: min_modules=9, min_source_files=10

## Tasks

### RTL-0123: Implement RTL state owner for FL state beat_index

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.beat_index
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.beat_index.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=beat_index; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.beat_index
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - beat_index width matches SSOT value 8
  - beat_index reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.beat_index

### RTL-0124: Implement RTL state owner for FL state out_of_window

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.out_of_window
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.out_of_window.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via function_model.state_variables.
SSOT item context: name=out_of_window; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.out_of_window
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - out_of_window width matches SSOT value 1
  - out_of_window reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.out_of_window

### RTL-0274: Implement transaction FM_AXI_READ

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AXI_READ
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AXI_READ.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: id=FM_AXI_READ; name=firmware_payload_read.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: function_model.transactions.FM_AXI_READ

### RTL-0275: Implement precondition for FM_AXI_READ: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: value=ARSIZE==5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: function_model.transactions.FM_AXI_READ.preconditions.precondition_0

### RTL-0276: Implement precondition for FM_AXI_READ: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_1.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: value=ARBURST==INCR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.preconditions.precondition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: function_model.transactions.FM_AXI_READ.preconditions.precondition_1

### RTL-0277: Implement precondition for FM_AXI_READ: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.preconditions.precondition_2.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: value=descriptor visible for the range or raw_sram_debug_read_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.preconditions.precondition_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: function_model.transactions.FM_AXI_READ.preconditions.precondition_2

### RTL-0278: Implement input for FM_AXI_READ: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_AXI_READ.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.inputs.input_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: id=FM_AXI_READ; name=firmware_payload_read; port=["s_axi_rresp", "s_axi_rlast"]; signal=["AR address/len", "out_of_window", "no_descriptor", "raw_sram_debug_read_enable", "beat_index", "arlen", "read_error"]; state=["fw_axi_read_beat_count", "fw_axi_read_error_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - DUT port ["s_axi_rresp", "s_axi_rlast"] is the implementation/observation point for firmware_payload_read
- SSOT refs: function_model.transactions.FM_AXI_READ.inputs.input_0

### RTL-0279: Implement output for FM_AXI_READ: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READ.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.outputs.output_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: value=one SRAM read per R beat; rdata returned unmodified; RLAST on final beat.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: function_model.transactions.FM_AXI_READ.outputs.output_0

### RTL-0280: Implement output for FM_AXI_READ: rresp_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READ.outputs.rresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.outputs.rresp_next.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=rresp_next; port=s_axi_rresp; expr=RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.outputs.rresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - rresp_next RTL expression implements SSOT expression RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY
  - DUT port s_axi_rresp is the implementation/observation point for rresp_next
- SSOT refs: function_model.transactions.FM_AXI_READ.outputs.rresp_next

### RTL-0281: Implement output for FM_AXI_READ: rlast_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READ.outputs.rlast_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.outputs.rlast_next.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=rlast_next; port=s_axi_rlast; expr=beat_index == arlen.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.outputs.rlast_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - rlast_next RTL expression implements SSOT expression beat_index == arlen
  - DUT port s_axi_rlast is the implementation/observation point for rlast_next
- SSOT refs: function_model.transactions.FM_AXI_READ.outputs.rlast_next

### RTL-0282: Implement output for FM_AXI_READ: fw_axi_read_beat_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_beat_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_beat_count.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: state=fw_axi_read_beat_count; expr=fw_axi_read_beat_count + 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_beat_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_beat_count RTL expression implements SSOT expression fw_axi_read_beat_count + 1
- SSOT refs: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_beat_count

### RTL-0283: Implement output for FM_AXI_READ: fw_axi_read_error_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_error_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_error_count.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: state=fw_axi_read_error_count; expr=fw_axi_read_error_count + (1 if read_error else 0).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_error_count RTL expression implements SSOT expression fw_axi_read_error_count + (1 if read_error else 0)
- SSOT refs: function_model.transactions.FM_AXI_READ.outputs.fw_axi_read_error_count

### RTL-0284: Implement output rule for FM_AXI_READ: rresp_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READ.output_rules.rresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.output_rules.rresp_next.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=rresp_next; port=s_axi_rresp; expr=RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.output_rules.rresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - rresp_next width matches SSOT value 2
  - rresp_next RTL expression implements SSOT expression RRESP_SLVERR if (out_of_window or (no_descriptor and not raw_sram_debug_read_enable)) else RRESP_OKAY
  - DUT port s_axi_rresp is the implementation/observation point for rresp_next
  - rresp_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READ.output_rules.rresp_next

### RTL-0285: Implement output rule for FM_AXI_READ: rlast_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READ.output_rules.rlast_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.output_rules.rlast_next.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=rlast_next; port=s_axi_rlast; expr=beat_index == arlen; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.output_rules.rlast_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - rlast_next width matches SSOT value 1
  - rlast_next RTL expression implements SSOT expression beat_index == arlen
  - DUT port s_axi_rlast is the implementation/observation point for rlast_next
  - rlast_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READ.output_rules.rlast_next

### RTL-0286: Implement state update for FM_AXI_READ: fw_axi_read_beat_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_beat_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_beat_count.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=fw_axi_read_beat_count; expr=fw_axi_read_beat_count + 1; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_beat_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fw_axi_read_beat_count width matches SSOT value 32
  - fw_axi_read_beat_count RTL expression implements SSOT expression fw_axi_read_beat_count + 1
  - fw_axi_read_beat_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_beat_count

### RTL-0287: Implement state update for FM_AXI_READ: fw_axi_read_error_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_error_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_error_count.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: name=fw_axi_read_error_count; expr=fw_axi_read_error_count + (1 if read_error else 0); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fw_axi_read_error_count width matches SSOT value 32
  - fw_axi_read_error_count RTL expression implements SSOT expression fw_axi_read_error_count + (1 if read_error else 0)
  - fw_axi_read_error_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AXI_READ.state_updates.fw_axi_read_error_count

### RTL-0288: Implement side effect for FM_AXI_READ: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AXI_READ.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.side_effects.side_effect_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: id=FM_AXI_READ; name=firmware_payload_read; port=["s_axi_rresp", "s_axi_rlast"]; signal=["fw_axi_read_beat_count increment", "out_of_window", "no_descriptor", "raw_sram_debug_read_enable", "beat_index", "a...; state=["fw_axi_read_beat_count", "fw_axi_read_error_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - DUT port ["s_axi_rresp", "s_axi_rlast"] is the implementation/observation point for firmware_payload_read
- SSOT refs: function_model.transactions.FM_AXI_READ.side_effects.side_effect_0

### RTL-0289: Implement error case for FM_AXI_READ: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_AXI_READ.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READ.error_cases.error_case_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via function_model.transactions.FM_AXI_READ.
SSOT item context: id=FM_AXI_READ; name=firmware_payload_read; port=["s_axi_rresp", "s_axi_rlast"]; signal=[{"condition": "read outside SRAM read window, or no completed descriptor and not raw_sram_debug_read_enable", "resul...; state=["fw_axi_read_beat_count", "fw_axi_read_error_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READ.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - DUT port ["s_axi_rresp", "s_axi_rlast"] is the implementation/observation point for firmware_payload_read
- SSOT refs: function_model.transactions.FM_AXI_READ.error_cases.error_case_0

### RTL-0305: Implement handshake rule: sram_rd_req_valid

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sram_rd_req_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sram_rd_req_valid.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=sram_rd_req_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sram_rd_req_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.sram_rd_req_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sram_rd_req_valid

### RTL-0306: Implement handshake rule: s_axi_rvalid/s_axi_rlast

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via cycle_model.handshake_rules.
SSOT item context: signal=s_axi_rvalid/s_axi_rlast.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.s_axi_rvalid_s_axi_rlast

### RTL-0430: Implement FSM state axi_read_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_0

### RTL-0431: Implement FSM state axi_read_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_1.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=ACCEPT_AR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_1

### RTL-0432: Implement FSM state axi_read_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_2.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=ISSUE_SRAM_RD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_2

### RTL-0433: Implement FSM state axi_read_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_3.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=WAIT_SRAM_RSP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_3

### RTL-0434: Implement FSM state axi_read_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_4.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=DRIVE_R.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_4

### RTL-0435: Implement FSM state axi_read_fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.axi_read_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.states.state_5.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: value=DONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.axi_read_fsm.states.state_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: fsm.axi_read_fsm.states.state_5

### RTL-0436: Implement FSM transition axi_read_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_0.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=IDLE; to=ACCEPT_AR; condition=arvalid && arready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_0 condition is implemented as RTL control logic: arvalid && arready
  - fsm.axi_read_fsm.transitions.transition_0 transition path IDLE -> ACCEPT_AR is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_0

### RTL-0437: Implement FSM transition axi_read_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_1.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=ACCEPT_AR; to=ISSUE_SRAM_RD; condition=ARSIZE==5 && in window && (descriptor present or raw_sram_debug_read_enable).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_1 condition is implemented as RTL control logic: ARSIZE==5 && in window && (descriptor present or raw_sram_debug_read_enable)
  - fsm.axi_read_fsm.transitions.transition_1 transition path ACCEPT_AR -> ISSUE_SRAM_RD is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_1

### RTL-0438: Implement FSM transition axi_read_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_2.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=ACCEPT_AR; to=DRIVE_R; condition=out-of-window/no-descriptor -> SLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_2 condition is implemented as RTL control logic: out-of-window/no-descriptor -> SLVERR
  - fsm.axi_read_fsm.transitions.transition_2 transition path ACCEPT_AR -> DRIVE_R is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_2

### RTL-0439: Implement FSM transition axi_read_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_3.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=ISSUE_SRAM_RD; to=WAIT_SRAM_RSP; condition=sram_rd_req accepted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_3 condition is implemented as RTL control logic: sram_rd_req accepted
  - fsm.axi_read_fsm.transitions.transition_3 transition path ISSUE_SRAM_RD -> WAIT_SRAM_RSP is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_3

### RTL-0440: Implement FSM transition axi_read_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_4.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=WAIT_SRAM_RSP; to=DRIVE_R; condition=sram_rd_rsp_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_4 condition is implemented as RTL control logic: sram_rd_rsp_valid
  - fsm.axi_read_fsm.transitions.transition_4 transition path WAIT_SRAM_RSP -> DRIVE_R is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_4

### RTL-0441: Implement FSM transition axi_read_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_5.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=DRIVE_R; to=ISSUE_SRAM_RD; condition=rvalid && rready && !rlast.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_5 condition is implemented as RTL control logic: rvalid && rready && !rlast
  - fsm.axi_read_fsm.transitions.transition_5 transition path DRIVE_R -> ISSUE_SRAM_RD is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_5

### RTL-0442: Implement FSM transition axi_read_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_6.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=DRIVE_R; to=DONE; condition=rvalid && rready && rlast.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_6 condition is implemented as RTL control logic: rvalid && rready && rlast
  - fsm.axi_read_fsm.transitions.transition_6 transition path DRIVE_R -> DONE is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_6

### RTL-0443: Implement FSM transition axi_read_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.axi_read_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.axi_read_fsm.transitions.transition_7.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via fsm.axi_read_fsm.
SSOT item context: from=DONE; to=IDLE; condition=next.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.axi_read_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - fsm.axi_read_fsm.transitions.transition_7 condition is implemented as RTL control logic: next
  - fsm.axi_read_fsm.transitions.transition_7 transition path DONE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.axi_read_fsm.transitions.transition_7

### RTL-0450: Implement feature firmware_read

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.firmware_read
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.firmware_read.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=firmware_read; output=rdata beats; SLVERR for out-of-window/no-descriptor reads.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.firmware_read
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.firmware_read

### RTL-0478: Prove module mctp_assembler_v3_axi_rd_payload is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_axi_rd_payload.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_axi_rd_payload.module_equivalence.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_axi_rd_payload.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
- SSOT refs: sub_modules.mctp_assembler_v3_axi_rd_payload.module_equivalence

### RTL-0070: Implement and connect port s_axi_araddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_araddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_araddr.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_araddr; width=16; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_araddr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_araddr width matches SSOT value 16
  - s_axi_araddr port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_araddr

### RTL-0071: Implement and connect port s_axi_arlen

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arlen
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arlen.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_arlen; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_arlen
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_arlen width matches SSOT value 8
  - s_axi_arlen port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_arlen

### RTL-0072: Implement and connect port s_axi_arsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arsize.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_arsize; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_arsize
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_arsize width matches SSOT value 3
  - s_axi_arsize port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_arsize

### RTL-0073: Implement and connect port s_axi_arburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arburst.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_arburst; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_arburst
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_arburst width matches SSOT value 2
  - s_axi_arburst port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_arburst

### RTL-0074: Implement and connect port s_axi_arvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arvalid.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_arvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_arvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_arvalid width matches SSOT value 1
  - s_axi_arvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_arvalid

### RTL-0075: Implement and connect port s_axi_arready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_arready.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_arready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_arready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_arready width matches SSOT value 1
  - s_axi_arready port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_arready

### RTL-0076: Implement and connect port s_axi_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rdata.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_rdata; width=256; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_rdata
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_rdata width matches SSOT value 256
  - s_axi_rdata port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_rdata

### RTL-0077: Implement and connect port s_axi_rresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rresp.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_rresp; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_rresp
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_rresp width matches SSOT value 2
  - s_axi_rresp port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_rresp

### RTL-0078: Implement and connect port s_axi_rlast

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rlast
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rlast.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_rlast; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_rlast
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_rlast width matches SSOT value 1
  - s_axi_rlast port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_rlast

### RTL-0079: Implement and connect port s_axi_rvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rvalid.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_rvalid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_rvalid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_rvalid width matches SSOT value 1
  - s_axi_rvalid port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_rvalid

### RTL-0080: Implement and connect port s_axi_rready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_slave.ports.s_axi_rready.
Owner: mctp_assembler_v3_axi_rd_payload in rtl/mctp_assembler_v3_axi_rd_payload.sv via io_list.interfaces.axi_rd_slave.
SSOT item context: name=s_axi_rready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_slave.ports.s_axi_rready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_rd_payload.sv
  - s_axi_rready width matches SSOT value 1
  - s_axi_rready port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_slave.ports.s_axi_rready
