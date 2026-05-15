# RTL Authoring Packet: module__priority_enc

- Kind: module
- Owner module: priority_enc
- Owner file: rtl/priority_enc.sv
- Task count: 39
- Required tasks: 39

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=4
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 21 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - priority_enc_regs.PADDR <= PADDR (observed_named_port_map)
  - priority_enc_regs.PCLK <= PCLK (observed_named_port_map)
  - priority_enc_regs.PENABLE <= PENABLE (observed_named_port_map)
  - priority_enc_regs.PRDATA <= PRDATA (observed_named_port_map)
  - priority_enc_regs.PREADY <= PREADY (observed_named_port_map)
  - priority_enc_regs.PRESETn <= PRESETn (observed_named_port_map)
  - priority_enc_regs.PSEL <= PSEL (observed_named_port_map)
  - priority_enc_regs.PSLVERR <= PSLVERR (observed_named_port_map)
- SSOT top IO contracts: 13

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: priority_enc in rtl/priority_enc.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: priority_enc in rtl/priority_enc.sv via top_module.
SSOT item context: value=priority_enc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: io_list

### RTL-0029: Implement top-level wrapper

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Instantiate priority_enc_regs and priority_enc_core; connect APB ports to regs, data_in to core, core outputs to top ports and STATUS register feedback.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: priority_enc in rtl/priority_enc.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top-level connects all submodules per integration spec
  - Lint clean
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Semantic source_refs covered: integration, sub_modules
- SSOT refs: integration, sub_modules, workflow_todos.rtl-gen[2]

### RTL-0088: Implement feature Priority Encoding

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Priority_Encoding
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Priority_Encoding.
Owner: priority_enc in rtl/priority_enc.sv via features.
SSOT item context: name=Priority Encoding; output=index_out (encoded index) and valid_out (any bit set).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Priority_Encoding
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: features.Priority_Encoding

### RTL-0089: Implement feature Runtime Masking

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Runtime_Masking
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Runtime_Masking.
Owner: priority_enc in rtl/priority_enc.sv via features.
SSOT item context: name=Runtime Masking; output=Masked inputs ignored in priority computation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Runtime_Masking
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: features.Runtime_Masking

### RTL-0090: Implement feature Enable Gating

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Enable_Gating
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Enable_Gating.
Owner: priority_enc in rtl/priority_enc.sv via features.
SSOT item context: name=Enable Gating; output=When disabled, index_out=0 and valid_out=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Enable_Gating
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: features.Enable_Gating

### RTL-0091: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: priority_enc in rtl/priority_enc.sv via error_handling.
SSOT item context: value=Software retry with corrected address..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0092: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: priority_enc in rtl/priority_enc.sv via security.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: security.assets.asset_0

### RTL-0093: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: value=PCLK period 20ns.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0094: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: value=Input delay 2ns.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0095: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: value=Output delay 3ns.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0096: Implement synthesis item area_um2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: name=area_um2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.ppa_targets.area_um2

### RTL-0097: Implement synthesis item power_mw

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: name=power_mw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.ppa_targets.power_mw

### RTL-0098: Implement synthesis item timing_met

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.timing_met
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.timing_met.
Owner: priority_enc in rtl/priority_enc.sv via synthesis.
SSOT item context: name=timing_met; value=True.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.timing_met
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: synthesis.ppa_targets.timing_met

### RTL-0101: Prove module priority_enc is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.priority_enc.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.priority_enc.module_equivalence.
Owner: priority_enc in rtl/priority_enc.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.priority_enc.module_equivalence
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: sub_modules.priority_enc.module_equivalence

### RTL-0030: Implement parameter N

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.N
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.N.
Owner: priority_enc in rtl/priority_enc.sv via parameters.
SSOT item context: name=N.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.N
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: parameters.N

### RTL-0031: Implement parameter INDEX_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.INDEX_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.INDEX_WIDTH.
Owner: priority_enc in rtl/priority_enc.sv via parameters.
SSOT item context: name=INDEX_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.INDEX_WIDTH
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: parameters.INDEX_WIDTH

### RTL-0032: Implement parameter PCLK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.PCLK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PCLK_FREQ_MHZ.
Owner: priority_enc in rtl/priority_enc.sv via parameters.
SSOT item context: name=PCLK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PCLK_FREQ_MHZ
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: parameters.PCLK_FREQ_MHZ

### RTL-0033: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: priority_enc in rtl/priority_enc.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/priority_enc.sv
- SSOT refs: parameters.RESET_POLARITY

### RTL-0034: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0035: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0036: Implement and connect port data_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.priority_inputs.ports.data_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.priority_inputs.ports.data_in.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=data_in; width=N; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.priority_inputs.ports.data_in
  - Primary implementation evidence is in rtl/priority_enc.sv
  - data_in width matches SSOT value N
  - data_in port direction remains input
- SSOT refs: io_list.interfaces.priority_inputs.ports.data_in

### RTL-0037: Implement and connect port index_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.priority_outputs.ports.index_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.priority_outputs.ports.index_out.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=index_out; width=INDEX_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.priority_outputs.ports.index_out
  - Primary implementation evidence is in rtl/priority_enc.sv
  - index_out width matches SSOT value INDEX_WIDTH
  - index_out port direction remains output
- SSOT refs: io_list.interfaces.priority_outputs.ports.index_out

### RTL-0038: Implement and connect port valid_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.priority_outputs.ports.valid_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.priority_outputs.ports.valid_out.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=valid_out; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.priority_outputs.ports.valid_out
  - Primary implementation evidence is in rtl/priority_enc.sv
  - valid_out width matches SSOT value 1
  - valid_out port direction remains output
- SSOT refs: io_list.interfaces.priority_outputs.ports.valid_out

### RTL-0039: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PADDR.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PADDR; width=12; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PADDR
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PADDR width matches SSOT value 12
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PADDR

### RTL-0040: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PSEL.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PSEL
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PSEL

### RTL-0041: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PENABLE.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PENABLE
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PENABLE

### RTL-0042: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PWRITE.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PWRITE
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PWRITE

### RTL-0043: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PWDATA.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PWDATA
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PWDATA width matches SSOT value 32
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PWDATA

### RTL-0044: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PRDATA.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PRDATA
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PRDATA width matches SSOT value 32
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PRDATA

### RTL-0045: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PREADY.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PREADY
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PREADY

### RTL-0046: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PSLVERR.
Owner: priority_enc in rtl/priority_enc.sv via io_list.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PSLVERR
  - Primary implementation evidence is in rtl/priority_enc.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PSLVERR

### RTL-0102: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC1; name=Basic priority encode; expected=index_out = bit position, valid_out = 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: index_out = bit position, valid_out = 1
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0103: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC2; name=Multiple inputs priority resolution; expected=index_out reflects highest-numbered asserted bit.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: index_out reflects highest-numbered asserted bit
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0104: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC3; name=Mask functionality; expected=Masked bits ignored in index_out/valid_out computation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: Masked bits ignored in index_out/valid_out computation
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0105: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC4; name=Enable gating; expected=index_out=0, valid_out=0 regardless of inputs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: index_out=0, valid_out=0 regardless of inputs
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0106: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC5; name=APB CSR read/write; expected=Register values match writes; STATUS reflects current core output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: Register values match writes; STATUS reflects current core output
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0107: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC6; name=Reset behavior; expected=CTRL=0x1, MASK=0x0, STATUS=0x0, index_out=0, valid_out=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: CTRL=0x1, MASK=0x0, STATUS=0x0, index_out=0, valid_out=0
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0108: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: priority_enc in rtl/priority_enc.sv via test_requirements.
SSOT item context: id=SC7; name=APB bad address; expected=PSLVERR=1, PRDATA=0, no register state change.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/priority_enc.sv
  - Downstream checker compares RTL-observed behavior against expected result: PSLVERR=1, PRDATA=0, no register state change
- SSOT refs: test_requirements.scenarios.SC7
