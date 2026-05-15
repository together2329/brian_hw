# RTL Authoring Packet: module__fifo_sync__test_requirements

- Kind: module
- Owner module: fifo_sync
- Owner file: rtl/fifo_sync.sv
- Task count: 20
- Required tasks: 20

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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 7/9 section=test_requirements task_limit=48
- Slice rule: Owner module fifo_sync is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
- SSOT top IO contracts: 20

## Tasks

### RTL-0250: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC1; name=Push single entry; expected=Data stored; count=1; full_o=0; empty_o=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Data stored; count=1; full_o=0; empty_o=0
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0251: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC2; name=Pop single entry; expected=rd_data_o=pattern_A; count=0; empty_o=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: rd_data_o=pattern_A; count=0; empty_o=1
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0252: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC3; name=Fill to full; expected=full_o=1 after DEPTH pushes; count_o=DEPTH; all entries stored correctly.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: full_o=1 after DEPTH pushes; count_o=DEPTH; all entries stored correctly
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0253: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC4; name=Overflow rejection; expected=No state change; count unchanged; previously stored data intact.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: No state change; count unchanged; previously stored data intact
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0254: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC5; name=Underflow rejection; expected=No state change; count remains 0; rd_data_o holds previous value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: No state change; count remains 0; rd_data_o holds previous value
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0255: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC6; name=Simultaneous push and pop; expected=Both accepted; count unchanged; new data pushed; old data popped correctly.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Both accepted; count unchanged; new data pushed; old data popped correctly
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0256: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC7; name=Simultaneous push and pop at boundary; expected=Push rejected (full), pop accepted; count decrements to DEPTH-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Push rejected (full), pop accepted; count decrements to DEPTH-1
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0257: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC8; name=Flush when partially full; expected=wr_ptr=0; rd_ptr=0; count=0; empty_o=1; full_o=0; all entries invalidated.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: wr_ptr=0; rd_ptr=0; count=0; empty_o=1; full_o=0; all entries invalidated
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0258: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC9; name=Flush when full; expected=All pointers and count cleared; full_o deasserts; empty_o asserts.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: All pointers and count cleared; full_o deasserts; empty_o asserts
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0259: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC10; name=Flush during simultaneous push/pop; expected=Flush takes precedence; push and pop ignored; state reset to empty.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Flush takes precedence; push and pop ignored; state reset to empty
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0260: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC11; name=Almost full threshold; expected=almost_full_o asserts at threshold; full_o not yet asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: almost_full_o asserts at threshold; full_o not yet asserted
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0261: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC12; name=Almost empty threshold; expected=almost_empty_o asserts at threshold; empty_o not yet asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: almost_empty_o asserts at threshold; empty_o not yet asserted
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0262: Keep RTL observable for scenario SC13

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC13
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC13.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC13; name=APB CSR read status; expected=FIFO_STATUS.count=3, full=0, empty=0, almost flags per threshold config.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC13
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: FIFO_STATUS.count=3, full=0, empty=0, almost flags per threshold config
- SSOT refs: test_requirements.scenarios.SC13

### RTL-0263: Keep RTL observable for scenario SC14

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC14
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC14.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC14; name=APB CSR write config; expected=almost_full_o and almost_empty_o reflect updated thresholds.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC14
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: almost_full_o and almost_empty_o reflect updated thresholds
- SSOT refs: test_requirements.scenarios.SC14

### RTL-0264: Keep RTL observable for scenario SC15

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC15
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC15.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC15; name=APB CSR flush; expected=FIFO flushed; pointers cleared; FIFO_STATUS reflects empty state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC15
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: FIFO flushed; pointers cleared; FIFO_STATUS reflects empty state
- SSOT refs: test_requirements.scenarios.SC15

### RTL-0265: Keep RTL observable for scenario SC16

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC16
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC16.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC16; name=APB error response; expected=pslverr=1; prdata=0 for reads; no FIFO state change.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC16
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: pslverr=1; prdata=0 for reads; no FIFO state change
- SSOT refs: test_requirements.scenarios.SC16

### RTL-0266: Keep RTL observable for scenario SC17

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC17
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC17.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC17; name=Wrap-around pointer; expected=Pointers wrap correctly; data integrity maintained; count accurate.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC17
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Pointers wrap correctly; data integrity maintained; count accurate
- SSOT refs: test_requirements.scenarios.SC17

### RTL-0267: Keep RTL observable for scenario SC18

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC18
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC18.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC18; name=Output register mode; expected=rd_data_o valid 1 cycle after rd_en_i acceptance; not combinationally.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC18
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: rd_data_o valid 1 cycle after rd_en_i acceptance; not combinationally
- SSOT refs: test_requirements.scenarios.SC18

### RTL-0268: Keep RTL observable for scenario SC19

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC19
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC19.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC19; name=Reset behavior; expected=All pointers/count cleared; flags reflect empty; rd_data_o undefined.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC19
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: All pointers/count cleared; flags reflect empty; rd_data_o undefined
- SSOT refs: test_requirements.scenarios.SC19

### RTL-0269: Keep RTL observable for scenario SC20

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC20
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC20.
Owner: fifo_sync in rtl/fifo_sync.sv via test_requirements.
SSOT item context: id=SC20; name=Reset deassertion; expected=Push accepted normally; count=1; no glitch on flags.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC20
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Downstream checker compares RTL-observed behavior against expected result: Push accepted normally; count=1; no glitch on flags
- SSOT refs: test_requirements.scenarios.SC20
