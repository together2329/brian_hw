# RTL Authoring Packet: module__debounce_cx1__contract

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 5
- Required tasks: 5

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 2/17 section=contract task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0027: Implement locked behavioral contract BC_DEB_BOUNCE

- Priority: critical
- Required: True
- Status: planned
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_DEB_BOUNCE
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_DEB_BOUNCE.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: signal=["btn_in", "db_out", "debounce_cx1", "fl_ctr", "fl_db", "fl_last"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - Contract BC_DEB_BOUNCE remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_DEB_BOUNCE
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_DEB_BOUNCE, rtl_contract

### RTL-0028: Implement locked behavioral contract BC_DEB_LINT

- Priority: critical
- Required: True
- Status: planned
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_DEB_LINT
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_DEB_LINT.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: signal=["db_out", "debounce_cx1", "fl_ctr", "fl_last"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - Contract BC_DEB_LINT remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_DEB_LINT
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_DEB_LINT, rtl_contract

### RTL-0029: Implement locked behavioral contract BC_DEB_RESET

- Priority: critical
- Required: True
- Status: planned
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_DEB_RESET
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_DEB_RESET.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: signal=["db_out", "debounce_cx1", "fl_ctr", "fl_db", "fl_last"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - Contract BC_DEB_RESET remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_DEB_RESET
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_DEB_RESET, rtl_contract

### RTL-0030: Implement locked behavioral contract BC_DEB_STABLE

- Priority: critical
- Required: True
- Status: planned
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_DEB_STABLE
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_DEB_STABLE.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: signal=["btn_in", "db_out", "debounce_cx1", "fl_ctr", "fl_db", "fl_last"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - Contract BC_DEB_STABLE remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_DEB_STABLE
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_DEB_STABLE, rtl_contract

### RTL-0031: Implement locked structural contract SC_DEB_PORTS

- Priority: critical
- Required: True
- Status: planned
- Category: contract.structural.rtl
- Source ref: req.structural_contracts.SC_DEB_PORTS
- Detail: This row is derived directly from req/structural_contracts.json. RTL top ports must satisfy the contract's signal names, direction, width, and timing ownership.
SSOT ref: req.structural_contracts.SC_DEB_PORTS.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: signal=["btn_in", "clk", "db_out", "rst_n"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - Contract SC_DEB_PORTS remains traceable to req/structural_contracts.json
  - Every structural signal is declared on the RTL top or explicitly waived by locked truth
  - Direction and width are checked against the RTL top declaration
  - Active structural inputs/outputs participate in live RTL logic or explicit SSOT waiver
  - Traceability keeps source_ref req.structural_contracts.SC_DEB_PORTS
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: io_list, req.structural_contracts.SC_DEB_PORTS, top_module
