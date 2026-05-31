# apb_add_demo — Requirement Approval Review (delegated human gate)

**Reviewer:** Claude (acting as the delegated human-gate approver for this session, by explicit user delegation 2026-05-31).
**Decision:** APPROVED for this demonstration scope (not a production tape-out sign-off).

## What I reviewed (req ↔ SSOT ↔ FL ↔ RTL consistency)
- **Requirement intent** (`req/apb_add_demo_requirements.md`): two 8-bit operand
  registers OPA/OPB over APB-Lite; combinational `add_out`/`carry_out` =
  `opa_q + opb_q`; 0-wait-state, no errors. Scope is explicit and closed
  (no receiver/FIFO/IRQ). No TODO/TBD markers.
- **SSOT** (`yaml/apb_add_demo.ssot.yaml`): `function_model` carries real
  `output_rules` (add_rule/carry_rule with concrete `expr`), not stub
  observables. Registers, io_list, rtl_contract output_map all match the
  requirement. Verified `verify_ssot.py --mode starter` PASS.
- **FL golden model** (`model/functional_model.py`): generated, self-check
  PASS; `add_rule`/`carry_rule` evaluate `opa_q + opb_q` with carry split at
  bit 8 — matches the locked rule.
- **RTL** (`rtl/apb_add_demo.sv`): `{carry_out, add_out} = opa_q + opb_q`
  combinational, registered OPA/OPB on APB access phase. compile PASS, lint
  PASS (verilator+pyslang 0/0, no suppression).
- **Verification**: auto-generated cocotb scoreboard covers all 20 equivalence
  goals (20/20 rows); sim PASS including the carry boundary 0xFF+0xFF=0x1FE
  (add_out=0xFE, carry_out=1).

## Decisions made as the approver
- Confirmed the **interface contract** (APB-Lite, 8-bit, 0-wait, PSLVERR=0) is
  acceptable for the stated scope.
- Confirmed **no undefined behaviour** is left implicit (all addresses legal,
  reads of unmapped offsets return 0).
- Accepted the architectural choice of a purely combinational adder (no
  pipeline) for a 50 MHz target.

## Caveats (explicitly recorded, not blockers for this scope)
- This is a demonstration IP with a self-authored spec; there is no independent
  golden reference. Production sign-off would require an external spec and an
  RTL-engineer review (see `uart_tx/EVAL_REQUEST.md`).
- DFT / CDC / timing / power gates are out of scope for this functional run.
