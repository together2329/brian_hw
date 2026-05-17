# dma_real — Requirements

## Overview

Multi-channel DMA controller IP with APB slave configuration interface and
AHB-Lite master data-transfer interface. Supports up to 4 independent DMA
channels with programmable source/destination addresses, transfer length,
and burst size. Round-robin arbitration among active channels. Per-channel
and combined interrupt outputs.

## Scope

- IP kind: peripheral
- Target scale: standard
- Quality profile: standard
- Approval policy: evidence_required

## Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| ADDR_WIDTH | int | 32 | Address bus width for both APB and AHB-Lite |
| DATA_WIDTH | int | 32 | Data bus width (must be 32) |
| N_CHANNELS | int | 4 | Number of independent DMA channels |
| BURST_MAX | int | 16 | Maximum burst length per AHB beat (1..16) |
| FIFO_DEPTH | int | 8 | Per-channel read FIFO depth in words |

## Interfaces

### APB Slave (configuration)

- Clock: pclk
- Reset: presetn (active-low)
- Port width: paddr[11:0], pwdata[31:0], prdata[31:0]
- All 5 register slots per channel plus global registers
- pslverr asserted on unmapped address access
- pready always asserted (no wait states)

### AHB-Lite Master (data transfer)

- Clock: hclk
- Reset: hresetn (active-low)
- Separate read and write phases via hwrite
- Burst support: INCR4 / INCR8 / INCR16 based on BURST_MAX
- hreadyout reflects transfer completion
- hresp: OKAY or ERROR

### Interrupt Outputs

- irq[N_CHANNELS-1:0]: per-channel done/error IRQ
- irq_combined: OR of all enabled channel IRQs

## Clock Domains

- Single clock domain: pclk = hclk (synchronous). The design uses pclk
  throughout. hclk is an alias for pclk and hresetn is an alias for presetn.
  No CDC logic is required for this version.

## Register Map

Base addresses per channel: CHx_BASE = CH0_BASE + (x * 0x20), x = 0..N_CHANNELS-1.

### Global Registers

| Offset | Name | Access | Description |
|---|---|---|---|
| 0x000 | GLOBAL_CTRL | rw | Bit 0: dma_en (global DMA enable). Bits [7:4]: reserved. |
| 0x004 | INT_STATUS | ro | Per-channel interrupt status (bit per channel). |
| 0x008 | INT_ENABLE | rw | Per-channel interrupt mask (1 = enabled). |
| 0x00C | INT_CLEAR | wo | Write-1-to-clear per-channel interrupt. |

### Per-Channel Registers (offset relative to CHx_BASE)

| Offset | Name | Access | Description |
|---|---|---|---|
| 0x000 | CHx_CTRL | rw | Bit 0: ch_en (channel enable). Bit 1: ch_start. Bit 2: ch_mode (0=mem-to-mem). Bits [7:4]: reserved. |
| 0x004 | CHx_SRC_ADDR | rw | Source start address. Must be word-aligned. |
| 0x008 | CHx_DST_ADDR | rw | Destination start address. Must be word-aligned. |
| 0x00C | CHx_LEN | rw | Transfer length in words (1..65536). 0 is invalid. |
| 0x010 | CHx_STATUS | ro | Bit 0: busy. Bit 1: done. Bit 2: error. Bits [4:3]: err_code (0=none, 1=align, 2=zero_len, 3=bus_err). |

## Functional Requirements

### FR-001: Channel Configuration

Software configures a channel by writing CHx_SRC_ADDR, CHx_DST_ADDR, and
CHx_LEN via APB. Writing CHx_CTRL.ch_start = 1 initiates the transfer.
CHx_CTRL.ch_en must be set before start is accepted.

### FR-002: Memory-to-Memory Transfer

Each active channel reads DATA_WIDTH-bit words from the source address via
AHB-Lite INCR burst, stores them in a per-channel FIFO, then writes them to
the destination address via AHB-Lite INCR burst. The transfer completes when
CHx_LEN words have been moved.

### FR-003: Round-Robin Arbitration

When multiple channels are active and requesting AHB access, the arbiter
selects channels in round-robin order. Each granted channel performs one
burst (up to BURST_MAX words) before the arbiter considers the next channel.

### FR-004: Burst Transfer

Each channel issues INCR bursts of up to BURST_MAX words. If CHx_LEN is not
a multiple of BURST_MAX, the final burst is shorter. Burst size calculation:
min(BURST_MAX, remaining_words).

### FR-005: Address Increment

Source address increments by 4 bytes per word transferred. Destination
address increments by 4 bytes per word transferred. Both addresses are
latched internally and updated as the transfer progresses.

### FR-006: Transfer Completion

When a channel completes its programmed transfer length, it asserts the
per-channel done status bit in CHx_STATUS.done and triggers an interrupt
if INT_ENABLE is set for that channel. The channel returns to IDLE state.

### FR-007: Error Handling

The DMA controller detects and reports the following error conditions:

| Error Code | Condition | Action |
|---|---|---|
| 1 (align) | src_addr[1:0] != 0 or dst_addr[1:0] != 0 at start | Reject transfer, set CHx_STATUS.error=1, err_code=1 |
| 2 (zero_len) | CHx_LEN == 0 at start | Reject transfer, set CHx_STATUS.error=1, err_code=2 |
| 3 (bus_err) | hresp == ERROR during AHB transfer | Abort transfer, set CHx_STATUS.error=1, err_code=3 |

Error status is latched until software clears it via INT_CLEAR.

### FR-008: Busy Reject

Writing ch_start while CHx_STATUS.busy == 1 is ignored. The channel
preserves its current state.

### FR-009: Global Enable

When GLOBAL_CTRL.dma_en == 0, no channel may start or continue transfers.
In-progress transfers complete their current burst, then pause. Setting
dma_en = 1 resumes paused channels.

### FR-010: Interrupt Behavior

- Per-channel IRQ is asserted when (CHx_STATUS.done OR CHx_STATUS.error)
  AND INT_ENABLE[ch] == 1.
- irq_combined is the OR of all per-channel IRQ outputs.
- Writing INT_CLEAR[ch] = 1 deasserts the IRQ if the condition has cleared.
- CHx_STATUS.done and CHx_STATUS.error are cleared when INT_CLEAR is written
  for the corresponding channel.

## FSM (Per Channel)

| State | Description |
|---|---|
| IDLE | Waiting for ch_start with valid configuration |
| CFG | Latch source/destination/length registers |
| REQUEST | Request AHB bus access via arbiter |
| READ | Perform AHB-Lite read burst from source |
| WRITE | Perform AHB-Lite write burst to destination |
| UPDATE | Update remaining count and addresses |
| DONE | Signal completion, assert done status |
| ERROR | Signal error, latch error code |

Transitions:

- IDLE -> CFG: ch_start && ch_en && dma_en && valid_cfg
- IDLE -> ERROR: ch_start && ch_en && !valid_cfg
- CFG -> REQUEST: next_cycle (unconditional)
- REQUEST -> READ: arbiter grants bus
- READ -> WRITE: read burst complete (FIFO has data)
- WRITE -> UPDATE: write burst complete
- UPDATE -> READ: remaining > 0
- UPDATE -> DONE: remaining == 0
- DONE -> IDLE: status sampled (INT_CLEAR or next start)
- ERROR -> IDLE: status sampled

## Sub-Module Decomposition

| Module | Responsibility |
|---|---|
| dma_real_top | Top-level wiring: instantiates all sub-modules, connects APB/AHB ports |
| dma_real_apb_cfg | APB slave decode: register read/write, per-channel config distribution |
| dma_real_arbiter | Round-robin arbitration among active channels |
| dma_real_channel | Per-channel FSM, address counters, remaining counter, burst control |
| dma_real_ahb_master | AHB-Lite master protocol engine: address/ data phase, burst sequencing |
| dma_real_irq | Interrupt aggregation: per-channel mask, status, combined IRQ |

## Design Constraints

- Single clock domain (pclk). No CDC.
- Active-low reset (presetn). All registers reset to 0.
- All addresses must be word-aligned (32-bit).
- No scatter-gather in this version.
- No half-word or byte transfers in this version.
- No address wrapping or striding in this version.

## Coverage Goals

### Functional Coverage

- Per-channel: valid transfer completion (done)
- Per-channel: alignment error path
- Per-channel: zero-length error path
- Per-channel: bus error path
- Per-channel: busy-reject path (start while busy)
- Multi-channel: two channels active simultaneously
- Multi-channel: round-robin switching between channels
- Global enable/disable with in-progress transfer

### FSM Coverage

- All per-channel FSM states visited
- All per-channel FSM transitions exercised
- Error transition from IDLE

### Cycle Coverage

- Burst completion latency (READ -> WRITE -> UPDATE)
- Arbitration latency (REQUEST -> READ grant)
- Done pulse observation
- Error pulse observation

## Quality Gates

- RTL compile: 0 errors (iverilog -g2012)
- DUT lint: 0 errors, 0 warnings (pyslang + verilator --lint-only -Wall)
- Scoreboard: 0 FL-vs-RTL mismatches
- Functional coverage: 100% of planned bins hit
- Goal audit: all non-human-gate checks pass
