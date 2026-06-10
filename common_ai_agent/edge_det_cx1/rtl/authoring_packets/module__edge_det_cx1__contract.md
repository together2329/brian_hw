# RTL Authoring Packet: module__edge_det_cx1__contract

- Kind: module
- Owner module: edge_det_cx1
- Owner file: rtl/edge_det_cx1.sv
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
- Owner refs: cycle_model, dataflow, decomposition, decomposition.units.edge_detect, decomposition.units.sync2ff, fsm, function_model, function_model.state_variables, function_model.state_variables.prev_sync, function_model.state_variables.sync1, function_model.state_variables.sync2, function_model.transactions, function_model.transactions.FM_FALL, function_model.transactions.FM_RISE, function_model.transactions.FM_STABLE, io_list
- Module slice: 2/12 section=contract task_limit=48
- Slice rule: Owner module edge_det_cx1 is split into 12 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0026: Implement locked behavioral contract BC_EDGE_SYNC

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_EDGE_SYNC
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_EDGE_SYNC.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: signal=["edge_det_cx1", "fall_out", "prev_sync", "rise_out", "sig_in", "sync1", "sync2"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_EDGE_SYNC remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_EDGE_SYNC
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_EDGE_SYNC, sub_modules[0]

### RTL-0027: Implement locked structural contract SC_EDGE_PORTS

- Priority: critical
- Required: True
- Status: pass
- Category: contract.structural.rtl
- Source ref: req.structural_contracts.SC_EDGE_PORTS
- Detail: This row is derived directly from req/structural_contracts.json. RTL top ports must satisfy the contract's signal names, direction, width, and timing ownership.
SSOT ref: req.structural_contracts.SC_EDGE_PORTS.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via single_owner.
SSOT item context: signal=["clk", "fall_out", "rise_out", "rst_n", "sig_in"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract SC_EDGE_PORTS remains traceable to req/structural_contracts.json
  - Every structural signal is declared on the RTL top or explicitly waived by locked truth
  - Direction and width are checked against the RTL top declaration
  - Active structural inputs/outputs participate in live RTL logic or explicit SSOT waiver
  - Traceability keeps source_ref req.structural_contracts.SC_EDGE_PORTS
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: io_list, req.structural_contracts.SC_EDGE_PORTS, top_module
