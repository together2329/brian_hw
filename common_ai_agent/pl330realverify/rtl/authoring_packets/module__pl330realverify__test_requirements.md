# RTL Authoring Packet: module__pl330realverify__test_requirements

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 7/9 section=test_requirements task_limit=48
- Slice rule: Owner module pl330realverify is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])
- SSOT top IO contracts: 46

## Tasks

### RTL-0382: Keep RTL observable for scenario SC_RESET_APB

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_RESET_APB
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_RESET_APB.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_RESET_APB; name=Reset and APB discovery; expected=Reset values match registers/function_model; reserved fields read zero; illegal APB access asserts pslverr only for t....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_RESET_APB
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Reset values match registers/function_model; reserved fields read zero; illegal APB access asserts pslverr only for t...
- SSOT refs: test_requirements.scenarios.SC_RESET_APB

### RTL-0383: Keep RTL observable for scenario SC_SINGLE_BEAT_COPY

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_SINGLE_BEAT_COPY
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_SINGLE_BEAT_COPY.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_SINGLE_BEAT_COPY; name=Single-beat DMA memory copy; expected=One read beat is written unchanged to DAR, SAR/DAR increment by 8, status reaches COMPLETED, CH_COMPLETE pending is s....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_SINGLE_BEAT_COPY
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: One read beat is written unchanged to DAR, SAR/DAR increment by 8, status reaches COMPLETED, CH_COMPLETE pending is s...
- SSOT refs: test_requirements.scenarios.SC_SINGLE_BEAT_COPY

### RTL-0384: Keep RTL observable for scenario SC_MULTI_BEAT_COPY

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_MULTI_BEAT_COPY
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_MULTI_BEAT_COPY.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_MULTI_BEAT_COPY; name=Multi-beat address and loop progression; expected=Every beat writes matching data, SAR/DAR increment by DATA_WIDTH/8 per beat, loop_remaining decreases, and completion....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_MULTI_BEAT_COPY
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Every beat writes matching data, SAR/DAR increment by DATA_WIDTH/8 per beat, loop_remaining decreases, and completion...
- SSOT refs: test_requirements.scenarios.SC_MULTI_BEAT_COPY

### RTL-0385: Keep RTL observable for scenario SC_AXI_BACKPRESSURE

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AXI_BACKPRESSURE
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AXI_BACKPRESSURE.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_AXI_BACKPRESSURE; name=AXI ready/valid hold behavior under backpressure; expected=Payload signals remain stable while valid waits for ready; architectural state updates only on completed handshakes..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AXI_BACKPRESSURE
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Payload signals remain stable while valid waits for ready; architectural state updates only on completed handshakes.
- SSOT refs: test_requirements.scenarios.SC_AXI_BACKPRESSURE

### RTL-0386: Keep RTL observable for scenario SC_WFP_EVENT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_WFP_EVENT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_WFP_EVENT.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_WFP_EVENT; name=Wait-for-peripheral event gating; expected=Channel remains WAITING_FOR_PERIPHERAL with no AXI issue until event is sampled, then resumes transfer..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_WFP_EVENT
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Channel remains WAITING_FOR_PERIPHERAL with no AXI issue until event is sampled, then resumes transfer.
- SSOT refs: test_requirements.scenarios.SC_WFP_EVENT

### RTL-0387: Keep RTL observable for scenario SC_AXI_READ_FAULT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AXI_READ_FAULT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AXI_READ_FAULT.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_AXI_READ_FAULT; name=AXI read fault propagation; expected=Channel transitions to FAULTED, error_code=ERR_AXI_RD, CH_FAULT pending set, no destination write for the failed beat..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AXI_READ_FAULT
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Channel transitions to FAULTED, error_code=ERR_AXI_RD, CH_FAULT pending set, no destination write for the failed beat.
- SSOT refs: test_requirements.scenarios.SC_AXI_READ_FAULT

### RTL-0388: Keep RTL observable for scenario SC_AXI_WRITE_FAULT

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_AXI_WRITE_FAULT
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_AXI_WRITE_FAULT.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_AXI_WRITE_FAULT; name=AXI write fault propagation; expected=Channel transitions to FAULTED, error_code=ERR_AXI_WR, CH_FAULT pending set, and completion interrupt is not raised..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_AXI_WRITE_FAULT
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Channel transitions to FAULTED, error_code=ERR_AXI_WR, CH_FAULT pending set, and completion interrupt is not raised.
- SSOT refs: test_requirements.scenarios.SC_AXI_WRITE_FAULT

### RTL-0389: Keep RTL observable for scenario SC_W1C_IRQ_CLEAR

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_W1C_IRQ_CLEAR
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_W1C_IRQ_CLEAR.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_W1C_IRQ_CLEAR; name=Interrupt enable and W1C clear; expected=Only bits written as one clear; dmac_irq reflects enabled pending bits after clear..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_W1C_IRQ_CLEAR
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Only bits written as one clear; dmac_irq reflects enabled pending bits after clear.
- SSOT refs: test_requirements.scenarios.SC_W1C_IRQ_CLEAR

### RTL-0390: Keep RTL observable for scenario SC_DEBUG_COMMAND

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC_DEBUG_COMMAND
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC_DEBUG_COMMAND.
Owner: pl330realverify in rtl/pl330realverify.sv via test_requirements.
SSOT item context: id=SC_DEBUG_COMMAND; name=Debug command pulse and rejection; expected=Idle debug command emits a bounded pulse; busy manager rejects with declared ERR_DEBUG_REJECT behavior when applicable..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC_DEBUG_COMMAND
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Downstream checker compares RTL-observed behavior against expected result: Idle debug command emits a bounded pulse; busy manager rejects with declared ERR_DEBUG_REJECT behavior when applicable.
- SSOT refs: test_requirements.scenarios.SC_DEBUG_COMMAND
