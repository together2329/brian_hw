# RTL Authoring Packet: module__generic_counter_ip

- Kind: module
- Owner module: generic_counter_ip
- Owner file: rtl/generic_counter_ip.sv
- Task count: 11
- Required tasks: 11

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- SSOT top IO contracts: 4

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via top_module.
SSOT item context: value=generic_counter_ip.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: io_list

### RTL-0024: Implement transaction FM_PRIMARY

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PRIMARY
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PRIMARY.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via function_model.
SSOT item context: id=FM_PRIMARY; name=primary_behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: function_model.transactions.FM_PRIMARY

### RTL-0025: Implement output for FM_PRIMARY: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_0.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via function_model.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; signal=["value"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_0
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_0

### RTL-0026: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via cycle_model.
SSOT item context: value=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0027: Implement feature double_value

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.double_value
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.double_value.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via single_owner.
SSOT item context: name=double_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.double_value
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: features.double_value

### RTL-0028: Prove module generic_counter_ip is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.generic_counter_ip.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.generic_counter_ip.module_equivalence.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.generic_counter_ip.module_equivalence
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
- SSOT refs: sub_modules.generic_counter_ip.module_equivalence

### RTL-0020: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.main.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.main.ports.clk.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via single_owner.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.main.ports.clk
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.main.ports.clk

### RTL-0021: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via single_owner.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0022: Implement and connect port data_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.data_in.ports.data_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.data_in.ports.data_in.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via single_owner.
SSOT item context: name=data_in; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.data_in.ports.data_in
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
  - data_in width matches SSOT value 8
  - data_in port direction remains input
- SSOT refs: io_list.interfaces.data_in.ports.data_in

### RTL-0023: Implement and connect port value

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.result_out.ports.value
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.result_out.ports.value.
Owner: generic_counter_ip in rtl/generic_counter_ip.sv via single_owner.
SSOT item context: name=value; width=9; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.result_out.ports.value
  - Primary implementation evidence is in rtl/generic_counter_ip.sv
  - value width matches SSOT value 9
  - value port direction remains output
- SSOT refs: io_list.interfaces.result_out.ports.value
