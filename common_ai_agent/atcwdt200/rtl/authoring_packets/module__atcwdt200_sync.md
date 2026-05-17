# RTL Authoring Packet: module__atcwdt200_sync

- Kind: module
- Owner module: atcwdt200_sync
- Owner file: rtl/atcwdt200_sync.sv
- Task count: 3
- Required tasks: 3

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
- Owner refs: cdc_requirements, cdc_requirements.crossings.extclk_to_pclk, cdc_requirements.crossings.wdt_pause_to_pclk, dataflow.sequence.sequence_2, decomposition.units.cdc_sync, io_list
- SSOT connection contracts:
  - atcwdt200_sync.pclk <= pclk (integration.connections[4])
  - atcwdt200_sync.presetn <= presetn (integration.connections[5])

## Tasks

### RTL-0198: Prove module atcwdt200_sync is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.atcwdt200_sync.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atcwdt200_sync.module_equivalence.
Owner: atcwdt200_sync in rtl/atcwdt200_sync.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atcwdt200_sync.module_equivalence
  - Primary implementation evidence is in rtl/atcwdt200_sync.sv
- SSOT refs: sub_modules.atcwdt200_sync.module_equivalence

### RTL-0025: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: atcwdt200_sync in rtl/atcwdt200_sync.sv via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/atcwdt200_sync.sv
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0026: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: atcwdt200_sync in rtl/atcwdt200_sync.sv via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.presetn
  - Primary implementation evidence is in rtl/atcwdt200_sync.sv
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.presetn
