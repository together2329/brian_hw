# RTL Authoring Packet: module__mctp_assembler_v3_axi_wr_ingress__test_requirements

- Kind: module
- Owner module: mctp_assembler_v3_axi_wr_ingress
- Owner file: rtl/mctp_assembler_v3_axi_wr_ingress.sv
- Task count: 20
- Required tasks: 20

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 20
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, function_model, function_model.transactions.FM_INGEST_TLP, io_list, io_list.interfaces.axi_wr_slave, test_requirements
- Module slice: 4/5 section=test_requirements task_limit=48
- Slice rule: Owner module mctp_assembler_v3_axi_wr_ingress is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])

## Tasks

### RTL-0474: Keep RTL observable for scenario SC_SINGLE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_SINGLE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_SINGLE.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_SINGLE; name=Valid single-packet message; expected=payload assembled, descriptor published, first==last header.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_SINGLE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: payload assembled, descriptor published, first==last header
- SSOT refs: test_requirements.scenarios.SC_SINGLE

### RTL-0475: Keep RTL observable for scenario SC_FRAG

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_FRAG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_FRAG.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_FRAG; name=Fragmented message across TLPs; expected=concatenated payload, no SRAM holes, descriptor payload_len correct.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_FRAG
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: concatenated payload, no SRAM holes, descriptor payload_len correct
- SSOT refs: test_requirements.scenarios.SC_FRAG

### RTL-0476: Keep RTL observable for scenario SC_INTERLEAVE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_INTERLEAVE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_INTERLEAVE.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_INTERLEAVE; name=Interleaved messages distinct keys; expected=independent contexts, B completes before A, partial words preserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_INTERLEAVE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: independent contexts, B completes before A, partial words preserved
- SSOT refs: test_requirements.scenarios.SC_INTERLEAVE

### RTL-0477: Keep RTL observable for scenario SC_UNALIGNED_TU

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_UNALIGNED_TU
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_UNALIGNED_TU.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_UNALIGNED_TU; name=TU=68B unaligned 32B continuation; expected=next fragment continues lane 4 of word@64, no gap.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_UNALIGNED_TU
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: next fragment continues lane 4 of word@64, no gap
- SSOT refs: test_requirements.scenarios.SC_UNALIGNED_TU

### RTL-0478: Keep RTL observable for scenario SC_MAX_TU

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_MAX_TU
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_MAX_TU.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_MAX_TU; name=Max TU 4096B over 129 beats; expected=129 W beats accepted, payload_len=4096.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_MAX_TU
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: 129 W beats accepted, payload_len=4096
- SSOT refs: test_requirements.scenarios.SC_MAX_TU

### RTL-0479: Keep RTL observable for scenario SC_PD_MALFORMED

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PD_MALFORMED
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PD_MALFORMED.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PD_MALFORMED; name=Malformed AXI/TLP drops; expected=PD_MALFORMED_TLP, no context/SRAM/descriptor side effect.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PD_MALFORMED
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_MALFORMED_TLP, no context/SRAM/descriptor side effect
- SSOT refs: test_requirements.scenarios.SC_PD_MALFORMED

### RTL-0480: Keep RTL observable for scenario SC_PD_VDM

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PD_VDM
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PD_VDM.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PD_VDM; name=Unsupported VDM constants; expected=PD_UNSUPPORTED_VDM.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PD_VDM
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_UNSUPPORTED_VDM
- SSOT refs: test_requirements.scenarios.SC_PD_VDM

### RTL-0481: Keep RTL observable for scenario SC_PD_MCTP

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PD_MCTP
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PD_MCTP.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PD_MCTP; name=Bad MCTP header version; expected=PD_BAD_MCTP_HEADER.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PD_MCTP
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_BAD_MCTP_HEADER
- SSOT refs: test_requirements.scenarios.SC_PD_MCTP

### RTL-0482: Keep RTL observable for scenario SC_PD_EID

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PD_EID
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PD_EID.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PD_EID; name=Dest EID reject; expected=PD_DEST_EID_REJECT.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PD_EID
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_DEST_EID_REJECT
- SSOT refs: test_requirements.scenarios.SC_PD_EID

### RTL-0483: Keep RTL observable for scenario SC_PD_MIDDLE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PD_MIDDLE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PD_MIDDLE.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PD_MIDDLE; name=Middle/EOM without SOM; expected=PD_UNEXPECTED_MIDDLE_END.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PD_MIDDLE
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_UNEXPECTED_MIDDLE_END
- SSOT refs: test_requirements.scenarios.SC_PD_MIDDLE

### RTL-0484: Keep RTL observable for scenario SC_AD_DUP

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_DUP
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_DUP.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_DUP; name=Duplicate SOM; expected=AD_DUPLICATE_SOM aborts exactly that context.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_DUP
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AD_DUPLICATE_SOM aborts exactly that context
- SSOT refs: test_requirements.scenarios.SC_AD_DUP

### RTL-0485: Keep RTL observable for scenario SC_AD_SEQ

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_SEQ
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_SEQ.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_SEQ; name=Sequence mismatch; expected=AD_SEQUENCE_MISMATCH abort.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_SEQ
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AD_SEQUENCE_MISMATCH abort
- SSOT refs: test_requirements.scenarios.SC_AD_SEQ

### RTL-0486: Keep RTL observable for scenario SC_AD_CTXFULL

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_CTXFULL
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_CTXFULL.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_CTXFULL; name=Context table full; expected=PD_BAD_OR_EXPIRED_TAG (table full), no alloc.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_CTXFULL
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: PD_BAD_OR_EXPIRED_TAG (table full), no alloc
- SSOT refs: test_requirements.scenarios.SC_AD_CTXFULL

### RTL-0487: Keep RTL observable for scenario SC_AD_SRAM

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_SRAM
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_SRAM.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_SRAM; name=SRAM overflow; expected=AD_SRAM_OVERFLOW abort.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_SRAM
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AD_SRAM_OVERFLOW abort
- SSOT refs: test_requirements.scenarios.SC_AD_SRAM

### RTL-0488: Keep RTL observable for scenario SC_AD_DESCFULL

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_DESCFULL
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_DESCFULL.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_DESCFULL; name=Descriptor queue full; expected=AD_DESCRIPTOR_FULL, no descriptor.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_DESCFULL
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AD_DESCRIPTOR_FULL, no descriptor
- SSOT refs: test_requirements.scenarios.SC_AD_DESCFULL

### RTL-0489: Keep RTL observable for scenario SC_AD_TIMEOUT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AD_TIMEOUT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AD_TIMEOUT.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_AD_TIMEOUT; name=Assembly timeout; expected=AD_TIMEOUT abort.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AD_TIMEOUT
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: AD_TIMEOUT abort
- SSOT refs: test_requirements.scenarios.SC_AD_TIMEOUT

### RTL-0490: Keep RTL observable for scenario SC_PRIORITY

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_PRIORITY
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_PRIORITY.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_PRIORITY; name=Drop priority; expected=earlier packet-drop reason wins.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_PRIORITY
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: earlier packet-drop reason wins
- SSOT refs: test_requirements.scenarios.SC_PRIORITY

### RTL-0491: Keep RTL observable for scenario SC_FW_READ

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_FW_READ
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_FW_READ.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_FW_READ; name=Firmware payload read; expected=payload bytes returned, RLAST on final beat.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_FW_READ
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: payload bytes returned, RLAST on final beat
- SSOT refs: test_requirements.scenarios.SC_FW_READ

### RTL-0492: Keep RTL observable for scenario SC_FW_READ_SLVERR

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_FW_READ_SLVERR
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_FW_READ_SLVERR.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_FW_READ_SLVERR; name=Read outside window; expected=RRESP=SLVERR.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_FW_READ_SLVERR
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: RRESP=SLVERR
- SSOT refs: test_requirements.scenarios.SC_FW_READ_SLVERR

### RTL-0493: Keep RTL observable for scenario SC_REG

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_REG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_REG.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via test_requirements.
SSOT item context: id=SC_REG; name=APB register access; expected=register behavior + per-Q visibility.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_REG
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - Downstream checker compares RTL-observed behavior against expected result: register behavior + per-Q visibility
- SSOT refs: test_requirements.scenarios.SC_REG
