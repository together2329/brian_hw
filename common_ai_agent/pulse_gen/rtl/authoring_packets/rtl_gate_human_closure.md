# RTL Authoring Packet: rtl_gate_human_closure

- Kind: gate
- Owner module: pulse_gen
- Owner file: rtl/pulse_gen.sv
- Task count: 4
- Required tasks: 4

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
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 1
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Locked-truth blockers:
  - manifest_connection_contract_evidence: 7 SSOT connection contract issue(s) remain. pulse_gen_core: RTL named port-map expression does not match SSOT connection signal terms; pulse_gen_regs: RTL named port-map expression does not match SSOT connection signal terms; pulse_gen_regs: RTL named port-map expression does not match SSOT connection signal terms
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen.PRDATA <= pulse_gen_regs.PRDATA (integration.connections[7])
  - pulse_gen.PREADY <= 1'b1 (zero-wait-state) (integration.connections[8])
  - pulse_gen.PSLVERR <= pulse_gen_regs.PSLVERR (integration.connections[9])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0003: Gate: SSOT function_model and cycle_model are present before RTL generation

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.ssot_required_sections
- Detail: rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.
SSOT ref: quality_gates.rtl_gen.ssot_required_sections.
Owner: pulse_gen in rtl/pulse_gen.sv via top_module.
- Current reason: SSOT function_model and cycle_model authority is present.
- Criteria:
  - function_model is present and non-empty in the SSOT
  - cycle_model is present and non-empty in the SSOT
  - Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL
  - Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.ssot_required_sections

### RTL-0004: Gate: SSOT-authored rtl-gen workflow TODOs are well formed

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.workflow_todo_contract
- Detail: Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.
SSOT ref: quality_gates.rtl_gen.workflow_todo_contract.
Owner: pulse_gen in rtl/pulse_gen.sv via top_module.
- Current reason: SSOT-authored rtl-gen workflow TODOs are well formed.
- Criteria:
  - Every workflow_todos.rtl-gen item has content
  - Every workflow_todos.rtl-gen item has detail
  - Every workflow_todos.rtl-gen item has at least one criteria entry
  - Traceability keeps source_ref quality_gates.rtl_gen.workflow_todo_contract
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.workflow_todo_contract

### RTL-0005: Gate: every SSOT-derived RTL behavior has an owner module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_traceability
- Detail: Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.
SSOT ref: quality_gates.rtl_gen.owner_traceability.
Owner: pulse_gen in rtl/pulse_gen.sv via top_module.
- Current reason: Every required SSOT-derived RTL behavior has an owner module.
- Criteria:
  - No required function_model task is orphaned
  - No required cycle_model task is orphaned
  - No required register/dataflow/FSM task is orphaned
  - Owner module and owner file are recorded in rtl_todo_plan.json
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_traceability
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_traceability

### RTL-0016: Gate: SSOT connection contracts match RTL child port maps

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_connection_contract_evidence
- Detail: Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts.
SSOT ref: quality_gates.rtl_gen.manifest_connection_contract_evidence.
Owner: pulse_gen in rtl/pulse_gen.sv via top_module.
- Current reason: 7 SSOT connection contract issue(s) remain. pulse_gen_core: RTL named port-map expression does not match SSOT connection signal terms; pulse_gen_regs: RTL named port-map expression does not match SSOT connection signal terms; pulse_gen_regs: RTL named port-map expression does not match SSOT connection signal terms
- Criteria:
  - Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections
  - Each SSOT connection contract resolves to a reachable manifest child module and port
  - RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_connection_contract_evidence
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_connection_contract_evidence
