# RTL Authoring Packet: module__fifo_sync_cx1__contract

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 2/11 section=contract task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0030: Implement locked behavioral contract BC_FIFO_FLAGS

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_FIFO_FLAGS
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_FIFO_FLAGS.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: signal=["count", "empty", "fifo_sync_cx1", "full"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_FIFO_FLAGS remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_FIFO_FLAGS
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: cycle_model.pipeline[0], cycle_model.pipeline[1], cycle_model.pipeline[2], features[2], features[3], function_model.transactions[0], function_model.transactions[0].output_rules[0], function_model.transactions[0].output_rules[1], function_model.transactions[1], function_model.transactions[1].output_rules[1], function_model.transactions[1].output_rules[2], req.behavioral_contracts.BC_FIFO_FLAGS

### RTL-0031: Implement locked behavioral contract BC_FIFO_LINT

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_FIFO_LINT
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_FIFO_LINT.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: signal=["fifo_memory", "fifo_sync_cx1", "rd_ptr", "wr_ptr"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_FIFO_LINT remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_FIFO_LINT
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: features[5], function_model.rules[0], req.behavioral_contracts.BC_FIFO_LINT

### RTL-0032: Implement locked behavioral contract BC_FIFO_READ

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_FIFO_READ
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_FIFO_READ.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: signal=["count", "empty", "fifo_sync_cx1", "head_data", "rd_data", "rd_ptr"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_FIFO_READ remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_FIFO_READ
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: cycle_model.handshake_rules[1], cycle_model.pipeline[1], features[1], function_model.transactions[1], function_model.transactions[1].output_rules[0], req.behavioral_contracts.BC_FIFO_READ

### RTL-0033: Implement locked behavioral contract BC_FIFO_RESET

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_FIFO_RESET
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_FIFO_RESET.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: signal=["count", "empty", "fifo_sync_cx1", "full", "rd_ptr", "wr_ptr"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_FIFO_RESET remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_FIFO_RESET
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: cycle_model.handshake_rules[2], features[4], function_model.reset, req.behavioral_contracts.BC_FIFO_RESET

### RTL-0034: Implement locked behavioral contract BC_FIFO_WRITE

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_FIFO_WRITE
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_FIFO_WRITE.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via cycle_model.
SSOT item context: signal=["count", "empty", "fifo_sync_cx1", "full", "wr_ptr"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_FIFO_WRITE remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_FIFO_WRITE
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: cycle_model.handshake_rules[0], cycle_model.pipeline[0], features[0], function_model.transactions[0], req.behavioral_contracts.BC_FIFO_WRITE

### RTL-0035: Implement locked structural contract SC_FIFO_PORTS

- Priority: critical
- Required: True
- Status: pass
- Category: contract.structural.rtl
- Source ref: req.structural_contracts.SC_FIFO_PORTS
- Detail: This row is derived directly from req/structural_contracts.json. RTL top ports must satisfy the contract's signal names, direction, width, and timing ownership.
SSOT ref: req.structural_contracts.SC_FIFO_PORTS.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via single_owner.
SSOT item context: signal=["clk", "empty", "full", "rd_data", "rd_en", "rst_n", "wr_data", "wr_en"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract SC_FIFO_PORTS remains traceable to req/structural_contracts.json
  - Every structural signal is declared on the RTL top or explicitly waived by locked truth
  - Direction and width are checked against the RTL top declaration
  - Active structural inputs/outputs participate in live RTL logic or explicit SSOT waiver
  - Traceability keeps source_ref req.structural_contracts.SC_FIFO_PORTS
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
- SSOT refs: io_list, req.structural_contracts.SC_FIFO_PORTS, top_module
