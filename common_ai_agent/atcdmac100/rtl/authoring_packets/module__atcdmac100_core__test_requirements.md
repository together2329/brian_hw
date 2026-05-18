# RTL Authoring Packet: module__atcdmac100_core__test_requirements

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
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
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 11/14 section=test_requirements task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= hresetn (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0326: Keep RTL observable for scenario SC_AHB_REG

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AHB_REG
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AHB_REG.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_AHB_REG; name=AHB register programming; expected=hready=1, hresp=OKAY, read data matches programmed or RO values, W1C clears only written status bits..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AHB_REG
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: hready=1, hresp=OKAY, read data matches programmed or RO values, W1C clears only written status bits.
- SSOT refs: test_requirements.scenarios.SC_AHB_REG

### RTL-0327: Keep RTL observable for scenario SC_MEM_COPY

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_MEM_COPY
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_MEM_COPY.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_MEM_COPY; name=single-channel memory copy; expected=AHB master issues read/write pairs, bytes_done advances, IntStatus.TC bit sets, channel disables..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_MEM_COPY
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: AHB master issues read/write pairs, bytes_done advances, IntStatus.TC bit sets, channel disables.
- SSOT refs: test_requirements.scenarios.SC_MEM_COPY

### RTL-0328: Keep RTL observable for scenario SC_ARB

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_ARB
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_ARB.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_ARB; name=priority round-robin arbitration; expected=High priority service precedes low priority; same priority rotates without starvation..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_ARB
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: High priority service precedes low priority; same priority rotates without starvation.
- SSOT refs: test_requirements.scenarios.SC_ARB

### RTL-0329: Keep RTL observable for scenario SC_HANDSHAKE

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_HANDSHAKE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_HANDSHAKE.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_HANDSHAKE; name=hardware request acknowledge; expected=Master traffic waits for request and dma_ack asserts after SrcBurstSize service, then deasserts after request drops..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_HANDSHAKE
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Master traffic waits for request and dma_ack asserts after SrcBurstSize service, then deasserts after request drops.
- SSOT refs: test_requirements.scenarios.SC_HANDSHAKE

### RTL-0330: Keep RTL observable for scenario SC_ERROR_ABORT

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_ERROR_ABORT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_ERROR_ABORT.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_ERROR_ABORT; name=error and abort handling; expected=Channel disables, IntStatus.Error or Abort sets, dma_int asserts according to mask, no ack on error..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_ERROR_ABORT
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Channel disables, IntStatus.Error or Abort sets, dma_int asserts according to mask, no ack on error.
- SSOT refs: test_requirements.scenarios.SC_ERROR_ABORT

### RTL-0331: Keep RTL observable for scenario SC_CHAIN

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_CHAIN
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_CHAIN.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC_CHAIN; name=chain transfer continuation; expected=Completion records chain pending/preload behavior and allows software to resume continuation..
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_CHAIN
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Completion records chain pending/preload behavior and allows software to resume continuation.
- SSOT refs: test_requirements.scenarios.SC_CHAIN
