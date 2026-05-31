# uart_tx — Requirement (human-owned)

## 1. Purpose
`uart_tx` is a minimal UART **transmitter** IP accessed through an APB-Lite
register interface. Software writes a byte to a data register; the block
serialises that byte on the `tx` line using the classic **8N1** framing
(1 start bit, 8 data bits LSB-first, 1 stop bit) at a software-programmable
baud divisor. There is no receiver and no FIFO in this revision; exactly one
byte is in flight at a time.

## 2. Interface
- Clock `PCLK`, active-low reset `PRESETn` (async assert, sync deassert).
- APB-Lite slave (32-bit data, 0-wait-state, `PREADY` always 1, `PSLVERR`
  always 0 — every address in range is legal).
- Serial output `tx` (idle level is logic 1).
- Status output `tx_busy` (1 while a frame is being shifted out).

## 3. Registers (byte offsets)
- `CTRL`   (0x0, rw): bit0 `ENABLE`. Transmission only starts when ENABLE=1.
- `DIV`    (0x4, rw): [15:0] clocks-per-bit (baud divisor). Reset value 4.
  A bit period lasts exactly `DIV` PCLK cycles. DIV must be >= 2.
- `TXDATA` (0x8, wo): [7:0] data byte. A **write** to this register while
  ENABLE=1 and the transmitter is idle starts a new frame.
- `STATUS` (0xC, ro): bit0 `BUSY` (mirrors `tx_busy`), bit1 `DONE` (set when a
  frame finishes, cleared when a new frame starts).

## 4. Functional rules (locked truth)
- The transmitted frame, sampled LSB-first on `tx` over time, is:
  start=0, then data[0..7], then stop=1. Encoded as a 10-bit word
  `frame = ((data << 1) | 0x200) & 0x3FF` where bit0 is the start bit sent
  first and bit9 is the stop bit sent last.
- While idle the `tx` line holds 1 and `tx_busy` is 0.
- On a qualifying TXDATA write the frame is latched, `tx_busy` becomes 1, the
  start bit is driven, and each subsequent bit is driven for `DIV` cycles.
- When the stop bit completes, `tx_busy` returns to 0 and `STATUS.DONE` is set.
- A TXDATA write while busy, or while ENABLE=0, is ignored (no new frame, no
  corruption of the in-flight frame).
- Reset forces `tx=1`, `tx_busy=0`, all registers to their reset values.

## 5. Acceptance criteria
- Every APB write/read obeys the 0-wait-state contract.
- The serial frame on `tx` must match the locked `frame` encoding for any
  data byte, verified bit-by-bit by the scoreboard against the functional
  model — not merely by checking `tx_busy` toggling.
- Functional coverage must include: reset behaviour, an accepted transmit of
  at least the boundary data values 0x00 / 0xFF / 0xA5, the busy-rejects-write
  case, and the disabled-rejects-write case.
- FL-vs-RTL comparison must classify every mismatch to SSOT, FL model, RTL,
  TB, coverage, tool, or human gate.

## 6. Explicitly out of scope (this revision)
- Receiver path, parity, multiple stop bits, hardware flow control, FIFO,
  and interrupts are not implemented. Parity/2-stop-bit support is a future
  request and must not be inferred into the RTL now.
