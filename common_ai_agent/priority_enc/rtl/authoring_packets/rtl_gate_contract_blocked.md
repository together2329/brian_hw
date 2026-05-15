# RTL Authoring Packet: rtl_gate_contract_blocked

- Kind: gate
- Owner module: priority_enc
- Owner file: rtl/priority_enc.sv
- Task count: 1
- Required tasks: 1

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 2
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=4
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 23 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - priority_enc_regs.PADDR <= PADDR (observed_named_port_map)
  - priority_enc_regs.PCLK <= PCLK (observed_named_port_map)
  - priority_enc_regs.PENABLE <= PENABLE (observed_named_port_map)
  - priority_enc_regs.PRDATA <= PRDATA (observed_named_port_map)
  - priority_enc_regs.PREADY <= PREADY (observed_named_port_map)
  - priority_enc_regs.PRESETn <= PRESETn (observed_named_port_map)
  - priority_enc_regs.PSEL <= PSEL (observed_named_port_map)
  - priority_enc_regs.PSLVERR <= PSLVERR (observed_named_port_map)
- Locked-truth blockers:
  - manifest_connection_contract_evidence: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
  - manifest_connection_contract_evidence: RTL audit has not run yet.
- SSOT top IO contracts: 13

## Tasks

### RTL-0016: Gate: SSOT connection contracts match RTL child port maps

- Priority: critical
- Required: True
- Status: planned
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_connection_contract_evidence
- Detail: Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts.
SSOT ref: quality_gates.rtl_gen.manifest_connection_contract_evidence.
Owner: priority_enc in rtl/priority_enc.sv via top_module.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections
  - Each SSOT connection contract resolves to a reachable manifest child module and port
  - RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_connection_contract_evidence
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_connection_contract_evidence
