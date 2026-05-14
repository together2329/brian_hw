# RTL Authoring Packet: module__todo_counter_pipe_core__features

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 7/9 section=features task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0227: Implement feature Up/Down Counting

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Up_Down_Counting
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Up_Down_Counting.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Up_Down_Counting.
SSOT item context: name=Up/Down Counting; output=Updated cnt value reflected in CNT register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Up_Down_Counting
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Up_Down_Counting

### RTL-0228: Implement feature Saturating Mode

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Saturating_Mode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Saturating_Mode.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Saturating_Mode.
SSOT item context: name=Saturating Mode; output=cnt held at limit; STATUS.overflow/underflow asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Saturating_Mode
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Saturating_Mode

### RTL-0229: Implement feature Wrap Mode

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Wrap_Mode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Wrap_Mode.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Wrap_Mode.
SSOT item context: name=Wrap Mode; output=cnt wraps to opposite extreme; STATUS flags asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Wrap_Mode
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Wrap_Mode

### RTL-0230: Implement feature Clear/Load Control

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Clear_Load_Control
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Clear_Load_Control.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Clear_Load_Control.
SSOT item context: name=Clear/Load Control; output=cnt updated on next core_clk edge after CDC convergence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Clear_Load_Control
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Clear_Load_Control

### RTL-0231: Implement feature Terminal Count Interrupt

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Terminal_Count_Interrupt
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Terminal_Count_Interrupt.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Terminal_Count_Interrupt.
SSOT item context: name=Terminal Count Interrupt; output=INTSTAT.tc_pending; counter_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Terminal_Count_Interrupt
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Terminal_Count_Interrupt

### RTL-0232: Implement feature Debug Cycle Counter

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Debug_Cycle_Counter
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Debug_Cycle_Counter.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via features.Debug_Cycle_Counter.
SSOT item context: name=Debug Cycle Counter; output=DBGCNT.dbg_cycle_count readable via APB after CDC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Debug_Cycle_Counter
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: features.Debug_Cycle_Counter
