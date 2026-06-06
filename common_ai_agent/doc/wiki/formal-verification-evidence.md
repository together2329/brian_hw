---
title: Formal Verification As Evidence
type: proposal
tags: [formal, sva, assume-assert-cover, evidence, validation, vacuity, liveness, mctp, direction]
updated: 2026-06-06
related: [mctp-assembler-contract-breakdown, llm-contract-repair-loop, spec-loop-and-equivalence-check, mctp-contract-slice-trial-and-error-20260606, contract-reflection-workflow, locked-truth-concept, evidence-contract-obligation-traceability, truth-coverage-gate, golden-todo-evidence]
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

## Mutation: Targeted Vs Blanket (two complementary axes)

Mutation answers two different questions — run both:

| | targeted (per-contract) | blanket (mechanical) |
|---|---|---|
| how | one deliberate bug per contract (`` `ifdef INJECT_X_BUG ``) | auto-generate many mutations across the RTL (operator flips, dropped assignments, stuck signals) |
| question | does each contract's evidence actually bite? | does the contract *set* have a hole? |
| a surviving mutant means | that contract's check is weak / vacuous | a **missing contract** (or an equivalent mutant) |
| metric | per-contract pass/fail | kill-rate %; survivors are the work list |

Targeted proves each brick is solid; blanket proves the wall has no gap. The
`mctp_rx_mc` ALLOC case is canonical: a *targeted* mutant survived only because the
contract itself was missing (added `C-ALLOC-NEW`) — exactly what a blanket sweep is
meant to surface, hit here by accident. See the worked record in
[[mctp-contract-slice-trial-and-error-20260606]] `## 2`.

Both are open-source: targeted via `` `ifdef ``; blanket via yosys `mutate`
(`mutate -list N` emits mutations; run the full contract suite against each and
classify survivors). The repo already has a blanket / kill-rate concept from
earlier mutation work — see [[general-ip-flow-trial-and-error-20260601]] and
[[mctp-assembler-scratch-flow-20260531]]; the new step is **tying blanket survivors
to the contract set** so each survivor maps to a missing contract, not just a
kill-rate number.

A complete closure gate runs both: every targeted mutant killed by its contract,
AND a blanket sweep whose survivors are each definitively classified. "Pass" then
means each contract bites *and* the set has no unaccounted hole.

### Survivor classification needs SEC, not a kill-rate guess (2026-06-06)

The raw blanket kill-rate can never reach 1.0 — equivalent mutants exist, and
embedded assertions have a structural **blind spot**: an assertion references the
(possibly mutated) signals, so a mutation on an *input* — or any self-consistent
perturbation — shifts the assertion's own notion of "expected" and survives. So a
kill-rate threshold is the wrong gate (it is either too loose or it rejects
harmless mutants). The right gate classifies each survivor with a **second,
independent lane**: sequential equivalence checking (a `miter -equiv` between the
mutated DUT and an unmutated gold copy, `chformal -remove` so only I/O is compared,
proven by k-induction). A survivor is then exactly one of:

- **equivalent** — SEC proves the outputs identical ⇒ harmless, not a hole;
- **sec_caught** — SEC finds an observable difference the embedded suite missed ⇒
  the equivalence lane catches it (covered, not a hole), and it is usually an input
  / self-consistent mutation no assertion could catch;
- **unknown** — SEC inconclusive ⇒ a real open item that must block signoff.

Gate = correct clean **AND** every targeted mutant killed **AND** zero `unknown`
survivors. This is the lesson behind [[spec-loop-and-equivalence-check]]: embedded
contracts and equivalence checking *compose* — together they leave no mutation
unaccounted, which neither does alone.

This is implemented and re-runnable in
[`examples/mctp_contract_slice/contract_check.py`](../../examples/mctp_contract_slice/contract_check.py):
targeted (`INJECT_*`) + blanket (`yosys mutate`) + SEC survivor classification,
emitting `signoff/mutation_contract_check.json`. Demonstrated on the assembler
slice: 11/11 targeted killed; embedded kill-rate ≈0.78; **all 8 blanket survivors
`sec_caught`, 0 unknown** — and adding the `C-ASM-CONTENT` / `C-ASM-DECODE`
value-level contracts (closing a hole the sweep first exposed: count + control-flow
were pinned, output *content* was not — the same "count ≠ content" gap as the v3
trust campaign) is the find→close loop in miniature.

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

Now wired (2026-06-06): `check_ip_signoff.py` has a `contract_mutation` gate that
consumes a re-runnable `<ip>/mutation/contract_mutation.json` (the
`mutation_contract_check` artifact produced by `contract_check.py`). It verifies
the **structured** verdict — correct clean on both lanes, every targeted mutant
killed, and every blanket survivor SEC-classified (zero `unknown`) — not a bare
`status: "pass"` string, so a hand-set status cannot pass without the matrix
backing it. The gate is backward-compatible (applicable only when the artifact
exists; legacy IPs are not-applicable). Tests:
`tests/test_ip_signoff_gate.py::test_ip_signoff_gate_contract_mutation_*`.

Remaining gap: `formal_status.json` itself is still trusted by
`check_verification_hardening` (status string + property count), and a *production*
IP like `mctp_assembler_v3` has no `INJECT_*` hooks, so it does not yet feed the
`contract_mutation` gate. The re-runnable evidence path exists and is demonstrated;
generating it for real production RTL (hook-free blanket + SEC on the actual
modules) is the next step.

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
