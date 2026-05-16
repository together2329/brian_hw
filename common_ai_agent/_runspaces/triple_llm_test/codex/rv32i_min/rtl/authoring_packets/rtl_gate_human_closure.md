# RTL Authoring Packet: rtl_gate_human_closure

- Kind: gate
- Owner module: rv32i_min
- Owner file: rtl/rv32i_min.sv
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
- Owner refs: integration, integration.connections, io_list
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- Locked-truth blockers:
  - manifest_connection_contract_evidence: 8 SSOT connection contract issue(s) remain. rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_memwb: RTL named port-map expression does not match SSOT connection signal terms
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])
  - rv32i_min_memwb.d_addr <= d_addr (integration.connections[3])
  - rv32i_min_memwb.d_wdata <= d_wdata (integration.connections[4])
  - rv32i_min_memwb.d_rdata <= d_rdata (integration.connections[5])
  - rv32i_min_memwb.d_we <= d_we (integration.connections[6])
  - rv32i_min_memwb.d_be <= d_be (integration.connections[7])
  - rv32i_min_memwb.d_valid <= d_valid (integration.connections[8])
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])
- SSOT top IO contracts: 24

## Tasks

### RTL-0003: Gate: SSOT function_model and cycle_model are present before RTL generation

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.ssot_required_sections
- Detail: rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.
SSOT ref: quality_gates.rtl_gen.ssot_required_sections.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: SSOT function_model and cycle_model authority is present.
- Criteria:
  - function_model is present and non-empty in the SSOT
  - cycle_model is present and non-empty in the SSOT
  - Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL
  - Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.ssot_required_sections

### RTL-0004: Gate: SSOT-authored rtl-gen workflow TODOs are well formed

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.workflow_todo_contract
- Detail: Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.
SSOT ref: quality_gates.rtl_gen.workflow_todo_contract.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: SSOT-authored rtl-gen workflow TODOs are well formed.
- Criteria:
  - Every workflow_todos.rtl-gen item has content
  - Every workflow_todos.rtl-gen item has detail
  - Every workflow_todos.rtl-gen item has at least one criteria entry
  - Traceability keeps source_ref quality_gates.rtl_gen.workflow_todo_contract
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.workflow_todo_contract

### RTL-0005: Gate: every SSOT-derived RTL behavior has an owner module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_traceability
- Detail: Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.
SSOT ref: quality_gates.rtl_gen.owner_traceability.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: Every required SSOT-derived RTL behavior has an owner module.
- Criteria:
  - No required function_model task is orphaned
  - No required cycle_model task is orphaned
  - No required register/dataflow/FSM task is orphaned
  - Owner module and owner file are recorded in rtl_todo_plan.json
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_traceability
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_traceability

### RTL-0016: Gate: SSOT connection contracts match RTL child port maps

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_connection_contract_evidence
- Detail: Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts.
SSOT ref: quality_gates.rtl_gen.manifest_connection_contract_evidence.
Owner: rv32i_min in rtl/rv32i_min.sv via top_fallback.
- Current reason: 8 SSOT connection contract issue(s) remain. rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_if: RTL named port-map expression does not match SSOT connection signal terms; rv32i_min_memwb: RTL named port-map expression does not match SSOT connection signal terms
- Criteria:
  - Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections
  - Each SSOT connection contract resolves to a reachable manifest child module and port
  - RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_connection_contract_evidence
  - Primary implementation evidence is in rtl/rv32i_min.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_connection_contract_evidence
