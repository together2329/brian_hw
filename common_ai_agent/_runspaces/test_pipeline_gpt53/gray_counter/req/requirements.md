# gray_counter IP Requirements

## Intent

Build a small synchronous Gray-code counter as a smoke fixture for the
common_ai_agent SSOT pipeline. The block is intentionally narrow: no bus,
no memory, no interrupt. It must still exercise SSOT, function-model,
cycle-model, equivalence goals, RTL, lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion the counter
  returns to `gray_value = 0` and `done` deasserts.
- `clear` synchronously forces `gray_value` to 0 and clears `done`.
- `enable` advances the counter by one Gray step on every rising clock
  edge while high.
- `gray_value[WIDTH-1:0]` is the registered Gray-coded output.
- `bin_value[WIDTH-1:0]` is the combinational binary equivalent of
  `gray_value` provided for observers and coverage.
- `done` pulses for exactly one cycle when the counter wraps from the
  maximum Gray code back to zero.

## Non-Goals

- No APB/AXI/CSR bus or register file.
- No clock-domain crossing, asynchronous interface, or reset-domain
  crossing.
- No memory, FIFO, or interrupt generation.
- The counter width is parameterized through SSOT; the default is 4 bits
  for the smoke fixture.

## Verification Hints

- Stimulus uses `enable` pulses with periodic `clear` and `rst_n`
  injection.
- Expected `bin_value` follows the standard `bin = gray ^ (gray >> 1)`
  identity.
- `done` must align with the wrap cycle, not with intermediate counts.
- Coverage should hit reset, clear-after-run, full wrap, hold (enable
  low), and a randomized walk.
