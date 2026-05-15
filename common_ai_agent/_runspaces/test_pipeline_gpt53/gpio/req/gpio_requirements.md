# gpio IP Requirements

## Intent

Build a small parameterizable bidirectional GPIO peripheral as a smoke
fixture for the common_ai_agent SSOT pipeline. The block is intentionally
narrow: no bus and no interrupt, just direct register-style ports that
exercise SSOT, function-model, cycle-model, equivalence goals, RTL,
lint, TB, sim, coverage, and audit.

## Functional Behavior

- `clk` is the only clock.
- `rst_n` is an active-low asynchronous reset; on assertion all output
  state returns to zero.
- `dir_in[WIDTH-1:0]` is a synchronous control that selects per-pin
  direction. `0` makes the pin an input, `1` makes the pin an output.
- `dout_in[WIDTH-1:0]` is the output data value to drive when the pin
  is configured as output.
- `pad_in[WIDTH-1:0]` is the observed pad value when the pin is an
  input.
- `dir_q[WIDTH-1:0]` is the registered direction state.
- `dout_q[WIDTH-1:0]` is the registered output-data state.
- `oe_o[WIDTH-1:0]` is the combinational output-enable to the pad
  ring; bit `i` is high iff `dir_q[i]` is `1`.
- `pad_o[WIDTH-1:0]` is the combinational output-data to the pad ring;
  bit `i` equals `dout_q[i]` when `dir_q[i]` is `1`, otherwise `0`.
- `din_q[WIDTH-1:0]` is the registered input sample of `pad_in` on the
  rising clock edge for every bit whose `dir_q` is `0`. Bits whose
  `dir_q` is `1` hold their previous `din_q` value.

## Non-Goals

- No APB, AXI, or CSR bus.
- No interrupt or edge-detect logic.
- No clock-domain crossing or asynchronous IO ring metastability
  modeling beyond the simple input sample.
- `WIDTH` is parameterized via SSOT; the smoke fixture default is 8
  bits.

## Verification Hints

- Reset clears `dir_q`, `dout_q`, `din_q`, `oe_o`, and `pad_o`.
- Toggling `dir_in` from 0 to 1 should make `oe_o` follow on the next
  cycle.
- When `dir_q[i]` is 0, `pad_o[i]` must stay at 0 regardless of
  `dout_q[i]`.
- When `dir_q[i]` is 1, `pad_o[i]` must equal `dout_q[i]` and `oe_o[i]`
  must be 1.
- `din_q[i]` only samples `pad_in[i]` for input bits; output bits keep
  their last sampled value.
- Coverage should hit: all-input, all-output, mixed direction, write
  while output, read while input, and a randomized walk that flips
  direction.
