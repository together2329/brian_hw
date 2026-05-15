# RTL Authoring Packet: module__spi_fifo

- Kind: module
- Owner module: spi_fifo
- Owner file: rtl/spi_fifo.sv
- Task count: 9
- Required tasks: 9

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
- Owner refs: cycle_model, cycle_model.backpressure, dataflow, dataflow.rx_path, dataflow.tx_path, memory, memory.instances
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_fifo.rx_push_data <= rx_word (integration.connections[3])

## Tasks

### RTL-0116: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: value=PCLK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0117: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0118: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0133: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.backpressure.
SSOT item context: value=TX backpressure appears as tx_full; writes are dropped with tx_overrun when full..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0134: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.backpressure.
SSOT item context: value=RX backpressure appears as rx_full at completion; received frame is dropped with rx_overrun when full..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0135: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: spi_fifo in rtl/spi_fifo.sv via cycle_model.
SSOT item context: value=Probe launch_accept, sample_edge, shift_edge, bit_index, cs_active, tx_fifo_level, rx_fifo_level, done_event.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0193: Implement memory item tx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.tx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.tx_fifo.
Owner: spi_fifo in rtl/spi_fifo.sv via memory.instances.
SSOT item context: name=tx_fifo; width=32; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.tx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - tx_fifo width matches SSOT value 32
  - tx_fifo timing uses SSOT cycle/latency 0
  - tx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.tx_fifo

### RTL-0194: Implement memory item rx_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.rx_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.rx_fifo.
Owner: spi_fifo in rtl/spi_fifo.sv via memory.instances.
SSOT item context: name=rx_fifo; width=32; depth=16; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.rx_fifo
  - Primary implementation evidence is in rtl/spi_fifo.sv
  - rx_fifo width matches SSOT value 32
  - rx_fifo timing uses SSOT cycle/latency 0
  - rx_fifo storage depth matches SSOT value 16
- SSOT refs: memory.instances.rx_fifo

### RTL-0244: Prove module spi_fifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi_fifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_fifo.module_equivalence.
Owner: spi_fifo in rtl/spi_fifo.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_fifo.module_equivalence
  - Primary implementation evidence is in rtl/spi_fifo.sv
- SSOT refs: sub_modules.spi_fifo.module_equivalence
