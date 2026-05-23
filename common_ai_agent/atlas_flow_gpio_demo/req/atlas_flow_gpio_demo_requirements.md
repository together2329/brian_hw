# atlas_flow_gpio_demo — Requirements

## Purpose

Create a minimal APB-Lite GPIO output mirror IP to exercise the ATLAS SSOT → FL/equiv/TB → simulation flow.

## Functional Requirements

1. Provide one APB-Lite slave interface clocked by `PCLK` and reset by active-low `PRESETn`.
2. Implement one 32-bit `DATA` register at byte offset `0x0`.
3. On an APB write access to offset `0x0`, latch `PWDATA[7:0]` into the DATA field.
4. Drive `gpio_out[7:0]` from the registered DATA field.
5. On an APB read access to offset `0x0`, return the DATA register on `PRDATA`.
6. Assert `PREADY=1` for zero-wait-state operation and `PSLVERR=0` for all accesses.
7. Reset must clear DATA and `gpio_out` to zero.

## Acceptance Criteria

- SSOT validates without TBD placeholders.
- Functional model and equivalence goals are generated from SSOT.
- Goal-driven cocotb scoreboard is generated from SSOT.
- RTL compiles and simulation reports all scoreboard checks passing.
