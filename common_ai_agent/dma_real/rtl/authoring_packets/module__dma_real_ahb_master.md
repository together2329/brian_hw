# RTL Authoring Packet: module__dma_real_ahb_master

- Kind: module
- Owner module: dma_real_ahb_master
- Owner file: rtl/dma_real_ahb_master.sv
- Task count: 19
- Required tasks: 19

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, dataflow.ordering.ordering_2, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, function_model.transactions.FM_DMA_STEP, io_list, io_list.interfaces.ahb_master

## Tasks

### RTL-0169: Implement handshake rule: ahb_address_phase

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.ahb_address_phase
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.ahb_address_phase.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via cycle_model.handshake_rules.
SSOT item context: name=ahb_address_phase.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.ahb_address_phase
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - ahb_address_phase appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.ahb_address_phase

### RTL-0170: Implement handshake rule: ahb_data_phase

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.ahb_data_phase
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.ahb_data_phase.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via cycle_model.handshake_rules.
SSOT item context: name=ahb_data_phase.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.ahb_data_phase
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - ahb_data_phase appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.ahb_data_phase

### RTL-0171: Implement handshake rule: ahb_1kb_boundary

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.ahb_1kb_boundary
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.ahb_1kb_boundary.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via cycle_model.handshake_rules.
SSOT item context: name=ahb_1kb_boundary.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.ahb_1kb_boundary
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - ahb_1kb_boundary appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.ahb_1kb_boundary

### RTL-0172: Implement handshake rule: ahb_error_response

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.ahb_error_response
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.ahb_error_response.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via cycle_model.handshake_rules.
SSOT item context: name=ahb_error_response.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.ahb_error_response
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - ahb_error_response appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.ahb_error_response

### RTL-0379: Prove module dma_real_ahb_master is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.dma_real_ahb_master.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.dma_real_ahb_master.module_equivalence.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.dma_real_ahb_master.module_equivalence
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
- SSOT refs: sub_modules.dma_real_ahb_master.module_equivalence

### RTL-0047: Implement and connect port haddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.haddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.haddr.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=haddr; width=ADDR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.haddr
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - haddr width matches SSOT value ADDR_WIDTH
  - haddr port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.haddr

### RTL-0048: Implement and connect port hwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hwrite.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hwrite; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hwrite
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hwrite width matches SSOT value 1
  - hwrite port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hwrite

### RTL-0049: Implement and connect port htrans

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.htrans
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.htrans.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=htrans; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.htrans
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - htrans width matches SSOT value 2
  - htrans port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.htrans

### RTL-0050: Implement and connect port hsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hsize.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hsize; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hsize
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hsize width matches SSOT value 3
  - hsize port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hsize

### RTL-0051: Implement and connect port hburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hburst.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hburst; width=3; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hburst
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hburst width matches SSOT value 3
  - hburst port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hburst

### RTL-0052: Implement and connect port hprot

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hprot
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hprot.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hprot; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hprot
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hprot width matches SSOT value 4
  - hprot port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hprot

### RTL-0053: Implement and connect port hmaster

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hmaster
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hmaster.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hmaster; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hmaster
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hmaster width matches SSOT value 4
  - hmaster port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hmaster

### RTL-0054: Implement and connect port hmastlock

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hmastlock
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hmastlock.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hmastlock; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hmastlock
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hmastlock width matches SSOT value 1
  - hmastlock port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hmastlock

### RTL-0055: Implement and connect port hwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hwdata.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hwdata; width=DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hwdata
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hwdata width matches SSOT value DATA_WIDTH
  - hwdata port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hwdata

### RTL-0056: Implement and connect port hrdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hrdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hrdata.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hrdata; width=DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hrdata
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hrdata width matches SSOT value DATA_WIDTH
  - hrdata port direction remains input
- SSOT refs: io_list.interfaces.ahb_master.ports.hrdata

### RTL-0057: Implement and connect port hready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hready.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hready
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hready width matches SSOT value 1
  - hready port direction remains input
- SSOT refs: io_list.interfaces.ahb_master.ports.hready

### RTL-0058: Implement and connect port hresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hresp.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hresp; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hresp
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hresp width matches SSOT value 2
  - hresp port direction remains input
- SSOT refs: io_list.interfaces.ahb_master.ports.hresp

### RTL-0059: Implement and connect port hbusreq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hbusreq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hbusreq.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hbusreq; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hbusreq
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hbusreq width matches SSOT value 1
  - hbusreq port direction remains output
- SSOT refs: io_list.interfaces.ahb_master.ports.hbusreq

### RTL-0060: Implement and connect port hgrant

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ahb_master.ports.hgrant
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ahb_master.ports.hgrant.
Owner: dma_real_ahb_master in rtl/dma_real_ahb_master.sv via io_list.interfaces.ahb_master.
SSOT item context: name=hgrant; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ahb_master.ports.hgrant
  - Primary implementation evidence is in rtl/dma_real_ahb_master.sv
  - hgrant width matches SSOT value 1
  - hgrant port direction remains input
- SSOT refs: io_list.interfaces.ahb_master.ports.hgrant
