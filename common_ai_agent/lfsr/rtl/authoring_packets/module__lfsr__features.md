# RTL Authoring Packet: module__lfsr__features

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
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
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 9/13 section=features task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0105: Implement feature PRBS Generation

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.PRBS_Generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.PRBS_Generation.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PRBS Generation; output=prbs_out (parallel LFSR_WIDTH word), prbs_bit (serial LSB).
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.PRBS_Generation
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: features.PRBS_Generation

### RTL-0106: Implement feature Polynomial Programming

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Polynomial_Programming
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Polynomial_Programming.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=Polynomial Programming; output=Updated polynomial drives XOR tap mask in LFSR feedback.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Polynomial_Programming
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: features.Polynomial_Programming

### RTL-0107: Implement feature Seed Loading

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Seed_Loading
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Seed_Loading.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=Seed Loading; output=LFSR state reinitialized; prbs_valid deasserted until next cycle.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Seed_Loading
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: features.Seed_Loading

### RTL-0108: Implement feature Lock-up Detection

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Lock_up_Detection
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Lock_up_Detection.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=Lock-up Detection; output=prbs_valid deasserted; STATUS.lockup flagged.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Lock_up_Detection
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: features.Lock_up_Detection
