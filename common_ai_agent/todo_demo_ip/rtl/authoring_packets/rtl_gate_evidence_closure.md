# RTL Authoring Packet: rtl_gate_evidence_closure

- Kind: gate
- Owner module: todo_demo_ip
- Owner file: rtl/todo_demo_ip.sv
- Task count: 9
- Required tasks: 9

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model

## Tasks

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: Static DUT RTL evidence audit has no missing required task.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: 1 owner logic structure issue(s) remain. todo_demo_ip: Behavior-owner module has no nonconstant assign, procedural block, state update, or child instance
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder markers or disallowed generated-RTL constructs

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. Generated RTL uses the project SystemVerilog subset: ANSI ports default to input/output logic, with no package/import/interface/modport, no function/task, no for/while, and no typedef/enum/always_ff/always_comb. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: 2 RTL placeholder/policy issue(s) remain. rtl/todo_demo_ip.sv:2: TODO (RTL source contains a placeholder implementation marker); rtl/todo_demo_ip.sv:7: TBD (RTL source contains a placeholder implementation marker)
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text
  - Listed RTL source files and rtl/<ip>_param.vh contain no banned package/function/task/loop constructs
  - Default generated RTL uses input/output logic ports and portable always @ syntax
  - FSMs use the conventional explicit style by default, unless SSOT/user specifies another synthesizable style
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: SSOT top IO contracts match the RTL top declaration.
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: SSOT top outputs have non-placeholder RTL drive evidence.
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: SSOT top inputs have RTL consumption evidence.
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: Every SSOT manifest-owned child module is declared and reachable from the top RTL hierarchy.
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: Every reachable manifest child instance has named, non-empty port connections.
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail: Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.
SSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.
Owner: todo_demo_ip in rtl/todo_demo_ip.sv via top_module.
- Current reason: Manifest child port maps carry live non-placeholder RTL signal flow.
- Criteria:
  - Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance
  - Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts
  - Named port-map entries reference ports declared by the child module
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence
  - Primary implementation evidence is in rtl/todo_demo_ip.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_signal_flow_evidence
