---
title: SpecLoop And Equivalence Check
type: proposal
tags: [spec-loop, equivalence-check, sec, formal, yosys, eqy, rtl-regeneration, direction]
updated: 2026-06-06
related: [formal-verification-evidence, llm-contract-repair-loop, req-obligation-contract-evidence-validation, locked-truth-concept, mctp-assembler-contract-breakdown, contract-reflection-workflow]
---

# SpecLoop And Equivalence Check

This page records a second methodology in the same family as
[[llm-contract-repair-loop]], and confirms (with a worked demo) that its formal
core — **equivalence checking** — is doable with open-source tools.

## SpecLoop

```text
RTL  ->  Requirement (extract)  ->  RTL (regenerate)  ->  EQ Check
     ->  Requirement Refine  ->  New RTL  ->  ...
```

The loop takes an existing RTL, extracts requirements/spec from it, regenerates
RTL from those requirements (e.g. with an LLM), then **equivalence-checks the
regenerated RTL against the original**. If they differ, the requirement
extraction missed something — refine the requirement and regenerate. The EQ
check is the guard that keeps regeneration honest.

The pivotal step is `EQ Check` = **sequential equivalence checking (SEC)**:
"does the new RTL behave identically to the reference RTL for all inputs over
time?" — the same job done by commercial Conformal / JasperGold SEC.

## Open-Source EQ Check — Feasible (demonstrated)

Yes. Three open-source routes:

| Tool | How | Notes |
|---|---|---|
| **yosys `equiv_make` + `equiv_induct` + `equiv_status`** | built-in sequential equivalence | no extra install; used in the demo below |
| **`eqy` (Equivalence checking with Yosys)** | dedicated SEC tool (the SEC sibling of `sby`) | handles harder cases, explicit signal mapping |
| **`sby` + miter** | XOR the two outputs, `assert` they match; BMC/induction | reuses the `sby` flow |

Worked demo at `examples/mctp_contract_slice/eqcheck/` (`run_eq.sh`):

```text
gold:  y <= a + a + b           (reference RTL)
eq:    t = a<<1; y <= t + b     (regenerated, written differently)
ne:    y <= a + b              (regeneration that missed the spec)

yosys equiv_make + equiv_induct + equiv_status -assert:
  gold vs eq  ->  EQUIVALENT (proven)
  gold vs ne  ->  NOT EQUIVALENT (unproven $equiv cells = counterexample exists)
```

Command shape:

```tcl
read_verilog gold.sv eq.sv
proc
async2sync                 # REQUIRED if the design uses async reset ($adff)
equiv_make dut_gold dut_eq m
hierarchy -top m
equiv_simple
equiv_induct
equiv_status -assert      # exits non-zero if any $equiv point is unproven
```

It also works on a **real** design, not just the toy. `run_asm_eq.sh` regenerates
two variants of `mctp_rx_assembler` from the reference and SEC-checks them:

```text
gold vs refactored   (== rewritten as ~|(a^b))   ->  EQUIVALENT (proven by k-induction)
gold vs spec-missing (OOS-drop forgotten)         ->  NOT EQUIVALENT (1 unproven $equiv cell)
```

So a regeneration that only restyles the logic is proven identical, while one that
drops a required behavior is caught — exactly the SpecLoop EQ-check gate.

## SpecLoop Vs The Contract Repair Loop

They are complementary — the difference is what serves as the golden reference:

| | golden reference | what it proves |
|---|---|---|
| [[llm-contract-repair-loop]] | locked truth / contracts | the RTL **satisfies the contracts** (property-based; mutation proves the checks bite) |
| **SpecLoop EQ check** | the original RTL | the new RTL is **identical to the original** (equivalence-based) |

The honest pairing: use the contract/property loop to make the *original* RTL
trustworthy (SEC only tells you two designs differ, not which is correct), then
use SpecLoop's EQ check to keep any regeneration faithful to that trusted
reference. A failing EQ check yields a concrete counterexample input — feed it
back as the requirement-refinement signal.

## Honest Caveats (open-source SEC)

1. **State encoding / retiming.** `equiv_induct` (k-induction) closes easily when
   the two designs have similar state (e.g. the LLM rewrote combinational logic
   but kept the FSM). If the regeneration **re-encodes state or retimes**, naive
   induction may not close — use `eqy` with a signal map, or a bounded miter.
2. **FF matching by name.** `equiv_make` matches flops/outputs by name; rename-
   heavy regenerations need guidance.
3. **SEC is relative.** It proves "same as the reference", not "correct". The
   reference must be trusted independently (that is the contract loop's job).
4. The usual formal limits still apply (state explosion on large designs →
   partition; see [[formal-verification-evidence]]).

한 줄 요약: SpecLoop의 EQ Check(= 순차 등가검사)는 오픈소스(yosys equiv / eqy /
sby-miter)로 실제로 가능하며 — 등가본은 "동일"로 증명, 스펙 놓친 본은 반례로
적발 — contract-property 루프(원본을 신뢰화)와 짝지으면 RTL 재생성을 정직하게
유지한다.
