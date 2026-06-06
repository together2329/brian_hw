---
title: Formal Verification As Evidence
type: proposal
tags: [formal, sva, assume-assert-cover, evidence, validation, vacuity, liveness, mctp, direction]
updated: 2026-06-06
related: [mctp-assembler-contract-breakdown, llm-contract-repair-loop, spec-loop-and-equivalence-check, contract-reflection-workflow, locked-truth-concept, evidence-contract-obligation-traceability, truth-coverage-gate, golden-todo-evidence]
---

# Formal Verification As Evidence

"Formal" here means **RTL formal verification** — mathematically proving (or
finding a counterexample to) a property over *all* reachable inputs/states — not
running many simulations. It is one evidence type in the
`req → obligation → contract → evidence → validation` spine
([[contract-reflection-workflow]], [[evidence-contract-obligation-traceability]])
and the deterministic proof half of [[llm-contract-repair-loop]].

```text
simulation : feed prepared testcases, check they pass.
formal     : the tool mathematically searches whether ANY input/state sequence
             can break the property — proving it, or returning a counterexample.
```

So formal is not "more tests". It proves a counterexample does or does not exist.

## What Formal Closes Well For An MCTP Assembler

```text
valid-ready protocol stability
reset / flush correctness
FSM illegal-state prevention
SOM / EOM ordering
packet length upper bound
header field stability
seq / tag field update rule
no output without accepted input
no stale partial packet after error / drop
```

Example questions formal answers directly:

```text
while out_valid=1 and out_ready=0, output packet fields must not change
no partial packet state may survive reset
no payload may be emitted without SOM
after EOM the assembler must transition to idle/next-packet correctly
an accepted input byte must not be emitted twice
an accepted input byte must not be lost outside allowed conditions
a packet length must never exceed max payload size
```

Valid-ready stability is a textbook formal property — simulation only catches it
if you authored the exact backpressure testcase; formal explores all backpressure
patterns itself:

```systemverilog
property p_out_stable_when_backpressured;
  @(posedge clk) disable iff (!rst_n)
    out_valid && !out_ready
    |=> out_valid && $stable({out_data, out_som, out_eom, out_len, out_tag, out_seq});
endproperty
assert property (p_out_stable_when_backpressured);
```

## assume / assert / cover

```text
assume : environment condition the NEIGHBOR interface must hold (constrains the proof).
assert : obligation the RTL-under-test must hold (what we prove).
cover  : a situation we want to confirm is actually reachable.
```

```systemverilog
// assume — the upstream source's contract, NOT this RTL's job
assume property (@(posedge clk) disable iff (!rst_n)
  in_valid && !in_ready |=> in_valid && $stable(in_data));

// assert — the assembler RTL's obligation
assert property (@(posedge clk) disable iff (!rst_n)
  out_valid && !out_ready |=> $stable(out_data));

// cover — prove the SOM..EOM output path is reachable at all
cover property (@(posedge clk) disable iff (!rst_n)
  out_som ##[1:20] out_eom);
```

## Formal As An Evidence Row

```text
REQ:        the assembler must hold output packet fields stable under backpressure.
OBIL:       while out_valid && !out_ready, out_data/out_som/out_eom/out_len/out_tag stay stable.
CONTRACT:   C-MCTP-ASM-OUT-HANDSHAKE (valid-ready output interface)
EVIDENCE:   formal proof — p_out_stable_when_backpressured proven
VALIDATION: requirement closed by formal evidence
```

```yaml
evidence:
  - id: E-MCTP-ASM-FORMAL-OUT-STABLE
    contract: C-MCTP-ASM-OUT-HANDSHAKE
    type: formal
    property: [p_out_stable_when_backpressured]
    result: proven
    strength: unbounded_or_inductive      # see "strength honesty" below
    assumes: [a_in_stable_when_not_ready]  # MUST be discharged on the driver
    covers:  [c_out_som_to_eom_reachable]   # guards against vacuous proof
```

## Four Possible Outcomes

```text
proven         the property holds in every reachable case.
failed         a counterexample exists; the tool returns a counterexample waveform.
bounded proven holds within N cycles; not proven beyond N.
inconclusive   state space too large / assumptions/property too complex to decide.
```

`failed` is *useful*: the counterexample waveform shows the exact input order
that made the assembler emit a wrong packet — this feeds directly into a
contract-linked failure ticket in [[llm-contract-repair-loop]].

## What Formal Struggles With (use abstraction)

```text
full payload ordering over a long message
data integrity across a large buffer
complex random-traffic end-to-end equivalence
whole long-message fragmentation
```

These are not "impossible", but proving them directly blows up the state space.
Split the contract instead:

```text
track one symbolic payload byte (not the whole payload)
keep input-count == output-count invariants
keep FIFO / order invariants
prove packet boundaries formally; verify payload data via simulation scoreboard
```

This is the formal/sim division already used per unit in
[[mctp-assembler-contract-breakdown]] (e.g. `ASM-PAYLOAD`: formal owns
length/pointer/symbolic-byte, sim owns full ordering + scoreboard).

## Hardening — Do Not Let Formal Lie

Formal can produce false confidence faster than simulation. Four guards (these
extend the anti-cheating patch policy in [[llm-contract-repair-loop]] and the
freshness/closure rules in [[golden-todo-evidence]]):

1. **Discharge every `assume`.** The worst formal outcome is not `failed` — it is
   "proven about a world that cannot happen". An over-constraining `assume` makes
   a property vacuously proven by excluding the failing environment. Each
   `assume` is an obligation on the *neighbor* block and must be discharged
   (proven as an `assert` on the driver, or otherwise validated). An undischarged
   `assume` means the proof proves nothing.
2. **Pair every `assert` with a reachable `cover`.** A `proven` assert whose
   antecedent is never reachable is vacuous. Prove the property *and* prove the
   scenario is reachable (e.g. cover `out_valid && !out_ready`, cover
   `out_som ##[1:N] out_eom`). This is the formal analog of mutation-kill for
   simulation ([[truth-coverage-gate]]).
3. **Strength honesty — bounded/inconclusive is NOT proven.** Record
   `strength: {proven | bounded:N | inductive | inconclusive}` on each evidence
   row. Validation must treat `bounded`/`inconclusive` as not-closed (or
   closed-with-caveat), never silently upgraded to `proven`. A bounded proof to
   depth N hides anything that only fails after N.
4. **Safety vs liveness.** Most MCTP properties are safety ("never X") and are
   tractable. "EOM ⇒ eventual commit" is liveness ("eventually Y"), needs
   fairness assumptions (e.g. downstream eventually ready), and is much harder —
   often only a bounded/1-cycle version is provable. Do not claim liveness
   closure as cheaply as safety. `C-ASM-END-COMMIT-ONCE` (no double commit) is
   safety/easy; "EOM implies commit" is liveness/hard.

## Current Implementation Vs Proposed (this repo)

Honest gap, verified in the source on 2026-06-06:

| Aspect | Shipped today | Needed for real formal evidence |
|---|---|---|
| SVA emission | `workflow/fl-model-gen/scripts/emit_formal_properties.py` writes `<ip>/verify/<ip>_assertions.sv` (assert/assume) from SSOT `invariants` / `forbidden_states` / `forbidden_environment`; emits placeholder TODO asserts when no `formal_property` block is given | keep, but forbid placeholder/TODO asserts from counting as evidence |
| Proof engine | **none** — no `sby`/SymbiYosys/`yosys-smtbmc`/Jasper/Pono invocation exists anywhere in `workflow/`, `core/`, `src/` | wire a real prover (open-source path: Yosys + SymbiYosys `sby` + `yosys-smtbmc`) and capture its actual verdict |
| `formal_status.json` | written by `workflow/mutation/scripts/classify_survivors.py`, not by a proof run (see [[mctp-assembler-scratch-flow-20260531]] clobber note) | produced by the prover; `result`/`strength`/`assumes`/`covers` populated from the engine |
| Signoff gate | `workflow/signoff/scripts/check_ip_signoff.py` accepts `formal_status.status in {pass, optional_not_run}` with ≥5 properties | require proven (not bounded/inconclusive), assumes discharged, covers reachable, fresh vs current RTL |

So today a `formal_status.json` saying "pass" with ≥5 properties can satisfy
signoff **without any property ever being proven by a solver**. The SVA-emission
shape exists; the proving does not. This is exactly the "confident-but-unproven"
trap warned about in [[llm-contract-repair-loop]] `## 11`. The real work is
wiring an actual formal engine and making the closure gate demand a genuine
verdict — not adding more assertion text.

## Demonstrated With sby + z3 (worked example, 2026-06-06)

The open-source prover path is now proven runnable end-to-end — the table's
"Needed" column is feasible, not hypothetical. On
[`examples/mctp_contract_slice/`](../../examples/mctp_contract_slice/):

```text
toolchain : yosys + yosys-smtbmc + SymbiYosys (sby) + z3
            (brew install z3; sby from github.com/YosysHQ/sby, make install PREFIX=~/.local)
correct RTL : k-induction PASS (mode prove) — unbounded proof of all contracts
mutant RTL  : BMC FAIL with a machine-found counterexample trace (trace.vcd)
anti-vacuity: assert-cell count > 0, cover statements reached, power-on reset assumed
```

Four real gotchas hit during bring-up (each caught because a planted mutant MUST
fail — if it survives, the verification, not the RTL, is wrong):

1. **`bind` is ignored by the yosys-native frontend** → the checker is dropped as
   unused → vacuous pass. Fix: embed assertions in the RTL under
   `` `ifdef FORMAL `` (they observe internal signals natively), or instantiate
   the checker via an explicit wrapper.
2. **An identity mutation (`x <= x`) is optimized to a no-op** → looks like a
   pass. Use an unambiguous mutation (e.g. `x <= 0`).
3. **yosys formal NBA precedence can differ from Verilog last-wins** on
   overlapping assignments → the verilator sim lane caught what formal modeled
   away. Run sim AND formal, never one alone.
4. **Formal with no reset constraint** starts from a free state → coincidental
   passes (an 8-bit counter init=255 made `255+1=0` mask a frozen-counter bug).
   Add a power-on `assume(!rst_n)`.

Still NOT done: wiring this into the repo signoff so `check_ip_signoff.py` demands
a real verdict (proven + assumes discharged + covers reachable + mutant-killed)
instead of accepting an unproven `formal_status.json`. That pipeline integration
is the remaining gap.

## Summary

```text
Formal proves, over all reachable behavior, whether a contract can be broken —
proving it or returning a counterexample. In an MCTP assembler it locks
handshake, FSM, packet boundary, length, and reset/error obligations as evidence.

But: discharge every assume, cover every assert, never upgrade bounded to proven,
and treat liveness as harder than safety. In THIS repo the signoff pipeline still
accepts an emitted-but-not-proven formal_status; the prover itself is now
demonstrated on examples/mctp_contract_slice/, so the outstanding work is the
pipeline integration, not feasibility.
```

한 줄 요약: formal은 "이 contract를 깨는 경우가 존재하는가?"를 수학적으로
증명/반례탐색하는 evidence이고, MCTP assembler에서 handshake·FSM·packet
boundary·length·reset/error 의무를 닫는 데 쓴다 — 단, assume discharge·cover·
strength 정직성·safety/liveness 구분을 지켜야 하고, 이 레포는 아직 SVA만 emit하고
prover가 없다는 게 진짜 갭이다.
