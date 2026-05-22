# model_compare_counter Requirements

Create a small synthesizable hardware IP named `model_compare_counter`.

The block has one clock `clk` and active-low reset `rst_n`. It exposes:

- `enable` input, 1 bit.
- `clear` input, 1 bit.
- `step` input, 4 bits.
- `count` output, 8 bits.
- `wrapped` output, 1 bit.
- `valid` output, 1 bit.

Behavior:

- On reset, `count`, `wrapped`, and `valid` are zero.
- `clear` has priority over `enable`.
- When `clear` is high, `count`, `wrapped`, and `valid` become zero on the next clock.
- When `enable` is high and `clear` is low, add `step` to `count` on the next clock.
- The addition wraps modulo 256.
- `wrapped` is asserted for one cycle when the addition overflows 8 bits.
- `valid` is asserted for one cycle when an enabled update is accepted.
- When neither clear nor enable is high, hold `count`; deassert `wrapped` and `valid`.

Cycle model:

- Single-cycle accept/update/observe behavior.
- Inputs are sampled on the rising edge.
- Outputs reflect the registered state after that edge.
- Clear priority must be visible in the cycle model.
- Backpressure is not required.

Verification scenarios:

- Reset state.
- Clear priority over enable.
- Increment without overflow.
- Increment with overflow.
- Hold when idle.
- Multiple sequential updates.

Quality requirements:

- Generate SSOT, functional model, cycle model, equivalence goals, RTL, lint evidence, cocotb/pyuvm testbench, simulation evidence, coverage, sim-debug evidence, and final goal audit.
- RTL must compile and lint clean with no warnings.
- Functional coverage and equivalence coverage must include the cycle model and the scenarios above.
