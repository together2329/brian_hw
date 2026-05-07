# RTL Authoring Packet: rtl_gate_human_closure

- Kind: gate
- Owner module: atciic100_real
- Owner file: rtl/atciic100_real.sv
- Task count: 7
- Required tasks: 7

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: False
- Evidence closure allowed: True
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 2
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Locked-truth blockers:
  - manifest_connection_contract_evidence: 9 SSOT connection contract issue(s) remain. atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_fifo: SSOT connection contract targets a module not declared in RTL
  - golden_authority_artifacts: model_signature.json drift at ssot_hash: expected current SSOT-derived value.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_fifo.data_in <= pwdata (sub_modules[0].connections[2])
  - atciic100_apbslv.cmd_reg <= cmd (sub_modules[1].connections[0])
  - atciic100_fifo.data_out <= tx_data (sub_modules[1].connections[1])
  - atciic100_gsf.scl_in <= scl_filtered (sub_modules[1].connections[2])
  - atciic100_apbslv.data_in <= pwdata (sub_modules[2].connections[0])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])
- SSOT top IO contracts: 15

## Tasks

### RTL-0003: Gate: SSOT function_model and cycle_model are present before RTL generation

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.ssot_required_sections
- Detail: rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.
SSOT ref: quality_gates.rtl_gen.ssot_required_sections.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: SSOT function_model and cycle_model authority is present.
- Criteria:
  - function_model is present and non-empty in the SSOT
  - cycle_model is present and non-empty in the SSOT
  - Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL
  - Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.ssot_required_sections

### RTL-0004: Gate: SSOT-authored rtl-gen workflow TODOs are well formed

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.workflow_todo_contract
- Detail: Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.
SSOT ref: quality_gates.rtl_gen.workflow_todo_contract.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: SSOT-authored rtl-gen workflow TODOs are well formed.
- Criteria:
  - Every workflow_todos.rtl-gen item has content
  - Every workflow_todos.rtl-gen item has detail
  - Every workflow_todos.rtl-gen item has at least one criteria entry
  - Traceability keeps source_ref quality_gates.rtl_gen.workflow_todo_contract
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.workflow_todo_contract

### RTL-0005: Gate: every SSOT-derived RTL behavior has an owner module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_traceability
- Detail: Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.
SSOT ref: quality_gates.rtl_gen.owner_traceability.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: Every required SSOT-derived RTL behavior has an owner module.
- Criteria:
  - No required function_model task is orphaned
  - No required cycle_model task is orphaned
  - No required register/dataflow/FSM task is orphaned
  - Owner module and owner file are recorded in rtl_todo_plan.json
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_traceability
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_traceability

### RTL-0016: Gate: SSOT connection contracts match RTL child port maps

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_connection_contract_evidence
- Detail: Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts.
SSOT ref: quality_gates.rtl_gen.manifest_connection_contract_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 9 SSOT connection contract issue(s) remain. atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_fifo: SSOT connection contract targets a module not declared in RTL
- Criteria:
  - Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections
  - Each SSOT connection contract resolves to a reachable manifest child module and port
  - RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_connection_contract_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_connection_contract_evidence

### RTL-0020: Gate: production RTL uses locked SSOT/FL/coverage authority artifacts

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.golden_authority_artifacts
- Detail: PL330-level RTL cannot proceed from prose alone. It must carry machine-readable authority artifacts that separate human-owned truth from LLM-editable implementation.
SSOT ref: quality_gates.rtl_gen.golden_authority_artifacts.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: model_signature.json drift at ssot_hash: expected current SSOT-derived value.
- Criteria:
  - governance/authority.json exists
  - authority.json is the current IP human_llm_authority_manifest
  - authority operating rules R1..R6 and LLM loops L1..L9 are present
  - human authority gates G1..G7 are approved before production RTL-GEN
  - repo_layout separates locked SSOT/model/coverage truth from LLM-editable rtl/tb/sim/report work
  - model/functional_model.py exists
  - model/fl_model_check.json passed=true
  - model/model_signature.json matches the current SSOT-derived golden model signature
  - model/decomposition.json complete=true with unblocked implementation units
  - cov/fcov_plan.json has planned bins before RTL signoff
  - verify/equivalence_goals.json has required, unblocked goals
  - Traceability keeps source_ref quality_gates.rtl_gen.golden_authority_artifacts
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.golden_authority_artifacts

### RTL-0021: Gate: production RTL scale target is locked or explicitly waived

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.target_scale
- Detail: When a calibration reference profile provides target-scale candidates, a human must lock the chosen minimum structural scale in SSOT quality_gates.rtl_gen.target_scale or record an explicit SSOT target_scale_waiver before rtl-gen can claim production signoff.
SSOT ref: quality_gates.rtl_gen.target_scale.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: No reference-derived target scale candidate is present, so no target-scale policy lock is required.
- Criteria:
  - Reference-derived suggested_ssot_target_scale candidates are review inputs only
  - SSOT quality_gates.rtl_gen.target_scale contains human-locked structural depth minima before PL330-level PASS claims
  - If target scale is intentionally not enforced, SSOT contains target_scale_waiver.approved=true with a rationale
  - Traceability keeps source_ref quality_gates.rtl_gen.target_scale
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.target_scale

### RTL-0023: Gate: production RTL has executable cycle/handshake model evidence

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.cycle_model_artifacts
- Detail: Complex DMA-class RTL needs a cycle-level oracle for latency, handshake, ordering, backpressure, and performance-sensitive behavior.
SSOT ref: quality_gates.rtl_gen.cycle_model_artifacts.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: Cycle model artifact and self-check are present.
- Criteria:
  - model/cycle_model.py exists
  - model/cl_model_check.json passed=true
  - cycle_model evidence traces to SSOT cycle_model
  - Traceability keeps source_ref quality_gates.rtl_gen.cycle_model_artifacts
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.cycle_model_artifacts
