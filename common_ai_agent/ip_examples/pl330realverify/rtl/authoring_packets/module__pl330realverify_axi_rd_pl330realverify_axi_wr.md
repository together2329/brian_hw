# RTL Authoring Packet: module__pl330realverify_axi_rd_pl330realverify_axi_wr

- Kind: module
- Owner module: pl330realverify_axi_rd/pl330realverify_axi_wr
- Owner file: rtl/pl330realverify_axi_rd.sv, rtl/pl330realverify_axi_wr.sv
- Task count: 1
- Required tasks: 1

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20

## Tasks

### RTL-0030: Implement AXI read/write single-outstanding protocol adapters

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Implement pl330realverify_axi_rd and pl330realverify_axi_wr with stable payload hold-until-ready behavior, response classification, single-outstanding policy, and ready/valid timing from cycle_model.handshake_rules.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: pl330realverify_axi_rd/pl330realverify_axi_wr in rtl/pl330realverify_axi_rd.sv, rtl/pl330realverify_axi_wr.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_AXI_ADAPTERS.
- Current reason: Owner RTL file is missing: rtl/pl330realverify_axi_rd.sv, rtl/pl330realverify_axi_wr.sv.
- Criteria:
  - AR/AW/W payloads remain stable while valid is asserted and ready is low
  - R data captures only on rvalid and rready with rresp OKAY
  - B response consumes only on bvalid and bready
  - Non-OKAY rresp and bresp produce the declared ERR_AXI_RD/ERR_AXI_WR fault indications
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv, rtl/pl330realverify_axi_wr.sv
  - Semantic source_refs covered: cycle_model.handshake_rules.AXI_AR, cycle_model.handshake_rules.AXI_AW, cycle_model.handshake_rules.AXI_B, cycle_model.handshake_rules.AXI_R, cycle_model.handshake_rules.AXI_W, error_handling.error_sources, io_list.interfaces.axi_rd_master, io_list.interfaces.axi_wr_master
- SSOT refs: cycle_model.handshake_rules.AXI_AR, cycle_model.handshake_rules.AXI_AW, cycle_model.handshake_rules.AXI_B, cycle_model.handshake_rules.AXI_R, cycle_model.handshake_rules.AXI_W, error_handling.error_sources, io_list.interfaces.axi_rd_master, io_list.interfaces.axi_wr_master, workflow_todos.rtl-gen[3]
