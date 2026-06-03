---
title: mctp_assembler_v3 — ingress req→impl fidelity gap (found + fixed via adversarial probe)
tags: [mctp, rtl-gen, tb-gen, equivalence, fidelity, silent-pass]
category: debugging
date: 2026-06-03
---

# mctp_assembler_v3 — ingress req→impl fidelity

Built `mctp_assembler_v3` from scratch through the workflow (req → SSOT → golden FL/CL → RTL slice → cocotb sim). The AXI write-ingress is the one implemented module of nine.

## req → implementation trace (FM_INGEST_TLP)

```
req:128   "Non-contiguous WSTRB ... is a malformed AXI/TLP ingress event"
   ↓      req:127 "final beat ... must use contiguous valid byte lanes starting at lane 0"
SSOT      function_model.FM_INGEST_TLP.tlp_accept
          = wlast_seen AND awsize==5 AND awburst==INCR AND wstrb_contiguous
            AND tlp_byte_count ∈ [16, MAX_TLP_BYTES]
   ↓
FL        model/functional_model.py  (executes the rule = oracle)
   ↓
RTL       rtl/mctp_assembler_v3_axi_wr_ingress.sv : tlp_accept
```

## The gap (and why the first sim was a false green)

First cocotb suite (6 directed scenarios) was all-PASS — but every scenario used
contiguous strobes, so it never exercised `wstrb_contiguous`. The authored RTL
had **dropped that term** from the accept condition (`aw_legal & wlast & byte-range`
only). An adversarial probe (`WSTRB=0x00FF00FF`, legal size/burst, 16 bytes) exposed
it: **DUT accept=1 but FL accept=0** → real FL/RTL divergence. Classic silent-PASS
shape (cf. [[silent-pass-exposure-tb-stimulus-gap-20260520]]): the directed suite
proved nothing about the case it avoided.

## Fix (RTL → match golden; never the reverse)

Added an LSB-contiguity accumulator in the ingress FSM: non-final beats must be
fully strobed (`wstrb == all-ones`); final beat must be an LSB-aligned run
(`w != 0 && (w & (w+1)) == 0`). `tlp_accept` now ANDs `strb_contig`. Re-run:
adversarial probe `DUT accept=0, FL accept=0` (agree), 6 directed scenarios still
pass → TESTS=2 PASS=2, compile/`-Wall` clean.

## Honest closure status

- **Closed:** ssot-gen gate (0 blockers), golden FL/CL self-checks, the ingress
  slice equivalence for the tested scenarios incl. the contiguity case.
- **NOT closed:** 8 of 9 modules unauthored (`derive_rtl_todos --audit-rtl` =
  `gate=fail`); the workflow's own goal-scoreboard (`emit_goal_scoreboard_cocotb.py`)
  is blocked (TB_INPUT_MAP needs every FL field on a real port), so the 90
  equivalence_goals + L1/L3/L5 gates (`scoreboard_events.jsonl`, `coverage.json`,
  assertions, `check_sim_pass.sh`) were **not** run. The passing cocotb TB is
  hand-authored and directed, not the workflow scoreboard.

## Authoritative signoff verdict (the wiki's definition of "closed")

Ran the canonical gates (`check_ip_signoff.py`) instead of trusting the hand TB:

```
status=fail  gates: 8/18 pass, 10 fail, 0 blocked
PASS: ssot, ip_contract, fl_model, cl_model, equivalence_goals(90),
      rtl_compile, mutation_guard(advisory), verification_hardening(advisory)
FAIL: rtl_todo (open_required=337, static_missing=276 → 8/9 modules unauthored),
      rtl_provenance(missing), lint(23 warnings), tb_python_compile(missing),
      simulation(no sim/results.xml), simulation_quality(missing),
      scoreboard(no sim/scoreboard_events.jsonl, rows=0), coverage(missing),
      truth_coverage(0/72 obligations covered), waivers(no goal_ledger.json)
```

The hand-authored cocotb TB (TESTS=2 PASS=2) lives in `tb/cocotb/` and emits NO
`sim/scoreboard_events.jsonl` / `simulation_quality.json` / `cov/coverage.json`, so it
contributes **zero** to signoff — textbook silent-green (runner PASS ≠ scoreboard PASS).
Bar to match: `mctp_assembler_scratch` = 18/18, truth 95/95, scoreboard 86/86.

## Lesson

The workflow's intent (req → golden FL → equivalence gate) is sound and would have
caught this — but only if the *workflow's* scoreboard/coverage gates run. A
hand-authored directed TB can go green while diverging from the oracle. Always add
an adversarial probe per req-declared malformed/edge case, and prefer the workflow
goal-scoreboard over directed-only TB. See [[mctp-assembler-scratch-flow-20260531]]
for the full-flow reference IP.
