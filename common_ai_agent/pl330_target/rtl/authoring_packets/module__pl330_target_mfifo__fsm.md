# RTL Authoring Packet: module__pl330_target_mfifo__fsm

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 24
- Required tasks: 24

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 4/11 section=fsm task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_mfifo.cfg_nonsecure_allowed_i <= mfifo_cfg_nonsecure_allowed_i (observed_named_port_map)
  - pl330_target_mfifo.channel_pc_o <= mfifo_channel_pc_o (observed_named_port_map)
  - pl330_target_mfifo.channel_state_o <= mfifo_channel_state_o (observed_named_port_map)
  - pl330_target_mfifo.clk <= clk (observed_named_port_map)
  - pl330_target_mfifo.cmd_accept_o <= mfifo_cmd_accept_o (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_addr_i <= mfifo_cmd_arg_addr_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_data_i <= mfifo_cmd_arg_data_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_error_o <= mfifo_cmd_error_o (observed_named_port_map)

## Tasks

### RTL-0215: Implement FSM state channel_state.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=STOPPED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_0

### RTL-0216: Implement FSM state channel_state.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=EXECUTING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_1

### RTL-0217: Implement FSM state channel_state.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=CACHE_MISS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_2

### RTL-0218: Implement FSM state channel_state.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_3.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=UPDATING_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_3
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_3

### RTL-0219: Implement FSM state channel_state.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_4.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=WAITING_FOR_EVENT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_4
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_4

### RTL-0220: Implement FSM state channel_state.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_5.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=AT_BARRIER.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_5
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_5

### RTL-0221: Implement FSM state channel_state.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_6.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=KILLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_6
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_6

### RTL-0222: Implement FSM state channel_state.state_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_7.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=COMPLETING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_7
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_7

### RTL-0223: Implement FSM state channel_state.state_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_8
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_8.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=FAULTING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_8
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_8

### RTL-0224: Implement FSM state channel_state.state_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_9
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_9.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=FAULTING_COMPLETING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_9
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_9

### RTL-0225: Implement FSM transition channel_state.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=STOPPED; to=EXECUTING; condition=DMAGO + secure check pass.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_0 condition is implemented as RTL control logic: DMAGO + secure check pass
  - fsm.channel_state.transitions.transition_0 transition path STOPPED -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_0

### RTL-0226: Implement FSM transition channel_state.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=CACHE_MISS; condition=icache miss.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_1 condition is implemented as RTL control logic: icache miss
  - fsm.channel_state.transitions.transition_1 transition path EXECUTING -> CACHE_MISS is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_1

### RTL-0227: Implement FSM transition channel_state.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=CACHE_MISS; to=EXECUTING; condition=fill complete.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_2 condition is implemented as RTL control logic: fill complete
  - fsm.channel_state.transitions.transition_2 transition path CACHE_MISS -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_2

### RTL-0228: Implement FSM transition channel_state.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_3.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=WAITING_FOR_EVENT; condition=DMAWFE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_3
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_3 condition is implemented as RTL control logic: DMAWFE
  - fsm.channel_state.transitions.transition_3 transition path EXECUTING -> WAITING_FOR_EVENT is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_3

### RTL-0229: Implement FSM transition channel_state.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_4.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=WAITING_FOR_EVENT; to=EXECUTING; condition=event signaled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_4
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_4 condition is implemented as RTL control logic: event signaled
  - fsm.channel_state.transitions.transition_4 transition path WAITING_FOR_EVENT -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_4

### RTL-0230: Implement FSM transition channel_state.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_5.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=AT_BARRIER; condition=DMAWFP barrier.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_5
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_5 condition is implemented as RTL control logic: DMAWFP barrier
  - fsm.channel_state.transitions.transition_5 transition path EXECUTING -> AT_BARRIER is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_5

### RTL-0231: Implement FSM transition channel_state.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_6.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=AT_BARRIER; to=EXECUTING; condition=barrier cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_6
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_6 condition is implemented as RTL control logic: barrier cleared
  - fsm.channel_state.transitions.transition_6 transition path AT_BARRIER -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_6

### RTL-0232: Implement FSM transition channel_state.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_7.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=COMPLETING; condition=DMAEND issued.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_7
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_7 condition is implemented as RTL control logic: DMAEND issued
  - fsm.channel_state.transitions.transition_7 transition path EXECUTING -> COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_7

### RTL-0233: Implement FSM transition channel_state.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_8.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=COMPLETING; to=STOPPED; condition=all outstanding drained.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_8
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_8 condition is implemented as RTL control logic: all outstanding drained
  - fsm.channel_state.transitions.transition_8 transition path COMPLETING -> STOPPED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_8

### RTL-0234: Implement FSM transition channel_state.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_9.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=any; to=KILLING; condition=DMAKILL via DBGCMD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_9
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_9 condition is implemented as RTL control logic: DMAKILL via DBGCMD
  - fsm.channel_state.transitions.transition_9 transition path any -> KILLING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_9

### RTL-0235: Implement FSM transition channel_state.transition_10

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_10.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=KILLING; to=STOPPED; condition=kill drained.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_10
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_10 condition is implemented as RTL control logic: kill drained
  - fsm.channel_state.transitions.transition_10 transition path KILLING -> STOPPED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_10

### RTL-0236: Implement FSM transition channel_state.transition_11

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_11
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_11.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=any; to=FAULTING; condition=any error_case.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_11
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_11 condition is implemented as RTL control logic: any error_case
  - fsm.channel_state.transitions.transition_11 transition path any -> FAULTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_11

### RTL-0237: Implement FSM transition channel_state.transition_12

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_12
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_12.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=FAULTING; to=FAULTING_COMPLETING; condition=fault recovery initiated.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_12
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_12 condition is implemented as RTL control logic: fault recovery initiated
  - fsm.channel_state.transitions.transition_12 transition path FAULTING -> FAULTING_COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_12

### RTL-0238: Implement FSM transition channel_state.transition_13

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_13
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_13.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=FAULTING_COMPLETING; to=STOPPED; condition=drain complete.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_13
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_13 condition is implemented as RTL control logic: drain complete
  - fsm.channel_state.transitions.transition_13 transition path FAULTING_COMPLETING -> STOPPED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_13
