# apb_add_demo — Requirement (human-owned)

## 1. Purpose
`apb_add_demo` is a minimal APB-Lite peripheral with two 8-bit operand
registers (OPA, OPB) and a **combinational** adder. It exposes `add_out`
(the low 8 bits of OPA + OPB) and `carry_out` (the 9th bit). It is a
same-cycle, register + combinational block chosen to exercise the fully
automated flow (including auto-generated testbench).

## 2. Interface
- Clock `PCLK`, active-low reset `PRESETn` (async assert, sync deassert).
- APB-Lite slave (8-bit data, 0-wait-state, `PREADY` always 1, `PSLVERR`
  always 0 — every in-range address is legal).
- `add_out[7:0]`  = (OPA + OPB) truncated to 8 bits.
- `carry_out`     = carry-out of OPA + OPB (bit 8).

## 3. Registers (byte offsets)
- `OPA` (0x0, rw): operand A, reset 0x00.
- `OPB` (0x4, rw): operand B, reset 0x00.

## 4. Functional rules (locked truth)
- `add_out` and `carry_out` are purely combinational of `opa_q`, `opb_q`:
  `{carry_out, add_out} = opa_q + opb_q`.
- A write to OPA/OPB latches PWDATA into that register on the access phase;
  the outputs reflect the new value the same cycle.
- Reset clears OPA=OPB=0 → add_out=0, carry_out=0.
- PREADY=1 always; PSLVERR=0 always.

## 5. Acceptance criteria
- Every APB write/read obeys the 0-wait-state contract.
- `add_out`/`carry_out` must match `opa_q + opb_q` for all operand values,
  verified by the scoreboard against the functional model, including the
  carry boundary (e.g. 0xFF + 0xFF).
- Functional coverage must include reset, single-operand write, both-operand
  write, and the carry-generating case.
