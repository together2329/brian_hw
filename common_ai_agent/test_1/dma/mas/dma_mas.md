# Module Architecture Specification (MAS)

## Module: `dma` — Direct Memory Access Controller

**Document Version:** 2.0  
**Date:** 2025-01-20  
**Author:** Auto-generated MAS (RTL-verified)  

---

## 1. Overview

### 1.1 Description
The DMA (Direct Memory Access) controller is a programmable peripheral that transfers data between memory-mapped sources and destinations without CPU intervention. It supports multiple independent channels, configurable transfer sizes, and interrupt generation upon completion or error. The implementation is a single flat SystemVerilog module (`dma.sv`) with one parameterized submodule (`dma_fifo.sv`) instantiated per channel.

### 1.2 Key Features
- **4 independent DMA channels** (parameterizable via `NUM_CHANNELS`) with individual configuration and status
- **Memory-to-memory**, **memory-to-peripheral**, and **peripheral-to-memory** transfers
- Configurable transfer widths: **8-bit, 16-bit, 32-bit**
- Programmable burst sizes: **1 (SINGLE), 4 (INCR4), 8 (INCR8), 16 (INCR16)** beats
- **Incrementing** and **fixed** addressing modes per source/destination
- Transfer sizes up to **1024 beats** per transaction (16-bit counter)
- **Interrupt generation** on transfer completion, half-transfer, and error conditions
- **Bus protocol:** AMBA APB (register access, zero wait states) + AMBA AHB-Lite (data transfer)
- **Priority-based arbitration** among channels with 4 configurable priority levels
- **Error detection** with AHB error response handling and auto-disable
- **Circular mode** for continuous transfers with automatic reload

### 1.3 Block-Level Interfaces
| Interface | Protocol | Description |
|-----------|----------|-------------|
| `apb_slave` | APB4 | CPU register access (configuration & status) |
| `ahb_master` | AHB-Lite | Data bus master for DMA transfers |
| `irq[NUM_CHANNELS-1:0]` | Level-sensitive | Interrupt request outputs per channel |

---

## 2. Module Interface

### 2.1 Port List

| Port Name | Direction | Width | Description |
|-----------|-----------|-------|-------------|
| `clk` | input | 1 | System clock (single clock domain) |
| `rst_n` | input | 1 | Active-low asynchronous reset |
| **APB Slave Interface** | | | |
| `psel` | input | 1 | APB peripheral select |
| `penable` | input | 1 | APB enable |
| `pwrite` | input | 1 | APB write indicator |
| `paddr` | input | 12 | APB address bus (word-aligned) |
| `pwdata` | input | 32 | APB write data |
| `prdata` | output | 32 | APB read data |
| `pready` | output | 1 | APB ready signal (always 1 — zero wait states) |
| `pslverr` | output | 1 | APB slave error response (reserved address access) |
| **AHB Master Interface** | | | |
| `hbusreq` | output | 1 | AHB bus request |
| `hgrant` | input | 1 | AHB bus grant |
| `haddr` | output | 32 | AHB address bus |
| `htrans` | output | 2 | AHB transfer type (IDLE/NONSEQ/SEQ) |
| `hwrite` | output | 1 | AHB write indicator |
| `hsize` | output | 3 | AHB transfer size (BYTE/HALFWORD/WORD) |
| `hburst` | output | 3 | AHB burst type (SINGLE/INCR4/INCR8/INCR16) |
| `hprot` | output | 4 | AHB protection control (default 4'b0011) |
| `hwdata` | output | 32 | AHB write data bus |
| `hrdata` | input | 32 | AHB read data bus |
| `hready` | input | 1 | AHB transfer done |
| `hresp` | input | 1 | AHB transfer response (0=OKAY, 1=ERROR) |
| **Interrupts** | | | |
| `irq` | output | `NUM_CHANNELS` | Per-channel interrupt request (level-sensitive) |

### 2.2 Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `NUM_CHANNELS` | 4 | Number of DMA channels |
| `DATA_WIDTH` | 32 | Data bus width in bits |
| `ADDR_WIDTH` | 32 | Address bus width in bits |
| `MAX_TRANSFER_SIZE` | 1024 | Maximum number of beats per transfer |
| `FIFO_DEPTH` | 8 | Internal data FIFO depth per channel |

---

## 3. Register Map

### 3.1 Global Registers (offsets 0x000–0x01C)

These registers are decoded first in the APB case statement and take priority over per-channel registers at the same address range.

| Offset | Name | Access | Reset | Description |
|--------|------|--------|-------|-------------|
| 0x000 | `DMA_EN` | R/W | 0x0 | Global DMA enable (bit 0). Must be 1 for any channel to operate. Clearing causes immediate abort of all active transfers. |
| 0x004 | `INT_STATUS` | R | 0x0 | Aggregated masked interrupt status (one bit per channel) |
| 0x008 | `INT_RAW` | R | 0x0 | Raw interrupt status before masking |
| 0x00C | `INT_CLEAR` | W (W1C) | — | Interrupt clear register (write-1-to-clear; read returns 0) |
| 0x010 | `INT_MASK` | R/W | 0xF | Interrupt mask per channel (0=enabled, 1=masked). Reset default: all masked. |
| 0x014 | `ERR_STATUS` | R | 0x0 | Error status per channel (sticky, cleared via ERR_CLEAR) |
| 0x018 | `ERR_CLEAR` | W (W1C) | — | Error clear register (write-1-to-clear; read returns 0) |
| 0x01C | `SW_REQ` | W | — | Software DMA request trigger per channel (pulse: auto-clears next cycle) |

### 3.2 Per-Channel Registers

Address decoding: `paddr[11:8]` selects the channel number, `paddr[7:0]` selects the register within the channel. This means:
- Channel 0: base `0x000` (registers 0x000–0x01C overlap with global registers; global decode takes priority)
- Channel 1: base `0x100` (registers 0x100–0x11C)
- Channel 2: base `0x200` (registers 0x200–0x21C)
- Channel 3: base `0x300` (registers 0x300–0x31C)

> **Note:** Channel 0's register space (0x000–0x01C) is entirely shadowed by global registers. Software must use channel 1–3 for normal operation, or acknowledge that channel 0's registers at 0x00–0x1C are unreachable when global registers occupy those addresses. This is a known limitation of the address map.

| Offset | Name | Access | Reset | Description |
|--------|------|--------|-------|-------------|
| 0x00 | `CH_EN` | R/W | 0x0 | Channel enable (bit 0). Auto-cleared on AHB error. |
| 0x04 | `CH_SRC_ADDR` | R/W | 0x0 | Source start address (word-aligned) |
| 0x08 | `CH_DST_ADDR` | R/W | 0x0 | Destination start address (word-aligned) |
| 0x0C | `CH_XFER_SIZE` | R/W | 0x0 | Transfer count in beats [15:0] (max 1024) |
| 0x10 | `CH_CTRL` | R/W | 0x0 | Control register (see bit fields below) |
| 0x14 | `CH_CFG` | R/W | 0x0 | Configuration register (see bit fields below) |
| 0x18 | `CH_STATUS` | R | 0x0 | Current channel status (see bit fields below) |
| 0x1C | `CH_REMAIN` | R | 0x0 | Remaining transfer count [15:0] |

#### CH_CTRL Register Bit Fields (offset 0x10)
| Bits | Field | Description |
|------|-------|-------------|
| [2:0] | SRC_WIDTH | Source transfer width: 0=8-bit, 1=16-bit, 2=32-bit |
| [5:3] | DST_WIDTH | Destination transfer width: 0=8-bit, 1=16-bit, 2=32-bit |
| [7:6] | SRC_BURST | Source burst size: 0=SINGLE, 1=INCR4, 2=INCR8, 3=INCR16 |
| [9:8] | DST_BURST | Destination burst size: 0=SINGLE, 1=INCR4, 2=INCR8, 3=INCR16 |
| [10] | SRC_INC | Source address increment: 0=fixed (peripheral FIFO), 1=incrementing (memory) |
| [11] | DST_INC | Destination address increment: 0=fixed (peripheral FIFO), 1=incrementing (memory) |
| [15:12] | — | Reserved |
| [16] | INT_EN | Interrupt on transfer complete |
| [17] | INT_ERR_EN | Interrupt on error |
| [31:18] | — | Reserved |

#### CH_CFG Register Bit Fields (offset 0x14)
| Bits | Field | Description |
|------|-------|-------------|
| [3:0] | SRC_PER | Source peripheral select (0xF = memory) |
| [7:4] | DST_PER | Destination peripheral select (0xF = memory) |
| [9:8] | PRIORITY | Channel priority level: 0=highest, 3=lowest |
| [10] | CIRCULAR | Circular mode enable (auto-reload on completion) |
| [11] | HALF_IRQ_EN | Half-transfer interrupt enable |
| [31:12] | — | Reserved |

#### CH_STATUS Register Bit Fields (offset 0x18, read-only)
| Bits | Field | Description |
|------|-------|-------------|
| [1:0] | STATE | FSM state: 0=IDLE, 1=SETUP, 2=READ, 3=WRITE (DONE reports as 0) |
| [2] | ERR | Bus error flag (sticky until channel restart) |
| [3] | DONE | Transfer complete flag (set when FSM reaches DONE state) |
| [31:4] | — | Reserved (read as 0) |

---

## 4. Architecture

### 4.1 Block Diagram

```
                    ┌───────────────────────────────────────────────────────┐
                    │                  DMA Controller (dma.sv)               │
                    │                                                       │
  APB Slave         │  ┌──────────────────────┐                              │
  Interface  ◄──────┼──►│  APB Register File    │                              │
  (psel,paddr...)   │  │  (write/read decode)   │                              │
                    │  └──────────┬────────────┘                              │
                    │             │ ch_en[], ch_src_addr[], ch_ctrl[], ...    │
                    │             ▼                                           │
                    │  ┌──────────────────────┐   ┌──────────────────────┐   │
                    │  │   Channel 0 FSM       │   │   Channel 1 FSM       │   │
                    │  │   IDLE→SETUP→READ→    │   │   IDLE→SETUP→READ→    │   │
                    │  │   WRITE→DONE          │   │   WRITE→DONE          │   │
                    │  │  ┌────────────────┐   │   │  ┌────────────────┐   │   │
                    │  │  │   dma_fifo     │   │   │  │   dma_fifo     │   │   │
                    │  │  │  (DEPTH=8)     │   │   │  │  (DEPTH=8)     │   │   │
                    │  │  └────────────────┘   │   │  └────────────────┘   │   │
                    │  └──────────┬────────────┘   └──────────┬────────────┘   │
                    │             │ ch_bus_request[]            │               │
                    │             ▼                            ▼               │
                    │  ┌──────────────────────┐                              │
                    │  │  Priority Arbiter     │                              │
                    │  │  (4-level priority)   │                              │
                    │  └──────────┬────────────┘                              │
                    │             │ arb_grant[], active_ch                     │
                    │             ▼                                           │
                    │  ┌──────────────────────┐                              │
                    │  │  AHB Master Interface  │                              │
                    │  │  (mux + registered out)│                              │
                    │  └──────────┬────────────┘                              │
                    │             │                                           │
                    │  ┌──────────┴────────────┐                              │
                    │  │  Interrupt Controller   │                              │
                    │  │  (raw/mask/status/irq)  │                              │
                    │  └───────────────────────┘                              │
                    └───────────────────────────────────────────────────────┘
                                      │
                              AHB Master Interface
                              (haddr, hwdata, htrans, ...)
```

### 4.2 Implementation Structure

The DMA controller is implemented as a **single flat module** (`dma.sv`) with one separate submodule:

| Submodule | File | Instances | Description |
|-----------|------|-----------|-------------|
| `dma_fifo` | `dma_fifo.sv` | 1 per channel | Parameterized synchronous FIFO (WIDTH=DATA_WIDTH, DEPTH=FIFO_DEPTH) |

All other functional blocks (register file, channel FSMs, arbiter, AHB master interface, interrupt controller) are implemented inline within `dma.sv` using generate blocks and `always_ff`/`always_comb` blocks.

### 4.3 Channel FSM

Each DMA channel implements the following state machine (typedef `ch_state_t`):

```
                  ┌─────────┐
          reset   │  IDLE   │◄─────────────────────────────┐
         ┌───────►│ (3'd0)  │                              │
         │        └────┬────┘                              │
         │             │ dma_en && ch_en && sw_req         │
         │             │ && xfer_size > 0                  │
         │             ▼                                   │
         │        ┌─────────┐                              │
         │        │  SETUP  │───► bus_request = 1          │
         │        │ (3'd1)  │                              │
         │        └────┬────┘                              │
         │             │ bus_grant                         │
         │             ▼                                   │
         │        ┌─────────┐                              │
         │        │  READ   │───► AHB read burst (src)     │
         │        │ (3'd2)  │     FIFO write               │
         │        └────┬────┘                              │
         │             │ burst_done || fifo_almost_full    │
         │             │ || last_beat                      │
         │             ▼                                   │
         │        ┌─────────┐                              │
         │        │  WRITE  │───► AHB write burst (dst)    │
         │        │ (3'd3)  │     FIFO read                │
         │        └────┬────┘                              │
         │             │ xfer_count == 0                   │
         │             ▼                                   │
         │        ┌─────────┐                              │
         │        │  DONE   │───► irq_pulse, bus_release   │
         │        │ (3'd4)  │                              │
         │        └────┬────┘                              │
         │             │ circular && !err ─────────────────┘
         │             │ (!circular || err)
         │             └──────────► IDLE
         └─────────────────┘
```

**State Descriptions:**
| State | Code | Description |
|-------|------|-------------|
| `CH_IDLE` | 3'd0 | Channel disabled or waiting for trigger. Bus request deasserted. |
| `CH_SETUP` | 3'd1 | Channel configured, requesting bus arbitration. `ch_bus_request` asserted. Loads burst counters on bus grant. |
| `CH_READ` | 3'd2 | Performing AHB read burst from source address. Data written to FIFO. Source address incremented if `SRC_INC=1`. Beat count and transfer count decremented. Transitions to WRITE on burst completion, FIFO almost-full, or last beat. |
| `CH_WRITE` | 3'd3 | Performing AHB write burst to destination address. Data read from FIFO. Destination address incremented if `DST_INC=1`. Transitions back to READ if more data needed, or DONE if transfer count is zero. |
| `CH_DONE` | 3'd4 | Transfer complete. Asserts `irq_pulse`. If circular mode and no error, reloads saved addresses/size and transitions to SETUP. Otherwise transitions to IDLE. |

**Important FSM behaviors:**
- **READ→WRITE→READ cycling:** For transfers larger than FIFO depth, the FSM cycles between READ and WRITE states to prevent FIFO overflow.
- **AHB error handling:** On `hresp == AHB_ERROR` in READ or WRITE state, immediately sets `ch_err_flag` and transitions to DONE.
- **Global disable override:** If `dma_en_reg` is cleared while a channel is active (not IDLE), the FSM is immediately forced to IDLE and `ch_bus_request` is deasserted. This is an **immediate abort**, not graceful.

### 4.4 Arbitration Scheme

The priority arbiter evaluates channel requests every clock cycle:

1. **Fixed priority levels:** Each channel has a 2-bit priority field (`ch_priority`, from `CH_CFG[9:8]`). Priority 0 is highest, priority 3 is lowest.
2. **Within same priority level:** Lower channel number wins (iteration order: channel 0 first).
3. **Single grant:** At most one channel is granted the bus per cycle (`arb_grant` is one-hot).
4. **Bus request:** `hbusreq` is asserted whenever any channel has `ch_bus_request` active.
5. **AHB ownership:** The granted channel's signals are muxed to the AHB output. Only channels in READ or WRITE states drive meaningful AHB transfers.

**Arbiter implementation (lines 560–597):**
```systemverilog
for (int pri = 0; pri < 4; pri++) begin        // Iterate priority levels 0..3
    for (int c = 0; c < NUM_CHANNELS; c++) begin // Iterate channels
        if (ch_priority[c] == pri[1:0] &&
            ch_bus_request[c] &&
            arb_grant == '0) begin
            arb_grant[c] <= 1'b1;               // First match wins
        end
    end
end
```

### 4.5 Data Flow
1. Software configures channel registers (source/dest addr, size, control, config)
2. Software enables the DMA globally (`DMA_EN = 1`)
3. Software triggers transfer (write to `SW_REQ` with corresponding channel bit)
4. Channel FSM: IDLE → SETUP (bus request) → READ (AHB read burst, FIFO write)
5. Channel FSM: READ → WRITE (AHB write burst, FIFO read)
6. Steps 4–5 repeat (READ↔WRITE cycling) until transfer count reaches zero
7. Channel FSM: WRITE → DONE (interrupt pulse, status update)
8. If circular mode: DONE → SETUP (auto-reload original addresses and size)
9. If not circular: DONE → IDLE

### 4.6 AHB Master Interface

The AHB master interface muxes the active (granted) channel's signals to the AHB bus:

- **Address phase:** `haddr`, `htrans`, `hwrite`, `hsize`, `hburst`, `hprot` driven when `hgrant` is asserted
- **Data phase:** `hwdata` driven one cycle after address phase (standard AHB pipelining)
- **Default protection:** `hprot = 4'b0011` (non-privileged, non-cacheable, data access)
- **Transfer type:** `AHB_NONSEQ` for first beat of burst, `AHB_SEQ` for subsequent beats, `AHB_IDLE` when no active transfer
- **Bus release:** `htrans = AHB_IDLE` when `hgrant` is deasserted

### 4.7 Interrupt Controller

Per-channel interrupt logic (lines 685–713):

- **Raw interrupt set** on: `ch_irq_pulse` (transfer complete), `ch_half_irq` (half-transfer), `ch_err_flag` (error)
- **Masked status:** `int_status = int_raw & ~int_mask`
- **Output:** `irq[ch] = int_status[ch]` (level-sensitive)
- **Clearing:** Writing 1 to `INT_CLEAR` bit clears both `int_raw` and `int_status` for that channel

---

## 5. Functional Requirements

### 5.1 FR-01: Register Access
The DMA controller shall expose an APB4 slave interface for register configuration. All registers shall be readable; writable registers shall update on the rising edge of `clk` when `psel`, `penable`, and `pwrite` are asserted. `pready` shall be tied permanently high (zero wait states). `pslverr` shall be asserted combinatorially for accesses to unmatched/reserved address space. Write-only registers (`INT_CLEAR`, `ERR_CLEAR`, `SW_REQ`) return 0 on read.

### 5.2 FR-02: Channel Configuration
Each channel shall support independently configurable source address, destination address, transfer count (16-bit, max 1024 beats), transfer width, burst size, and address increment mode. Source and destination widths are encoded separately in `CH_CTRL`. The `CH_CFG` register configures peripheral select, priority, circular mode, and half-transfer interrupt.

### 5.3 FR-03: Memory-to-Memory Transfer
When both `SRC_PER` and `DST_PER` are set to 0xF (memory), the channel shall perform memory-to-memory transfers initiated by software request (`SW_REQ`). The channel shall read from the source address, buffer through the internal FIFO, and write to the destination address.

### 5.4 FR-04: Peripheral Request Support
Each channel may be configured to respond to hardware DMA requests from peripherals via `SRC_PER`/`DST_PER` fields. In the current implementation, the peripheral request interface is defined in the configuration but the hardware request signals are not exposed as ports — transfers are initiated via `SW_REQ`.

### 5.5 FR-05: Transfer Width Alignment
Source and destination addresses should be aligned to their respective transfer widths. The AHB `hsize` signal is derived from the width encoding via `width_to_hsize()`: 0→BYTE(000), 1→HALFWORD(001), 2→WORD(010).

### 5.6 FR-06: Burst Handling
Burst sizes of 1 (SINGLE), 4 (INCR4), 8 (INCR8), and 16 (INCR16) shall be supported. The AHB `hburst` signal is driven accordingly. Separate burst sizes can be configured for source and destination reads/writes respectively.

### 5.7 FR-07: Address Increment Modes
- **Incrementing (`SRC_INC`/`DST_INC = 1`):** Address increments by the transfer width size (1/2/4 bytes) after each beat
- **Fixed (`SRC_INC`/`DST_INC = 0`):** Address remains constant — used for peripheral FIFO access

### 5.8 FR-08: Interrupt Generation
Each channel shall generate an interrupt upon:
- Transfer completion (`ch_irq_pulse` from DONE state, if `CH_CTRL.INT_EN = 1`)
- Bus error detection (if `CH_CTRL.INT_ERR_EN = 1`)
- Half-transfer point (if `CH_CFG.HALF_IRQ_EN = 1`)

Interrupts are level-sensitive and remain asserted until cleared via `INT_CLEAR` (write-1-to-clear). The `INT_MASK` register allows per-channel interrupt masking (1=masked, reset default all masked).

### 5.9 FR-09: Error Handling
If the AHB slave returns an error response (`hresp == AHB_ERROR`), the channel shall:
1. Immediately set `ch_err_flag`
2. Transition to DONE state
3. Set the corresponding bit in `ERR_STATUS` (sticky)
4. Auto-clear `ch_en` for the affected channel (channel disabled)
5. Generate an interrupt if `INT_ERR_EN` is set

Error status is cleared via `ERR_CLEAR` (write-1-to-clear).

### 5.10 FR-10: Circular Mode
When `CH_CFG.CIRCULAR = 1` and no error occurred, the DONE state shall automatically reload the original source address, destination address, and transfer count from the saved values (`ch_saved_*`), and transition back to SETUP to continue transferring without software intervention.

### 5.11 FR-11: Global Enable
The `DMA_EN` register bit 0 must be set to 1 for any channel to leave IDLE state. Clearing this bit shall **immediately abort** all in-progress transfers (FSM forced to IDLE, bus request deasserted) — this is NOT a graceful shutdown. Current AHB transactions may be left incomplete on the bus.

### 5.12 FR-12: Channel Status
The `CH_STATUS` register shall reflect (read-only):
| Bit(s) | Field | Encoding |
|--------|-------|----------|
| [1:0] | FSM state | 0=IDLE, 1=SETUP, 2=READ, 3=WRITE (DONE maps to 0) |
| [2] | Error flag | 1=AHB error occurred |
| [3] | Transfer complete | 1=DONE state reached |

### 5.13 FR-13: Reset Behavior
On assertion of `rst_n` (active-low asynchronous):
- All registers shall be reset to their default values
- All channels shall enter IDLE state
- All FIFOs shall be flushed (pointers reset)
- All interrupt outputs shall be deasserted
- AHB bus signals shall be driven to idle values (`htrans=IDLE`, `hbusreq=0`)
- `INT_MASK` reset to all-ones (all interrupts masked)

---

## 6. Timing & Performance

### 6.1 Clock Requirements
- Single clock domain design (`clk`)
- APB and AHB share the same clock
- All sequential logic uses `posedge clk` with async `negedge rst_n`

### 6.2 Throughput
- Maximum sustained throughput: 1 word per clock cycle (after arbitration latency)
- FIFO depth of 8 provides buffering for READ→WRITE pipelining
- `almost_full` threshold (depth ≥ 6) triggers early transition from READ to WRITE

### 6.3 Latency
- Register write to FSM activation: 1 clock cycle (registered APB write → next cycle FSM evaluates)
- SW_REQ to bus request: 1 clock cycle
- Transfer complete to IRQ assertion: 1 clock cycle (DONE state → irq_pulse → interrupt logic)

---

## 7. Design Constraints

### 7.1 Clock Domain Crossing
None. Single clock domain.

### 7.2 Reset Strategy
Asynchronous assert (`negedge rst_n`), no synchronous deassert in the RTL. All `always_ff` blocks use `posedge clk or negedge rst_n`. Reset synchronizer assumed to be external.

### 7.3 Area Target
- Gate count scales with `NUM_CHANNELS` and `FIFO_DEPTH`
- Each channel includes: FSM (~50 FFs), FIFO (8×32 = 256 bits SRAM), address/count registers

### 7.4 Power Considerations
- No explicit clock gating in RTL (all channels clocked continuously)
- Register updates gated by APB write enable

---

## 8. Verification Plan

The testbench (`tb_dma.sv`) contains 25 test cases covering all functional requirements:

| # | Test Name | FR Ref | Description |
|---|-----------|--------|-------------|
| 1 | `test_reset` | FR-13 | Reset values verified for all readable registers |
| 2 | `test_register_rw` | FR-01 | Write/read all global and per-channel registers |
| 3 | `test_apb_slave_error` | FR-01 | Access reserved address → pslverr assertion |
| 4 | `test_single_transfer` | FR-03 | Single-beat memory-to-memory transfer with IRQ |
| 5 | `test_burst_incr4` | FR-06 | INCR4 burst transfer (4 words) |
| 6 | `test_burst_incr8` | FR-06 | INCR8 burst transfer (8 words) |
| 7 | `test_burst_incr16` | FR-06 | INCR16 burst transfer (16 words) |
| 8 | `test_large_transfer` | — | Transfer >FIFO depth, tests READ→WRITE→READ cycling |
| 9 | `test_multi_channel` | FR-03/04 | Simultaneous transfers on multiple channels |
| 10 | `test_priority_arbitration` | §4.4 | Verify priority-based bus arbitration ordering |
| 11 | `test_interrupts` | FR-08 | Completion interrupt, status, clear |
| 12 | `test_error_handling` | FR-09 | AHB error response → ERR_STATUS, auto-disable |
| 13 | `test_circular_mode` | FR-10 | Continuous circular transfer with reload |
| 14 | `test_global_enable` | FR-11 | DMA_EN disable aborts active transfers |
| 15 | `test_channel_status` | FR-12 | CH_STATUS reflects FSM state correctly |
| 16 | `test_reset_during_transfer` | FR-13 | Mid-transfer reset behavior |
| 17 | `test_fixed_address` | FR-07 | Fixed address mode (peripheral FIFO simulation) |
| 18 | `test_int_clear_w1c` | FR-08 | Write-1-to-clear mechanism |
| 19 | `test_zero_length_transfer` | — | Edge case: xfer_size = 0 (no transfer initiated) |
| 20 | `test_sequential_transfers` | — | Multiple transfers on same channel |
| 21 | `test_back_pressure` | — | AHB slave deasserting hready during burst |
| 22 | `test_independent_channels` | — | All 4 channels configured independently |
| 23 | `test_sw_req_without_enable` | — | Edge case: SW_REQ with channel disabled |
| 24 | `test_err_clear_w1c` | FR-09 | Error status write-1-to-clear |
| 25 | `test_ahb_protocol` | — | AHB signal protocol verification (hbusreq, htrans) |

### 8.1 Testbench Infrastructure
- **Memory model:** Simple array-based memory for AHB slave simulation
- **APB tasks:** `apb_write()`, `apb_read()` for register access
- **Channel config:** `config_channel()` helper for multi-register setup
- **Sync primitives:** `wait_irq()` with timeout, `start_channel()`
- **Reset:** `apply_reset()` generates proper reset sequence
- **Check framework:** `check()` with pass/fail counting
- **Timeout watchdog:** 10M cycle global timeout

---

## 9. Submodule Interface Contracts

### 9.1 `dma_fifo` (separate module: `dma_fifo.sv`)
```
Parameters: WIDTH=DATA_WIDTH, DEPTH=FIFO_DEPTH
Inputs:  clk, rst_n, wr_en, wr_data[WIDTH-1:0], rd_en
Outputs: rd_data[WIDTH-1:0], full, empty, almost_full, almost_empty, count[$clog2(DEPTH+1)-1:0]
Behavior:
  - Synchronous read (combinational rd_data from memory, registered pointer increment)
  - Write on posedge clk when wr_en && !full
  - Read on posedge clk when rd_en && !empty
  - almost_full when count >= DEPTH-2
  - almost_empty when count <= 1
  - Async reset clears both pointers
```

### 9.2 APB Register File (inline within `dma.sv`, lines 196–317)
```
Inputs:  clk, rst_n, psel, penable, pwrite, paddr[11:0], pwdata[31:0]
         ch_status[NUM_CHANNELS-1:0][31:0], ch_remain[NUM_CHANNELS-1:0][15:0]
         int_raw_reg[NUM_CHANNELS-1:0], int_status_reg[NUM_CHANNELS-1:0]
         int_mask_reg[NUM_CHANNELS-1:0], err_status_reg[NUM_CHANNELS-1:0], dma_en_reg
Outputs: prdata[31:0], pready (const 1), pslverr
         dma_en_reg, int_mask_reg, int_raw_reg, int_status_reg (W1C)
         err_status_reg (W1C), sw_req_pulse
         ch_en[], ch_src_addr[], ch_dst_addr[], ch_xfer_size[], ch_ctrl[], ch_cfg[]
Side effects:
  - Auto-clears ch_en[ch] when ch_err_flag[ch] is set (error auto-disable)
  - sw_req_pulse auto-clears after one cycle
```

### 9.3 Per-Channel FSM (inline, generate block, lines 373–551)
```
Inputs:  clk, rst_n, dma_en_reg
         ch_en[ch], ch_src_addr[ch], ch_dst_addr[ch], ch_xfer_size[ch]
         ch_ctrl[ch], ch_cfg[ch], sw_req_pulse[ch]
         ch_bus_grant[ch], fifo_full[ch], fifo_empty[ch], fifo_almost_full[ch]
         fifo_count[ch], hready, hresp
Outputs: ch_state[ch], ch_status[ch], ch_remain[ch], ch_bus_request[ch]
         fifo_wr_en[ch], fifo_wr_data[ch], fifo_rd_en[ch]
         ch_cur_src_addr[ch], ch_cur_dst_addr[ch], ch_xfer_count[ch]
         ch_err_flag[ch], ch_irq_pulse[ch], ch_half_irq[ch]
```

### 9.4 Priority Arbiter (inline, lines 560–597)
```
Inputs:  clk, rst_n, ch_bus_request[NUM_CHANNELS-1:0], ch_priority[NUM_CHANNELS-1:0]
Outputs: arb_grant[NUM_CHANNELS-1:0] (one-hot), active_ch[$clog2(NUM_CHANNELS)-1:0]
         arb_any_active
```

### 9.5 AHB Master Interface (inline, lines 603–679)
```
Inputs:  clk, rst_n, hgrant, hready, hresp, hrdata[DATA_WIDTH-1:0]
         arb_grant[NUM_CHANNELS-1:0], active_ch
         ch_state[], ch_cur_src_addr[], ch_cur_dst_addr[]
         ch_src_width[], ch_dst_width[], ch_src_burst[], ch_dst_burst[]
         ch_burst_count[], fifo_rd_data[]
Outputs: hbusreq, haddr[ADDR_WIDTH-1:0], htrans[1:0], hwrite
         hsize[2:0], hburst[2:0], hprot[3:0], hwdata[DATA_WIDTH-1:0]
```

### 9.6 Interrupt Controller (inline, lines 685–713)
```
Inputs:  clk, rst_n, ch_irq_pulse[NUM_CHANNELS-1:0], ch_half_irq[NUM_CHANNELS-1:0]
         ch_err_flag[NUM_CHANNELS-1:0], int_mask_reg[NUM_CHANNELS-1:0]
Outputs: int_raw_reg[NUM_CHANNELS-1:0], int_status_reg[NUM_CHANNELS-1:0]
         irq[NUM_CHANNELS-1:0]
```

---

## 10. Known Limitations

1. **Channel 0 address shadowing:** Channel 0's per-channel registers (offset 0x00–0x1C at base 0x000) are entirely overlapped by global registers. Software cannot access channel 0 configuration through the standard address map.
2. **No peripheral request ports:** The `SRC_PER`/`DST_PER` fields are defined in `CH_CFG` but no hardware request input ports exist on the module. All transfers are software-initiated via `SW_REQ`.
3. **Immediate abort on global disable:** Clearing `DMA_EN` immediately forces all channels to IDLE without completing current AHB bursts, potentially leaving the AHB bus in an inconsistent state.
4. **No packing/unpacking logic:** Different source and destination widths are configurable in `CH_CTRL` but the data path does not implement width conversion — data passes through the FIFO as-is.
5. **No 1KB boundary checking:** Bursts are not prevented from crossing 1KB address boundaries as required by AHB specification.

---

## 11. Revision History

| Version | Date | Description |
|---------|------|-------------|
| 1.0 | 2025-01-20 | Initial MAS creation |
| 2.0 | 2025-01-20 | RTL-verified update: corrected arbitration scheme, global enable behavior, implementation structure, added known limitations, added CH_STATUS detail, verified all register bit mappings against RTL |

---

*End of Module Architecture Specification*
