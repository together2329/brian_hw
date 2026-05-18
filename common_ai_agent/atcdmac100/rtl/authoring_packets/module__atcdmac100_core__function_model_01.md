# RTL Authoring Packet: module__atcdmac100_core__function_model_01

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
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
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 2/14 section=function_model task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= hresetn (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0057: Implement RTL state owner for FL state dmac_reset_pulse

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dmac_reset_pulse
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dmac_reset_pulse.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dmac_reset_pulse; width=1; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dmac_reset_pulse
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dmac_reset_pulse width matches SSOT value 1
  - dmac_reset_pulse reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dmac_reset_pulse

### RTL-0058: Implement RTL state owner for FL state active_ch

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.active_ch
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=active_ch; width=3; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.active_ch
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - active_ch width matches SSOT value 3
  - active_ch reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.active_ch

### RTL-0059: Implement RTL state owner for FL state busy

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.busy
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=busy; width=1; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.busy

### RTL-0060: Implement RTL state owner for FL state ch_enable

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ch_enable
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=ch_enable; width=8; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ch_enable width matches SSOT value 8
  - ch_enable reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ch_enable

### RTL-0061: Implement RTL state owner for FL state int_tc

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_tc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=int_tc; width=8; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - int_tc width matches SSOT value 8
  - int_tc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_tc

### RTL-0062: Implement RTL state owner for FL state int_abort

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_abort
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=int_abort; width=8; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_abort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - int_abort width matches SSOT value 8
  - int_abort reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_abort

### RTL-0063: Implement RTL state owner for FL state int_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.int_error
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=int_error; width=8; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - int_error width matches SSOT value 8
  - int_error reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.int_error

### RTL-0064: Implement RTL state owner for FL state bytes_done

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.bytes_done
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=bytes_done; width=22; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - bytes_done width matches SSOT value 22
  - bytes_done reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.bytes_done

### RTL-0065: Implement RTL state owner for FL state src_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.src_addr_cur
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=src_addr_cur; width=ADDR_WIDTH; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.src_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - src_addr_cur width matches SSOT value ADDR_WIDTH
  - src_addr_cur reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.src_addr_cur

### RTL-0066: Implement RTL state owner for FL state dst_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dst_addr_cur
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dst_addr_cur; width=ADDR_WIDTH; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dst_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dst_addr_cur width matches SSOT value ADDR_WIDTH
  - dst_addr_cur reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dst_addr_cur

### RTL-0067: Implement RTL state owner for FL state read_data_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.read_data_hold
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=read_data_hold; width=32; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.read_data_hold
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - read_data_hold width matches SSOT value 32
  - read_data_hold reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.read_data_hold

### RTL-0068: Implement RTL state owner for FL state chain_pending

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.chain_pending
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.chain_pending.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=chain_pending; width=1; reset=0.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.chain_pending
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - chain_pending width matches SSOT value 1
  - chain_pending reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.chain_pending

### RTL-0069: Implement transaction FM_RESET

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RESET.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RESET
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_RESET

### RTL-0070: Implement precondition for FM_RESET: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=hresetn == 0 or DMACtrl.Reset write is observed.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_RESET.preconditions.precondition_0

### RTL-0071: Implement output for FM_RESET: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hready"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_0

### RTL-0072: Implement output for FM_RESET: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hresp"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_1

### RTL-0073: Implement output for FM_RESET: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hrdata"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_2

### RTL-0074: Implement output for FM_RESET: output_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["dma_int"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_3

### RTL-0075: Implement output for FM_RESET: output_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_4.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["dma_ack"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_4
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_4

### RTL-0076: Implement output for FM_RESET: output_5

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_5
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_5.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hbusreq_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_5
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_5

### RTL-0077: Implement output for FM_RESET: output_6

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_6
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_6.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["htrans_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_6
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_6

### RTL-0078: Implement output for FM_RESET: output_7

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_7
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_7.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["haddr_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_7
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_7

### RTL-0079: Implement output for FM_RESET: output_8

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_8
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_8.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hwrite_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_8
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_8

### RTL-0080: Implement output for FM_RESET: output_9

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_9
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_9.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hsize_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_9
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_9

### RTL-0081: Implement output for FM_RESET: output_10

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_10
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_10.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hburst_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_10
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_10

### RTL-0082: Implement output for FM_RESET: output_11

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_11
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_11.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["hwdata_mst"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_11
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_11

### RTL-0083: Implement output rule for FM_RESET: hready_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.hready_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.hready_reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hready_reset; port=hready; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.hready_reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hready_reset width matches SSOT value 1
  - hready_reset RTL expression implements SSOT expression 0
  - DUT port hready is the implementation/observation point for hready_reset
  - hready_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.hready_reset

### RTL-0084: Implement output rule for FM_RESET: hresp_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.hresp_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.hresp_reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=hresp_reset; port=hresp; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.hresp_reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - hresp_reset width matches SSOT value 2
  - hresp_reset RTL expression implements SSOT expression 0
  - DUT port hresp is the implementation/observation point for hresp_reset
  - hresp_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.hresp_reset

### RTL-0085: Implement output rule for FM_RESET: dma_int_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.dma_int_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.dma_int_reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=dma_int_reset; port=dma_int; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.dma_int_reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - dma_int_reset width matches SSOT value 1
  - dma_int_reset RTL expression implements SSOT expression 0
  - DUT port dma_int is the implementation/observation point for dma_int_reset
  - dma_int_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.dma_int_reset

### RTL-0086: Implement output rule for FM_RESET: htrans_mst_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RESET.output_rules.htrans_mst_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.output_rules.htrans_mst_reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: name=htrans_mst_reset; port=htrans_mst; expr=0; width=2.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.output_rules.htrans_mst_reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - htrans_mst_reset width matches SSOT value 2
  - htrans_mst_reset RTL expression implements SSOT expression 0
  - DUT port htrans_mst is the implementation/observation point for htrans_mst_reset
  - htrans_mst_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RESET.output_rules.htrans_mst_reset

### RTL-0087: Implement state update for FM_RESET: dmac_reset_pulse

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=dmac_reset_pulse; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse width matches SSOT value 1
  - function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.dmac_reset_pulse

### RTL-0088: Implement state update for FM_RESET: active_ch

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.active_ch
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.active_ch.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=active_ch; expr=0; width=3.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.active_ch
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.active_ch width matches SSOT value 3
  - function_model.transactions.FM_RESET.state_updates.active_ch RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.active_ch updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.active_ch

### RTL-0089: Implement state update for FM_RESET: busy

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.busy
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.busy.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=busy; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.busy
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.busy width matches SSOT value 1
  - function_model.transactions.FM_RESET.state_updates.busy RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.busy updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.busy

### RTL-0090: Implement state update for FM_RESET: ch_enable

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.ch_enable
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.ch_enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=ch_enable; expr=0; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.ch_enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.ch_enable width matches SSOT value 8
  - function_model.transactions.FM_RESET.state_updates.ch_enable RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.ch_enable updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.ch_enable

### RTL-0091: Implement state update for FM_RESET: int_tc

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.int_tc
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.int_tc.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_tc; expr=0; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.int_tc
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.int_tc width matches SSOT value 8
  - function_model.transactions.FM_RESET.state_updates.int_tc RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.int_tc updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.int_tc

### RTL-0092: Implement state update for FM_RESET: int_abort

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.int_abort
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.int_abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_abort; expr=0; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.int_abort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.int_abort width matches SSOT value 8
  - function_model.transactions.FM_RESET.state_updates.int_abort RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.int_abort updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.int_abort

### RTL-0093: Implement state update for FM_RESET: int_error

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.int_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.int_error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=int_error; expr=0; width=8.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.int_error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.int_error width matches SSOT value 8
  - function_model.transactions.FM_RESET.state_updates.int_error RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.int_error updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.int_error

### RTL-0094: Implement state update for FM_RESET: bytes_done

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.bytes_done
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.bytes_done.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=bytes_done; expr=0; width=22.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.bytes_done
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.bytes_done width matches SSOT value 22
  - function_model.transactions.FM_RESET.state_updates.bytes_done RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.bytes_done updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.bytes_done

### RTL-0095: Implement state update for FM_RESET: src_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.src_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.src_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=src_addr_cur; expr=0; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.src_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.src_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.src_addr_cur

### RTL-0096: Implement state update for FM_RESET: dst_addr_cur

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.dst_addr_cur
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.dst_addr_cur.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=dst_addr_cur; expr=0; width=ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.dst_addr_cur
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur width matches SSOT value ADDR_WIDTH
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.dst_addr_cur updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.dst_addr_cur

### RTL-0097: Implement state update for FM_RESET: read_data_hold

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.read_data_hold
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.read_data_hold.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=read_data_hold; expr=0; width=32.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.read_data_hold
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.read_data_hold width matches SSOT value 32
  - function_model.transactions.FM_RESET.state_updates.read_data_hold RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.read_data_hold updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.read_data_hold

### RTL-0098: Implement state update for FM_RESET: chain_pending

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RESET.state_updates.chain_pending
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.state_updates.chain_pending.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: state=chain_pending; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.state_updates.chain_pending
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - function_model.transactions.FM_RESET.state_updates.chain_pending width matches SSOT value 1
  - function_model.transactions.FM_RESET.state_updates.chain_pending RTL expression implements SSOT expression 0
  - function_model.transactions.FM_RESET.state_updates.chain_pending updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RESET.state_updates.chain_pending

### RTL-0099: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["disable all channels, clear active state, clear interrupt status"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0100: Implement error case for FM_RESET: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_RESET.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.error_cases.error_case_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_RESET; name=hardware or software reset; port=["hready", "hresp", "dma_int", "htrans_mst"]; signal=["illegal size, alignment, reserved mode, or AHB error records IntStatus.Error and disables the channel"]; state=["dmac_reset_pulse", "active_ch", "busy", "ch_enable", "int_tc", "int_abort", "int_error", "bytes_done", "src_addr_cu....
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.error_cases.error_case_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int", "htrans_mst"] is the implementation/observation point for hardware or software reset
- SSOT refs: function_model.transactions.FM_RESET.error_cases.error_case_0

### RTL-0101: Implement transaction FM_AHB_WRITE

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AHB_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AHB_WRITE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_WRITE

### RTL-0102: Implement precondition for FM_AHB_WRITE: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: value=hsel and hreadyin and htrans[1] and hwrite.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: function_model.transactions.FM_AHB_WRITE.preconditions.precondition_0

### RTL-0103: Implement output for FM_AHB_WRITE: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.output_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["hready=1"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.output_0

### RTL-0104: Implement output for FM_AHB_WRITE: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_AHB_WRITE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AHB_WRITE.outputs.output_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via function_model.
SSOT item context: id=FM_AHB_WRITE; name=AHB slave register write; port=["hready", "hresp", "dma_int"]; signal=["hresp=OKAY for valid register writes"]; state=["dmac_reset_pulse", "int_tc", "int_abort", "int_error", "ch_enable"].
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AHB_WRITE.outputs.output_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DUT port ["hready", "hresp", "dma_int"] is the implementation/observation point for AHB slave register write
- SSOT refs: function_model.transactions.FM_AHB_WRITE.outputs.output_1
