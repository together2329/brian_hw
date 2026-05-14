# RTL Authoring Packet: module__regfile

- Kind: module
- Owner module: regfile
- Owner file: rtl/cortex_m0lite_regfile.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: function_model, function_model.state_variables, parameters, registers, registers.register_list
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - regfile.clk <= clk (integration.connections[5])
  - regfile.rst_n <= core_rst_n_sync (integration.connections[5])
  - regfile.wb_rf_we <= wb_rf_we (integration.connections[5])
  - regfile.wb_rf_waddr <= wb_rf_waddr (integration.connections[5])
  - regfile.wb_rf_wdata <= wb_rf_wdata (integration.connections[5])

## Tasks

### RTL-0072: Implement RTL state owner for FL state pc_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc_q.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via function_model.state_variables.
SSOT item context: name=pc_q; width=XLEN; reset=RESET_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc_q
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
  - pc_q width matches SSOT value XLEN
  - pc_q reset behavior matches SSOT value RESET_PC
- SSOT refs: function_model.state_variables.pc_q

### RTL-0073: Implement RTL state owner for FL state rf_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.rf_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.rf_q.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via function_model.state_variables.
SSOT item context: name=rf_q; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.rf_q
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
  - rf_q width matches SSOT value 32
  - rf_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.rf_q

### RTL-0074: Implement RTL state owner for FL state nzcv_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.nzcv_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.nzcv_q.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via function_model.state_variables.
SSOT item context: name=nzcv_q; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.nzcv_q
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
  - nzcv_q width matches SSOT value 4
  - nzcv_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.nzcv_q

### RTL-0075: Implement RTL state owner for FL state trap_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.trap_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.trap_q.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via function_model.state_variables.
SSOT item context: name=trap_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.trap_q
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
  - trap_q width matches SSOT value 1
  - trap_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.trap_q

### RTL-0129: Implement memory item regfile_storage

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.regfile_storage
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.regfile_storage.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via semantic_terms:regfile.
SSOT item context: name=regfile_storage; width=XLEN; depth=REG_COUNT; reset=implementation_defined_zero_or_retained_by_architectural_rule.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.regfile_storage
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
  - regfile_storage width matches SSOT value XLEN
  - regfile_storage reset behavior matches SSOT value implementation_defined_zero_or_retained_by_architectural_rule
  - regfile_storage storage depth matches SSOT value REG_COUNT
- SSOT refs: memory.instances.regfile_storage

### RTL-0182: Prove module regfile is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.regfile.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.regfile.module_equivalence.
Owner: regfile in rtl/cortex_m0lite_regfile.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.regfile.module_equivalence
  - Primary implementation evidence is in rtl/cortex_m0lite_regfile.sv
- SSOT refs: sub_modules.regfile.module_equivalence
