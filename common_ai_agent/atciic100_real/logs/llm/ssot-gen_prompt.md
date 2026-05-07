Generate canonical SSOT YAML for atciic100_real from atciic100_real/req/atciic100_real_requirements.md.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Valid success schema:
{
  "files": [
    {
      "path": "atciic100_real/yaml/atciic100_real.ssot.yaml",
      "kind": "ssot",
      "content": "<complete YAML document as a JSON string>"
    }
  ]
}

The YAML content must be general IP SSOT, not a fixed template workaround. It must derive semantics from the requirements and include these top-level sections: top_module, sub_modules, parameters, io_list, features, dataflow, function_model, cycle_model, clock_reset_domains, cdc_requirements, rdc_requirements, registers, memory, interrupts, fsm, timing, power, security, error_handling, debug_observability, integration, dft, synthesis, coding_rules, reuse_modules, custom, dir_structure, filelist, rtl_contract, test_requirements, quality_gates, traceability, workflow_todos, generation_flow. function_model and cycle_model are mandatory and must be substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, coverage planning, and mismatch ownership.

The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh atciic100_real` without repair. Required validator details:
- function_model.state_variables, function_model.transactions, and function_model.invariants must be non-empty lists.
- Every function_model.transactions[] item must include id, name, preconditions, outputs, and either side_effects or error_cases. If state_updates exist, also summarize them in side_effects.
- cycle_model must include clock, reset, latency, non-empty handshake_rules, non-empty pipeline, and non-empty ordering.
- timing must include target_clocks and latency_budget.
- power must include non-empty domains and power_states.
- security must include classification, non-empty assets, and non-empty threat_model.
- error_handling must include non-empty error_sources plus propagation and recovery.
- debug_observability must include waveform_must_probe and trace_events.
- integration must include bus_attachment and dependencies.
- dft must include scan_required, controllability, and observability.
- synthesis must include dialect, constraints, and required_outputs.
- every test_requirements.scenarios[] item must include id, name, stimulus, expected, checker, and coverage.
- quality_gates must be a mapping with ssot, rtl, dv, coverage, eda, and signoff; each gate must be a mapping with pass and evidence.
- If quality_gates.rtl_gen.profile is production, or the IP is DMA330/PL330-class, quality_gates.rtl_gen must include pass/evidence and every manifest-owned child module must have machine-readable integration.connections or sub_modules[].connections records with module/port/signal fields.
- traceability.yaml_to_output must be a non-empty list.

- workflow_todos.rtl-gen must be a non-empty list of LLM-authored RTL TODOs. Each item must include id, content, detail, criteria, source_refs, priority, required, and owner_module/owner_file when inferable from sub_modules. These TODOs are the downstream rtl-gen work ledger and must be specific to this IP, not fixed boilerplate.

If the requirements leave a semantic decision undefined, return exactly this JSON shape instead of files[]:
{
  "human_gate": {
    "decision_needed": "<specific RTL-engineer decision>",
    "evidence": {"requirement_refs": [], "ssot_refs": [], "tool_logs": [], "goal_ids": []},
    "options": [{"label": "<option>", "effect": "<downstream effect>"}],
    "recommended_default": {"label": "<option>", "why": "<reason>"},
    "downstream_effect": ["function_model", "cycle_model", "rtl_contract", "tb scoreboard"]
  }
}

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
read access when driven as LOW
paddr[5:2] I AMBA APB address bus
prdata[31:0] O AMBA APB read data bus
pwdata[31:0] I AMBA APB write data bus
I2C controller signals
i2c_int O Interrupt signal
i2c_req O DMA request
i2c_ack I DMA acknowledge
sda_o O I2C serial data output
scl_o O I2C serial clock output
sda_i I I2C serial data input
scl_i I I2C serial clock input
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 4
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p17
AndeShape™ ATCIIC100 Data Sheet
3.2.4. Status Register
The Status Register keeps the interrupt status and I2C-bus status.
Table 6. Status Register
Name Bit Type Description Reset
Reserved 31:15 - - -
LineSDA 14 RO Indicates the current status of the SDA line on SDA line status
the bus.
1: High
0: Low
LineSCL 13 RO Indicates the current status of the SCL line on SCL line status
the bus.
1: High
0: Low
GenCall 12 RO Indicates that the address of the current 0x0
transaction is a general call address.
This status is only valid in slave mode.
1: General call
0: Not general call
BusBusy 11 RO Indicates that the bus is busy. 0x0
The bus is busy when a START condition is on
bus and it ends when a STOP condition is seen
on bus.
1: Busy
0: Not busy
ACK 10 RO Indicates the type of the last 0x0
received/transmitted acknowledgement bit.
1: ACK
0: NACK
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 9
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p18
AndeShape™ ATCIIC100 Data Sheet
Name Bit Type Description Reset
Cmpl 9 R/W1C Transaction Completion 0x0
Master: Indicates that a transaction has been
issued from this master and completed without
losing the bus arbitration.
Slave: Indicates that a transaction addressing
the controller has been completed. This status
bit must be cleared to receive the next
transaction; otherwise, the next incoming
transaction will be blocked.
ByteRecv 8 R/W1C Indicates that a byte of data has been received. 0x0
ByteTrans 7 R/W1C Indicates that a byte of data has been 0x0
transmitted.
Start 6 R/W1C Indicates that a START Condition or a repeated 0x0
START condition has been
transmitted/received.
Stop 5 R/W1C Indicates that a STOP Condition has been 0x0
transmitted/received.
ArbLose 4 R/W1C Indicates that the controller has lost the bus 0x0
arbitration (master mode only).
AddrHit 3 R/W1C Master: indicates that a slave has responded to 0x0
the transaction.
Slave: indicates that a transaction is targeting
the controller (including the General Call).
FIFOHalf 2 RO Transmitter: Indicates that the FIFO is 0x0
half-full.
Receiver: Indicates that the FIFO is
half-empty.
FIFOFull 1 RO Indicates that the FIFO is full. 0x0
FIFOEmpty 0 RO Indicates that the FIFO is empty. 0x1
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 10
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p19
AndeShape™ ATCIIC100 Data Sheet
3.2.5. Address Register
The Address Register keeps the slave address. When programmed as a master, it is the target
slave address for the next transaction. When programmed as a slave, it is the controller’s address
on the bus.
Table 7. Address Register
Name Bit Type Description Reset
Reserved 31:10 - - -
Addr 9:0 R/W The slave address. 0x0
For 7-bit addressing mode, the most significant
3 bits are ignored and only the least-significant
7 bits of Addr are valid.
3.2.6. Data Register
The Data Register is the data access port for the FIFO.
Table 8. Data Register
Name Bit Type Description Reset
Reserved 31:8 - - -
Data 7:0 R/W Write this register to put one byte of data to the 0x0
FIFO.
Read this register to get one byte of data from
the FIFO.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 11
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p20
AndeShape™ ATCIIC100 Data Sheet
3.2.7. Control Register
The Control Register controls a transaction’s phase choices and records the progress of Data
phase.
Table 9. Control Register
Name Bit Type Description Reset
Reserved 31:13 - - -
Phase_start 12 R/W Enable this bit to send a START condition at the 0x1
beginning of transaction.
Master mode only.
Phase_addr 11 R/W Enable this bit to send the address after START 0x1
condition.
Master mode only.
Phase_data 10 R/W Enable this bit to send the data after Address 0x1
phase.
Master mode only.
Phase_stop 9 R/W Enable this bit to send a STOP condition at the 0x1
end of a transaction.
Master mode only.
Dir 8 R/W Transaction direction 0x0
Master: Set this bit to determine the direction
for the next transaction.
0: Transmitter
1: Receiver
Slave: The direction of the last received
transaction.
0: Receiver
1: Transmitter
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 12
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p21
AndeShape™ ATCIIC100 Data Sheet
Name Bit Type Description Reset
DataCnt 7:0 R/W Data counts in bytes. 0x0
Master: The number of bytes to
transmit/receive. 0 means 256 bytes. DataCnt
will be decreased by one for each byte
transmitted/received.
Slave: the meaning of DataCnt depends on the
DMA mode:
If DMA is not enabled, DataCnt is the number of
bytes transmitted/received from the bus master.
It is reset to 0 when the controller is addressed
and then increased by one for each byte of data
transmitted/received.
If DMA is enabled, DataCnt is the number of
bytes to transmit/receive. It will not be reset to 0
when the slave is addressed and it will be
decreased by one for each byte of data
transmitted/received.
3.2.8. Command Register
Table 10. Command Register
Name Bit Type Description Reset
Reserved 31:3 - - -
CMD 2:0 R/W Write this register with the following values to 0x0
perform the corresponding actions:
0x0: no action
0x1: issue a data transaction (Master only)
0x2: respond with an ACK to the received byte
0x3: respond with a NACK to the received byte
0x4: clear the FIFO
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 13
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p22
AndeShape™ ATCIIC100 Data Sheet
Name Bit Type Description Reset
0x5: reset the I2C controller (abort current
transaction, set the SDA and SCL line to the
open-drain mode, reset the Status Register and
the Interrupt Enable Register, and empty the
FIFO)
When issuing a data transaction by writing 0x1
to this register, the CMD field stays at 0x1 for
the duration of the entire transaction, and it is
only cleared to 0x0 after when the transaction
has completed or when the controller loses the
arbitration.
Note: No transaction will be issued by the
controller when all phases (Start, Address, Data
and Stop) are disabled.
3.2.9. Setup Register
The Setup Register keeps the programmable configurations and the I2C-bus timing parameters.
For detail timing settings, see Section 5.1 Timing Setup Guide.
Table 11. Controller Setting Register
Name Bit Type Description Reset
Reserved 31:22 - - -
T_SUDAT 28:24 R/W T_SUDAT defines the data setup time before 0x5
releasing the SCL.
Setup time = (4 + T_SP + T_SUDAT) * t
pclk
t = PCLK period
pclk
T_SP 23:21 R/W T_SP defines the pulse width of spikes that 0x1
must be suppressed by the input filter.
Pulse width = T_SP * t
pclk
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 14
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p23
AndeShape™ ATCIIC100 Data Sheet
Name Bit Type Description Reset
T_HDDAT 20:16 R/W T_SUDAT defines the data hold time after SCL 0x5
goes LOW
Hold time = (4 + T_SP + T_HDDAT) * t
pclk
Reserved 15:14 - - -
T_SCLRatio 13 R/W The LOW period of the generated SCL clock is 0x1
defined by the combination of T_SCLRatio and
T_SCLHi values. When T_SCLRatio = 0, the
LOW period is equal to HIGH period. When
T_SCLRatio = 1, the LOW period is roughly
two times of HIGH period.
SCL LOW period = (4 + T_SP + T_SCLHi *
ratio) * t
pclk
1: ratio = 2
0: ratio = 1
This field is only valid when the controller is in
the master mode.
T_SCLHi 12:4 R/W The HIGH period of generated SCL clock is 0x10
defined by T_SCLHi.
SCL HIGH period = (4 + T_SP + T_SCLHi) *
t
pclk
The T_SCLHi value must be greater than T_SP
and T_HDDAT values.
This field is only valid when the controller is in
the master mode.
DMAEn 3 R/W Enable the direct memory access mode data 0x0
transfer.
1: Enable
0: Disable
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 15
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p24
AndeShape™ ATCIIC100 Data Sheet
Name Bit Type Description Reset
Master 2 R/W Configure this device as a master or a slave. 0x0
1: Master mode
0: Slave mode
Addressing 1 R/W I2C addressing mode: 0x0
1: 10-bit addressing mode
0: 7-bit addressing mode
IICEn 0 R/W Enable the ATCIIC100 I2C controller. 0x0
1: Enable
0: Disable
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 16
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p25
AndeShape™ ATCIIC100 Data Sheet
4.RTL Configuration
4.1. Data FIFO Size
The ATCIIC100 controller uses a FIFO as buffer to the I2C-bus. The data to be transmitted or
received are stored in the FIFO. Define ATCIIC100_FIFO_DEPTH_n to configure an n-byte
FIFO, where n is the number 2, 4, 8 or 16.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 17
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p26
AndeShape™ ATCIIC100 Data Sheet
5.Programming Sequence
5.1. Timing Setup Guide
Before enabling the ATCIIC100 controller, you must setup the I2C-bus timing parameters1 by
programming the Setup Register. As an I2C slave, the spike suppression width, the data setup
time and the data hold time must be programmed properly according to the APB clock frequency
and the speed of the I2C-bus. As an I2C master, the I2C-bus clock frequency must be
programmed as well.
The following sub-sections show how to determine the Setup Register to meet the I2C-bus timing
parameters. All the examples assume that the APB clock frequency is 40MHz, i.e. the APB clock
period is 25ns. If the APB clock frequency of your design is not 40MHz, please derive the register
fields accordingly.
1 See NXP Semiconductors’ “I2C-bus specification and user manual” for details.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 18
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p27
AndeShape™ ATCIIC100 Data Sheet
5.1.1. Spike Suppression Width
Table 12 shows the pulse width of spikes that must be suppressed by the input filter. For the
Fast-mode and the Fast-mode Plus, spikes less than 50ns must be suppressed. i.e.
T_SP = 50ns/25ns = 2
Table 12. Timing Parameters for Spike Suppression
Standard-mode Fast-mode Fast-mode Plus Unit
Symbol Parameter
Min Max Min Max Min Max
t Pulse width of spikes that must be - - 0 50 0 50 ns
SP
suppressed by the input filter.
5.1.2. Data Setup Time
Data setup time defines the time in which the SDA should be held steady before the SCL rising
edge. Table 13 shows the timing parameters for the data setup time. The equation of data setup
time shown in Table 11 is:
Setup time = (4 + T_SP + T_SUDAT) * t
pclk
For the Standard-mode,
250ns = (4 + 2 + T_SUDAT) * 25ns
Then,
T_SUDAT = 4
For the other modes, T_SUDAT can be calculated similarly.
Table 13. Timing Parameters for the Data Setup Time
Standard-mode Fast-mode Fast-mode Plus Unit
Symbol Parameter
Min Max Min Max Min Max
t Data setup time 250 - 100 - 50 - ns
SUDAT
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 19
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p28
AndeShape™ ATCIIC100 Data Sheet
5.1.3. Data Hold Time
Data hold time defines the time in which the SDA should be held steady after the SCL falling
edge. Table 14 shows the timing parameters for the data hold time. The equation of data hold
time shown in Table 11 is:
Hold time = (4 + T_SP + T_HDDAT) * t
pclk
For the Standard-mode,
300ns = (4 + 2 + T_HDDAT) * 25ns
Then,
T_HDDAT = 6
For the other modes, T_HDDAT can be calculated similarly.
Table 14. Timing Parameters for the Data Hold Time
Standard-mode Fast-mode Fast-mode Plus Unit
Symbol Parameter
Min Max Min Max Min Max
t Data hold time 300 - 300 - 0 - ns
HDDAT
5.1.4. I2C-Bus Clock Frequency
The I2C-bus clock frequency is specified by the t and t parameters, which are shown in
HIGH LOW
Table 15 and can be achieved through the T_SCLHi and T_SCLRatio fields of the Setup Register.
Table 15. Timing Parameters for the SCL Clock
Standard-mode Fast-mode Fast-mode Plus Unit
Symbol Parameter
Min Max Min Max Min Max
t HIGH period of the SCL clock 4.0 - 0.6 - 0.26 - µs
HIGH
t LOW period of the SCL clock 4.7 - 1.3 - 0.5 - µs
LOW
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 20
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p29
AndeShape™ ATCIIC100 Data Sheet
For the Standard-mode, the minimum requirements of t and t are close, so T_SCLRatio
HIGH LOW
can be set to 0 (i.e. ratio = 1) to simplify the settings. The equations for the SCL periods shown in
Table 11 are:
SCL HIGH period = (4 + T_SP + T_SCLHi) * t >= 4000ns
pclk
SCL LOW period = (4 + T_SP + T_SCLHi * ratio) * t >= 4700ns
pclk
Substitute 2 for T_SP, 1 for ratio and 25ns for t , the equations become:
pclk
(4 + 2 + T_SCLHi) * 25ns >= 4000ns
(4 + 2 + T_SCLHi * 1) * 25ns >= 4700ns
Then,
T_SCLHi >= 182
For the Fast-mode, the minimum requirement of t is about 2 times of t , so T_SCLRatio
LOW HIGH
can be set to 1 (i.e. ratio = 2). The equations for the SCL periods are:
The following examples show two bus clock setups:
SCL HIGH period = (4 + T_SP + T_SCLHi) * t >= 600ns
pclk
SCL LOW period = (4 + T_SP + T_SCLHi * ratio) * t >= 1300ns
pclk
Substitute 2 for T_SP, 2 for ratio and 25ns for t , the equations become:
pclk
(4 + 2 + T_SCLHi) * 25ns >= 600ns
(4 + 2 + T_SCLHi * 2) * 25ns >= 1300ns
Then,
T_SCLHi >= 23
For the Fast-mode Plus, T_SCLHi can be calculated similarly.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 21
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3

### PDF p30
AndeShape™ ATCIIC100 Data Sheet
5.2. Master Mode
The following examples demonstrate how to initiate I2C transactions at the Master mode.
5.2.1. Data Transmit without DMA
Step 1 Setup the controller by programming the Setup Register:
 Master = 1
 IICEn = 1
 timing parameters.
Step 2 Set the data count, direction and phase choices in the Control
Register:
 Phase_start = 1
 Phase_addr = 1
 Phase_data = 1
 Phase_stop = 1
 Dir = 0
 DataCnt = data counts in bytes.
Step 3 Write the address of the target slave to the Address Register.
Step 4 Enable the Completion Interrupt and FIFO Empty Interrupt in the
Interrupt Enable Register:
 Cmpl = 1
 FIFOEmpty = 1.
Step 5 Write 0x1 to the Command register to issue the transaction.
The information contained herein is the exclusive property of Andes Technology Co. and shall not be distributed,
Page 22
reproduced, or disclosed in whole or in part without prior written permission of Andes Technology Corporation.
AndeShape_ATCIIC100_DS091_V1.3