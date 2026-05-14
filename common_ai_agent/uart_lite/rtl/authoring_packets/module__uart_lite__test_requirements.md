# RTL Authoring Packet: module__uart_lite__test_requirements

- Kind: module
- Owner module: uart_lite
- Owner file: rtl/uart_lite.sv
- Task count: 17
- Required tasks: 17

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
- Module slice: 7/8 section=test_requirements task_limit=48
- Slice rule: Owner module uart_lite is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])
  - uart_lite_core.tx_o <= tx (integration.connections[3])
  - uart_lite_core.rx_i <= rx (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0270: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC1; name=TX single byte no parity 1 stop; expected=tx line shows start=0, DATA_WIDTH data bits LSB-first, 1 stop=1 bit. STAT.tx_empty=1 after frame. bytes_tx increments..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: tx line shows start=0, DATA_WIDTH data bits LSB-first, 1 stop=1 bit. STAT.tx_empty=1 after frame. bytes_tx increments.
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0271: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC2; name=RX single byte no parity 1 stop; expected=Byte pushed to RX FIFO. RXDATA reads correct byte. bytes_rx increments. No error flags..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Byte pushed to RX FIFO. RXDATA reads correct byte. bytes_rx increments. No error flags.
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0272: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC3; name=TX with even parity; expected=Parity bit after data: 0 (even number of 1s: 4 in 0xA5). tx shows start, 8 data, parity=0, 1 stop..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Parity bit after data: 0 (even number of 1s: 4 in 0xA5). tx shows start, 8 data, parity=0, 1 stop.
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0273: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC4; name=RX with odd parity match; expected=Byte 0xA5 pushed to RX FIFO. No parity_err. parities_errored unchanged..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Byte 0xA5 pushed to RX FIFO. No parity_err. parities_errored unchanged.
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0274: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC5; name=RX parity error; expected=parity_err sticky flag set. Byte still pushed to RX FIFO. parities_errored increments..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: parity_err sticky flag set. Byte still pushed to RX FIFO. parities_errored increments.
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0275: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC6; name=RX framing error; expected=frame_err sticky flag set. Byte pushed to RX FIFO. frames_errored increments..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: frame_err sticky flag set. Byte pushed to RX FIFO. frames_errored increments.
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0276: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC7; name=RX overrun; expected=17th byte discarded. overrun_err sticky flag set. RX FIFO still has 16 bytes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: 17th byte discarded. overrun_err sticky flag set. RX FIFO still has 16 bytes.
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0277: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC8; name=TX underrun; expected=No underrun during normal operation. To trigger underrun: disable TX FIFO write while FSM mid-frame (not directly pos....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: No underrun during normal operation. To trigger underrun: disable TX FIFO write while FSM mid-frame (not directly pos...
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0278: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC9; name=Loopback mode; expected=Transmitted bytes appear in RX FIFO. External rx line ignored. TX and RX data match..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Transmitted bytes appear in RX FIFO. External rx line ignored. TX and RX data match.
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0279: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC10; name=Break send; expected=tx line held low for at least one full frame duration. break_send self-clears to 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: tx line held low for at least one full frame duration. break_send self-clears to 0.
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0280: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC11; name=2 stop bits TX/RX; expected=TX sends 2 stop bits. RX accepts 2 stop bits..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: TX sends 2 stop bits. RX accepts 2 stop bits.
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0281: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC12; name=Interrupts — tx_empty; expected=INTPEND.tx_empty_pend asserts when TX FIFO goes empty. uart_irq asserts. Write 1 to INTPEND.tx_empty_pend clears it; ....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: INTPEND.tx_empty_pend asserts when TX FIFO goes empty. uart_irq asserts. Write 1 to INTPEND.tx_empty_pend clears it; ...
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0282: Keep RTL observable for scenario SC13

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC13
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC13.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC13; name=Interrupts — rx_not_empty + clear via W1C; expected=INTPEND.rx_not_empty_pend asserts. uart_irq asserts. Software W1C clears pend..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC13
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: INTPEND.rx_not_empty_pend asserts. uart_irq asserts. Software W1C clears pend.
- SSOT refs: test_requirements.scenarios.SC13

### RTL-0283: Keep RTL observable for scenario SC14

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC14
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC14.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC14; name=DATA_WIDTH=5; expected=TX sends 5 data bits. RX receives 5 data bits. Upper bits in TXDATA ignored, RXDATA zero-filled above bit 4..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC14
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: TX sends 5 data bits. RX receives 5 data bits. Upper bits in TXDATA ignored, RXDATA zero-filled above bit 4.
- SSOT refs: test_requirements.scenarios.SC14

### RTL-0284: Keep RTL observable for scenario SC15

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC15
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC15.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC15; name=FIFO full/empty flags; expected=STAT.tx_full, tx_empty, rx_full, rx_empty track FIFO levels correctly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC15
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: STAT.tx_full, tx_empty, rx_full, rx_empty track FIFO levels correctly.
- SSOT refs: test_requirements.scenarios.SC15

### RTL-0285: Keep RTL observable for scenario SC16

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC16
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC16.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC16; name=Spurious start bit rejection; expected=RX FSM returns to RX_IDLE; no byte captured; no error flag..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC16
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: RX FSM returns to RX_IDLE; no byte captured; no error flag.
- SSOT refs: test_requirements.scenarios.SC16

### RTL-0286: Keep RTL observable for scenario SC17

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC17
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC17.
Owner: uart_lite in rtl/uart_lite.sv via test_requirements.
SSOT item context: id=SC17; name=Baud rate change mid-operation; expected=Current frame completes at old rate. Next frame uses new rate..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC17
  - Primary implementation evidence is in rtl/uart_lite.sv
  - Downstream checker compares RTL-observed behavior against expected result: Current frame completes at old rate. Next frame uses new rate.
- SSOT refs: test_requirements.scenarios.SC17
