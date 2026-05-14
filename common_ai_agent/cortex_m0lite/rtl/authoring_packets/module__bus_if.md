# RTL Authoring Packet: module__bus_if

- Kind: module
- Owner module: bus_if
- Owner file: rtl/cortex_m0lite_bus_if.sv
- Task count: 3
- Required tasks: 3

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: cycle_model, error_handling, io_list, io_list.interfaces, parameters
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - bus_if.hclk <= hclk (integration.connections[6])
  - bus_if.hresetn <= bus_rst_n_sync (integration.connections[6])
  - bus_if.if_bus_req <= if_bus_req (integration.connections[6])
  - bus_if.ex_bus_req <= ex_bus_req (integration.connections[6])
  - bus_if.i_haddr <= i_haddr (integration.connections[6])
  - bus_if.d_haddr <= d_haddr (integration.connections[6])

## Tasks

### RTL-0157: Implement security item bus_integrity

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.bus_integrity
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.bus_integrity.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via semantic_terms:bus.
SSOT item context: name=bus_integrity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.bus_integrity
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
- SSOT refs: security.assets.bus_integrity

### RTL-0174: Implement synthesis item bus_frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.bus_frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.bus_frequency_mhz_min.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via semantic_terms:bus.
SSOT item context: name=bus_frequency_mhz_min; value=150.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.bus_frequency_mhz_min
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
- SSOT refs: synthesis.ppa_targets.bus_frequency_mhz_min

### RTL-0183: Prove module bus_if is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.bus_if.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.bus_if.module_equivalence.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.bus_if.module_equivalence
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
- SSOT refs: sub_modules.bus_if.module_equivalence
