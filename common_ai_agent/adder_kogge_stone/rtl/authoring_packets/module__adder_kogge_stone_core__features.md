# RTL Authoring Packet: module__adder_kogge_stone_core__features

- Kind: module
- Owner module: adder_kogge_stone_core
- Owner file: rtl/adder_kogge_stone_core.sv
- Task count: 2
- Required tasks: 2

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
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, decomposition.units.ks_datapath, features, features.ks_addition, fsm, fsm.adder_fsm, function_model, function_model.state_updates, function_model.transactions, function_model.transactions.FM_ADD
- Module slice: 4/6 section=features task_limit=48
- Slice rule: Owner module adder_kogge_stone_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0120: Implement feature ks_addition

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.ks_addition
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.ks_addition.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via features.ks_addition.
SSOT item context: name=ks_addition; output=Registered sum_o[DATA_WIDTH-1:0] and cout_o on the cycle following start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.ks_addition
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: features.ks_addition

### RTL-0121: Implement feature apb_lite_csr

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.apb_lite_csr
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.apb_lite_csr.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via features.
SSOT item context: name=apb_lite_csr; output=prdata[31:0], pready, pslverr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.apb_lite_csr
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: features.apb_lite_csr
