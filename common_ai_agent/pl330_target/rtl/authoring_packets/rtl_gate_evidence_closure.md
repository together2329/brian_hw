# RTL Authoring Packet: rtl_gate_evidence_closure

- Kind: gate
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 10
- Required tasks: 10

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
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_engine.busy <= engine_busy (observed_named_port_map)
  - pl330_target_engine.channel_state <= engine_channel_state (observed_named_port_map)
  - pl330_target_engine.clk <= clk (observed_named_port_map)
  - pl330_target_engine.cmd_channel <= engine_cmd_channel (observed_named_port_map)
  - pl330_target_engine.cmd_dst_addr <= engine_cmd_dst_addr (observed_named_port_map)
  - pl330_target_engine.cmd_len <= engine_cmd_len (observed_named_port_map)
  - pl330_target_engine.cmd_opcode <= engine_cmd_opcode (observed_named_port_map)
  - pl330_target_engine.cmd_privileged <= engine_cmd_privileged (observed_named_port_map)
- SSOT top IO contracts: 11

## Tasks

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Static DUT RTL evidence audit has no missing required task.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Behavior-owner RTL modules contain real implementation structure.
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder implementation markers

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: RTL sources contain no placeholder implementation markers.
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top IO contracts match the RTL top declaration.
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top outputs have non-placeholder RTL drive evidence.
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top inputs have RTL consumption evidence.
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Every SSOT manifest-owned child module is declared and reachable from the top RTL hierarchy.
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Every reachable manifest child instance has named, non-empty port connections.
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail: Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.
SSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Manifest child port maps carry live non-placeholder RTL signal flow.
- Criteria:
  - Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance
  - Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts
  - Named port-map entries reference ports declared by the child module
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_signal_flow_evidence

### RTL-0022: Gate: production RTL has SSOT-scaled implementation depth

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_implementation_depth_evidence
- Detail: Production-profile RTL cannot be a shallow shell that merely satisfies names, ports, or compile checks. The RTL must contain aggregate implementation structure scaled from the current SSOT task count, behavior-owner modules, and manifest hierarchy.
SSOT ref: quality_gates.rtl_gen.rtl_implementation_depth_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Production RTL implementation depth meets SSOT-derived/target-scale thresholds (score=2984, required=83).
- Criteria:
  - Implementation depth thresholds are derived from SSOT owner/task complexity, not a fixed IP template
  - Listed DUT RTL sources contain enough nonconstant logic, procedural/state/control structure, and child instances for the SSOT profile
  - Production multi-module IPs distribute implementation depth across behavior-owner modules instead of hiding behavior in a wrapper shell
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_implementation_depth_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_implementation_depth_evidence
