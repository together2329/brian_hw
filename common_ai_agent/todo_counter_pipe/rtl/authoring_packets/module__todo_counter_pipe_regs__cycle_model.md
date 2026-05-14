# RTL Authoring Packet: module__todo_counter_pipe_regs__cycle_model

- Kind: module
- Owner module: todo_counter_pipe_regs
- Owner file: rtl/todo_counter_pipe_regs.sv
- Task count: 5
- Required tasks: 5

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
- Owner refs: cycle_model.handshake_rules.counter_irq, cycle_model.handshake_rules.prdata, cycle_model.handshake_rules.pready, cycle_model.pipeline.S0_APB_ACCESS, cycle_model.pipeline.S4_STATUS_UPDATE, decomposition.units.apb_decode, function_model.transactions.FM10, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CNT, registers.register_list.CTRL, registers.register_list.DBGCNT, registers.register_list.INTCLR
- Module slice: 3/7 section=cycle_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_regs.bus_clk <= bus_clk (integration.connections[0])
  - todo_counter_pipe_regs.bus_rst_n <= bus_rst_n (integration.connections[1])
  - todo_counter_pipe_regs.irq_o <= counter_irq (integration.connections[2])

## Tasks

### RTL-0163: Implement handshake rule: pready

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.pready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.pready.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via cycle_model.handshake_rules.pready.
SSOT item context: signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.pready
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - cycle_model.handshake_rules.pready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.pready

### RTL-0164: Implement handshake rule: prdata

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.prdata
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.prdata.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via cycle_model.handshake_rules.prdata.
SSOT item context: signal=prdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.prdata
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - cycle_model.handshake_rules.prdata appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.prdata

### RTL-0166: Implement handshake rule: counter_irq

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.counter_irq
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.counter_irq.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via cycle_model.handshake_rules.counter_irq.
SSOT item context: signal=counter_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.counter_irq
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - cycle_model.handshake_rules.counter_irq appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.counter_irq

### RTL-0167: Implement pipeline stage: S0_APB_ACCESS

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_APB_ACCESS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_APB_ACCESS.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via cycle_model.pipeline.S0_APB_ACCESS.
SSOT item context: stage=S0_APB_ACCESS; action=APB decode: paddr→register select, pwrite→read/write, pwdata→write data captured on psel&&penable; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_APB_ACCESS
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - cycle_model.pipeline.S0_APB_ACCESS timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.S0_APB_ACCESS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_APB_ACCESS

### RTL-0171: Implement pipeline stage: S4_STATUS_UPDATE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_STATUS_UPDATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_STATUS_UPDATE.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via cycle_model.pipeline.S4_STATUS_UPDATE.
SSOT item context: stage=S4_STATUS_UPDATE; action=Latched status reflected in CNT/STATUS/INTSTAT registers; W1C clear logic evaluated; counter_irq updated; cycle=0..1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_STATUS_UPDATE
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - cycle_model.pipeline.S4_STATUS_UPDATE timing uses SSOT cycle/latency 0..1
  - cycle_model.pipeline.S4_STATUS_UPDATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_STATUS_UPDATE
