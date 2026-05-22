# RTL Authoring Packet: module__arm_m0_min_if

- Kind: module
- Owner module: arm_m0_min_if
- Owner file: rtl/arm_m0_min_if.sv
- Task count: 23
- Required tasks: 23

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, io_list, io_list.interfaces.ahb_i_master, timing, timing.fetch_path
- SSOT connection contracts:
  - arm_m0_min_if.i_haddr <= i_haddr (integration.connections[0])
  - arm_m0_min_if.i_htrans <= i_htrans (integration.connections[1])
  - arm_m0_min_if.i_hready <= i_hready (integration.connections[2])
  - arm_m0_min_if.i_hrdata <= i_hrdata (integration.connections[3])
  - arm_m0_min_if.i_hresp <= i_hresp (integration.connections[4])

## Tasks

### RTL-0088: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0089: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0091: Implement handshake rule: i_htrans

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.i_htrans
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.i_htrans.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=i_htrans.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.i_htrans
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.handshake_rules.i_htrans appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.i_htrans

### RTL-0092: Implement handshake rule: d_htrans

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.d_htrans
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.d_htrans.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=d_htrans.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.d_htrans
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.handshake_rules.d_htrans appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.d_htrans

### RTL-0093: Implement handshake rule: d_hwdata

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.d_hwdata
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.d_hwdata.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.handshake_rules.
SSOT item context: signal=d_hwdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.d_hwdata
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.handshake_rules.d_hwdata appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.d_hwdata

### RTL-0094: Implement pipeline stage: IF

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.IF
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.IF.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.pipeline.
SSOT item context: stage=IF; action=Drive instruction address/control and capture instruction on ready; cycle=n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.IF
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.pipeline.IF timing uses SSOT cycle/latency n
  - cycle_model.pipeline.IF appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.IF

### RTL-0095: Implement pipeline stage: ID

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.ID
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.ID.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.pipeline.
SSOT item context: stage=ID; action=Decode instruction and read source operands; cycle=n+1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.ID
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.pipeline.ID timing uses SSOT cycle/latency n+1
  - cycle_model.pipeline.ID appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.ID

### RTL-0099: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.
SSOT item context: value=i_hready=0 stalls IF and upstream PC progression without corrupting ID/EX committed state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0100: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.
SSOT item context: value=d_hready=0 stalls memory operation in EX; no duplicate commit allowed..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0101: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via cycle_model.
SSOT item context: value=Expose stage valid/stall indicators, pc, decode class, bus handshakes, and fault_halt for waveform and checker correl....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0142: Prove module arm_m0_min_if is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.arm_m0_min_if.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arm_m0_min_if.module_equivalence.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arm_m0_min_if.module_equivalence
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
- SSOT refs: sub_modules.arm_m0_min_if.module_equivalence

### RTL-0033: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0034: Implement and connect port rst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst.ports.rst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst.ports.rst.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.
SSOT item context: name=rst; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst.ports.rst
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - rst width matches SSOT value 1
  - rst port direction remains input
- SSOT refs: io_list.resets.rst.ports.rst

### RTL-0035: Implement and connect port i_haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_haddr.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_haddr; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_haddr
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_haddr width matches SSOT value 32
  - i_haddr port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_haddr

### RTL-0036: Implement and connect port i_htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_htrans.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_htrans; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_htrans
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_htrans width matches SSOT value 2
  - i_htrans port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_htrans

### RTL-0037: Implement and connect port i_hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hwrite.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hwrite; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hwrite
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hwrite width matches SSOT value 1
  - i_hwrite port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hwrite

### RTL-0038: Implement and connect port i_hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hsize.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hsize; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hsize
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hsize width matches SSOT value 3
  - i_hsize port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hsize

### RTL-0039: Implement and connect port i_hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hburst.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hburst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hburst
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hburst width matches SSOT value 3
  - i_hburst port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hburst

### RTL-0040: Implement and connect port i_hprot

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hprot
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hprot.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hprot; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hprot
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hprot width matches SSOT value 4
  - i_hprot port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hprot

### RTL-0041: Implement and connect port i_hmastlock

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hmastlock
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hmastlock.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hmastlock; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hmastlock
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hmastlock width matches SSOT value 1
  - i_hmastlock port direction remains output
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hmastlock

### RTL-0042: Implement and connect port i_hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hready.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hready
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hready width matches SSOT value 1
  - i_hready port direction remains input
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hready

### RTL-0043: Implement and connect port i_hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hrdata.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hrdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hrdata
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hrdata width matches SSOT value 32
  - i_hrdata port direction remains input
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hrdata

### RTL-0044: Implement and connect port i_hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_i_master.ports.i_hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_i_master.ports.i_hresp.
Owner: arm_m0_min_if in rtl/arm_m0_min_if.sv via io_list.interfaces.ahb_i_master.
SSOT item context: name=i_hresp; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_i_master.ports.i_hresp
  - Primary implementation evidence is in rtl/arm_m0_min_if.sv
  - i_hresp width matches SSOT value 1
  - i_hresp port direction remains input
- SSOT refs: io_list.interfaces.ahb_i_master.ports.i_hresp
