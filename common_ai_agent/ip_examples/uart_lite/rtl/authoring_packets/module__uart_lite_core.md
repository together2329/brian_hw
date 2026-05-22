# RTL Authoring Packet: module__uart_lite_core

- Kind: module
- Owner module: uart_lite_core
- Owner file: rtl/uart_lite_core.sv
- Task count: 33
- Required tasks: 33

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, decomposition.units.execute, features, function_model, function_model.state_variables, function_model.transactions
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])
  - uart_lite_core.tx_o <= tx (integration.connections[3])
  - uart_lite_core.rx_i <= rx (integration.connections[4])

## Tasks

### RTL-0027: Implement the SSOT-declared UART transceiver pipeline

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model transactions (FM_TX_BYTE, FM_RX_BYTE, FM_BREAK_SEND, FM_LOOPBACK), cycle_model TX/RX pipeline stages, FSM states/transitions, and ownership refs into RTL state/datapath/control logic across the 7 sub-modules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: uart_lite_core in rtl/uart_lite_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPL_UART_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is present in each declared owner_file per sub_modules
  - DUT-only compile passes on all 8 RTL files
  - DUT lint passes with no unwaived errors
  - FunctionalModel expected result and RTL observed result can be compared for every function_model transaction
  - Every cycle_model pipeline stage and handshake rule is traceable to RTL logic
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm, function_model.transactions
- SSOT refs: cycle_model.pipeline, fsm, function_model.transactions, workflow_todos.rtl-gen[0]

### RTL-0053: Implement RTL state owner for FL state tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_fifo.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=tx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_fifo
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - tx_fifo reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.tx_fifo

### RTL-0054: Implement RTL state owner for FL state rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rx_fifo
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rx_fifo.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=rx_fifo; reset=empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_fifo
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - rx_fifo reset behavior matches SSOT value empty
- SSOT refs: function_model.state_variables.rx_fifo

### RTL-0055: Implement RTL state owner for FL state tx_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.tx_active
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.tx_active.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=tx_active.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.tx_active
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.tx_active

### RTL-0056: Implement RTL state owner for FL state rx_active

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rx_active
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rx_active.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=rx_active.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rx_active
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.rx_active

### RTL-0057: Implement RTL state owner for FL state baud_div

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.baud_div
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.baud_div.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=baud_div; reset=324.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.baud_div
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - baud_div reset behavior matches SSOT value 324
- SSOT refs: function_model.state_variables.baud_div

### RTL-0058: Implement RTL state owner for FL state parity_en

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.parity_en
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.parity_en.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=parity_en.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.parity_en
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.parity_en

### RTL-0059: Implement RTL state owner for FL state parity_odd

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.parity_odd
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.parity_odd.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=parity_odd.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.parity_odd
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.parity_odd

### RTL-0060: Implement RTL state owner for FL state stop_bits

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.stop_bits
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.stop_bits.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=stop_bits.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.stop_bits
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.stop_bits

### RTL-0061: Implement RTL state owner for FL state loopback

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.loopback
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.loopback.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=loopback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.loopback
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.loopback

### RTL-0062: Implement RTL state owner for FL state break_send

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.break_send
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.break_send.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.state_variables.
SSOT item context: name=break_send.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.break_send
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.state_variables.break_send

### RTL-0094: Implement transaction FM_BREAK_SEND

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_BREAK_SEND
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_BREAK_SEND.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: id=FM_BREAK_SEND; name=send_break.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND

### RTL-0095: Implement precondition for FM_BREAK_SEND: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_BREAK_SEND.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.preconditions.precondition_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=break_send written to 1 via CTRL register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND.preconditions.precondition_0

### RTL-0096: Implement input for FM_BREAK_SEND: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_BREAK_SEND.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.inputs.input_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND.inputs.input_0

### RTL-0097: Implement output for FM_BREAK_SEND: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_BREAK_SEND.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.outputs.output_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=tx line forced low for duration of one full frame (start+data+parity+stop bits).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND.outputs.output_0

### RTL-0098: Implement output rule for FM_BREAK_SEND: tx_serial

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_BREAK_SEND.output_rules.tx_serial
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.output_rules.tx_serial.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: name=tx_serial; port=tx; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.output_rules.tx_serial
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - tx_serial RTL expression implements SSOT expression 1
  - DUT port tx is the implementation/observation point for tx_serial
  - tx_serial is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_BREAK_SEND.output_rules.tx_serial

### RTL-0099: Implement state update for FM_BREAK_SEND: tx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_BREAK_SEND.state_updates.tx
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.state_updates.tx.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: name=tx; expr=0; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.state_updates.tx
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - tx reset behavior matches SSOT value 1
  - tx RTL expression implements SSOT expression 0
  - tx updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_BREAK_SEND.state_updates.tx

### RTL-0100: Implement side effect for FM_BREAK_SEND: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=break_send self-clears to 0 after break completes.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_0

### RTL-0101: Implement side effect for FM_BREAK_SEND: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=TX FSM held in IDLE during break.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_BREAK_SEND.side_effects.side_effect_1

### RTL-0102: Implement transaction FM_LOOPBACK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_LOOPBACK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_LOOPBACK.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: id=FM_LOOPBACK; name=loopback_mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK

### RTL-0103: Implement precondition for FM_LOOPBACK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=loopback == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.preconditions.precondition_0

### RTL-0104: Implement input for FM_LOOPBACK: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_LOOPBACK.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.inputs.input_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=tx line output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.inputs.input_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.inputs.input_0

### RTL-0105: Implement output for FM_LOOPBACK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_LOOPBACK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.outputs.output_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=rx synchronizer input connected to tx output (after 2-FF synchronizer stage).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.outputs.output_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.outputs.output_0

### RTL-0106: Implement output rule for FM_LOOPBACK: loopback_tx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_LOOPBACK.output_rules.loopback_tx
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.output_rules.loopback_tx.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: name=loopback_tx; port=tx; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.output_rules.loopback_tx
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - loopback_tx RTL expression implements SSOT expression 1
  - DUT port tx is the implementation/observation point for loopback_tx
  - loopback_tx is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_LOOPBACK.output_rules.loopback_tx

### RTL-0107: Implement state update for FM_LOOPBACK: tx

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_LOOPBACK.state_updates.tx
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.state_updates.tx.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: name=tx; expr=1; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.state_updates.tx
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - tx reset behavior matches SSOT value 1
  - tx RTL expression implements SSOT expression 1
  - tx updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_LOOPBACK.state_updates.tx

### RTL-0108: Implement side effect for FM_LOOPBACK: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=External rx pin ignored.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_0

### RTL-0109: Implement side effect for FM_LOOPBACK: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1.
Owner: uart_lite_core in rtl/uart_lite_core.sv via function_model.transactions.
SSOT item context: value=All TX bytes appear as received bytes when rx_enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: function_model.transactions.FM_LOOPBACK.side_effects.side_effect_1

### RTL-0238: Implement feature TX serialization

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.TX_serialization
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.TX_serialization.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=TX serialization; output=Serial UART frame on tx pin.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.TX_serialization
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.TX_serialization

### RTL-0239: Implement feature RX deserialization

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.RX_deserialization
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.RX_deserialization.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=RX deserialization; output=Received byte available in RXDATA register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.RX_deserialization
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.RX_deserialization

### RTL-0240: Implement feature Parity generation/checking

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Parity_generation_checking
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Parity_generation_checking.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Parity generation/checking; output=parity_err sticky flag on mismatch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Parity_generation_checking
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Parity_generation_checking

### RTL-0241: Implement feature Loopback test mode

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Loopback_test_mode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Loopback_test_mode.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Loopback test mode; output=Transmitted bytes appear in RX FIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Loopback_test_mode
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Loopback_test_mode

### RTL-0242: Implement feature Break send

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Break_send
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Break_send.
Owner: uart_lite_core in rtl/uart_lite_core.sv via features.
SSOT item context: name=Break send; output=Break condition on tx line.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Break_send
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: features.Break_send

### RTL-0268: Prove module uart_lite_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_core.module_equivalence.
Owner: uart_lite_core in rtl/uart_lite_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_core.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_core.sv
- SSOT refs: sub_modules.uart_lite_core.module_equivalence
