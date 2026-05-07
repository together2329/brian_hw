Repair the SSOT YAML artifact for atciic100_real. This is repair attempt 2.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "atciic100_real/yaml/atciic100_real.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}
  ]
}

Repair rules:
- Do not use a fixed IP template or hardcoded workaround.
- Preserve product semantics from the requirement and current SSOT wherever they are valid.
- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.
- Fix the concrete parse/validator failures below, and also check for sibling contract defects.
- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh atciic100_real`.
- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.

Failure summary:
human_gate: SSOT disk validator failed: [check_ssot_disk] FAIL: atciic100_real/yaml/atciic100_real.ssot.yaml failed YAML/model validation

Blocker artifact:


Validator log:
cmd: bash /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow/ssot-gen/scripts/check_ssot_disk.sh atciic100_real
cwd: /Users/brian/Desktop/Project/brian_hw/common_ai_agent
returncode: 1
stdout:
[check_ssot_disk] FAIL: atciic100_real/yaml/atciic100_real.ssot.yaml failed YAML/model validation
  test_requirements.scoreboard_checks is required


Requirements:
# ATCIIC100-class IIC controller — requirement for ssot-gen

## Goal
Generate a production-grade YAML SSOT for an I2C / IIC controller IP at the
quality and scope of the Andes ATCIIC100 reference RTL located at:

  /Users/brian/Desktop/andes/atciic100/hdl  (5 modules, 1409 LoC, 2016 release)

This SSOT will be consumed by /golden-all and rtl-gen workflows to produce
verification harness + RTL skeleton. Match the Andes ATCIIC100 reference
behaviorally; the SSOT does not need to be byte-identical, but every reference
module + interface + register must be represented.

## Interface (from Andes reference top module port list)
- APB slave: paddr[5:2], pclk, presetn, psel, penable, pwrite, pwdata[31:0], prdata[31:0]
- I2C bus: scl_i, sda_i, scl_o, sda_o (open-drain master + slave)
- DMA: dma_req, dma_ack
- Interrupt: i2c_int (single output)

## Reference modules to mirror (sub_modules in SSOT)
1. atciic100_apbslv  — APB slave + register file (CFG, INT_EN, INT_ST, ADDR, DATA, CMD, SETUP, TPM, TSP, ID, REV, HWCFG)
2. atciic100_ctrl    — I2C protocol FSM (IDLE/START/ADDR/DAT/STOP/ARBLOST), master+slave roles, byte transfer
3. atciic100_fifo    — bidirectional byte FIFO (depth 2/4/8/16 configurable via FIFO_DEPTH)
4. atciic100_gsf     — glitch-suppression filter (filter pulses < t_sp)

## Reference parameters
- DATA_WIDTH = 8
- FIFO_DEPTH (parameter): 2/4/8/16
- INDEX_WIDTH = log2(FIFO_DEPTH)
- ID = 16'h0202, REV_MAJOR = 12'h100, REV_MINOR = 4'h2

## Required SSOT sections (must all be substantive)
- top_module, parameters, clocks, resets
- io_list (APB + I2C + DMA + IRQ as 4 distinct interfaces)
- features (master/slave, multi-master arb, gen-call, DMA, glitch suppress)
- function_model.transactions (at least 9): reset, csr_read, csr_write,
  master_send, master_recv, slave_send, slave_recv, general_call, dma_request
- function_model.state_variables (cmd, cfg, int_en, int_st, setup, addr, datacnt,
  phase, fifo_count, master, trans, arb_lost)
- function_model.invariants (≥3 — fifo bound, phase-trans linkage, arb-lost timing)
- cycle_model.handshake_rules (APB setup/access, I2C start/stop, I2C byte,
  glitch suppress, DMA req/ack)
- cycle_model.ordering (start→addr→data→stop; arb-lose terminates)
- cycle_model.arbitration (multi-master open-drain)
- cycle_model.backpressure (fifo full → SCL stretch; fifo empty → STOP after current)
- registers.register_list (full register map, offsets per Andes layout)
- memory.instances (tx_rx_fifo)
- interrupts (i2c_int from any int_st bit & int_en)
- fsm.iic_phase (states + transitions per Andes ctrl module)
- error_handling.error_sources (ack_neg, arb_lose, fifo_overrun, dma_timeout, glitch_inject)
- debug_observability (waveform_must_probe with all top ports + phase + datacnt + fifo_count)
- security (assets/threats can be empty for this IP)
- test_requirements.scenarios (≥10 scenarios: reset, APB R/W, master TX/RX,
  slave TX/RX, gen-call, arb-lose, fifo-full, DMA flow, glitch suppression)
- test_requirements.coverage_goals.planned_bins (≥7 bins)
- synthesis.ppa_targets (frequency_mhz_min: 100; null area/power until human locks)
- quality_gates (ppa.fmax_target_mhz=100; coverage.fl_bin_hit_min=100)
- traceability (reference_rtl path, reference_modules list, reference_loc)

## Cardinal rules for this SSOT
- Match Andes naming where natural (apbslv/ctrl/fifo/gsf in sub_modules).
- Do NOT fabricate timing values that aren't in the reference (t_high/t_low/
  t_hddat/t_sudat/t_sp register fields exist; their default cycle counts are
  awaiting-human-lock pending human approval — leave as parameters).
- target_scale: production (already locked by this requirement).
- Use ownership: manifest for all 4 sub_modules.
- Generation order recorded in generation_flow.golden_emit_order.

## Output
- Single YAML file at `atciic100_real/yaml/atciic100_real.ssot.yaml`.
- Pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh atciic100_real`.
- `[SSOT HANDOFF]` block at the end pointing to rtl-gen as next stage.


# === ANDES DATASHEET KEY PAGES (registers + operating modes) ===
### PDF p6
AndeShape™ ATCIIC100 Data Sheet
List of Tables
TABLE 1. ATCIIC100 SIGNAL DESCRIPTION ................................................................................................................................. 4
TABLE 2. ATCIIC100 REGISTERS SUMMARY ................................................................................................................................ 5
TABLE 3. ID AND REVISION REGISTER .......................................................................................................................................... 6
TABLE 4. CONFIGURATION REGISTER ........................................................................................................................................... 7
TABLE 5. INTERRUPT ENABLE REGISTER ...................................................................................................................................... 7
TABLE 6. STATUS REGISTER .......................................................................................................................................................... 9
TABLE 7. ADDRESS REGISTER ....................................................................................................................................................... 11
TABLE 8. DATA REGISTER ............................................................................................................................................................. 11
TABLE 9. CONTROL REGISTER ..................................................................................................................................................... 12
TABLE 10. COMMAND REGISTER ................................................................................................................................................. 13
TABLE 11. CONTROLLER SETTING REGISTER ............................................................................................................................... 14
TABLE 12. TIMING PARAMETERS FOR SPIKE SUPPRESSION ........................................................................................................ 19
TABLE 13. TIMING PARAMETERS FOR THE DATA SETUP TIME .................................................................................................... 19
TABLE 14. TIMING PARAMETERS FOR THE DATA HOLD TIME .................................................................................................... 20
TABLE 15. TIMING PARAMETERS FOR THE SCL CLOCK ............................................................................................................... 20
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page v
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p7
AndeShape™ ATCIIC100 Data Sheet
List of Figures
FIGURE 1. ATCIIC100 BLOCK DIAGRAM ...................................................................................................................................... 1
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page vi
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p8
AndeShape™ ATCIIC100 Data Sheet
Typographical Convention Index
Document Element Font Font Style Size Color
Normal text Georgia Normal 12 Black
Command line, Lucida Console Normal 11 Indigo
source code or
file paths
VARIABLES OR LUCIDA CONSOLE BOLD + ALL-CAPS 11 INDIGO
PARAMETERS IN
COMMAND LINE,
SOURCE CODE OR
FILE PATHS
Note or warning Georgia Normal 12 Red
Hyperlink Georgia Underlined 12 Blue
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page vii
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p9
AndeShape™ ATCIIC100 Data Sheet
1. Introduction
The ATCIIC100 controller is an I2C (Inter-Integrated Circuit) master/slave controller.
1.1. Features
 Support AMBA 2.0 APB bus
 Support Standard-mode (100 Kb/s), Fast-mode (400 Kb/s) and Fast-mode Plus (1 Mb/s)
protocols
 Programmable Master/Slave mode
 Support 7-bit and 10-bit addressing mode
 Support general call address
 Auto clock stretching
 Programmable clock/data timing
 Support direct memory access (DMA)
1.2. Block Diagram
SDA input
Glitch
APB Bus
Suppression
Register Control logics/ SCL input
Filter
File State machines
SDA output
Interrupt
SCL output
DMA DMA
acknowledg request
Figure 1. ATCIIC100 Block Diagram
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 1
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p10
AndeShape™ ATCIIC100 Data Sheet
1.3. Function Description
The ATCIIC100 controller can act as either an I2C master device or an I2C slave device,
depending on the control register settings.
1.3.1. I2C Master
As an I2C master, the controller provides an efficient way to initiate I2C transactions. Every
transaction can be delineated by four phases: Start, Address, Data and Stop. At the Start phase, a
START condition is generated. At the Address phase, an address is sent. At the Data phase, one
or more data bytes are transferred. At the Stop phase, a STOP condition is generated. The
existence of each phase can be controlled independently.
1.3.2. I2C Slave
As an I2C slave, the controller is addressed when the address byte of an I2C transaction matches
the Address Register. An Address Hit interrupt can be generated for the software to prepare for
the subsequent operations.
1.3.3. General Call Address
The General Call Address is a special address to address all slave devices on the I2C-bus. The
ATCIIC100 controller at the slave mode will respond with an ACK to the general call address and
set the GenCall field of the Status Register.
1.3.4. Auto Clock Stretch
The ATCIIC100 can automatically pause bus transactions by stretching clocks on the I2C-bus
when the software is not ready for the next byte of data or when the FIFO is full. Auto Clock
Stretch is supported at both the master mode and the slave mode.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 2
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p11
AndeShape™ ATCIIC100 Data Sheet
1.3.5. Auto-ACK
With Auto-ACK, the ATCIIC100 automatically generates proper acknowledgements for each byte
received. Every received byte will be responded with an ACK, except for the last byte, which
should be responded with a NACK according to the I2C-bus protocol. On the other hand, if the
software needs to determine each byte’s acknowledgement status, Auto-ACK can be turned off
by enabling the Byte Receive Interrupt.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 3
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p12
AndeShape™ ATCIIC100 Data Sheet
2.Signal Description
Table 1 shows the input/output (I/O) signal description of ATCIIC100.
Table 1. ATCIIC100 Signal Description
Name I/O Type Description
AMBA APB signals
pclk I AMBA APB clock
presetn I AMBA APB reset signal; active low
psel I AMBA APB slave select signal from the APB decoder
penable I AMBA APB enable signal
pwrite I AMBA APB transfer direction signal
This signal indicates a write access when driven as HIGH and a
read access when driv
... <truncated 16934 chars>

Current SSOT YAML:
# =============================================================================
# SSOT for atciic100_real — Andes ATCIIC100 I2C Controller
# =============================================================================

top_module:
  name: "atciic100_real"
  version: "1.0"
  type: "peripheral"
  description: "I2C Master/Slave Controller with APB interface, DMA, and glitch suppression."
  reference_spec: "Andes ATCIIC100 Data Sheet DS091_V1.3"
  target:
    technology: "generic"
    clock_freq_mhz: 40
    area_um2: null
    power_mw: null

sub_modules:
  - name: "atciic100_apbslv"
    file: "rtl/atciic100_apbslv.v"
    ownership: "manifest"
    ssot_gen: true
    implements: ["io_list.interfaces.apb_slave", "registers"]
    source_sections: ["io_list", "registers"]
    register_refs: ["registers.register_list"]
    connections:
      - { module: "atciic100_ctrl", port: "cmd", signal: "cmd_reg" }
      - { module: "atciic100_ctrl", port: "setup", signal: "setup_reg" }
      - { module: "atciic100_fifo", port: "data_in", signal: "pwdata" }
    description: "APB Slave Interface and Register File"

  - name: "atciic100_ctrl"
    file: "rtl/atciic100_ctrl.v"
    ownership: "manifest"
    ssot_gen: false
    implements: ["function_model", "cycle_model", "fsm"]
    source_sections: ["function_model", "cycle_model", "fsm"]
    function_model_refs: ["function_model.transactions"]
    connections:
      - { module: "atciic100_apbslv", port: "cmd_reg", signal: "cmd" }
      - { module: "atciic100_fifo", port: "data_out", signal: "tx_data" }
      - { module: "atciic100_gsf", port: "scl_in", signal: "scl_filtered" }
    description: "I2C Protocol FSM and Datapath"

  - name: "atciic100_fifo"
    file: "rtl/atciic100_fifo.v"
    ownership: "manifest"
    ssot_gen: true
    implements: ["memory.instances"]
    source_sections: ["memory"]
    connections:
      - { module: "atciic100_apbslv", port: "data_in", signal: "pwdata" }
      - { module: "atciic100_ctrl", port: "data_out", signal: "rx_data" }
    description: "Bidirectional Data FIFO"

  - name: "atciic100_gsf"
    file: "rtl/atciic100_gsf.v"
    ownership: "manifest"
    ssot_gen: true
    implements: ["features.glitch_suppression"]
    source_sections: ["features"]
    connections:
      - { module: "atciic100_ctrl", port: "scl_i", signal: "scl_filtered" }
    description: "Glitch Suppression Filter"

decomposition:
  units:
    - { id: "apb_reg", kind: "control", source_refs: ["registers"], rtl_candidates: ["atciic100_apbslv"] }
    - { id: "fsm", kind: "control", source_refs: ["fsm"], rtl_candidates: ["atciic100_ctrl"] }
    - { id: "buffer", kind: "datapath", source_refs: ["memory"], rtl_candidates: ["atciic100_fifo"] }

parameters:
  - { name: "DATA_WIDTH", default: 8, type: int, description: "Data width (fixed 8-bit)", drives: ["atciic100_fifo.v"] }
  - { name: "FIFO_DEPTH", default: 8, type: int, description: "FIFO depth (2, 4, 8, 16)", drives: ["atciic100_fifo.v"] }
  - { name: "INDEX_WIDTH", default: 3, type: int, description: "FIFO index width log2(FIFO_DEPTH)", drives: ["atciic100_fifo.v"] }
  - { name: "TP_AUTOACK", default: 1, type: int, description: "Auto-ACK support threshold parameter", drives: ["atciic100_ctrl.v"] }

io_list:
  clock_domains:
    - name: "pclk"
      frequency_mhz: 40
      description: "APB Clock"
      ports:
        - { name: "pclk", width: 1, direction: "input", description: "APB Clock" }
  resets:
    - name: "presetn"
      polarity: "active_low"
      sync_async: "async_assert_sync_deassert"
      description: "APB Reset"
      ports:
        - { name: "presetn", width: 1, direction: "input", description: "APB Reset Active-Low" }
  interfaces:
    - name: "apb_slave"
      type: "AMBA_APB"
      role: "slave"
      description: "APB Register Interface"
      ports:
        - { name: "psel", width: 1, direction: "input", description: "APB Select" }
        - { name: "penable", width: 1, direction: "input", description: "APB Enable" }
        - { name: "pwrite", width: 1, direction: "input", description: "APB Write" }
        - { name: "paddr", width: 4, direction: "input", description: "APB Address (paddr[5:2])" }
        - { name: "pwdata", width: 32, direction: "input", description: "APB Write Data" }
        - { name: "prdata", width: 32, direction: "output", description: "APB Read Data" }
    - name: "i2c_bus"
      type: "I2C"
      role: "master_slave"
      description: "I2C Serial Interface"
      ports:
        - { name: "scl_i", width: 1, direction: "input", description: "I2C Clock Input" }
        - { name: "sda_i", width: 1, direction: "input", description: "I2C Data Input" }
        - { name: "scl_o", width: 1, direction: "output", description: "I2C Clock Output (Open Drain)" }
        - { name: "sda_o", width: 1, direction: "output", description: "I2C Data Output (Open Drain)" }
    - name: "dma_if"
      type: "DMA_REQ_ACK"
      role: "master"
      description: "DMA Interface"
      ports:
        - { name: "i2c_req", width: 1, direction: "output", description: "DMA Request" }
        - { name: "i2c_ack", width: 1, direction: "input", description: "DMA Acknowledge" }
    - name: "interrupt"
      type: "IRQ"
      role: "master"
      description: "Interrupt Output"
      ports:
        - { name: "i2c_int", width: 1, direction: "output", description: "Interrupt" }

features:
  - name: "Master Transmit/Receive"
    trigger: "CMD=0x1 with Master=1 in SETUP"
    datapath: "APB->FIFO->Shift->SDA (TX) or SDA->Shift->FIFO->APB (RX)"
    control: "Phase_start, Phase_addr, Phase_data, Phase_stop in CTRL reg"
    output: "I2C Bus Transaction"
  - name: "Slave Transmit/Receive"
    trigger: "Address match on bus"
    datapath: "SDA->Shift->FIFO (RX) or FIFO->Shift->SDA (TX)"
    control: "AddrHit interrupt triggers software response"
    output: "Ack/Nack response"
  - name: "Multi-Master Arbitration"
    trigger: "SDA low when master drives high"
    datapath: "Compare SDA_O vs SDA_I on SCL rising edge"
    control: "ArbLose status bit set, FSM resets to IDLE"
    output: "Arbitration Lost Status"
  - name: "General Call"
    trigger: "Address byte = 0x00 in slave mode"
    datapath: "Standard receive path"
    control: "GenCall status bit set"
    output: "Ack response to address 0x00"
  - name: "Glitch Suppression"
    trigger: "SCL_i or SDA_i pulse width < T_SP * t_pclk"
    datapath: "Digital filter on inputs"
    control: "Continuous"
    output: "Filtered SCL/SDA to internal logic"
  - name: "Auto Clock Stretching"
    trigger: "FIFO Full (RX) or Empty (TX)"
    datapath: "Hold SCL low"
    control: "Hardware automatic"
    output: "Stalled bus clock"

dataflow:
  master_tx:
    source: "APB Master (CPU)"
    burst: "Single Byte (APB writes) or DMA"
    buffer: "FIFO"
    sequence: "APB -> DATA Reg -> FIFO -> Shift Reg -> SDA_O"
  master_rx:
    source: "I2C Bus (SDA_I)"
    burst: "Single Byte"
    buffer: "FIFO"
    sequence: "SDA_I -> Shift Reg -> FIFO -> DATA Reg -> APB"
  slave_tx:
    source: "APB Master (CPU)"
    burst: "Single Byte"
    buffer: "FIFO"
    sequence: "APB -> DATA Reg -> FIFO -> Shift Reg -> SDA_O"
  slave_rx:
    source: "I2C Bus (SDA_I)"
    burst: "Single Byte"
    buffer: "FIFO"
    sequence: "SDA_I -> Shift Reg -> FIFO -> DATA Reg -> APB"

function_model:
  purpose: "Executable behavioral contract for atciic100_real."
  state_variables:
    - { name: "cmd", source: "registers.CMD", reset: 0, description: "Current command" }
    - { name: "cfg", source: "registers.CFG", reset: 0, description: "Global config" }
    - { name: "int_en", source: "registers.INT_EN", reset: 0, description: "Interrupt enables" }
    - { name: "int_st", source: "registers.INT_ST", reset: 0x1, description: "Interrupt status (FIFOEmpty=1)" }
    - { name: "setup", source: "registers.SETUP", reset: 0, description: "Timing/Setup config" }
    - { name: "addr", source: "registers.ADDR", reset: 0, description: "Target/Own address" }
    - { name: "ctrl", source: "registers.CTRL", reset: 0x1F00, description: "Phase/Direction/Count" }
    - { name: "phase", source: "fsm.iic_phase", reset: "IDLE", description: "Current FSM phase" }
    - { name: "fifo_count", source: "memory.instances[0].count", reset: 0, description: "Current FIFO depth" }
    - { name: "master", source: "setup.Master", reset: 0, description: "Master/Slave mode flag" }
    - { name: "trans", source: "ctrl.Dir", reset: 0, description: "Transmitter/Receiver flag" }
    - { name: "arb_lost", source: "int_st.ArbLose", reset: 0, description: "Arbitration lost flag" }
    - { name: "datacnt", source: "ctrl.DataCnt", reset: 0, description: "Remaining byte count" }
  transactions:
    - id: "FM1"
      name: "reset"
      preconditions: ["presetn == 0"]
      inputs: []
      outputs: ["All registers reset to default", "FIFO cleared", "FSM=IDLE"]
      side_effects: ["i2c_int goes low", "Bus lines released (open drain)"]
      error_cases: []
    - id: "FM2"
      name: "csr_read"
      preconditions: ["psel==1 && penable==1 && pwrite==0"]
      inputs: ["paddr"]
      outputs: ["prdata = RegisterFile[paddr]"]
      side_effects: ["APB read completes in 2 cycles (setup then access phase)", "INT_ST read does not clear W1C bits (only write-1 clears)"]
      error_cases: []
    - id: "FM3"
      name: "csr_write"
      preconditions: ["psel==1 && penable==1 && pwrite==1"]
      inputs: ["paddr", "pwdata"]
      outputs: ["RegisterFile[paddr] updated"]
      side_effects: ["CMD triggers action if valid", "SETUP updates timing"]
      error_cases: []
    - id: "FM4"
      name: "master_send"
      preconditions: ["master==1", "trans==0", "cmd==1", "fifo_count > 0"]
      inputs: ["addr", "data"]
      outputs: ["SCL/SDA signals driven for Start->Addr->Data->Stop", "Target slave ACK/NACK"]
      side_effects: ["datacnt decrements", "ByteTrans interrupt", "Cmpl interrupt"]
      error_cases:
        - { condition: "No ACK from slave", result: "int_st.ACK = 0, check NACK" }
        - { condition: "Arbitration Lost", result: "arb_lost=1, STOP driving bus" }
    - id: "FM5"
      name: "master_recv"
      preconditions: ["master==1", "trans==1", "cmd==1"]
      inputs: ["addr"]
      outputs: ["SCL/SDA signals driven for Start->Addr->Data->Stop", "Data pushed to FIFO"]
      side_effects: ["datacnt decrements", "ByteRecv interrupt", "FIFO status updates"]
      error_cases:
        - { condition: "Slave NACK on address", result: "Transaction aborted, Stop sent, ACK status updated" }
    - id: "FM6"
      name: "slave_send"
      preconditions: ["master==0", "trans==1", "addr matched"]
      inputs: ["bus_clk", "bus_data"]
      outputs: ["Data from FIFO shifted out"]
      side_effects: ["ByteTrans interrupt"]
      error_cases:
        - { condition: "FIFO Empty", result: "Clock Stretching" }
    - id: "FM7"
      name: "slave_recv"
      preconditions: ["master==0", "trans==0", "addr matched"]
      inputs: ["bus_clk", "bus_data"]
      outputs: ["Data pushed to FIFO"]
      side_effects: ["ByteRecv interrupt"]
      error_cases:
        - { condition: "FIFO Full", result: "Clock Stretching or Overrun" }
    - id: "FM8"
      name: "general_call"
      preconditions: ["master==0", "Address byte == 0x00"]
      inputs: ["bus_clk", "bus_data"]
      outputs: ["ACK response", "int_st.GenCall = 1"]
      side_effects: ["AddrHit interrupt"]
      error_cases:
        - { condition: "Controller disabled (IICEn=0)", result: "No ACK, general call ignored" }
    - id: "FM9"
      name: "dma_request"
      preconditions: ["setup.DMAEn == 1", "(trans==1 && fifo_count > 0) || (trans==0 && fifo_count < FIFO_DEPTH)"]
      inputs: ["DMA Enable"]
      outputs: ["i2c_req = 1"]
      side_effects: ["DMA transfers data between FIFO and memory via external DMA controller"]
      error_cases:
        - { condition: "DMA acknowledge timeout", result: "FIFO overrun or underrun may occur; DMA disabled until re-enabled" }
  invariants:
    - "FIFO count never exceeds FIFO_DEPTH parameter."
    - "Phase transitions follow IDLE->START->ADDR->DAT->STOP strictly, unless ArbLose occurs."
    - "Arbitration Lost (ArbLose) terminates transmission immediately and releases bus."

# ---------------------------------------------------------------------------
# Cycle Model
# ---------------------------------------------------------------------------
cycle_model:
  purpose: "Cycle/handshake contract for atciic100_real."
  clock: "pclk"
  reset:
    assertion: "presetn low clears state"
    deassertion: "State usable on next edge"
  latency:
    register_access: { min_cycles: 2, max_cycles: 2, description: "Setup/Access phases" }
    i2c_byte: { min_cycles: 9, max_cycles: null, description: "8 data bits + 1 ACK, scaled by T_SCLHi" }
  handshake_rules:
    - { signal: "psel/penable", rule: "APB protocol requires setup then access phase." }
    - { signal: "scl_o/sda_o", rule: "Open drain; drive low or float high." }
    - { signal: "i2c_req", rule: "Hold high until i2c_ack received." }
    - { signal: "scl_i filtering", rule: "Ignore pulses < T_SP * t_pclk." }
  pipeline:
    - { stage: "IDLE", cycle: 0, action: "Wait for CMD or Address Match" }
    - { stage: "START", cycle: 1, action: "Generate Start Condition (SDA H->L while SCL High)" }
    - { stage: "ADDR", cycle: "2..9", action: "Shift out/in Address + R/W bit" }
    - { stage: "DAT", cycle: "10..N", action: "Shift Data Bytes" }
    - { stage: "STOP", cycle: "N+1", action: "Generate Stop Condition (SDA L->H while SCL High)" }
  ordering:
    - "Start must precede Addr."
    - "Addr must precede Data."
    - "Stop must follow Data or ArbLose."
  arbitration:
    - "Sample SDA_I on SCL rising edge. If SDA_I=0 but SDA_O=1, ArbLose."
  backpressure:
    - "FIFO Full holds SCL Low (Clock Stretching)."

# ---------------------------------------------------------------------------
# Clock & Reset
# ---------------------------------------------------------------------------
clock_reset_domains:
  domains:
    - { name: "pclk", frequency_mhz: 40, description: "APB Clock" }
  reset_scheme:
    signal: "presetn"
    polarity: "active_low"
    type: "async_assert_sync_deassert"

cdc_requirements:
  crossings: []
  synchronizers: []
  note: "Single clock domain."

rdc_requirements:
  crossings: []
  synchronizers: []
  note: "No reset domain crossings."

# ---------------------------------------------------------------------------
# Registers
# ---------------------------------------------------------------------------
registers:
  config:
    register_width: 32
    addr_width: 6
    byte_addressable: true
  register_list:
    - name: "ID"
      offset: 0x00
      width: 32
      access: "ro"
      reset: 0x00000202
      category: "info"
      description: "Device ID"
      fields:
        - { name: "ID", bits: [15, 0], access: "ro", reset: 0x0202, description: "0x0202" }
    - name: "REV"
      offset: 0x04
      width: 32
      access: "ro"
      reset: 0x00001002
      category: "info"
      description: "Revision ID"
      fields:
        - { name: "MAJOR", bits: [31, 20], access: "ro", reset: 0x100, description: "Major Rev" }
        - { name: "MINOR", bits: [19, 16], access: "ro", reset: 0x2, description: "Minor Rev" }
    - name: "CFG"
      offset: 0x08
      width: 32
      access: "ro"
      reset: 0x00000000
      category: "info"
      description: "Hardware Config"
      fields:
        - { name: "FIFO_DEPTH", bits: [3, 0], access: "ro", reset: 0x8, description: "Log2(FIFO Depth)" }
    - name: "INT_EN"
      offset: 0x0C
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "interrupt"
      description: "Interrupt Enable"
      fields:
        - { name: "EN", bits: [15, 0], access: "rw", reset: 0x0, description: "Enable bits matching INT_ST" }
    - name: "INT_ST"
      offset: 0x10
      width: 32
      access: "rw1c"
      reset: 0x00000001
      category: "status"
      description: "Interrupt Status"
      fields:
        - { name: "FIFOEmpty", bits: [0, 0], access: "ro", reset: 0x1, description: "FIFO Empty" }
        - { name: "FIFOFull", bits: [1, 1], access: "ro", reset: 0x0, description: "FIFO Full" }
        - { name: "FIFOHalf", bits: [2, 2], access: "ro", reset: 0x0, description: "FIFO Half" }
        - { name: "AddrHit", bits: [3, 3], access: "rw1c", reset: 0x0, description: "Address Hit" }
        - { name: "ArbLose", bits: [4, 4], access: "rw1c", reset: 0x0, description: "Arbitration Lost" }
        - { name: "Stop", bits: [5, 5], access: "rw1c", reset: 0x0, description: "Stop Detected" }
        - { name: "Start", bits: [6, 6], access: "rw1c", reset: 0x0, description: "Start Detected" }
        - { name: "ByteTrans", bits: [7, 7], access: "rw1c", reset: 0x0, description: "Byte Transmitted" }
        - { name: "ByteRecv", bits: [8, 8], access: "rw1c", reset: 0x0, description: "Byte Received" }
        - { name: "Cmpl", bits: [9, 9], access: "rw1c", reset: 0x0, description: "Completion" }
        - { name: "ACK", bits: [10, 10], access: "ro", reset: 0x0, description: "Last ACK Value" }
        - { name: "BusBusy", bits: [11, 11], access: "ro", reset: 0x0, description: "Bus Busy" }
        - { name: "GenCall", bits: [12, 12], access: "ro", reset: 0x0, description: "General Call" }
        - { name: "LineSCL", bits: [13, 13], access: "ro", reset: 0x0, description: "SCL Line State" }
        - { name: "LineSDA", bits: [14, 14], access: "ro", reset: 0x0, description: "SDA Line State" }
    - name: "ADDR"
      offset: 0x14
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "control"
      description: "I2C Address"
      fields:
        - { name: "Addr", bits: [9, 0], access: "rw", reset: 0x0, description: "Target/Self Address" }
    - name: "DATA"
      offset: 0x18
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "data"
      description: "Data FIFO Port"
      fields:
        - { name: "Data", bits: [7, 0], access: "rw", reset: 0x0, description: "FIFO Write/Read" }
    - name: "CMD"
      offset: 0x1C
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "control"
      description: "Command Register"
      fields:
        - { name: "CMD", bits: [2, 0], access: "rw", reset: 0x0, description: "0=None, 1=Issue TX, 2=ACK, 3=NACK, 4=Clear FIFO, 5=Reset" }
    - name: "CTRL"
      offset: 0x20
      width: 32
      access: "rw"
      reset: 0x00001F00
      category: "control"
      description: "Control Register"
      fields:
        - { name: "DataCnt", bits: [7, 0], access: "rw", reset: 0x0, description: "Data Byte Count (0=256)" }
        - { name: "Dir", bits: [8, 8], access: "rw", reset: 0x0, description: "Direction (0=TX, 1=RX)" }
        - { name: "Phase_stop", bits: [9, 9], access: "rw", reset: 0x1, description: "Enable Stop Phase" }
        - { name: "Phase_data", bits: [10, 10], access: "rw", reset: 0x1, description: "Enable Data Phase" }
        - { name: "Phase_addr", bits: [11, 11], access: "rw", reset: 0x1, description: "Enable Address Phase" }
        - { name: "Phase_start", bits: [12, 12], access: "rw", reset: 0x1, description: "Enable Start Phase" }
    - name: "SETUP"
      offset: 0x24
      width: 32
      access: "rw"
      reset: 0x00000000
      category: "control"
      description: "Setup Register"
      fields:
        - { name: "IICEn", bits: [0, 0], access: "rw", reset: 0x0, description: "Enable Controller" }
        - { name: "Addressing", bits: [1, 1], access: "rw", reset: 0x0, description: "0=7-bit, 1=10-bit" }
        - { name: "Master", bits: [2, 2], access: "rw", reset: 0x0, description: "0=Slave, 1=Master" }
        - { name: "DMAEn", bits: [3, 3], access: "rw", reset: 0x0, description: "Enable DMA" }
        - { name: "T_SCLHi", bits: [12, 4], access: "rw", reset: 0x10, description: "SCL High Count" }
        - { name: "T_SCLRatio", bits: [13, 13], access: "rw", reset: 0x1, description: "SCL Ratio" }
        - { name: "T_HDDAT", bits: [20, 16], access: "rw", reset: 0x5, description: "Hold Delay" }
        - { name: "T_SP", bits: [23, 21], access: "rw", reset: 0x1, description: "Spike Suppression" }
        - { name: "T_SUDAT", bits: [28, 24], access: "rw", reset: 0x5, description: "Setup Delay" }

memory:
  instances:
    - { name: "tx_rx_fifo", type: "fifo", depth: "FIFO_DEPTH", width: 8, read_ports: 1, write_ports: 1, latency: 0, description: "Bidirectional Data FIFO" }

interrupts:
  sources:
    - { name: "IRQ_COMB", bit: 0, type: "level", enable_reg: "INT_EN", status_reg: "INT_ST", clear: "W1C", description: "Combined Interrupt" }
  output:
    signal: "i2c_int"
    polarity: "active_high"
    type: "level"

fsm:
  iic_phase:
    states:
      - "IDLE"
      - "START"
      - "ADDR"
      - "DAT"
      - "STOP"
      - "ARBLOST"
    transitions:
      - { from: "IDLE", to: "START", condition: "cmd==1 && master==1 && Phase_start" }
      - { from: "IDLE", to: "ADDR", condition: "cmd==1 && master==1 && !Phase_start && Phase_addr" }
      - { from: "IDLE", to: "DAT", condition: "cmd==1 && master==1 && !Phase_start && !Phase_addr && Phase_data" }
      - { from: "START", to: "ADDR", condition: "Start sent" }
      - { from: "ADDR", to: "DAT", condition: "Addr sent and ACK received" }
      - { from: "ADDR", to: "STOP", condition: "Addr sent and NACK received" }
      - { from: "ADDR", to: "ARBLOST", condition: "Arbitration Lost" }
      - { from: "DAT", to: "STOP", condition: "DataCnt==0" }
      - { from: "DAT", to: "DAT", condition: "DataCnt>0" }
      - { from: "DAT", to: "ARBLOST", condition: "Arbitration Lost" }
      - { from: "STOP", to: "IDLE", condition: "Stop sent" }
      - { from: "ARBLOST", to: "IDLE", condition: "Immediate" }

timing:
  target_clocks:
    - { name: "pclk", freq_mhz: 40 }
  latency_budget:
    - { path: "APB_Write_to_FIFO", max_ns: 50 }
    - { path: "FIFO_to_SDA", max_ns: "T_SCLHi * 25" }

power:
  domains:
    - { name: "VDD", voltage: "1.8V", rails: ["Logic", "IO"] }
  power_states:
    - { name: "ON", description: "Active" }
    - { name: "OFF", description: "Power Gated" }

security:
  classification: "Internal"
  assets:
    - { name: "I2C_Data", type: "Data", confidentiality: "Low" }
  threat_model:
    - { threat: "Bus Interference", mitigation: "Glitch Filter" }

error_handling:
  error_sources:
    - { id: "ERR_ACK", source: "Slave NACK", effect: "Transaction stops" }
    - { id: "ERR_ARB", source: "Multi-Master Collision", effect: "ArbLost Status" }
    - { id: "ERR_FIFO", source: "Overrun/Underrun", effect: "Data Loss/Clocking Stretching" }
    - { id: "ERR_DMA_TIMEOUT", source: "DMA acknowledge not received", effect: "FIFO overrun or underrun" }
    - { id: "ERR_GLITCH_INJECT", source: "Injected glitch on SCL/SDA", effect: "Filtered by GSF if within T_SP" }
  propagation:
    - "Set Status Bits in INT_ST"
    - "Assert i2c_int if enabled"
  recovery:
    - "Software clears status bits"
    - "Issue CMD Reset (0x5)"

debug_observability:
  waveform_must_probe:
    - "scl_i"
    - "sda_i"
    - "scl_o"
    - "sda_o"
    - "i2c_int"
    - "phase"
    - "datacnt"
    - "fifo_count"
  trace_events:
    - { name: "I2C_START", description: "Start condition detected" }
    - { name: "I2C_STOP", description: "Stop condition detected" }

integration:
  bus_attachment:
    - { bus: "APB", role: "slave" }
  dependencies:
    - { name: "APB Bus", version: "AMBA 2.0" }

dft:
  scan_required: false
  controllability: "Full via APB registers"
  observability: "Full via status registers and interrupt"

synthesis:
  dialect: "verilog_2001"
  constraints:
    - { name: "pclk", type: "clock", period_ns: 25 }
  required_outputs:
    - "netlist"
    - "sdc"

coding_rules:
  verilog_style: "verilog_2001"
  conventions:
    - "Nonblocking assignments for sequential logic."
    - "Blocking for combinational."

reuse_modules: []

custom:
  note: "None"

dir_structure:
  template_dirs:
    rtl: "templates/rtl/"
    sim: "templates/sim/"
  output_dirs:
    rtl: "rtl/"
    sim: "sim/"
  yaml_dir: "yaml/"
  generators_dir: "generators/"

filelist:
  rtl:
    - "rtl/atciic100_apbslv.v"
    - "rtl/atciic100_ctrl.v"
    - "rtl/atciic100_fifo.v"
    - "rtl/atciic100_gsf.v"
    - "rtl/atciic100_real.v"
  sim:
    - "sim/tb_top.v"

rtl_contract:
  fl_vs_rtl_equivalence: "Required"
  coverage_model: "Required"

test_requirements:
  scenarios:
    - { id: "SC1", name: "Reset", stimulus: "Assert presetn", expected: "Registers default, FIFO empty", checker: "Register readback", coverage: ["Reset"] }
    - { id: "SC2", name: "APB Read", stimulus: "APB Read ID", expected: "0x0202", checker: "Data check", coverage: ["APB_R"] }
    - { id: "SC3", name: "APB Write", stimulus: "APB Write SETUP", expected: "Setup updated", checker: "Readback", coverage: ["APB_W"] }
    - { id: "SC4", name: "Master TX", stimulus: "Full TX sequence", expected: "Data on bus", checker: "Slave model response", coverage: ["Master_TX"] }
    - { id: "SC5", name: "Master RX", stimulus: "Full RX sequence", expected: "Data in FIFO", checker: "FIFO read", coverage: ["Master_RX"] }
    - { id: "SC6", name: "Slave TX", stimulus: "Addressed as slave", expected: "Data driven", checker: "Master model check", coverage: ["Slave_TX"] }
    - { id: "SC7", name: "Slave RX", stimulus: "Addressed as slave", expected: "Data in FIFO", checker: "FIFO read", coverage: ["Slave_RX"] }
    - { id: "SC8", name: "Gen Call", stimulus: "Addr 0x00", expected: "GenCall status", checker: "Status bit", coverage: ["Gen_Call"] }
    - { id: "SC9", name: "Arb Lose", stimulus: "Multi-master collision", expected: "ArbLost status", checker: "Status bit", coverage: ["Arb_Lose"] }
    - { id: "SC10", name: "FIFO Full", stimulus: "Write beyond depth", expected: "Full status", checker: "Status bit", coverage: ["FIFO_Full"] }
    - { id: "SC11", name: "DMA Flow", stimulus: "Enable DMA", expected: "Req/Ack handshake", checker: "Signal timing", coverage: ["DMA"] }
    - { id: "SC12", name: "Glitch", stimulus: "Short pulse on SCL", expected: "Ignored", checker: "No state change", coverage: ["Glitch"] }
  coverage_goals:
    planned_bins:
      - "Reset"
      - "APB_R"
      - "APB_W"
      - "Master_TX"
      - "Master_RX"
      - "Slave_TX"
      - "Slave_RX"
      - "Gen_Call"
      - "Arb_Lose"
      - "FIFO_Full"
      - "DMA"
      - "Glitch"

quality_gates:
  ssot:
    pass: "All sections filled and validated."
    evidence: ["yaml/atciic100_real.ssot.yaml"]
  rtl:
    pass: "Compiles, Lints, and implements FM/CM."
    evidence: ["compile.log", "lint.log"]
  rtl_gen:
    profile: "production"
    pass: "FL/CL equivalence."
    evidence: ["cov/coverage."]
  dv:
    pass: "All scenarios pass."
    evidence: ["sim/report.html"]
  coverage:
    pass: "100% planned bins."
    evidence: ["cov/coverage."]
  eda:
    pass: "Timing met."
    evidence: ["sta/timing.rpt"]
  signoff:
    pass: "All gates pass."
    evidence: ["signoff/checklist.md"]

traceability:
  yaml_to_output:
    - { yaml: "registers", output: "atciic100_apbslv.v" }
    - { yaml: "fsm", output: "atciic100_ctrl.v" }
    - { yaml: "memory", output: "atciic100_fifo.v" }
    - { yaml: "io_list", output: "atciic100_real.v" }

workflow_todos:
  rtl-gen:
    - id: "RTL_TODO_APB"
      content: "Implement APB Slave Logic"
      detail: "Decode paddr[5:2] to specific registers. Implement read data mux and write decode."
      criteria: ["APB R/W functional"]
      source_refs: ["registers"]
      priority: "high"
      required: true
      owner_module: "atciic100_apbslv"
      owner_file: "rtl/atciic100_apbslv.v"
    - id: "RTL_TODO_FIFO"
      content: "Implement FIFO Buffer"
      detail: "Parameterized depth pointer logic. Full/Empty flags."
      criteria: ["Depth parameterizable"]
      source_refs: ["memory"]
      priority: "high"
      required: true
      owner_module: "atciic100_fifo"
      owner_file: "rtl/atciic100_fifo.v"
    - id: "RTL_TODO_FSM"
      content: "Implement I2C Protocol FSM"
      detail: "State machine for Master/Slave modes, Start/Stop/Addr/Data phases."
      criteria: ["FSM state coverage"]
      source_refs: ["fsm", "function_model"]
      priority: "high"
      required: true
      owner_module: "atciic100_ctrl"
      owner_file: "rtl/atciic100_ctrl.v"
    - id: "RTL_TODO_GSF"
      content: "Implement Glitch Filter"
      detail: "Digital filter for SCL/SDA inputs based on T_SP."
      criteria: ["Glitch rejection functional"]
      source_refs: ["features.glitch_suppression"]
      priority: "medium"
      required: true
      owner_module: "atciic100_gsf"
      owner_file: "rtl/atciic100_gsf.v"
    - id: "RTL_TODO_TOP"
      content: "Integrate Modules in Top Wrapper"
      detail: "Instantiate sub-modules and wire ports."
      criteria: ["Integration compile passes"]
      source_refs: ["sub_modules"]
      priority: "high"
      required: true
      owner_module: "atciic100_real"
      owner_file: "rtl/atciic100_real.v"

# ---------------------------------------------------------------------------
# Generation Flow
# ---------------------------------------------------------------------------
generation_flow:
  golden_emit_order:
    - "atciic100_gsf"
    - "atciic100_fifo"
    - "atciic100_apbslv"
    - "atciic100_ctrl"
    - "atciic100_real"
  steps:
    - { name: "validate_ssot", command: "bash workflow/ssot-gen/scripts/check_ssot_disk.sh atciic100_real", description: "Validate SSOT" }
    - { name: "handoff_rtl", command: "/ssot-rtl atciic100_real", description: "Downstream RTL generation" }
