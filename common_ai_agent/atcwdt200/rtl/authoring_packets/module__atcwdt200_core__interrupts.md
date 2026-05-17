# RTL Authoring Packet: module__atcwdt200_core__interrupts

- Kind: module
- Owner module: atcwdt200_core
- Owner file: rtl/atcwdt200_core.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, dataflow.sequence.sequence_2, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sinks.sinks_1, dataflow.sinks.sinks_2, decomposition.units.watchdog_core, fsm, fsm.watchdog, function_model, function_model.transactions.restart, function_model.transactions.timeout_decode, function_model.transactions.watchdog_tick
- Module slice: 4/6 section=interrupts task_limit=48
- Slice rule: Owner module atcwdt200_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_core.pclk <= pclk (integration.connections[2])
  - atcwdt200_core.presetn <= presetn (integration.connections[3])

## Tasks

### RTL-0157: Implement interrupt item WDT_INTZERO

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.WDT_INTZERO
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.WDT_INTZERO.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via interrupts.
SSOT item context: name=WDT_INTZERO; clear=W1C.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.WDT_INTZERO
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - WDT_INTZERO clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.WDT_INTZERO

### RTL-0158: Implement interrupt item WDT_RSTZERO

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.WDT_RSTZERO
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.WDT_RSTZERO.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via interrupts.
SSOT item context: name=WDT_RSTZERO; clear=reset_only.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.WDT_RSTZERO
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - WDT_RSTZERO clear behavior matches SSOT clear policy reset_only
- SSOT refs: interrupts.sources.WDT_RSTZERO
