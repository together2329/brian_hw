# RTL Authoring Packet: module__mctp_assembler_v3_axi_wr_ingress__fsm

- Kind: module
- Owner module: mctp_assembler_v3_axi_wr_ingress
- Owner file: rtl/mctp_assembler_v3_axi_wr_ingress.sv
- Task count: 11
- Required tasks: 11

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
- Owner refs: cycle_model, cycle_model.handshake_rules, function_model, function_model.transactions.FM_INGEST_TLP, io_list, io_list.interfaces.axi_wr_slave, test_requirements
- Module slice: 4/6 section=fsm task_limit=48
- Slice rule: Owner module mctp_assembler_v3_axi_wr_ingress is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])

## Tasks

### RTL-0406: Implement FSM state ingress_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=ACCEPT_AW.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_1

### RTL-0407: Implement FSM state ingress_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=COLLECT_W.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_2

### RTL-0408: Implement FSM state ingress_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_3.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=CHECK_LEGAL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_3

### RTL-0409: Implement FSM state ingress_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_4.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=EMIT_TLP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_4

### RTL-0410: Implement FSM state ingress_fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_5.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=RESP_B.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_5

### RTL-0411: Implement FSM transition ingress_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=IDLE; to=ACCEPT_AW; condition=awvalid && awready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_0 condition is implemented as RTL control logic: awvalid && awready
  - fsm.ingress_fsm.transitions.transition_0 transition path IDLE -> ACCEPT_AW is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_0

### RTL-0412: Implement FSM transition ingress_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=ACCEPT_AW; to=COLLECT_W; condition=AWSIZE==5 && AWBURST==INCR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_1 condition is implemented as RTL control logic: AWSIZE==5 && AWBURST==INCR
  - fsm.ingress_fsm.transitions.transition_1 transition path ACCEPT_AW -> COLLECT_W is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_1

### RTL-0414: Implement FSM transition ingress_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_3.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=COLLECT_W; to=CHECK_LEGAL; condition=wlast && wvalid && wready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_3 condition is implemented as RTL control logic: wlast && wvalid && wready
  - fsm.ingress_fsm.transitions.transition_3 transition path COLLECT_W -> CHECK_LEGAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_3

### RTL-0415: Implement FSM transition ingress_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_4.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=CHECK_LEGAL; to=EMIT_TLP; condition=beat-count/WSTRB/length legal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_4 condition is implemented as RTL control logic: beat-count/WSTRB/length legal
  - fsm.ingress_fsm.transitions.transition_4 transition path CHECK_LEGAL -> EMIT_TLP is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_4

### RTL-0417: Implement FSM transition ingress_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_6.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=EMIT_TLP; to=RESP_B; condition=TLP bytes emitted to parser.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_6 condition is implemented as RTL control logic: TLP bytes emitted to parser
  - fsm.ingress_fsm.transitions.transition_6 transition path EMIT_TLP -> RESP_B is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_6

### RTL-0418: Implement FSM transition ingress_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_7.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=RESP_B; to=IDLE; condition=bvalid && bready (OKAY).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_7 condition is implemented as RTL control logic: bvalid && bready (OKAY)
  - fsm.ingress_fsm.transitions.transition_7 transition path RESP_B -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_7
