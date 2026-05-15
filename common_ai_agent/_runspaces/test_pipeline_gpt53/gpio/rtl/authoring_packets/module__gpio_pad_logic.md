# RTL Authoring Packet: module__gpio_pad_logic

- Kind: module
- Owner module: gpio_pad_logic
- Owner file: rtl/gpio_pad_logic.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules.HR_COMB_OUTPUTS, function_model, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, io_list, io_list.interfaces.gpio_pad
- SSOT connection contracts:
  - gpio_pad_logic.dir_q <= dir_q (integration.connections[11])
  - gpio_pad_logic.dout_q <= dout_q (integration.connections[12])
  - gpio_pad_logic.oe_o <= oe_o (integration.connections[13])
  - gpio_pad_logic.pad_o <= pad_o (integration.connections[14])

## Tasks

### RTL-0022: Implement combinational pad drive logic

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Derive oe_o and pad_o directly from dir_q and dout_q
SSOT ref: workflow_todos.rtl-gen[2].
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via workflow_todos.owner.
SSOT item context: id=RTL_GPIO_PAD.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - oe_o equals dir_q bitwise
  - pad_o equals dout_q & dir_q
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - Semantic source_refs covered: cycle_model.handshake_rules.HR_COMB_OUTPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
- SSOT refs: cycle_model.handshake_rules.HR_COMB_OUTPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, workflow_todos.rtl-gen[2]

### RTL-0057: Implement transaction FM3_DRIVE_PAD_OUTPUTS

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: id=FM3_DRIVE_PAD_OUTPUTS; name=derive_output_enable_and_pad_drive.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS

### RTL-0058: Implement precondition for FM3_DRIVE_PAD_OUTPUTS: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.preconditions.precondition_0.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=dir_state and dout_state are defined.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.preconditions.precondition_0

### RTL-0059: Implement input for FM3_DRIVE_PAD_OUTPUTS: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_0.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=dir_state.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_0
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_0

### RTL-0060: Implement input for FM3_DRIVE_PAD_OUTPUTS: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_1.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=dout_state.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_1
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.inputs.input_1

### RTL-0061: Implement output for FM3_DRIVE_PAD_OUTPUTS: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_0.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=oe_o equals dir_state.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_0
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_0

### RTL-0062: Implement output for FM3_DRIVE_PAD_OUTPUTS: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_1.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=pad_o equals dout_state where dir_state is 1 else 0.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_1
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.outputs.output_1

### RTL-0063: Implement output rule for FM3_DRIVE_PAD_OUTPUTS: oe_comb

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.oe_comb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.oe_comb.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: name=oe_comb; port=oe_o; expr=dir_q; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.oe_comb
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - oe_comb width matches SSOT value WIDTH
  - oe_comb RTL expression implements SSOT expression dir_q
  - DUT port oe_o is the implementation/observation point for oe_comb
  - oe_comb is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.oe_comb

### RTL-0064: Implement output rule for FM3_DRIVE_PAD_OUTPUTS: pad_comb

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.pad_comb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.pad_comb.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: name=pad_comb; port=pad_o; expr=dout_q & dir_q; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.pad_comb
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - pad_comb width matches SSOT value WIDTH
  - pad_comb RTL expression implements SSOT expression dout_q & dir_q
  - DUT port pad_o is the implementation/observation point for pad_comb
  - pad_comb is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.output_rules.pad_comb

### RTL-0065: Implement side effect for FM3_DRIVE_PAD_OUTPUTS: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.side_effects.side_effect_0.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.
SSOT item context: value=no sequential state change.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: function_model.transactions.FM3_DRIVE_PAD_OUTPUTS.side_effects.side_effect_0

### RTL-0086: Implement handshake rule: HR_COMB_OUTPUTS

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.HR_COMB_OUTPUTS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.HR_COMB_OUTPUTS.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via cycle_model.handshake_rules.HR_COMB_OUTPUTS.
SSOT item context: id=HR_COMB_OUTPUTS; signal=oe_o/pad_o.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.HR_COMB_OUTPUTS
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - HR_COMB_OUTPUTS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.HR_COMB_OUTPUTS

### RTL-0134: Prove module gpio_pad_logic is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.gpio_pad_logic.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.gpio_pad_logic.module_equivalence.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.gpio_pad_logic.module_equivalence
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
- SSOT refs: sub_modules.gpio_pad_logic.module_equivalence

### RTL-0024: Implement and connect port clk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0025: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0026: Implement and connect port dir_in

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_ctrl.ports.dir_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_ctrl.ports.dir_in.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=dir_in; width=WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_ctrl.ports.dir_in
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - dir_in width matches SSOT value WIDTH
  - dir_in port direction remains input
- SSOT refs: io_list.interfaces.gpio_ctrl.ports.dir_in

### RTL-0027: Implement and connect port dout_in

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_ctrl.ports.dout_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_ctrl.ports.dout_in.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=dout_in; width=WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_ctrl.ports.dout_in
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - dout_in width matches SSOT value WIDTH
  - dout_in port direction remains input
- SSOT refs: io_list.interfaces.gpio_ctrl.ports.dout_in

### RTL-0028: Implement and connect port pad_in

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_pad.ports.pad_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_pad.ports.pad_in.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.interfaces.gpio_pad.
SSOT item context: name=pad_in; width=WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_pad.ports.pad_in
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - pad_in width matches SSOT value WIDTH
  - pad_in port direction remains input
- SSOT refs: io_list.interfaces.gpio_pad.ports.pad_in

### RTL-0029: Implement and connect port oe_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_pad.ports.oe_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_pad.ports.oe_o.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.interfaces.gpio_pad.
SSOT item context: name=oe_o; width=WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_pad.ports.oe_o
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - oe_o width matches SSOT value WIDTH
  - oe_o port direction remains output
- SSOT refs: io_list.interfaces.gpio_pad.ports.oe_o

### RTL-0030: Implement and connect port pad_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_pad.ports.pad_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_pad.ports.pad_o.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.interfaces.gpio_pad.
SSOT item context: name=pad_o; width=WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_pad.ports.pad_o
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - pad_o width matches SSOT value WIDTH
  - pad_o port direction remains output
- SSOT refs: io_list.interfaces.gpio_pad.ports.pad_o

### RTL-0031: Implement and connect port dir_q

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_state.ports.dir_q
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_state.ports.dir_q.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=dir_q; width=WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_state.ports.dir_q
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - dir_q width matches SSOT value WIDTH
  - dir_q port direction remains output
- SSOT refs: io_list.interfaces.gpio_state.ports.dir_q

### RTL-0032: Implement and connect port dout_q

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_state.ports.dout_q
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_state.ports.dout_q.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=dout_q; width=WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_state.ports.dout_q
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - dout_q width matches SSOT value WIDTH
  - dout_q port direction remains output
- SSOT refs: io_list.interfaces.gpio_state.ports.dout_q

### RTL-0033: Implement and connect port din_q

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.gpio_state.ports.din_q
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.gpio_state.ports.din_q.
Owner: gpio_pad_logic in rtl/gpio_pad_logic.sv via io_list.
SSOT item context: name=din_q; width=WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/gpio_pad_logic.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.gpio_state.ports.din_q
  - Primary implementation evidence is in rtl/gpio_pad_logic.sv
  - din_q width matches SSOT value WIDTH
  - din_q port direction remains output
- SSOT refs: io_list.interfaces.gpio_state.ports.din_q
