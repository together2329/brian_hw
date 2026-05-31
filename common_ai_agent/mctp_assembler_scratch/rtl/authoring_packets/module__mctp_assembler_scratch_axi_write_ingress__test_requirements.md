# RTL Authoring Packet: module__mctp_assembler_scratch_axi_write_ingress__test_requirements

- Kind: module
- Owner module: mctp_assembler_scratch_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_axi_write_ingress.sv
- Task count: 22
- Required tasks: 22

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
- LLM-actionable open tasks: 22
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 4/6 section=test_requirements task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_axi_write_ingress is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0432: Keep RTL observable for scenario SC_VALID_SINGLE_PACKET

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_VALID_SINGLE_PACKET
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_VALID_SINGLE_PACKET.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_VALID_SINGLE_PACKET; name=Valid single packet; expected=Descriptor published and SRAM payload byte count matches payload.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_VALID_SINGLE_PACKET
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: Descriptor published and SRAM payload byte count matches payload
- SSOT refs: test_requirements.scenarios.SC_VALID_SINGLE_PACKET

### RTL-0433: Keep RTL observable for scenario SC_MULTI_FRAGMENT_TU64

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_MULTI_FRAGMENT_TU64
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_MULTI_FRAGMENT_TU64.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_MULTI_FRAGMENT_TU64; name=Multi-fragment TU64; expected=One completed message with ordered payload bytes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_MULTI_FRAGMENT_TU64
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: One completed message with ordered payload bytes
- SSOT refs: test_requirements.scenarios.SC_MULTI_FRAGMENT_TU64

### RTL-0434: Keep RTL observable for scenario SC_MAX_TU_4096_129_BEATS

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_MAX_TU_4096_129_BEATS
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_MAX_TU_4096_129_BEATS.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_MAX_TU_4096_129_BEATS; name=Maximum 4096B transmission unit; expected=No overflow and descriptor byte count equals 4096.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_MAX_TU_4096_129_BEATS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: No overflow and descriptor byte count equals 4096
- SSOT refs: test_requirements.scenarios.SC_MAX_TU_4096_129_BEATS

### RTL-0435: Keep RTL observable for scenario SC_INTERLEAVE_TWO_KEYS

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_INTERLEAVE_TWO_KEYS
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_INTERLEAVE_TWO_KEYS.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_INTERLEAVE_TWO_KEYS; name=Interleaved two keys; expected=Two independent Q FSMs complete without cross-contamination.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_INTERLEAVE_TWO_KEYS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: Two independent Q FSMs complete without cross-contamination
- SSOT refs: test_requirements.scenarios.SC_INTERLEAVE_TWO_KEYS

### RTL-0436: Keep RTL observable for scenario SC_UNALIGNED_SRAM_PACK_NO_HOLES

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_UNALIGNED_SRAM_PACK_NO_HOLES
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_UNALIGNED_SRAM_PACK_NO_HOLES.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_UNALIGNED_SRAM_PACK_NO_HOLES; name=Unaligned SRAM pack without holes; expected=SRAM byte lanes are contiguous and final strobe trims only trailing bytes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_UNALIGNED_SRAM_PACK_NO_HOLES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: SRAM byte lanes are contiguous and final strobe trims only trailing bytes
- SSOT refs: test_requirements.scenarios.SC_UNALIGNED_SRAM_PACK_NO_HOLES

### RTL-0437: Keep RTL observable for scenario SC_FIRST_LAST_TLP_HEADERS

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_FIRST_LAST_TLP_HEADERS
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_FIRST_LAST_TLP_HEADERS.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_FIRST_LAST_TLP_HEADERS; name=First and last TLP headers stored; expected=Per-Q first snapshot equals first TLP header and last snapshot equals EOM TLP header.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_FIRST_LAST_TLP_HEADERS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: Per-Q first snapshot equals first TLP header and last snapshot equals EOM TLP header
- SSOT refs: test_requirements.scenarios.SC_FIRST_LAST_TLP_HEADERS

### RTL-0438: Keep RTL observable for scenario SC_AXI_READBACK_TRIM

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AXI_READBACK_TRIM
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AXI_READBACK_TRIM.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_AXI_READBACK_TRIM; name=AXI readback trims final short packet; expected=AXI R data returns exactly descriptor byte count and zero SLVERR on extra no-descriptor read.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AXI_READBACK_TRIM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AXI R data returns exactly descriptor byte count and zero SLVERR on extra no-descriptor read
- SSOT refs: test_requirements.scenarios.SC_AXI_READBACK_TRIM

### RTL-0439: Keep RTL observable for scenario SC_APB_REGS_PER_Q

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_APB_REGS_PER_Q
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_APB_REGS_PER_Q.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=SC_APB_REGS_PER_Q; name=APB per-Q visibility; expected=Register values match selected context model.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_APB_REGS_PER_Q
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: Register values match selected context model
- SSOT refs: test_requirements.scenarios.SC_APB_REGS_PER_Q

### RTL-0440: Keep RTL observable for scenario PD_DISABLED_DROP_MODE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_DISABLED_DROP_MODE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_DISABLED_DROP_MODE.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_DISABLED_DROP_MODE; name=Drop mode packet drop; expected=no_sram_write and packet drop counter increments.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_DISABLED_DROP_MODE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and packet drop counter increments
- SSOT refs: test_requirements.scenarios.PD_DISABLED_DROP_MODE

### RTL-0441: Keep RTL observable for scenario PD_MALFORMED_TLP

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_MALFORMED_TLP
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_MALFORMED_TLP.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_MALFORMED_TLP; name=Malformed TLP packet drop; expected=no_sram_write and PD_MALFORMED_TLP counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_MALFORMED_TLP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_MALFORMED_TLP counted
- SSOT refs: test_requirements.scenarios.PD_MALFORMED_TLP

### RTL-0442: Keep RTL observable for scenario PD_UNSUPPORTED_VDM

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_UNSUPPORTED_VDM
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_UNSUPPORTED_VDM.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_UNSUPPORTED_VDM; name=Unsupported VDM packet drop; expected=no_sram_write and PD_UNSUPPORTED_VDM counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_UNSUPPORTED_VDM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_UNSUPPORTED_VDM counted
- SSOT refs: test_requirements.scenarios.PD_UNSUPPORTED_VDM

### RTL-0443: Keep RTL observable for scenario PD_BAD_MCTP_HEADER

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_BAD_MCTP_HEADER
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_BAD_MCTP_HEADER.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_BAD_MCTP_HEADER; name=Bad MCTP header packet drop; expected=no_sram_write and PD_BAD_MCTP_HEADER counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_BAD_MCTP_HEADER
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_BAD_MCTP_HEADER counted
- SSOT refs: test_requirements.scenarios.PD_BAD_MCTP_HEADER

### RTL-0444: Keep RTL observable for scenario PD_BAD_PAD_OR_ALIGNMENT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_BAD_PAD_OR_ALIGNMENT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_BAD_PAD_OR_ALIGNMENT.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_BAD_PAD_OR_ALIGNMENT; name=Bad pad or alignment packet drop; expected=no_sram_write and PD_BAD_PAD_OR_ALIGNMENT counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_BAD_PAD_OR_ALIGNMENT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_BAD_PAD_OR_ALIGNMENT counted
- SSOT refs: test_requirements.scenarios.PD_BAD_PAD_OR_ALIGNMENT

### RTL-0445: Keep RTL observable for scenario PD_DEST_EID_REJECT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_DEST_EID_REJECT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_DEST_EID_REJECT.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_DEST_EID_REJECT; name=Destination EID reject packet drop; expected=no_sram_write and PD_DEST_EID_REJECT counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_DEST_EID_REJECT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_DEST_EID_REJECT counted
- SSOT refs: test_requirements.scenarios.PD_DEST_EID_REJECT

### RTL-0446: Keep RTL observable for scenario PD_UNEXPECTED_MIDDLE_END

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_UNEXPECTED_MIDDLE_END
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_UNEXPECTED_MIDDLE_END.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_UNEXPECTED_MIDDLE_END; name=Unexpected middle or end packet drop; expected=no_sram_write and PD_UNEXPECTED_MIDDLE_END counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_UNEXPECTED_MIDDLE_END
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_UNEXPECTED_MIDDLE_END counted
- SSOT refs: test_requirements.scenarios.PD_UNEXPECTED_MIDDLE_END

### RTL-0447: Keep RTL observable for scenario PD_BAD_OR_EXPIRED_TAG

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.PD_BAD_OR_EXPIRED_TAG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.PD_BAD_OR_EXPIRED_TAG.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=PD_BAD_OR_EXPIRED_TAG; name=Bad or expired tag packet drop; expected=no_sram_write and PD_BAD_OR_EXPIRED_TAG counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.PD_BAD_OR_EXPIRED_TAG
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and PD_BAD_OR_EXPIRED_TAG counted
- SSOT refs: test_requirements.scenarios.PD_BAD_OR_EXPIRED_TAG

### RTL-0448: Keep RTL observable for scenario AD_DUPLICATE_SOM

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_DUPLICATE_SOM
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_DUPLICATE_SOM.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_DUPLICATE_SOM; name=Duplicate SOM assembly drop; expected=no_sram_write and AD_DUPLICATE_SOM counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_DUPLICATE_SOM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and AD_DUPLICATE_SOM counted
- SSOT refs: test_requirements.scenarios.AD_DUPLICATE_SOM

### RTL-0449: Keep RTL observable for scenario AD_SEQUENCE_MISMATCH

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_SEQUENCE_MISMATCH
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_SEQUENCE_MISMATCH.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_SEQUENCE_MISMATCH; name=Sequence mismatch assembly drop; expected=no_sram_write and AD_SEQUENCE_MISMATCH counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_SEQUENCE_MISMATCH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and AD_SEQUENCE_MISMATCH counted
- SSOT refs: test_requirements.scenarios.AD_SEQUENCE_MISMATCH

### RTL-0450: Keep RTL observable for scenario AD_MESSAGE_OVERFLOW

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_MESSAGE_OVERFLOW
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_MESSAGE_OVERFLOW.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_MESSAGE_OVERFLOW; name=Message overflow assembly drop; expected=no_sram_write and AD_MESSAGE_OVERFLOW counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_MESSAGE_OVERFLOW
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and AD_MESSAGE_OVERFLOW counted
- SSOT refs: test_requirements.scenarios.AD_MESSAGE_OVERFLOW

### RTL-0451: Keep RTL observable for scenario AD_SRAM_OVERFLOW

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_SRAM_OVERFLOW
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_SRAM_OVERFLOW.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_SRAM_OVERFLOW; name=SRAM overflow assembly drop; expected=no_sram_write and AD_SRAM_OVERFLOW counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_SRAM_OVERFLOW
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no_sram_write and AD_SRAM_OVERFLOW counted
- SSOT refs: test_requirements.scenarios.AD_SRAM_OVERFLOW

### RTL-0452: Keep RTL observable for scenario AD_DESCRIPTOR_FULL

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_DESCRIPTOR_FULL
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_DESCRIPTOR_FULL.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_DESCRIPTOR_FULL; name=Descriptor full assembly drop; expected=no descriptor publish and AD_DESCRIPTOR_FULL counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_DESCRIPTOR_FULL
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: no descriptor publish and AD_DESCRIPTOR_FULL counted
- SSOT refs: test_requirements.scenarios.AD_DESCRIPTOR_FULL

### RTL-0453: Keep RTL observable for scenario AD_TIMEOUT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.AD_TIMEOUT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.AD_TIMEOUT.
Owner: mctp_assembler_scratch_axi_write_ingress in rtl/mctp_assembler_scratch_axi_write_ingress.sv via test_requirements.
SSOT item context: id=AD_TIMEOUT; name=Timeout assembly drop; expected=context clears and AD_TIMEOUT counted.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.AD_TIMEOUT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_axi_write_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: context clears and AD_TIMEOUT counted
- SSOT refs: test_requirements.scenarios.AD_TIMEOUT
