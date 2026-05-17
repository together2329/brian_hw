# RTL Authoring Packet: module__pl330realverify_axi_rd

- Kind: module
- Owner module: pl330realverify_axi_rd
- Owner file: rtl/pl330realverify_axi_rd.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 22
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.AXI_AR, cycle_model.handshake_rules.AXI_R, decomposition.units.axi_read_adapter, error_handling, error_handling.error_sources.ERR_AXI_RD, function_model.transactions.FM_TRANSFER, function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD, io_list, io_list.interfaces.axi_rd_master
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_axi_rd.clk_i <= dmaclk (sub_modules[2].connections[0])
  - pl330realverify_axi_rd.rst_ni <= dmacresetn (sub_modules[2].connections[1])
  - pl330realverify_axi_rd.arvalid_o <= arvalid (sub_modules[2].connections[2])
  - pl330realverify_axi_rd.arready_i <= arready (sub_modules[2].connections[3])
  - pl330realverify_axi_rd.rvalid_i <= rvalid (sub_modules[2].connections[4])
  - pl330realverify_axi_rd.rready_o <= rready (sub_modules[2].connections[5])
  - pl330realverify_axi_rd.rdata_i <= rdata (sub_modules[2].connections[6])
  - pl330realverify_axi_rd.rresp_i <= rresp (sub_modules[2].connections[7])
  - pl330realverify_axi_rd.arvalid_o <= arvalid (integration.connections[12])
  - pl330realverify_axi_rd.arready_i <= arready (integration.connections[13])
  - pl330realverify_axi_rd.rvalid_i <= rvalid (integration.connections[14])
  - pl330realverify_axi_rd.rready_o <= rready (integration.connections[15])

## Tasks

### RTL-0138: Implement transaction FM_TRANSFER

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_TRANSFER
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_TRANSFER.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
- SSOT refs: function_model.transactions.FM_TRANSFER

### RTL-0162: Implement error case for FM_TRANSFER: ERR_AXI_RD

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD.
SSOT item context: id=FM_TRANSFER; name=single_or_multi_beat_memory_copy; port=["wdata", "wstrb", "dmac_irq"]; signal=[{"condition": "rvalid == 1 and rready == 1 and rresp != 0", "id": "ERR_AXI_RD", "result": "status=FAULTED, error_cod...; state=["rd_buf", "sar", "dar", "loop_remaining", "status", "error_code", "intstatus"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - DUT port ["wdata", "wstrb", "dmac_irq"] is the implementation/observation point for single_or_multi_beat_memory_copy
- SSOT refs: function_model.transactions.FM_TRANSFER.error_cases.ERR_AXI_RD

### RTL-0207: Implement handshake rule: AXI_AR

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.AXI_AR
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.AXI_AR.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via cycle_model.handshake_rules.AXI_AR.
SSOT item context: id=AXI_AR; signal=arvalid.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.AXI_AR
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - AXI_AR appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.AXI_AR

### RTL-0208: Implement handshake rule: AXI_R

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.AXI_R
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.AXI_R.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via cycle_model.handshake_rules.AXI_AR.
SSOT item context: id=AXI_R; signal=rready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.AXI_R
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - AXI_R appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.AXI_R

### RTL-0210: Implement handshake rule: AXI_W

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.AXI_W
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.AXI_W.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via cycle_model.handshake_rules.AXI_AR.
SSOT item context: id=AXI_W; signal=wvalid.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.AXI_W
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - AXI_W appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.AXI_W

### RTL-0211: Implement handshake rule: AXI_B

- Priority: high
- Required: True
- Status: planned
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.AXI_B
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.AXI_B.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via cycle_model.handshake_rules.AXI_AR.
SSOT item context: id=AXI_B; signal=bready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.AXI_B
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - AXI_B appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.AXI_B

### RTL-0377: Prove module pl330realverify_axi_rd is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.pl330realverify_axi_rd.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330realverify_axi_rd.module_equivalence.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330realverify_axi_rd.module_equivalence
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
- SSOT refs: sub_modules.pl330realverify_axi_rd.module_equivalence

### RTL-0053: Implement and connect port arid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arid.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arid; width=6; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arid
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arid width matches SSOT value 6
  - arid port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arid

### RTL-0054: Implement and connect port araddr

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.araddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.araddr.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=araddr; width=32; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.araddr
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - araddr width matches SSOT value 32
  - araddr port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.araddr

### RTL-0055: Implement and connect port arlen

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arlen
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arlen.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arlen; width=8; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arlen
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arlen width matches SSOT value 8
  - arlen port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arlen

### RTL-0056: Implement and connect port arsize

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arsize.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arsize; width=3; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arsize
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arsize width matches SSOT value 3
  - arsize port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arsize

### RTL-0057: Implement and connect port arburst

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arburst.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arburst; width=2; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arburst
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arburst width matches SSOT value 2
  - arburst port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arburst

### RTL-0058: Implement and connect port arcache

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arcache
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arcache.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arcache; width=4; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arcache
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arcache width matches SSOT value 4
  - arcache port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arcache

### RTL-0059: Implement and connect port arprot

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arprot
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arprot.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arprot; width=3; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arprot
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arprot width matches SSOT value 3
  - arprot port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arprot

### RTL-0060: Implement and connect port arvalid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arvalid.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arvalid; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arvalid
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arvalid width matches SSOT value 1
  - arvalid port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arvalid

### RTL-0061: Implement and connect port arready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.arready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.arready.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=arready; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.arready
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - arready width matches SSOT value 1
  - arready port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.arready

### RTL-0062: Implement and connect port rid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rid.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rid; width=6; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rid
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rid width matches SSOT value 6
  - rid port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rid

### RTL-0063: Implement and connect port rdata

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rdata.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rdata; width=64; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rdata
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rdata width matches SSOT value 64
  - rdata port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rdata

### RTL-0064: Implement and connect port rresp

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rresp.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rresp; width=2; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rresp
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rresp width matches SSOT value 2
  - rresp port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rresp

### RTL-0065: Implement and connect port rlast

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rlast
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rlast.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rlast; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rlast
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rlast width matches SSOT value 1
  - rlast port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rlast

### RTL-0066: Implement and connect port rvalid

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rvalid.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rvalid; width=1; direction=input.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rvalid
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rvalid width matches SSOT value 1
  - rvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rvalid

### RTL-0067: Implement and connect port rready

- Priority: normal
- Required: True
- Status: planned
- Category: io_list.port
- Source ref: io_list.interfaces.axi_rd_master.ports.rready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_rd_master.ports.rready.
Owner: pl330realverify_axi_rd in rtl/pl330realverify_axi_rd.sv via io_list.interfaces.axi_rd_master.
SSOT item context: name=rready; width=1; direction=output.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_rd_master.ports.rready
  - Primary implementation evidence is in rtl/pl330realverify_axi_rd.sv
  - rready width matches SSOT value 1
  - rready port direction remains output
- SSOT refs: io_list.interfaces.axi_rd_master.ports.rready
