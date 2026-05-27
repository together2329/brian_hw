# apb_uart_txrx_demo — Enhanced APB UART v2+ Requirements

## Goal

Build and verify a backward-compatible APB-attached UART IP that extends the
previous fixed-8N1 one-byte demo into a bounded, production-style UART block.
The enhanced UART keeps the same external APB/UART/IRQ pins while adding:

- configurable UART frame format: 5/6/7/8 data bits, no/even/odd parity, 1 or 2 stop bits;
- shallow TX and RX FIFOs with level, full, empty, threshold, and clear controls;
- APB register programming and readback for frame, FIFO, timeout, loopback, and scratch state;
- UART TX frame generation from queued APB writes;
- UART RX frame reception into a FIFO with majority-vote sampling and false-start rejection;
- status, interrupt, timeout, loopback, and sticky error behavior;
- directed scenario verification plus constrained-random APB/UART stress.

The previous fixed-8N1 behavior remains the reset/default operating mode except
that TX/RX buffering is now FIFO-backed rather than one-byte holding-register
backed.

## Default architecture decisions

| Topic | Decision |
|---|---|
| Bus | APB3-style slave, zero wait-state by default |
| Clock/reset | Single `pclk`; active-low `preset_n` |
| UART reset/default frame | 8N1: 8 data bits, no parity, 1 stop bit |
| UART enhanced frame | Data bits = 5/6/7/8; parity = none/even/odd; stop bits = 1 or 2 |
| Baud | Programmable integer divisor; default divisor 4 for fast simulation; 0 coerces to 1 |
| Buffers | Shallow synchronous TX and RX FIFOs; default depth 4 entries unless overridden by parameter |
| TX behavior | APB write to `TXDATA` pushes TX FIFO when enabled and not full; TX drains FIFO into UART frames |
| RX behavior | UART serial input is synchronized, sampled with 3-sample majority voting, and valid frames are pushed to RX FIFO |
| FIFO status | TX/RX FIFO level, full, empty, and threshold indications are APB-readable |
| Errors | Framing error, parity error, overrun, break detect, and RX timeout are sticky until cleared |
| Interrupts | Single level `irq`; enabled TX, RX, FIFO threshold, timeout, and error sources |
| Loopback | Internal loopback mode routes TX serial stream into RX sampler for self-test without adding pins |
| Invalid APB address | `pslverr=1`, no architectural state update |
| Verification style | Self-checking SV testbench, APB driver, UART serial driver/monitor, scoreboard, coverage, random regression |

## Top-level interface

The enhanced UART preserves the existing top-level APB/UART/IRQ pins. An
optional FIFO depth parameter may be added, but existing instantiations that use
only the original parameters remain source-compatible.

```systemverilog
module apb_uart_txrx_demo #(
  parameter integer APB_ADDR_WIDTH = 8,
  parameter integer BAUD_DIV_WIDTH = 16,
  parameter integer FIFO_DEPTH     = 4
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      psel,
  input  logic                      penable,
  input  logic                      pwrite,
  input  logic [APB_ADDR_WIDTH-1:0] paddr,
  input  logic [31:0]               pwdata,
  output logic [31:0]               prdata,
  output logic                      pready,
  output logic                      pslverr,
  output logic                      uart_tx,
  input  logic                      uart_rx,
  output logic                      irq
);
```

No RTS/CTS/modem/DMA pins are part of this v2+ increment.

## Register map

All registers are 32-bit APB word accesses. Only documented low bits are
implemented; reserved bits read as 0 and ignore writes. Existing offsets from
the fixed-8N1 demo are preserved.

| Offset | Name | Access | Reset | Description |
|---:|---|---|---:|---|
| `0x00` | `CTRL` | RW/WO bits | `0x0000_0001` | Global enable, interrupt enables, RX clear, TX break, loopback, timeout/threshold IRQ enables |
| `0x04` | `STATUS` | RO/W1C errors | `0x0000_0002` | RX/TX status, FIFO status summary, sticky errors, timeout, irq pending |
| `0x08` | `BAUD_DIV` | RW | `0x0000_0004` | UART bit-time divisor in pclk cycles; write 0 coerces to 1 |
| `0x0C` | `TXDATA` | WO push | `0x0000_0000` | Write low byte to push TX FIFO if enabled and not full |
| `0x10` | `RXDATA` | RO pop | `0x0000_0000` | Read low byte from RX FIFO; read pops one byte if data is present |
| `0x14` | `IRQ_STATUS` | RO/W1C | `0x0000_0000` | Sticky and level interrupt source state |
| `0x18` | `FRAME_CFG` | RW | `0x0000_0003` | Data width, parity, and stop-bit configuration; reset is 8N1 |
| `0x1C` | `FIFO_CTRL` | WO/RW bits | `0x0000_0000` | TX/RX FIFO clear controls and reserved future FIFO mode bits |
| `0x20` | `FIFO_STATUS` | RO | `0x0000_0001` | TX/RX FIFO levels and full/empty/threshold state |
| `0x24` | `FIFO_THRESH` | RW | `0x0000_0101` | TX and RX FIFO threshold settings |
| `0x28` | `RX_TIMEOUT` | RW | `0x0000_0000` | RX timeout count in pclk cycles; 0 disables timeout detection |
| `0x2C` | `SCRATCH` | RW | `0x0000_0000` | Software scratch register with no UART side effects |

### `CTRL` fields at `0x00`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `enable` | RW | 1 | UART TX/RX enable. When 0, TX does not launch new frames and RX sampler is idle. |
| `[1]` | `tx_irq_en` | RW | 0 | Enable TX interrupt sources (`IRQ_STATUS.tx_done` and TX threshold/empty when enabled). |
| `[2]` | `rx_irq_en` | RW | 0 | Enable RX interrupt sources (`RX FIFO non-empty` and RX threshold when enabled). |
| `[3]` | `err_irq_en` | RW | 0 | Enable error interrupt sources (`frame_err`, `parity_err`, `overrun_err`, `break_err`, sticky error). |
| `[4]` | `rx_clear` | WO | 0 | Write 1 clears RX FIFO and RX-valid state; self-clearing. |
| `[5]` | `tx_break` | RW | 0 | Force `uart_tx` low while set and block new TX frame launches. |
| `[6]` | `loopback_en` | RW | 0 | Route internal TX serial stream to RX sampler instead of external `uart_rx`. |
| `[7]` | `timeout_irq_en` | RW | 0 | Enable RX timeout interrupt source. |
| `[8]` | `fifo_irq_en` | RW | 0 | Enable FIFO threshold interrupt sources. |
| `[31:9]` | reserved | RO | 0 | Reserved; reads 0 and ignores writes. |

### `STATUS` fields at `0x04`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `rx_valid` | RO | 0 | RX FIFO is not empty. |
| `[1]` | `tx_empty` | RO | 1 | TX FIFO is empty and TX shifter is idle. |
| `[2]` | `tx_busy` | RO | 0 | TX shifter is actively emitting a frame. |
| `[3]` | `frame_err` | W1C | 0 | Sticky stop-bit/framing error. |
| `[4]` | `overrun_err` | W1C | 0 | Sticky RX FIFO overrun; new byte was discarded because RX FIFO was full. |
| `[5]` | `irq_pending` | RO | 0 | Combined interrupt pending after enables. |
| `[6]` | `tx_full` | RO | 0 | TX FIFO is full. |
| `[7]` | `rx_full` | RO | 0 | RX FIFO is full. |
| `[8]` | `parity_err` | W1C | 0 | Sticky parity mismatch error. |
| `[9]` | `break_err` | W1C | 0 | Sticky RX break-detect error. |
| `[10]` | `rx_timeout` | W1C | 0 | Sticky RX timeout pending. |
| `[11]` | `tx_threshold` | RO | 0 | TX FIFO level is at or below programmed TX threshold. |
| `[12]` | `rx_threshold` | RO | 0 | RX FIFO level is at or above programmed RX threshold. |
| `[31:13]` | reserved | RO | 0 | Reserved. |

### `IRQ_STATUS` fields at `0x14`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `tx_done` | W1C | 0 | Sticky set when a configured TX frame completes. |
| `[1]` | `rx_valid_irq` | RO | 0 | Mirrors `STATUS.rx_valid`. |
| `[2]` | `error` | W1C | 0 | Sticky aggregate of frame/parity/overrun/break errors. |
| `[3]` | `rx_timeout` | W1C | 0 | Sticky RX timeout source. |
| `[4]` | `tx_threshold` | RO | 0 | Mirrors TX threshold level source. |
| `[5]` | `rx_threshold` | RO | 0 | Mirrors RX threshold level source. |
| `[31:6]` | reserved | RO | 0 | Reserved. |

### `FRAME_CFG` fields at `0x18`

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[1:0]` | `data_bits_sel` | RW | 3 | `0=5`, `1=6`, `2=7`, `3=8` active data bits. |
| `[2]` | `parity_en` | RW | 0 | Include/check a parity bit when 1. |
| `[3]` | `parity_odd` | RW | 0 | `0=even parity`, `1=odd parity` when parity is enabled. |
| `[4]` | `stop2` | RW | 0 | `0=1 stop bit`, `1=2 stop bit-times`. |
| `[31:5]` | reserved | RO | 0 | Reserved. |

### `FIFO_CTRL`, `FIFO_STATUS`, `FIFO_THRESH`, `RX_TIMEOUT`, and `SCRATCH`

`FIFO_CTRL` (`0x1C`) fields:

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[0]` | `tx_fifo_clear` | WO | 0 | Write 1 clears the TX FIFO; self-clearing. |
| `[1]` | `rx_fifo_clear` | WO | 0 | Write 1 clears the RX FIFO; self-clearing. |
| `[31:2]` | reserved | RO | 0 | Reserved. |

`FIFO_STATUS` (`0x20`) fields:

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `tx_level` | RO | 0 | Number of bytes currently queued in TX FIFO. |
| `[15:8]` | `rx_level` | RO | 0 | Number of bytes currently queued in RX FIFO. |
| `[16]` | `tx_empty` | RO | 1 | TX FIFO empty. |
| `[17]` | `tx_full` | RO | 0 | TX FIFO full. |
| `[18]` | `rx_empty` | RO | 1 | RX FIFO empty. |
| `[19]` | `rx_full` | RO | 0 | RX FIFO full. |
| `[20]` | `tx_threshold` | RO | 0 | TX FIFO level is at or below `FIFO_THRESH.tx_threshold`. |
| `[21]` | `rx_threshold` | RO | 0 | RX FIFO level is at or above `FIFO_THRESH.rx_threshold`. |
| `[31:22]` | reserved | RO | 0 | Reserved. |

`FIFO_THRESH` (`0x24`) fields:

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[7:0]` | `tx_threshold` | RW | 1 | TX threshold level; source is true when TX FIFO level <= threshold. |
| `[15:8]` | `rx_threshold` | RW | 1 | RX threshold level; source is true when RX FIFO level >= threshold. |
| `[31:16]` | reserved | RO | 0 | Reserved. |

`RX_TIMEOUT` (`0x28`) fields:

| Bits | Field | Access | Reset | Description |
|---:|---|---|---:|---|
| `[15:0]` | `timeout_cycles` | RW | 0 | Number of pclk cycles to wait while RX FIFO is non-empty with no RX read/new byte before setting timeout; 0 disables timeout. |
| `[31:16]` | reserved | RO | 0 | Reserved. |

`SCRATCH` (`0x2C`) is a full 32-bit RW software scratch register. It has no UART datapath, status, error, or interrupt side effects.

## APB protocol contract

- Setup phase: `psel=1, penable=0`.
- Access phase: `psel=1, penable=1`.
- Transfer completes in access phase because `pready=1`.
- Write updates occur only in access phase with `pwrite=1`.
- Read data is valid during access phase with `pwrite=0`.
- Invalid address or unsupported access asserts `pslverr` for that access and does not update architectural state.
- Unsupported writes include writes to read-only pop/status registers and `TXDATA` writes when `enable=0` or the TX FIFO is full.
- Reads from an empty `RXDATA` return 0 and do not assert `pslverr`.

## UART TX contract

- `uart_tx` idles high when not transmitting and `CTRL.tx_break=0`.
- `CTRL.tx_break=1` forces `uart_tx=0` and prevents launching new TX frames.
- TX frame format is configured by `FRAME_CFG`:
  - start bit: `0`;
  - data bits: 5/6/7/8 bits, LSB first;
  - optional parity bit when `parity_en=1`;
  - stop bits: one or two bit-times of `1`.
- Parity is computed over only the active data bits:
  - even parity drives the parity bit so data+parity has an even number of 1s;
  - odd parity drives the parity bit so data+parity has an odd number of 1s.
- APB writes to `TXDATA` push `pwdata[7:0]` into the TX FIFO when enabled and not full.
- For 5/6/7-bit modes, transmitted bits above the configured data width are ignored.
- The TX engine consumes exactly one FIFO byte per frame and serializes it according to the frame configuration captured at frame launch.
- `STATUS.tx_busy` is high while the TX shifter is active.
- `STATUS.tx_empty` is high only when the TX FIFO is empty and the TX shifter is idle.
- `STATUS.tx_full` is high when the TX FIFO cannot accept another byte.
- `IRQ_STATUS.tx_done` sets at each configured frame completion.
- TX threshold status is true when the TX FIFO level is at or below `FIFO_THRESH.tx_threshold`.

## UART RX contract

- External `uart_rx` idles high.
- In normal mode, RX samples the synchronized external `uart_rx` pin.
- In loopback mode, RX samples the internal TX serial stream instead of the external `uart_rx` pin.
- RX detects a falling start bit, rejects false starts/glitches that return high by the start-bit decision point, and samples each configured bit using baud-derived 3-sample majority voting.
- RX frame format follows `FRAME_CFG`:
  - active data bits: 5/6/7/8 bits, LSB first;
  - optional parity bit checked when `parity_en=1`;
  - one or two stop bit-times, both required high when `stop2=1`.
- A good frame pushes one byte into the RX FIFO and sets `STATUS.rx_valid`.
- For 5/6/7-bit modes, bits above the active data width are zeroed in the byte pushed to the RX FIFO.
- A parity mismatch sets `STATUS.parity_err` and `IRQ_STATUS.error`; if RX FIFO space exists, the received data byte is still pushed.
- A bad stop bit sets `STATUS.frame_err` and `IRQ_STATUS.error`; if RX FIFO space exists, the received data byte is still pushed.
- A break condition is detected when the line remains low through a complete frame window; it sets `STATUS.break_err` and `IRQ_STATUS.error`. The implementation may push `0x00` if RX FIFO space exists, but software must rely on the sticky break error bit to classify the event.
- If a complete received byte cannot be pushed because RX FIFO is full, `STATUS.overrun_err` and `IRQ_STATUS.error` set and the new byte is discarded.
- Reading `RXDATA` returns and pops the oldest RX FIFO byte; `STATUS.rx_valid` clears when the FIFO becomes empty.
- RX threshold status is true when the RX FIFO level is at or above `FIFO_THRESH.rx_threshold`.

## RX timeout contract

- `RX_TIMEOUT.timeout_cycles=0` disables timeout detection.
- When timeout is enabled and RX FIFO is non-empty, a pclk counter increments while no RXDATA read and no new RX byte push occurs.
- A RXDATA read, new RX byte push, RX FIFO clear, or empty RX FIFO resets the timeout counter.
- When the counter reaches `timeout_cycles`, `STATUS.rx_timeout` and `IRQ_STATUS.rx_timeout` set sticky until W1C-cleared.
- `CTRL.timeout_irq_en` gates the timeout source into `irq`.

## FIFO contract

- TX and RX FIFOs are single-clock synchronous FIFOs in the `pclk` domain.
- FIFO depth is at least 4 entries in the default implementation.
- Same-cycle push/pop behavior is well-defined and must not corrupt ordering.
- TX FIFO order is first-in first-out from APB writes to transmitted frames.
- RX FIFO order is first-in first-out from received frames to APB reads.
- `FIFO_CTRL.tx_fifo_clear` clears queued TX bytes; an active TX frame may complete or return idle as implementation-defined, but no cleared queued byte may transmit afterward.
- `FIFO_CTRL.rx_fifo_clear`, `CTRL.rx_clear`, and reset clear RX FIFO contents and deassert `STATUS.rx_valid`.
- FIFO threshold status is level-based and updates as FIFO levels change.

## Loopback contract

- `CTRL.loopback_en=1` selects the internal TX serial stream as the RX sampler input.
- External `uart_tx` continues to show the transmitted serial stream.
- External `uart_rx` is ignored while loopback is enabled.
- Loopback is intended for local self-test and must exercise the same TX framing, RX sampling, FIFO, status, and error paths as normal operation.

## Interrupt contract

`irq` is high when any enabled pending source exists:

- `CTRL.tx_irq_en && IRQ_STATUS.tx_done`;
- `CTRL.rx_irq_en && STATUS.rx_valid`;
- `CTRL.err_irq_en && (STATUS.frame_err || STATUS.parity_err || STATUS.overrun_err || STATUS.break_err || IRQ_STATUS.error)`;
- `CTRL.timeout_irq_en && IRQ_STATUS.rx_timeout`;
- `CTRL.fifo_irq_en && (IRQ_STATUS.tx_threshold || IRQ_STATUS.rx_threshold)`.

`IRQ_STATUS.tx_done`, `IRQ_STATUS.error`, and `IRQ_STATUS.rx_timeout` are sticky W1C bits.
`IRQ_STATUS.rx_valid_irq`, `IRQ_STATUS.tx_threshold`, and `IRQ_STATUS.rx_threshold` are level mirrors.

## Directed verification scenarios

The directed testbench must retain the existing legacy scenarios and add v2+
coverage scenarios. Required directed scenarios:

1. `SC_APB_RESET`: reset values for all legacy and enhanced registers and idle `uart_tx=1`.
2. `SC_APB_RW`: APB write/read for `CTRL`, `BAUD_DIV`, `FRAME_CFG`, `FIFO_THRESH`, `RX_TIMEOUT`, and `SCRATCH`; reserved bits read as 0.
3. `SC_APB_INVALID`: invalid address asserts `pslverr` and preserves state.
4. `SC_TX_ONE_BYTE`: default 8N1 write one TX byte and decode `uart_tx` frame.
5. `SC_TX_BACK_TO_BACK`: default 8N1 send two bytes separated by legal readiness check.
6. `SC_TX_IRQ`: enable TX IRQ and verify tx_done/irq behavior.
7. `SC_RX_ONE_BYTE`: default 8N1 inject one RX frame and read `RXDATA`.
8. `SC_RX_BACK_TO_BACK`: inject two frames with reads between them.
9. `SC_RX_FRAMING_ERROR`: inject bad stop bit and verify frame error/irq.
10. `SC_RX_OVERRUN`: fill RX FIFO then inject another frame and verify overrun/discard behavior.
11. `SC_RX_IRQ`: enable RX IRQ and verify irq assertion/clear.
12. `SC_BAUD_VARIANTS`: repeat TX/RX with at least two baud divisors.
13. `SC_RX_MAJORITY_NOISE`: verify majority-vote tolerance around center samples.
14. `SC_RX_FALSE_START`: verify false-start rejection and subsequent good-frame recovery.
15. `SC_FRAME_CFG_RW`: verify enhanced frame configuration reset, write/read, and reserved masks.
16. `SC_TX_DATA_WIDTHS`: verify TX serialization for at least 7-bit and 5-bit modes.
17. `SC_RX_DATA_WIDTHS`: verify RX masking/zero-extension for at least 7-bit and 5-bit modes.
18. `SC_TX_PARITY_EVEN_ODD`: verify TX parity bit generation for even and odd parity.
19. `SC_RX_PARITY_GOOD`: verify RX accepts good even/odd parity frames without parity error.
20. `SC_RX_PARITY_ERROR`: verify bad parity sets `parity_err` and error IRQ while preserving received data if FIFO space exists.
21. `SC_TX_STOP2`: verify TX emits two stop bit-times when `stop2=1`.
22. `SC_RX_STOP2`: verify RX requires both stop bit-times high when `stop2=1`.
23. `SC_TX_FIFO_BURST`: push multiple bytes while TX is busy and verify serialized FIFO order.
24. `SC_RX_FIFO_ORDER`: inject multiple RX frames and verify FIFO read order/levels.
25. `SC_TX_FIFO_FULL`: fill TX FIFO and verify an additional `TXDATA` write reports `pslverr` without corrupting order.
26. `SC_FIFO_CLEAR`: verify TX and RX FIFO clear controls update levels/status.
27. `SC_FIFO_THRESHOLD_IRQ`: program thresholds and verify threshold status and IRQ behavior.
28. `SC_RX_TIMEOUT_IRQ`: program RX timeout and verify sticky timeout status/IRQ and W1C clear.
29. `SC_LOOPBACK`: enable loopback, transmit a byte, and verify RX FIFO receives the same byte through the internal path.
30. `SC_BREAK`: assert TX break and/or inject RX break; verify line behavior and sticky break error handling.
31. `SC_SCRATCH`: verify scratch register read/write and absence of UART side effects.

## Random verification plan

- Random APB reads/writes constrained to implemented and invalid offsets.
- Random legal frame configurations: data bits 5/6/7/8, parity none/even/odd, stop1/stop2.
- Random TX bytes with masking according to configured data width and random inter-write gaps.
- Random TX FIFO bursts, including attempts to write when full.
- Random RX frames with random byte values, legal/good parity, occasional wrong parity, occasional bad stop bits, and occasional break-like low windows.
- Random RX FIFO drain timing, overrun attempts, FIFO clear pulses, threshold values, timeout values, and loopback enable toggles.
- Random interrupt enable toggles for TX, RX, error, timeout, and FIFO threshold sources.
- Scoreboard tracks register model, FIFO contents/order, expected TX decoded frames, expected RX visible bytes, error flags, timeout state, threshold state, loopback behavior, and IRQ.
- Seed-based reproducibility via `+SEED=<n>` and transaction count via `+TXNS=<n>`.

## Coverage plan

Required functional/cycle bins:

- APB read/write every implemented register, including enhanced registers.
- Invalid APB read/write.
- Reset/default compatibility with legacy fixed 8N1 behavior.
- TX byte classes: `0x00`, `0xff`, walking/random values, and masked 5/6/7-bit values.
- RX byte classes: `0x00`, `0xff`, walking/random values, and masked 5/6/7-bit values.
- Data width modes 5, 6, 7, and 8 bits.
- Parity modes none, even, and odd.
- Good TX parity generation and good RX parity checking.
- RX parity error detection.
- Stop1 and stop2 TX/RX behavior.
- TX FIFO empty/non-empty/full transitions, burst ordering, threshold status, and clear.
- RX FIFO empty/non-empty/full transitions, burst ordering, threshold status, and clear.
- TX busy/empty transitions and tx_done IRQ.
- RX valid set/clear and RX IRQ.
- Error IRQ for framing, parity, overrun, and break.
- RX timeout status/IRQ and W1C clear.
- Loopback TX-to-RX self-test.
- Baud divisor minimum/default/alternate.
- Majority-vote noise tolerance and false-start rejection.

## Evidence deliverables

Expected deliverables for the enhanced challenge:

- `apb_uart_txrx_demo/yaml/apb_uart_txrx_demo.ssot.yaml`
- `apb_uart_txrx_demo/rtl/uart_fifo_sync.sv`
- `apb_uart_txrx_demo/rtl/uart_tx_framed.sv`
- `apb_uart_txrx_demo/rtl/uart_rx_framed.sv`
- `apb_uart_txrx_demo/rtl/apb_uart_regs.sv`
- `apb_uart_txrx_demo/rtl/apb_uart_irq.sv`
- `apb_uart_txrx_demo/rtl/apb_uart_txrx_demo.sv`
- `apb_uart_txrx_demo/list/apb_uart_txrx_demo.f`
- `apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo.sv`
- `apb_uart_txrx_demo/sim/run_sim.sh`
- `apb_uart_txrx_demo/sim/sim.log`
- `apb_uart_txrx_demo/sim/sim_results.json`
- `apb_uart_txrx_demo/sim/scoreboard_events.csv`
- `apb_uart_txrx_demo/sim/coverage_results.json`
- `apb_uart_txrx_demo/sim/waveform_manifest.json`
- `apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo_random.sv`
- `apb_uart_txrx_demo/sim/run_random_regression.sh`
- `apb_uart_txrx_demo/sim/random/random_regression_summary.json`
- `apb_uart_txrx_demo/verify/static_signoff_results.json`
- `.session/apb_uart_txrx_demo/signoff/*`

## Explicit scope limits / non-goals

This v2+ increment intentionally remains a bounded APB UART demo, not a full
16550-compatible UART or SoC subsystem. The following are excluded unless a
future user decision explicitly expands the top-level interface or scope:

- No RTS/CTS hardware flow-control pins.
- No modem pins or modem status/control register compatibility beyond documented scratch/loopback-style software state.
- No DMA interface, DMA request pins, AXI/AHB bridge, or bus-master behavior.
- No multi-clock CDC beyond the local UART RX synchronizer in the single `pclk` domain.
- No fractional baud generator or 16x external baud tick pin.
- No 1.5-stop-bit 5-bit special mode; `stop2=1` means two full stop bit-times for all data widths.
- No per-byte RX error tag FIFO in this increment; errors are exposed as sticky aggregate status bits.
- No ASIC backend signoff unless added later.
