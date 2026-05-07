# RTL Authoring Packet: rtl_gate_evidence_closure

- Kind: gate
- Owner module: atciic100_real
- Owner file: rtl/atciic100_real.sv
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
- Integration signoff allowed: True
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
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

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 50 static-evidence-required task(s) still lack DUT RTL evidence.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 5 owner logic structure issue(s) remain. atciic100_apbslv: Behavior-owner module is not declared in its owner file; atciic100_ctrl: Behavior-owner module is not declared in its owner file; atciic100_fifo: Behavior-owner module is not declared in its owner file
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder implementation markers

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 1 RTL placeholder marker(s) remain. None:None: None
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 1 top IO contract issue(s) remain. atciic100_real: SSOT top module is not declared in listed RTL sources
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 1 top output drive issue(s) remain. atciic100_real: SSOT top module is not declared, so output drive evidence cannot be checked
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 1 top input consumption issue(s) remain. atciic100_real: SSOT top module is not declared, so input consumption evidence cannot be checked
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 5 manifest hierarchy integration issue(s) remain. atciic100_real: SSOT top module is not declared in listed RTL sources; atciic100_apbslv: SSOT manifest child module is not declared in listed RTL sources; atciic100_ctrl: SSOT manifest child module is not declared in listed RTL sources
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: Every reachable manifest child instance has named, non-empty port connections.
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail: Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.
SSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 1 manifest signal-flow issue(s) remain. atciic100_real: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked
- Criteria:
  - Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance
  - Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts
  - Named port-map entries reference ports declared by the child module
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_signal_flow_evidence

### RTL-0022: Gate: production RTL has SSOT-scaled implementation depth

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_implementation_depth_evidence
- Detail: Production-profile RTL cannot be a shallow shell that merely satisfies names, ports, or compile checks. The RTL must contain aggregate implementation structure scaled from the current SSOT task count, behavior-owner modules, and manifest hierarchy.
SSOT ref: quality_gates.rtl_gen.rtl_implementation_depth_evidence.
Owner: atciic100_real in rtl/atciic100_real.sv via top_module.
- Current reason: 4 production RTL implementation-depth issue(s) remain. No listed DUT RTL sources are available for production implementation-depth audit; Production RTL implementation depth score is below the SSOT-derived or target-scale threshold: actual=0 required=92; Too few RTL modules contain implementation structure for the SSOT behavior complexity: actual=0 required=5
- Criteria:
  - Implementation depth thresholds are derived from SSOT owner/task complexity, not a fixed IP template
  - Listed DUT RTL sources contain enough nonconstant logic, procedural/state/control structure, and child instances for the SSOT profile
  - Production multi-module IPs distribute implementation depth across behavior-owner modules instead of hiding behavior in a wrapper shell
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_implementation_depth_evidence
  - Primary implementation evidence is in rtl/atciic100_real.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_implementation_depth_evidence
