# RTL Authoring Packet: module__atciic100_gsf

- Kind: module
- Owner module: atciic100_gsf
- Owner file: rtl/atciic100_gsf.v
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: features, features.glitch_suppression
- SSOT connection contracts:
  - atciic100_gsf.scl_in <= scl_filtered (sub_modules[1].connections[2])

## Tasks

### RTL-0030: Implement Glitch Filter

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Digital filter for SCL/SDA inputs based on T_SP.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: atciic100_gsf in rtl/atciic100_gsf.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_GSF.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Glitch rejection functional
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/atciic100_gsf.v
  - Semantic source_refs covered: features.glitch_suppression
- SSOT refs: features.glitch_suppression, workflow_todos.rtl-gen[3]

### RTL-0203: Implement feature Master Transmit/Receive

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Master_Transmit_Receive
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Master_Transmit_Receive.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Master Transmit/Receive; output=I2C Bus Transaction.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Master_Transmit_Receive
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Master_Transmit_Receive

### RTL-0204: Implement feature Slave Transmit/Receive

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Slave_Transmit_Receive
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Slave_Transmit_Receive.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Slave Transmit/Receive; output=Ack/Nack response.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Slave_Transmit_Receive
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Slave_Transmit_Receive

### RTL-0205: Implement feature Multi-Master Arbitration

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Multi_Master_Arbitration
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Multi_Master_Arbitration.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Multi-Master Arbitration; output=Arbitration Lost Status.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Multi_Master_Arbitration
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Multi_Master_Arbitration

### RTL-0206: Implement feature General Call

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.General_Call
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.General_Call.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=General Call; output=Ack response to address 0x00.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.General_Call
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.General_Call

### RTL-0207: Implement feature Glitch Suppression

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Glitch_Suppression
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Glitch_Suppression.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Glitch Suppression; output=Filtered SCL/SDA to internal logic.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Glitch_Suppression
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Glitch_Suppression

### RTL-0208: Implement feature Auto Clock Stretching

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Auto_Clock_Stretching
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Auto_Clock_Stretching.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Auto Clock Stretching; output=Stalled bus clock.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Auto_Clock_Stretching
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Auto_Clock_Stretching

### RTL-0209: Implement feature Auto-ACK

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Auto_ACK
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Auto_ACK.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via features.
SSOT item context: name=Auto-ACK; output=Proper ACK/NACK on bus.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Auto_ACK
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: features.Auto_ACK

### RTL-0221: Prove module atciic100_gsf is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_gsf.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_gsf.module_equivalence.
Owner: atciic100_gsf in rtl/atciic100_gsf.v via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_gsf.v.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_gsf.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_gsf.v
- SSOT refs: sub_modules.atciic100_gsf.module_equivalence
