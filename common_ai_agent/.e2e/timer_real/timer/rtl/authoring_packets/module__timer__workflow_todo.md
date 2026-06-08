# RTL Authoring Packet: module__timer__workflow_todo

- Kind: module
- Owner module: timer
- Owner file: rtl/timer.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 8/8 section=workflow_todo task_limit=48
- Slice rule: Owner module timer is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
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
- SSOT top IO contracts: 11

## Tasks

### RTL-0020: Implement timer top module ports and reset behavior.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Create rtl/timer.sv with pclk, presetn, APB-style slave ports, irq output, active-low reset, and integration wiring to timer_regs and timer_core as declared by io_list and integration.connections.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: timer in rtl/timer.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_TOP_AND_PORTS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl/timer.sv module name is timer and compiles standalone.
  - Active-low reset implements rtl_contract.reset_behavior.
  - Top ports match io_list.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/timer.sv
  - Semantic source_refs covered: integration.connections, io_list, rtl_contract.reset_behavior, top_module
- SSOT refs: integration.connections, io_list, rtl_contract.reset_behavior, top_module, workflow_todos.rtl-gen[0]

### RTL-0023: Preserve signals needed for structured scoreboard events and debug observability.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Ensure implementation exposes or makes observable pclk, presetn, APB controls, prdata, pready, pslverr, irq, load_q, enable_q, and count_q for cocotb/pyuvm checks.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: timer in rtl/timer.sv via workflow_todos.owner.
SSOT item context: id=RTL_TIMER_SCOREBOARD_EVENTS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Structured scoreboard events can be emitted for reset, LOAD write, ENABLE write, STATUS read, and irq pulse.
  - Waveform probes listed in debug_observability are available.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/timer.sv
  - Semantic source_refs covered: debug_observability.trace_events, debug_observability.waveform_must_probe, test_requirements.scenarios
- SSOT refs: debug_observability.trace_events, debug_observability.waveform_must_probe, test_requirements.scenarios, workflow_todos.rtl-gen[3]
