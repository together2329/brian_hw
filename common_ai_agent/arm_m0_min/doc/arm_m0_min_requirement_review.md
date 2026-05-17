# arm_m0_min Requirement Review Packet

Approval status: pending user review. This file is evidence for review, not a
human-approved requirement artifact.

## Purpose

`arm_m0_min` is a minimal CPU-class IP used to validate the common_ai_agent
SSOT-to-RTL verification flow on a processor rather than a small peripheral.
The design is intentionally small but CPU-shaped: instruction fetch, decode,
execute/writeback, register file, ALU, branch control, AHB-Lite instruction
and data master interfaces, fault halt behavior, and SSOT-derived functional
and cycle coverage.

## User-Level Intent Captured

- Create one CPU IP that can exercise the full common workflow.
- Use the project wiki and common workflow contracts as authority.
- Do not accept pass-for-pass evidence.
- Use machine evidence for RTL compile, lint, sim, FL-vs-RTL comparison, and
  function/cycle coverage.
- Leave human-owned semantic approval as an explicit gate.

## Locked Design Summary

| Topic | Requirement |
|---|---|
| IP name | `arm_m0_min` |
| IP kind | CPU |
| ISA profile | Minimal ARMv6-M-like Thumb teaching subset |
| Instructions | `ADD`, `SUB`, `AND`, `ORR`, `EOR`, `MOV`, `CMP`, `LDR`, `STR`, `B`, `BEQ`, `BNE`, `LSL`, `LSR`, `ASR` |
| Pipeline | 3-stage in-order IF / ID / EX-WB |
| Issue width | Single issue |
| Datapath width | 32-bit |
| Instruction width | 16-bit Thumb-style decode subset |
| Register file | 16 x 32-bit architectural registers |
| PC behavior | PC resets to `RESET_PC`, advances by 2 on non-branch instruction fetch, and redirects on branch-taken conditions |
| Flags | `NZCV`; `CMP` updates flags, other listed ALU ops do not update flags unless explicitly extended later |
| Instruction bus | AHB-Lite-like read-only instruction master |
| Data bus | AHB-Lite-like load/store data master |
| Fault behavior | Instruction or data bus error drives `fault_halt`; reset clears halt state |
| Reset | Synchronous active-high reset |
| Interrupts | Not included |
| NVIC/SysTick | Not included |
| Caches/MMU/MPU | Not included |
| Target | Generic educational CPU reference for workflow validation |

## Interface Requirements

The top module exposes separate instruction and data AHB-Lite-style masters.
The instruction side drives `i_haddr`, `i_htrans`, `i_hwrite`, `i_hsize`,
`i_hburst`, `i_hprot`, and `i_hmastlock`, and consumes `i_hready`,
`i_hrdata`, and `i_hresp`. Instruction writes are not supported, so
`i_hwrite` remains deasserted.

The data side drives `d_haddr`, `d_htrans`, `d_hwrite`, `d_hsize`, `d_hburst`,
`d_hprot`, `d_hmastlock`, and `d_hwdata`, and consumes `d_hready`,
`d_hrdata`, and `d_hresp`. Load/store behavior must respect data-bus ready
and response signaling.

## Functional Requirements

- Reset places the core into a known state with PC at the configured reset
  address and fault halt cleared.
- Instruction fetch issues non-idle instruction transfers while the core is
  running and not fault halted.
- Decode supports the listed instruction subset and rejects unsupported
  encodings through fault behavior.
- ALU operations produce the same architectural result as the generated
  FunctionalModel for all covered operations.
- `CMP` updates `NZCV` according to the FunctionalModel.
- Branch instructions update the next PC according to the FunctionalModel and
  the active condition flags.
- Load/store operations use the data master interface and follow the generated
  FunctionalModel's load/store transaction contract.
- Bus error response on instruction or data side enters `fault_halt`.
- `fault_halt` blocks further architectural progress until reset.

## Cycle and Coverage Requirements

- Instruction fetch backpressure must be covered and must not corrupt PC or
  architectural state.
- Data-side memory stall behavior must be covered.
- Pipeline ordering must be covered so observed RTL transaction order remains
  consistent with the cycle model.
- Function coverage must cover the instruction/transaction classes represented
  by the FunctionalModel.
- Cycle coverage must cover handshakes, latency buckets, state transitions,
  fault transitions, and pipeline ordering bins derived from SSOT.
- Coverage credit must come from passing scoreboard rows with concrete
  `rtl_observed` signal values; raw FunctionalModel hits alone are debug
  evidence only.

## Verification Evidence Required Before Signoff

- SSOT validator passes in signoff mode.
- Generated FunctionalModel self-check passes.
- Equivalence goals are generated from SSOT and are not blocked.
- RTL compiles with a real HDL tool.
- DUT-only lint passes with zero errors and zero warnings.
- Generated cocotb simulation passes.
- Every required equivalence goal has a scoreboard row.
- FL-vs-RTL comparison reports all goals passed with no stale evidence.
- Functional and cycle coverage domains meet their SSOT targets using
  RTL-observed scoreboard evidence.
- The wiki captures the run status, remaining limitations, and reproduction
  commands.

## Current Evidence Snapshot

As of the 2026-05-17 refresh:

- SSOT validator: pass, 36 sections, 0 unresolved markers.
- RTL files: 8 SystemVerilog files.
- RTL compile: pass, `iverilog -g2012`.
- RTL lint: pass, `pyslang+verilator`, 0 errors, 0 warnings.
- cocotb simulation: pass, 1 testcase, 0 failures, 0 errors.
- Scoreboard: 39 required goals, 39 rows, 39 goals covered.
- FL-vs-RTL compare: 39 checked, 39 passed, 0 failed, 0 blocked, 0 untested.
- Function coverage: 19 / 19, 100%.
- Cycle coverage: 17 / 17, 100%.
- Goal audit: 15 / 16 checks pass; the only remaining blocker is the
  human-approved requirement artifact.

## Known Limitations

- This is a minimal teaching-profile CPU, not a production ARM-compatible
  Cortex-M implementation.
- The instruction subset is intentionally limited.
- Interrupts, exception return, privilege, debug, memory protection, caches,
  and system peripherals are outside the locked scope.
- Internal pipeline latch memory goals are currently proven through top-level
  CPU-observable behavior and overlapping model outputs. Deep signoff should
  add hierarchy-aware internal probes before claiming direct latch-retention
  proof.
- Structural line/branch instrumentation was not part of the latest refresh;
  function and cycle coverage are green through RTL-observed scoreboard
  evidence.

## Approval Decision Needed

Approve this requirement packet only if the locked scope above matches the
intended CPU reference. Approval means downstream evidence can treat the
semantic requirement contract as human-owned and frozen for this reference run.
If the intended CPU scope should include interrupts, exception semantics,
privilege, a larger ISA subset, a different reset policy, or production-grade
ARM compatibility, this packet should be rejected and the SSOT should be
reopened before further signoff.

## Reviewer Checklist

Approve only if all of these are acceptable:

- The CPU is a minimal ARMv6-M-like teaching/reference CPU, not a production
  Cortex-M-compatible core.
- The supported instruction set is limited to the listed 15 Thumb-style
  operations.
- Interrupts, exception return, privilege, debug, MPU/MMU/cache, NVIC, SysTick,
  and production-grade ARM compatibility are intentionally out of scope.
- Function/cycle coverage through RTL-observed scoreboard rows is sufficient
  for this reference run; deeper hierarchy probes are a future signoff
  hardening task.

If approved, promote this reviewed packet into the human-owned `req/` contract:

```sh
python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min \
  --root . \
  --source arm_m0_min/doc/arm_m0_min_requirement_review.md \
  --approved-by brian \
  --decision-note "approved locked minimal CPU scope"

python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .
```

If rejected, keep `arm_m0_min/review/decision_needed_req_requirement_approval.json`
open and reopen the SSOT scope before regenerating downstream artifacts.
