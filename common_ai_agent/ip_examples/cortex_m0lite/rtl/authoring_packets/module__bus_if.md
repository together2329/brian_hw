# RTL Authoring Packet: module__bus_if

- Kind: module
- Owner module: bus_if
- Owner file: rtl/cortex_m0lite_bus_if.sv
- Task count: 7
- Required tasks: 7

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

### RTL-0038: Implement parameter BUS_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BUS_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BUS_FREQ_MHZ.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via parameters.
SSOT item context: name=BUS_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BUS_FREQ_MHZ
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
- SSOT refs: parameters.BUS_FREQ_MHZ

### RTL-0046: Implement and connect port hclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.bus_clk.ports.hclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.bus_clk.ports.hclk.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via io_list.
SSOT item context: name=hclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.bus_clk.ports.hclk
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
  - hclk width matches SSOT value 1
  - hclk port direction remains input
- SSOT refs: io_list.clock_domains.bus_clk.ports.hclk

### RTL-0048: Implement and connect port hresetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.bus_rst_n.ports.hresetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.bus_rst_n.ports.hresetn.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via io_list.
SSOT item context: name=hresetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.bus_rst_n.ports.hresetn
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
  - hresetn width matches SSOT value 1
  - hresetn port direction remains input
- SSOT refs: io_list.resets.bus_rst_n.ports.hresetn

### RTL-0067: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.irq_if.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.irq_if.ports.irq.
Owner: bus_if in rtl/cortex_m0lite_bus_if.sv via io_list.interfaces.
SSOT item context: name=irq; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.irq_if.ports.irq
  - Primary implementation evidence is in rtl/cortex_m0lite_bus_if.sv
  - irq width matches SSOT value 1
  - irq port direction remains input
- SSOT refs: io_list.interfaces.irq_if.ports.irq
