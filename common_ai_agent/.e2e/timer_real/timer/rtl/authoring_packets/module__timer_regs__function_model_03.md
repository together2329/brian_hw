# RTL Authoring Packet: module__timer_regs__function_model_03

- Kind: module
- Owner module: timer_regs
- Owner file: rtl/timer_regs.sv
- Task count: 3
- Required tasks: 3

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
- Owner refs: error_handling, function_model, function_model.invariants, function_model.state_variables, function_model.transactions.FM_APB_READ_STATUS, function_model.transactions.FM_APB_UNMAPPED_ACCESS, function_model.transactions.FM_APB_WRITE_CTRL, function_model.transactions.FM_APB_WRITE_LOAD, function_model.transactions.FM_DISABLED_HOLD, function_model.transactions.FM_TICK_DECREMENT, function_model.transactions.FM_TICK_RELOAD_IRQ, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.LOAD, registers.register_list.STATUS
- Module slice: 3/7 section=function_model task_limit=48
- Slice rule: Owner module timer_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])

## Tasks

### RTL-0138: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: timer_regs in rtl/timer_regs.sv via function_model.invariants.
SSOT item context: port=["pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]; signal=enable_q == 0 or enable_q == 1; state=["enable_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"] is the implementation/observation point for ["pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]
- SSOT refs: function_model.invariants.invariant_2

### RTL-0139: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: timer_regs in rtl/timer_regs.sv via function_model.invariants.
SSOT item context: port=["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]; signal=irq_q == 0 or irq_q == 1; state=["irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"] is the implementation/observation point for ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]
- SSOT refs: function_model.invariants.invariant_3

### RTL-0140: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: timer_regs in rtl/timer_regs.sv via function_model.invariants.
SSOT item context: port=["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]; signal=enable_q == 0 and psel == 0 implies irq_q == 0; state=["enable_q", "irq_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/timer_regs.sv
  - DUT port ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"] is the implementation/observation point for ["pready", "pslverr", "pready", "pslverr", "prdata", "pready", "pslverr", "irq", "irq", "irq", "pready", "pslverr"]
- SSOT refs: function_model.invariants.invariant_4
