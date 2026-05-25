# apb_uart_txrx_demo — APB UART TX/RX Requirements

## Goal
Build and verify a small APB-attached UART IP that exercises both directions of serial behavior:

- APB register programming and readback
- UART TX frame generation from APB writes
- UART RX frame reception into APB-readable data
- Status, interrupt, and error behavior
- Directed scenario verification plus constrained-random APB/UART stress

This is a challenge IP intended to extend the previous counter verification flow to a realistic peripheral.

## Default architecture decisions

| Topic | Decision |
|---|---|
| Bus | APB3-style slave, zero wait-state by default |
| Clock/reset | Single `pclk`; active-low `preset_n` |
| UART default frame | 8N1: 8 data bits, no parity, 1 stop bit |
| Baud | Programmable integer divisor; default divisor 4 for fast simulation |
| Buffers | One-byte TX holding register and one-byte RX holding register for first implementation |
| TX behavior | APB write to `TXDATA` starts a UART frame when transmitter is idle |
| RX behavior | UART serial input is sampled into RX holding register when a valid frame completes |
| Errors | Framing error on bad stop bit; overrun if new RX byte arrives while RX full |
| Interrupts | Level `irq`; enabled RX-valid, TX-done/TX-empty, and error sources |
| Invalid APB address | `pslverr=1`, no architectural state update |
| Verification style | Self-checking SV testbench, APB driver, UART serial driver/monitor, scoreboard, coverage, random regression |

## Top-level interface

```systemverilog
module apb_uart_txrx_demo #(
  parameter integer APB_ADDR_WIDTH = 8,
  parameter integer BAUD_DIV_WIDTH = 16
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

## Register map

All registers are 32-bit APB word accesses. Only documented low bits are implemented; reserved bits read as 0 and ignore writes.

| Offset | Name | Access | Reset | Description |
|---:|---|---|---:|---|
| `0x00` | `CTRL` | RW | `0x0000_0001` | bit0 enable, bit1 tx_irq_en, bit2 rx_irq_en, bit3 err_irq_en, bit4 rx_clear, bit5 tx_break |
| `0x04` | `STATUS` | RO/W1C errors | `0x0000_0002` | bit0 rx_valid, bit1 tx_empty, bit2 tx_busy, bit3 frame_err, bit4 overrun_err, bit5 irq_pending |
| `0x08` | `BAUD_DIV` | RW | `0x0000_0004` | Baud bit-time divisor in pclk cycles; 0 coerces to 1 |
| `0x0C` | `TXDATA` | WO | `0x0000_0000` | Write low byte to start TX if enabled and not busy |
| `0x10` | `RXDATA` | RO | `0x0000_0000` | Read low byte; read clears rx_valid if data present |
| `0x14` | `IRQ_STATUS` | RO/W1C | `0x0000_0000` | bit0 tx_done, bit1 rx_valid, bit2 error; W1C clears sticky tx_done/error bits |

## APB protocol contract

- Setup phase: `psel=1, penable=0`.
- Access phase: `psel=1, penable=1`.
- Transfer completes in access phase because `pready=1`.
- Write updates occur only in access phase with `pwrite=1`.
- Read data is valid during access phase with `pwrite=0`.
- Invalid address or unsupported write policy asserts `pslverr` for that access and does not update state.

## UART TX contract

- `uart_tx` idles high when not transmitting and break is not set.
- TX frame format is fixed 8N1 for this first challenge:
  - start bit: `0`
  - data bits: 8 bits, LSB first
  - stop bit: `1`
- One UART bit lasts `BAUD_DIV` pclk cycles.
- APB write to `TXDATA` when enabled and TX idle launches the frame.
- `STATUS.tx_busy` is high while frame is active.
- `STATUS.tx_empty` is high when TX can accept a new byte.
- `IRQ_STATUS.tx_done` sets at frame completion.

## UART RX contract

- `uart_rx` idles high.
- RX detects a falling start bit and samples at bit centers.
- Valid 8N1 frame loads `RXDATA`, sets `STATUS.rx_valid`, and sets `IRQ_STATUS.rx_valid`.
- Reading `RXDATA` returns the byte and clears `STATUS.rx_valid` if no newer byte is pending.
- Bad stop bit sets `STATUS.frame_err` and `IRQ_STATUS.error`.
- Receiving a new complete byte while `rx_valid=1` sets `STATUS.overrun_err` and `IRQ_STATUS.error`; the existing byte is preserved.

## Interrupt contract

`irq` is high when any enabled pending source exists:

- `CTRL.tx_irq_en && IRQ_STATUS.tx_done`
- `CTRL.rx_irq_en && STATUS.rx_valid`
- `CTRL.err_irq_en && (STATUS.frame_err || STATUS.overrun_err || IRQ_STATUS.error)`

## Directed verification scenarios

1. `SC_APB_RESET`: reset values for all registers and idle `uart_tx=1`.
2. `SC_APB_RW`: APB write/read for `CTRL` and `BAUD_DIV`; reserved bits read as 0.
3. `SC_APB_INVALID`: invalid address asserts `pslverr` and preserves state.
4. `SC_TX_ONE_BYTE`: write one TX byte and decode `uart_tx` frame.
5. `SC_TX_BACK_TO_BACK`: send two bytes separated by legal readiness check.
6. `SC_TX_IRQ`: enable TX IRQ and verify tx_done/irq behavior.
7. `SC_RX_ONE_BYTE`: inject one RX frame and read `RXDATA`.
8. `SC_RX_BACK_TO_BACK`: inject two frames with reads between them.
9. `SC_RX_FRAMING_ERROR`: inject bad stop bit and verify error/irq.
10. `SC_RX_OVERRUN`: inject two frames without reading and verify overrun preservation.
11. `SC_RX_IRQ`: enable RX IRQ and verify irq assertion/clear.
12. `SC_BAUD_VARIANTS`: repeat TX/RX with at least two baud divisors.

## Random verification plan

- Random APB reads/writes constrained to implemented and invalid offsets.
- Random TX bytes with random inter-write gaps.
- Random RX frames with random byte values and occasional bad stop bit.
- Random interrupt enable toggles.
- Scoreboard tracks register model, expected TX decoded bytes, expected RX visible bytes, error flags, and IRQ.
- Seed-based reproducibility via `+SEED=<n>`.

## Coverage plan

Required bins:

- APB read/write every implemented register.
- Invalid APB access.
- TX byte classes: `0x00`, `0xff`, walking/random values.
- RX byte classes: `0x00`, `0xff`, walking/random values.
- TX busy/empty transitions.
- RX valid set/clear.
- TX IRQ, RX IRQ, error IRQ.
- Framing error and overrun error.
- Baud divisor minimum/default/alternate.
- Back-to-back TX and RX scenarios.

## Evidence deliverables

Expected deliverables for the challenge:

- `apb_uart_txrx_demo/yaml/apb_uart_txrx_demo.ssot.yaml`
- `apb_uart_txrx_demo/rtl/apb_uart_txrx_demo.sv`
- `apb_uart_txrx_demo/list/apb_uart_txrx_demo.f`
- `apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo.sv`
- `apb_uart_txrx_demo/sim/run_sim.sh`
- `apb_uart_txrx_demo/sim/sim.log`
- `apb_uart_txrx_demo/sim/sim_results.json`
- `apb_uart_txrx_demo/sim/scoreboard_events.csv`
- `apb_uart_txrx_demo/sim/coverage_results.json`
- `apb_uart_txrx_demo/sim/tb_apb_uart_txrx_demo_random.sv`
- `apb_uart_txrx_demo/sim/run_random_regression.sh`
- `.session/apb_uart_txrx_demo/signoff/*`

## Explicit scope limits

- First implementation is fixed 8N1, not full configurable parity/stop/data-width UART.
- One-byte TX/RX holding registers are used before FIFO expansion.
- No DMA, modem pins, flow control, or AXI/AHB bridge.
- No ASIC backend signoff unless added later.
