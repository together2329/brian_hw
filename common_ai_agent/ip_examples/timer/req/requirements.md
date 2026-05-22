# Timer IP Requirements

## Intent

Create a small single-clock countdown timer IP that is useful as a smoke test
for the ATLAS SSOT pipeline. The block is intentionally narrow: it has no bus,
no memory, and no interrupt line. It should still exercise function-model,
cycle-model, RTL, test, coverage, lint, and debug handoff paths.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset.
- `clear` stops the timer, clears `count`, clears `running`, and clears `done`.
- `start` loads `load_value` into the timer and sets `running` when the loaded
  value is non-zero.
- On each cycle with `enable` asserted, a running timer decrements `count`.
- `done` pulses when the timer consumes count value 1 and then the timer stops
  at zero.
- If `enable` is deasserted, the timer holds its current state.
- `count`, `running`, and `done` are observable outputs for test and waveform
  debug.

## Non-Goals

- No APB, AXI, or CSR bus is required for this smoke fixture.
- No clock-domain crossing, reset-domain crossing, memory, or interrupt
  generation is required.
- The default counter width is 16 bits and is parameterized through the SSOT.
