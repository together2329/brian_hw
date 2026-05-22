# uart_lite Requirements

## Purpose

`uart_lite` is a simple parameterized UART transceiver intended for embedded
host-controller integration. It exposes an APB-lite control/status surface so a
system-on-chip can configure baud rate, parity, stop-bit count, and observe
status without bit-banging. The IP is intentionally small — single clock
domain, single transmitter, single receiver — and is not a candidate for
high-throughput or high-fan-in applications.

## Interfaces

- **APB-lite slave**, 8-bit byte address, 32-bit data, PSEL/PENABLE/PWRITE
  handshake with PREADY assertion in the access phase and PSLVERR for illegal
  offsets at or above `0x30`.
- **Serial pins** `tx_o` and `rx_pin_i`, with a 2-flip-flop synchroniser
  inside RX before any FSM sampling.
- **Single interrupt** `uart_irq_o`, OR of `tx_empty`, `rx_not_empty`,
  `rx_overrun`, `frame_err`, and `parity_err` gated by per-source enables.

## Clock and Reset

- One clock domain `PCLK`, nominal 50 MHz (parameterized via baud divisor).
- Asynchronous active-low reset `PRESETn`, captured as an asynchronous
  assert / synchronous deassert through the resync logic in `uart_lite_core`.

## Parameters

| Name           | Range / Default               | Effect                                  |
|----------------|-------------------------------|-----------------------------------------|
| `DATA_WIDTH`   | 5 .. 8, default 8             | Frame data bit count                    |
| `FIFO_DEPTH`   | power-of-two, default 16      | TX and RX FIFO entries                  |
| `OVERSAMPLE`   | default 16                    | RX oversample factor (mid-bit @ 7/16)   |

## Register Map (word-aligned, 4-byte offsets)

- `CTRL` (0x00): `tx_enable`, `rx_enable`, `loopback`, `break_send`,
  `parity_en`, `parity_odd`, `stop_bits` (0=1 stop, 1=2 stop).
- `STAT` (0x04): sticky `frame_err`, `parity_err`, `overrun_err`,
  `underrun_err`, plus live `tx_full`, `tx_empty`, `rx_empty`, `rx_full`,
  `tx_busy`, `rx_busy`.
- `BAUD` (0x08): 16-bit baud divisor (reset 0x144 = 324 -> 9600 baud at 50MHz).
- `TXDATA` (0x0C): write-only, pushes byte into TX FIFO.
- `RXDATA` (0x10): read-only, pops byte from RX FIFO.
- `INTEN` (0x14): per-source interrupt mask.
- `INTPEND` (0x18): per-source pending bits (W1C on write).
- `CLR_STAT` (0x1C): write-1-to-clear for sticky error flags.
- `DBG_BYTES_TX` (0x20), `DBG_BYTES_RX` (0x24),
  `DBG_FRAMES_ERR` (0x28), `DBG_PARITIES_ERR` (0x2C):
  read-only 32-bit debug counters.

## Functional Behaviour

- TX path: byte popped from TX FIFO is serialised LSB-first with optional
  parity and 1 or 2 stop bits at the rate determined by the baud generator.
  `break_send` overrides the data path and drives the line low for a frame
  duration; the bit clears automatically.
- RX path: synchronised line is mid-bit sampled at oversample count 7/16
  for start-bit confirmation, then every full oversample period for the
  data bits. Parity, framing, and overrun errors set their sticky status
  bits and pending interrupts.
- Loopback test mode internally routes `tx_o` to the RX sampling stage,
  bypassing the external pin, for self-test.

## Quality Gates

Production sign-off requires DUT compile and lint clean (no errors, no
warnings, no policy-banned constructs), full SSOT TODO closure, fresh
FL-vs-RTL equivalence audit, and human approval on G1..G9 as recorded in
`governance/authority.json`.

## Verification Intent

Coverage targets are documented in `cov/fcov_plan.json` and
`cov/cl_fcov_plan.json`; production sign-off requires every functional
bin hit from RTL-observed evidence (not FL-only). Sim debug evidence is
owned by `sim_debug`; uart_lite must keep RTL observable for FIFO levels,
FSM state, and per-source interrupt sources.

This file is the human-approved requirement record for `uart_lite`. Any
material change to interfaces, register map, or behaviour above this line
must be re-approved before SSOT, FL, or RTL can claim PASS.
