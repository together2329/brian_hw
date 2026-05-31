# RTL Authoring Packet: module__mctp_assembler_scratch_axi_write_ingress__cycle_model

- Kind: module
- Owner module: mctp_assembler_scratch_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_axi_write_ingress.sv
- Task count: 16
- Required tasks: 16

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
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
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 3/6 section=cycle_model task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_axi_write_ingress is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0294: Implement cycle-model clock

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: value=axi_aclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0295: Implement cycle-model reset

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: value=axi_aresetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0296: Implement cycle-model latency

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0301: Implement pipeline stage: axi_write_collect

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.axi_write_collect
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.axi_write_collect.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=axi_write_collect; action=Collect one raw TLP write transaction through WLAST.; cycle=variable_1_to_129.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.axi_write_collect
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.axi_write_collect timing uses SSOT cycle/latency variable_1_to_129
  - cycle_model.pipeline.axi_write_collect appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.axi_write_collect

### RTL-0302: Implement pipeline stage: pcie_vdm_filter

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.pcie_vdm_filter
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.pcie_vdm_filter.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=pcie_vdm_filter; action=Decode required PCIe VDM fields and classify packet drops.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.pcie_vdm_filter
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.pcie_vdm_filter timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.pcie_vdm_filter appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.pcie_vdm_filter

### RTL-0303: Implement pipeline stage: mctp_parse

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.mctp_parse
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.mctp_parse.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=mctp_parse; action=Decode MCTP transport fields and form context key.; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.mctp_parse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.mctp_parse timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.mctp_parse appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.mctp_parse

### RTL-0304: Implement pipeline stage: context_lookup_update

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.context_lookup_update
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.context_lookup_update.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=context_lookup_update; action=Allocate; cycle=1_to_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.context_lookup_update
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.context_lookup_update timing uses SSOT cycle/latency 1_to_4
  - cycle_model.pipeline.context_lookup_update appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.context_lookup_update

### RTL-0305: Implement pipeline stage: sram_pack_write

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.sram_pack_write
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.sram_pack_write.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=sram_pack_write; action=Emit packed 256-bit SRAM writes without holes.; cycle=0_to_32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.sram_pack_write
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.sram_pack_write timing uses SSOT cycle/latency 0_to_32
  - cycle_model.pipeline.sram_pack_write appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.sram_pack_write

### RTL-0306: Implement pipeline stage: descriptor_irq

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.descriptor_irq
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.descriptor_irq.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=descriptor_irq; action=Publish descriptor; cycle=1_to_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.descriptor_irq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.descriptor_irq timing uses SSOT cycle/latency 1_to_3
  - cycle_model.pipeline.descriptor_irq appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.descriptor_irq

### RTL-0307: Implement pipeline stage: axi_readback

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.axi_readback
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.axi_readback.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: stage=axi_readback; action=Read SRAM payload and return AXI R beats.; cycle=1_to_8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.axi_readback
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.pipeline.axi_readback timing uses SSOT cycle/latency 1_to_8
  - cycle_model.pipeline.axi_readback appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.axi_readback

### RTL-0308: Implement ordering rule: one_tlp_per_axi_write_transaction

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.one_tlp_per_axi_write_transaction
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.one_tlp_per_axi_write_transaction.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: name=one_tlp_per_axi_write_transaction.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.one_tlp_per_axi_write_transaction
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - one_tlp_per_axi_write_transaction appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.one_tlp_per_axi_write_transaction

### RTL-0309: Implement ordering rule: per_key_fragment_order

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.per_key_fragment_order
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.per_key_fragment_order.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: name=per_key_fragment_order.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.per_key_fragment_order
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - per_key_fragment_order appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.per_key_fragment_order

### RTL-0311: Implement ordering rule: readback_after_descriptor

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.readback_after_descriptor
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.readback_after_descriptor.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: name=readback_after_descriptor.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.readback_after_descriptor
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - readback_after_descriptor appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.readback_after_descriptor

### RTL-0312: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: value=AXI write backpressure is applied when context table, descriptor FIFO, or SRAM pack resources cannot accept more data..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0313: Implement backpressure rule: backpressure_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_1.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: value=AXI read backpressure is applied while waiting for SRAM read responses..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.backpressure.backpressure_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_1

### RTL-0314: Implement backpressure rule: backpressure_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_2.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via cycle_model.
SSOT item context: value=SRAM read requests yield to SRAM write requests in the first-target arbiter..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - cycle_model.backpressure.backpressure_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_2
