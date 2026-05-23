# RTL Authoring Packet: module__fresh_rule_ip

- Kind: module
- Owner module: fresh_rule_ip
- Owner file: rtl/fresh_rule_ip.sv
- Task count: 22
- Required tasks: 22

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
- LLM-actionable open tasks: 22
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- SSOT top IO contracts: 8

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: planned
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via top_module.
- Current reason: RTL audit has not run yet.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: planned
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via top_module.
SSOT item context: value=fresh_rule_ip.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
- SSOT refs: io_list

### RTL-0028: Implement RTL state owner for FL state accepted_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_variable
- Source ref: function_model.state_variables.accepted_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.accepted_count.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: name=accepted_count; width=8; reset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.accepted_count
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - accepted_count width matches SSOT value 8
  - accepted_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.accepted_count

### RTL-0029: Implement transaction FM_PRIMARY

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PRIMARY
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PRIMARY.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: id=FM_PRIMARY; name=primary_behavior.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
- SSOT refs: function_model.transactions.FM_PRIMARY

### RTL-0030: Implement output for FM_PRIMARY: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PRIMARY.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.outputs.output_0.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["result"]; signal=["result", "value"]; state=["accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.outputs.output_0
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - DUT port ["result"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.outputs.output_0

### RTL-0031: Implement output rule for FM_PRIMARY: result

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PRIMARY.output_rules.result
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.output_rules.result.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: name=result; port=result; expr=value * 2; width=9.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.output_rules.result
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - result width matches SSOT value 9
  - result RTL expression implements SSOT expression value * 2
  - DUT port result is the implementation/observation point for result
  - result is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PRIMARY.output_rules.result

### RTL-0032: Implement state update for FM_PRIMARY: accepted_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PRIMARY.state_updates.accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.state_updates.accepted_count.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: name=accepted_count; expr=accepted_count + 1; width=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.state_updates.accepted_count
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - accepted_count width matches SSOT value 8
  - accepted_count RTL expression implements SSOT expression accepted_count + 1
  - accepted_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PRIMARY.state_updates.accepted_count

### RTL-0033: Implement side effect for FM_PRIMARY: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via function_model.
SSOT item context: id=FM_PRIMARY; name=primary_behavior; port=["result"]; signal=["accepted_count increments on each sampled transaction", "value"]; state=["accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PRIMARY.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - DUT port ["result"] is the implementation/observation point for primary_behavior
- SSOT refs: function_model.transactions.FM_PRIMARY.side_effects.side_effect_0

### RTL-0034: Implement cycle-model latency

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via cycle_model.
SSOT item context: value=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0035: Implement handshake rule: valid_sample

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.valid_sample
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.valid_sample.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via cycle_model.
SSOT item context: name=valid_sample.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.valid_sample
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - valid_sample appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.valid_sample

### RTL-0036: Implement feature double_value

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.double_value
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.double_value.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=double_value.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.double_value
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
- SSOT refs: features.double_value

### RTL-0037: Prove module fresh_rule_ip is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.fresh_rule_ip.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.fresh_rule_ip.module_equivalence.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.fresh_rule_ip.module_equivalence
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
- SSOT refs: sub_modules.fresh_rule_ip.module_equivalence

### RTL-0020: Implement and connect port clk

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.clock_domains.main.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.main.ports.clk.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.main.ports.clk
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.main.ports.clk

### RTL-0021: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0022: Implement and connect port valid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.valid.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=valid; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.valid
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - valid width matches SSOT value 1
  - valid port direction remains input
- SSOT refs: io_list.interfaces.rule_io.ports.valid

### RTL-0023: Implement and connect port data_in

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.data_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.data_in.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=data_in; width=8; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.data_in
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - data_in width matches SSOT value 8
  - data_in port direction remains input
- SSOT refs: io_list.interfaces.rule_io.ports.data_in

### RTL-0024: Implement and connect port result

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.result
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.result.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=result; width=9; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.result
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - result width matches SSOT value 9
  - result port direction remains output
- SSOT refs: io_list.interfaces.rule_io.ports.result

### RTL-0025: Implement and connect port ready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.ready.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=ready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.ready
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - ready width matches SSOT value 1
  - ready port direction remains output
- SSOT refs: io_list.interfaces.rule_io.ports.ready

### RTL-0026: Implement and connect port result_valid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.result_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.result_valid.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=result_valid; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.result_valid
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - result_valid width matches SSOT value 1
  - result_valid port direction remains output
- SSOT refs: io_list.interfaces.rule_io.ports.result_valid

### RTL-0027: Implement and connect port accepted_count

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.rule_io.ports.accepted_count
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.rule_io.ports.accepted_count.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: name=accepted_count; width=8; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.rule_io.ports.accepted_count
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - accepted_count width matches SSOT value 8
  - accepted_count port direction remains output
- SSOT refs: io_list.interfaces.rule_io.ports.accepted_count

### RTL-0038: Keep RTL observable for scenario SC_RULE_DOUBLE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_RULE_DOUBLE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_RULE_DOUBLE.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: id=SC_RULE_DOUBLE; name=double sampled input; expected=result equals FunctionalModel result and result_valid pulses.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_RULE_DOUBLE
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - Downstream checker compares RTL-observed behavior against expected result: result equals FunctionalModel result and result_valid pulses
- SSOT refs: test_requirements.scenarios.SC_RULE_DOUBLE

### RTL-0039: Provide RTL evidence for coverage bin FCOV_RULE_DOUBLE

- Priority: normal
- Required: True
- Status: planned
- Category: coverage.functional_bin
- Source ref: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
- Detail: Coverage can pass only when a scoreboard row with RTL-observed evidence hits this SSOT bin.
SSOT ref: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE.
Owner: fresh_rule_ip in rtl/fresh_rule_ip.sv via single_owner.
SSOT item context: id=FCOV_RULE_DOUBLE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Bin has a scoreboard coverage_refs entry
  - Scoreboard row includes concrete rtl_observed DUT signals
  - Coverage summary marks the bin hit from RTL-observed evidence, not raw model-only coverage
  - Traceability keeps source_ref test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
  - Primary implementation evidence is in rtl/fresh_rule_ip.sv
  - FCOV_RULE_DOUBLE can be hit only by scoreboard_events.jsonl with concrete rtl_observed DUT signals
- SSOT refs: test_requirements.coverage_goals.planned_bins.FCOV_RULE_DOUBLE
