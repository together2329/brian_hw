# uart_lite_real — Requirements

## Purpose

`uart_lite_real` is a parameterized UART transceiver for embedded
host-controller integration.  It exposes an APB4 control/status surface so
a system-on-chip can configure baud rate, parity, stop-bit count, and observe
status without bit-banging.  The IP is intentionally small — single clock
domain, single transmitter, single receiver — and targets the same
functional profile as the reference `uart_lite` IP, but is a clean-slate
implementation under the name `uart_lite_real`.

## Interfaces

- **APB4 slave**, 8-bit byte address, 32-bit data, PSEL/PENABLE/PWRITE
  handshake with PREADY assertion in the access phase and PSLVERR for
  illegal offsets at or above `0x30`.
- **Serial pins** `tx` (output) and `rx` (input), with a 2-flip-flop
  synchronizer inside RX before any FSM sampling.
- **Single interrupt** `uart_irq`, OR of `tx_empty`, `rx_not_empty`,
  `rx_overrun`, `frame_err`, and `parity_err` gated by per-source enables.

## Clock and Reset

- One clock domain `PCLK`, nominal 50 MHz (parameterized via baud divisor).
- Asynchronous active-low reset `PRESETn`, captured as async assert /
  sync deassert through resync logic in the core module.

## Parameters

| Name              | Range / Default            | Effect                                |
|-------------------|---------------------------|---------------------------------------|
| `DATA_WIDTH`      | 5 .. 8, default 8          | Frame data bit count                  |
| `FIFO_DEPTH`      | power-of-two, default 16   | TX and RX FIFO entries                |
| `OVERSAMPLE`      | default 16                 | RX oversample factor (mid-bit @ 7/16) |
| `APB_ADDR_WIDTH`  | default 8                  | APB address width                     |
| `APB_DATA_WIDTH`  | default 32                 | APB data width                        |
| `CLOCK_FREQ_MHZ`  | default 50                 | Target clock frequency in MHz         |
| `RESET_POLARITY`  | active_low                 | Reset polarity                        |

## Register Map (word-aligned, 4-byte offsets)

| Offset | Name             | Access | Description                              |
|--------|------------------|--------|------------------------------------------|
| 0x00   | CTRL             | RW     | tx_en, rx_en, loopback, break, parity, stop |
| 0x04   | STAT             | RO     | FIFO flags + sticky errors               |
| 0x08   | BAUD             | RW     | 16-bit baud divisor (reset 324)          |
| 0x0C   | TXDATA           | WO     | Push byte into TX FIFO                   |
| 0x10   | RXDATA           | RO     | Pop byte from RX FIFO                    |
| 0x14   | INTEN            | RW     | Per-source interrupt mask                |
| 0x18   | INTPEND          | RW     | Pending bits (W1C on write)              |
| 0x1C   | CLR_STAT         | RW     | W1C for sticky error flags               |
| 0x20   | DBG_BYTES_TX     | RO     | Bytes-transmitted counter (wrapping)     |
| 0x24   | DBG_BYTES_RX     | RO     | Bytes-received counter (wrapping)        |
| 0x28   | DBG_FRAMES_ERR   | RO     | Framing error counter (wrapping)         |
| 0x2C   | DBG_PARITIES_ERR | RO     | Parity error counter (wrapping)          |

Addresses ≥ 0x30 return PSLVERR with PREADY=1.

## Functional Behaviour

### TX Path
Byte popped from TX FIFO is serialized LSB-first with optional parity and
1 or 2 stop bits at the rate determined by the baud generator.
`break_send` overrides the data path and drives the line low for a frame
duration; the bit clears automatically.

### RX Path
Synchronized line is mid-bit sampled at oversample count 7/16 for start-bit
confirmation, then every full oversample period for the data bits.
Parity, framing, and overrun errors set their sticky status bits and
pending interrupts.

### Loopback
`CTRL.loopback = 1` internally routes `tx` output to the RX sampling
stage (after 2-FF synchronizer), bypassing the external pin, for self-test.

### Error Handling
- **Frame error**: stop bit sampled low → sticky `frame_err`, debug counter
  increments, byte still pushed if FIFO space available.
- **Parity error**: computed parity ≠ received parity → sticky `parity_err`,
  debug counter increments, byte still pushed if FIFO space available.
- **Overrun**: RX FIFO full when new byte ready → sticky `overrun_err`,
  byte discarded.
- **Underrun**: TX FIFO empty when TX FSM requests byte → sticky
  `underrun_err`, frame aborted, TX returns to idle (mark).
- All sticky flags cleared via CLR_STAT W1C.

## Quality Gates

Production sign-off requires:
1. DUT compile clean (iverilog -g2012, zero errors).
2. Lint clean (zero unwaived errors/warnings).
3. Full SSOT TODO closure.
4. Fresh FL-vs-RTL equivalence audit.
5. Simulation PASS on all scenarios.
6. Functional coverage bins 100% hit.
7. Goal audit ≥ 15/16.
8. Human approval on requirement gate (req human gate).

## Verification Intent

Coverage targets document all TX/RX FSM states, parity modes, FIFO
corner cases, error injection scenarios, interrupt generation, and loopback.
Production sign-off requires every functional bin hit from RTL-observed
evidence (not FL-only).  Sim debug evidence is owned by `sim_debug`;
uart_lite_real must keep RTL observable for FIFO levels, FSM state, and
per-source interrupt sources.

---

*This file is the human-approved requirement record for `uart_lite_real`.
Any material change to interfaces, register map, or behaviour above this
line must be re-approved before SSOT, FL, or RTL can claim PASS.*
