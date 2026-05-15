# RTL Authoring Packet: module__fifo_sync_ptrs

- Kind: module
- Owner module: fifo_sync_ptrs
- Owner file: rtl/fifo_sync_ptrs.sv
- Task count: 46
- Required tasks: 46

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, decomposition.units.pointer_control, fsm, fsm.ptr_fsm, function_model, function_model.state_variables
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0027: Implement pointer management and fill counter

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model state_variables (wr_ptr, rd_ptr, count) and cycle_model pipeline stages into sequential always block with push/pop acceptance logic. Wrapping is modular at DEPTH. Count increments on push, decrements on pop, clamped to [0..DEPTH].
SSOT ref: workflow_todos.rtl-gen[0].
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO_PTRS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - wr_ptr and rd_ptr are declared with correct width ($clog2(DEPTH))
  - count is declared with width $clog2(DEPTH+1)
  - Push increments wr_ptr and count when wr_en_i && !full_o && !flush_i
  - Pop increments rd_ptr and decrements count when rd_en_i && !empty_o && !flush_i
  - Simultaneous push/pop: both pointers advance, count unchanged
  - Flush: all three reset to 0, priority over push/pop
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm.ptr_fsm, function_model.state_variables
- SSOT refs: cycle_model.pipeline, fsm.ptr_fsm, function_model.state_variables, workflow_todos.rtl-gen[0]

### RTL-0061: Implement RTL state owner for FL state wr_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.wr_ptr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.wr_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.state_variables.
SSOT item context: name=wr_ptr; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - wr_ptr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.wr_ptr

### RTL-0062: Implement RTL state owner for FL state rd_ptr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rd_ptr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rd_ptr.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.state_variables.
SSOT item context: name=rd_ptr; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - rd_ptr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rd_ptr

### RTL-0063: Implement RTL state owner for FL state count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.count.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.state_variables.
SSOT item context: name=count; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.count
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.count

### RTL-0064: Implement RTL state owner for FL state mem

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.mem
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.mem.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.state_variables.
SSOT item context: name=mem; reset=0x0 per entry.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.mem
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - mem reset behavior matches SSOT value 0x0 per entry
- SSOT refs: function_model.state_variables.mem

### RTL-0150: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=count is always in range [0, DEPTH]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0151: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=full_o == 1 if and only if count == DEPTH..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0152: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=empty_o == 1 if and only if count == 0..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0153: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=wr_ptr and rd_ptr are always in range [0, DEPTH-1]..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0154: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=No read data changes unless rd_en_i is accepted or flush occurs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_4

### RTL-0155: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Simultaneous push/pop leaves count unchanged..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_5

### RTL-0156: Preserve FL invariant invariant_6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_6
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_6.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via function_model.
SSOT item context: value=Overflow and underflow are silently rejected with no state corruption..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_6
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: function_model.invariants.invariant_6

### RTL-0157: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0158: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0160: Implement handshake rule: wr_en_i

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.wr_en_i
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.wr_en_i.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.handshake_rules.
SSOT item context: signal=wr_en_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.wr_en_i
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.handshake_rules.wr_en_i appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.wr_en_i

### RTL-0161: Implement handshake rule: rd_en_i

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.rd_en_i
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.rd_en_i.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.handshake_rules.
SSOT item context: signal=rd_en_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.rd_en_i
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.handshake_rules.rd_en_i appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.rd_en_i

### RTL-0162: Implement handshake rule: full_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.full_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.full_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.handshake_rules.
SSOT item context: signal=full_o.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.full_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.handshake_rules.full_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.full_o

### RTL-0163: Implement handshake rule: empty_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.empty_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.empty_o.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.handshake_rules.
SSOT item context: signal=empty_o.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.empty_o
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.handshake_rules.empty_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.empty_o

### RTL-0164: Implement handshake rule: flush_i

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.flush_i
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.flush_i.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.handshake_rules.
SSOT item context: signal=flush_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.flush_i
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.handshake_rules.flush_i appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.flush_i

### RTL-0165: Implement pipeline stage: S0_SAMPLE_INPUTS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_SAMPLE_INPUTS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_SAMPLE_INPUTS.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.pipeline.
SSOT item context: stage=S0_SAMPLE_INPUTS; action=Sample wr_en_i, rd_en_i, flush_i, wr_data_i on rising PCLK edge; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_SAMPLE_INPUTS
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.pipeline.S0_SAMPLE_INPUTS timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_SAMPLE_INPUTS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_SAMPLE_INPUTS

### RTL-0166: Implement pipeline stage: S1_EVAL_ACCEPT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_EVAL_ACCEPT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_EVAL_ACCEPT.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.pipeline.
SSOT item context: stage=S1_EVAL_ACCEPT; action=Combinational: determine push_accepted = wr_en_i && !full_o && !flush_i; pop_accepted = rd_en_i && !empty_o && !flush_i; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_EVAL_ACCEPT
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.pipeline.S1_EVAL_ACCEPT timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S1_EVAL_ACCEPT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_EVAL_ACCEPT

### RTL-0167: Implement pipeline stage: S2_UPDATE_PTRS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_UPDATE_PTRS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_UPDATE_PTRS.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.pipeline.
SSOT item context: stage=S2_UPDATE_PTRS; action=Update wr_ptr, rd_ptr, count registers based on push/pop acceptance; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_UPDATE_PTRS
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.pipeline.S2_UPDATE_PTRS timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S2_UPDATE_PTRS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_UPDATE_PTRS

### RTL-0168: Implement pipeline stage: S3_WRITE_MEM

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S3_WRITE_MEM
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S3_WRITE_MEM.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.pipeline.
SSOT item context: stage=S3_WRITE_MEM; action=Write wr_data_i to mem[wr_ptr] when push_accepted; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S3_WRITE_MEM
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.pipeline.S3_WRITE_MEM timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S3_WRITE_MEM appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S3_WRITE_MEM

### RTL-0169: Implement pipeline stage: S4_UPDATE_FLAGS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_UPDATE_FLAGS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_UPDATE_FLAGS.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.pipeline.
SSOT item context: stage=S4_UPDATE_FLAGS; action=Flags (full, empty, almost_full, almost_empty, count) reflect new pointer state; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_UPDATE_FLAGS
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.pipeline.S4_UPDATE_FLAGS timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.S4_UPDATE_FLAGS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_UPDATE_FLAGS

### RTL-0170: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=Push data is captured into memory in the same cycle as pointer update..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0171: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=Pop data is available combinationally from memory (USE_OUTPUT_REGISTER=0) or one cycle later (USE_OUTPUT_REGISTER=1)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0172: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=Flush clears all state in the cycle it is sampled; concurrent push/pop are ignored..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0173: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=Flag updates are visible on the cycle after pointer/count changes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0174: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=full_o provides natural backpressure to the writer; the writer must deassert wr_en_i or accept rejection..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0175: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=empty_o provides natural backpressure to the reader; the reader must deassert rd_en_i or accept undefined data..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0176: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0192: Implement FSM state ptr_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=EMPTY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_0

### RTL-0193: Implement FSM state ptr_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=ALMOST_EMPTY.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_1

### RTL-0194: Implement FSM state ptr_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=NORMAL.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_2

### RTL-0195: Implement FSM state ptr_fsm.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=ALMOST_FULL.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_3

### RTL-0196: Implement FSM state ptr_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=FULL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_4

### RTL-0197: Implement FSM transition ptr_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=EMPTY; to=NORMAL; condition=push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_0 condition is implemented as RTL control logic: push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_0 transition path EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_0

### RTL-0198: Implement FSM transition ptr_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=EMPTY; to=ALMOST_EMPTY; condition=push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_1 condition is implemented as RTL control logic: push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0
  - fsm.ptr_fsm.transitions.transition_1 transition path EMPTY -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_1

### RTL-0199: Implement FSM transition ptr_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_EMPTY; to=EMPTY; condition=pop_accepted && count becomes 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_2 condition is implemented as RTL control logic: pop_accepted && count becomes 0
  - fsm.ptr_fsm.transitions.transition_2 transition path ALMOST_EMPTY -> EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_2

### RTL-0200: Implement FSM transition ptr_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_EMPTY; to=NORMAL; condition=push_accepted && count > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_3 condition is implemented as RTL control logic: push_accepted && count > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_3 transition path ALMOST_EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_3

### RTL-0201: Implement FSM transition ptr_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=NORMAL; to=ALMOST_FULL; condition=push_accepted && count >= ALMOST_FULL_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_4 condition is implemented as RTL control logic: push_accepted && count >= ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_4 transition path NORMAL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_4

### RTL-0202: Implement FSM transition ptr_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_5.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=NORMAL; to=ALMOST_EMPTY; condition=pop_accepted && count <= ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_5 condition is implemented as RTL control logic: pop_accepted && count <= ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_5 transition path NORMAL -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_5

### RTL-0203: Implement FSM transition ptr_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_6.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_FULL; to=FULL; condition=push_accepted && count == DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_6 condition is implemented as RTL control logic: push_accepted && count == DEPTH
  - fsm.ptr_fsm.transitions.transition_6 transition path ALMOST_FULL -> FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_6

### RTL-0204: Implement FSM transition ptr_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_7.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_FULL; to=NORMAL; condition=pop_accepted && count < ALMOST_FULL_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_7 condition is implemented as RTL control logic: pop_accepted && count < ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_7 transition path ALMOST_FULL -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_7

### RTL-0205: Implement FSM transition ptr_fsm.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_8.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=FULL; to=ALMOST_FULL; condition=pop_accepted && count == DEPTH-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_8 condition is implemented as RTL control logic: pop_accepted && count == DEPTH-1
  - fsm.ptr_fsm.transitions.transition_8 transition path FULL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_8

### RTL-0245: Prove module fifo_sync_ptrs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.fifo_sync_ptrs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.fifo_sync_ptrs.module_equivalence.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.fifo_sync_ptrs.module_equivalence
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: sub_modules.fifo_sync_ptrs.module_equivalence
