# RTL Authoring Packet: module__gray_code_cx1__contract

- Kind: module
- Owner module: gray_code_cx1
- Owner file: rtl/gray_code_cx1.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_PRIMARY, io_list, rtl_contract, test_requirements
- Module slice: 2/11 section=contract task_limit=48
- Slice rule: Owner module gray_code_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_code_cx1.clk <= clk (integration.connections[0])
  - gray_code_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0030: Implement locked behavioral contract BC_GC_DECODE

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_GC_DECODE
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_GC_DECODE.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via single_owner.
SSOT item context: signal=["bin_out", "gray_code_cx1", "gray_in", "gray_to_bin"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_GC_DECODE remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_GC_DECODE
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: features[1], function_model.transactions[0], function_model.transactions[0].output_rules[1], req.behavioral_contracts.BC_GC_DECODE

### RTL-0031: Implement locked behavioral contract BC_GC_ENCODE

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_GC_ENCODE
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_GC_ENCODE.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via single_owner.
SSOT item context: signal=["bin_in", "gray_code_cx1", "gray_out", "xF"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_GC_ENCODE remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_GC_ENCODE
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: features[0], function_model.transactions[0], function_model.transactions[0].output_rules[0], req.behavioral_contracts.BC_GC_ENCODE

### RTL-0032: Implement locked behavioral contract BC_GC_LINT

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_GC_LINT
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_GC_LINT.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via single_owner.
SSOT item context: signal=["bin_out", "gray_code_cx1", "gray_out"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_GC_LINT remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_GC_LINT
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: features[3], req.behavioral_contracts.BC_GC_LINT

### RTL-0033: Implement locked behavioral contract BC_GC_RESET

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_GC_RESET
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_GC_RESET.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via single_owner.
SSOT item context: signal=["bin_out", "gray_code_cx1", "gray_out"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_GC_RESET remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_GC_RESET
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: features[2], function_model.transactions[0], req.behavioral_contracts.BC_GC_RESET

### RTL-0034: Implement locked structural contract SC_GC_PORTS

- Priority: critical
- Required: True
- Status: pass
- Category: contract.structural.rtl
- Source ref: req.structural_contracts.SC_GC_PORTS
- Detail: This row is derived directly from req/structural_contracts.json. RTL top ports must satisfy the contract's signal names, direction, width, and timing ownership.
SSOT ref: req.structural_contracts.SC_GC_PORTS.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via single_owner.
SSOT item context: signal=["bin_in", "bin_out", "clk", "gray_in", "gray_out", "mode", "rst_n", "valid"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract SC_GC_PORTS remains traceable to req/structural_contracts.json
  - Every structural signal is declared on the RTL top or explicitly waived by locked truth
  - Direction and width are checked against the RTL top declaration
  - Active structural inputs/outputs participate in live RTL logic or explicit SSOT waiver
  - Traceability keeps source_ref req.structural_contracts.SC_GC_PORTS
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
- SSOT refs: io_list, req.structural_contracts.SC_GC_PORTS, top_module
