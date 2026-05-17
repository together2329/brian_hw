# RTL Authoring Packet: module__dma_real_irq

- Kind: module
- Owner module: dma_real_irq
- Owner file: rtl/dma_real_irq.sv
- Task count: 6
- Required tasks: 6

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: function_model.state_variables, interrupts, io_list.interfaces.irq_outputs, registers, registers.register_list

## Tasks

### RTL-0025: Implement interrupt aggregation with sticky latch

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[5]
- Detail: dma_real_irq aggregates per-channel done/error status with INT_ENABLE mask in pclk domain. Done/error pulses from hclk domain cross via pulse synchronizer.
SSOT ref: workflow_todos.rtl-gen[5].
Owner: dma_real_irq in rtl/dma_real_irq.sv via interrupts.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch]
  - INT_CLEAR clears done_q and error_q with priority over new pulse
  - pulse synchronizer for hclk-to-pclk crossing
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[5]
  - Primary implementation evidence is in rtl/dma_real_irq.sv
  - Semantic source_refs covered: cdc_requirements, interrupts, io_list.interfaces.irq_outputs
- SSOT refs: cdc_requirements, interrupts, io_list.interfaces.irq_outputs, workflow_todos.rtl-gen[5]

### RTL-0306: Implement interrupt item irq

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.outputs
- Source ref: interrupts.outputs.irq
- Detail: This SSOT interrupts.outputs item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.outputs.irq.
Owner: dma_real_irq in rtl/dma_real_irq.sv via interrupts.
SSOT item context: name=irq; width=N_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.outputs.irq
  - Primary implementation evidence is in rtl/dma_real_irq.sv
  - irq width matches SSOT value N_CHANNELS
- SSOT refs: interrupts.outputs.irq

### RTL-0307: Implement interrupt item irq_combined

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.outputs
- Source ref: interrupts.outputs.irq_combined
- Detail: This SSOT interrupts.outputs item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.outputs.irq_combined.
Owner: dma_real_irq in rtl/dma_real_irq.sv via interrupts.
SSOT item context: name=irq_combined; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.outputs.irq_combined
  - Primary implementation evidence is in rtl/dma_real_irq.sv
  - irq_combined width matches SSOT value 1
- SSOT refs: interrupts.outputs.irq_combined

### RTL-0380: Prove module dma_real_irq is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.dma_real_irq.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.dma_real_irq.module_equivalence.
Owner: dma_real_irq in rtl/dma_real_irq.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.dma_real_irq.module_equivalence
  - Primary implementation evidence is in rtl/dma_real_irq.sv
- SSOT refs: sub_modules.dma_real_irq.module_equivalence

### RTL-0061: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.irq_outputs.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.irq_outputs.ports.irq.
Owner: dma_real_irq in rtl/dma_real_irq.sv via io_list.interfaces.irq_outputs.
SSOT item context: name=irq; width=N_CHANNELS; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.irq_outputs.ports.irq
  - Primary implementation evidence is in rtl/dma_real_irq.sv
  - irq width matches SSOT value N_CHANNELS
  - irq port direction remains output
- SSOT refs: io_list.interfaces.irq_outputs.ports.irq

### RTL-0062: Implement and connect port irq_combined

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.irq_outputs.ports.irq_combined
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.irq_outputs.ports.irq_combined.
Owner: dma_real_irq in rtl/dma_real_irq.sv via io_list.interfaces.irq_outputs.
SSOT item context: name=irq_combined; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.irq_outputs.ports.irq_combined
  - Primary implementation evidence is in rtl/dma_real_irq.sv
  - irq_combined width matches SSOT value 1
  - irq_combined port direction remains output
- SSOT refs: io_list.interfaces.irq_outputs.ports.irq_combined
