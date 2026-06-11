# LLM-Authored Oracles (FL/CL/TB) + Contract Validation — Design Direction (2026-06-10)

User decision (2026-06-10): **FL, CL, and TB should be LLM-authored rather than
deterministically compiled; honesty moves to contract validation.** The
deterministic emitters stop absorbing ever-richer hardware semantics and
demote to baseline/cross-check oracles.

Generalized principle (user, same day): **delegate generation to the LLM
broadly; the system's load-bearing job is EVIDENCE VALIDATION.** Wherever a
deterministic generator exists mainly to keep the LLM honest, prefer
LLM-authored artifacts gated by machine-checkable evidence (contracts,
mutation, cross-oracles, provenance, disk/sim evidence batteries). Determinism
is for VALIDATORS — gates must stay deterministic, reproducible, and
content-semantic; generators need not be. This matches where the system was
already strongest: the phase-1/phase-2 walks showed the gates are real
([[stage-validation-reflections-20260610]] "the gates are the work queue"),
so the gates — not the generators — are the trust anchor.

## Why (the motivating failure)

Third headless IP `apb_watchdog_v1` ([[headless-stage-validation-phase2-20260610]])
stalled at sim 47/55 on a class the deterministic FL **cannot express**: a
write-triggered side effect (KICK write reloads COUNT from TIMEOUT). The FL
oracle applies exactly one transaction per goal and mirrors register VALUES via
`state_variables[].source` — "a write to X loads Y from Z" has no projection.
Each such idiom (strobes, write-side-effects, multi-event flows) forces another
semantic into `emit_fl_model.py`; the compiler is becoming an interpreter of an
open-ended SSOT semantics language. The pulse-counter family fit it; a watchdog
already does not. This is the same trajectory that made fixed TB templates fail
before IP-specific datapath stimulus ([[project-mctp-v3-datapath-tb]] arc).

## Architecture

Same pattern the repo already uses for RTL (LLM-authored + provenance + gate
battery). FL/CL/TB stop being special:

- **Authority**: locked req bundle + SSOT stay the single semantic truth.
  LLM-authored FL/CL/TB are *projections* of it, like RTL.
- **Authoring**: per-IP Python FL (`model/functional_model.py`), CL, and the
  cocotb TB authored by the LLM from the SSOT function/cycle model + locked
  contracts. The current emitters' OUTPUT becomes scaffolding/reference input,
  not the artifact.

### FL/CL/TB Contract gates (the load-bearing layer)

1. **SSOT semantic-conformance gate** — execute every SSOT
   `function_model.transactions[]` (preconditions, output_rules,
   state_updates, invariants) and locked behavioral-contract rule against the
   LLM oracle; content-semantic comparison, not count-semantic
   ([[project-mctp-v3-trust-campaign]] lesson). Blocking on any divergence
   without an SSOT-cited waiver.
2. **Mutation gate** — inject mutations into the LLM oracle (and stimulus);
   the scoreboard must catch them. Gate criterion is `unknown == 0`, not kill
   rate ([[project-contract-mutation-gate]] pattern).
3. **Dual-oracle cross-check** — keep the deterministic emitter FL/CL as a
   BASELINE oracle. Wherever the deterministic semantics are expressible, the
   LLM oracle must agree; divergence raises a blocking question. This is the
   primary defense against **correlated error** (the same LLM authoring both
   RTL and its oracle, making equivalence vacuous).
4. **Provenance gate** — FL/CL/TB get authoring provenance + operator-edit
   detection, exactly like `rtl_authoring_provenance.json`.

### Correlated-error defenses (beyond gate 3)

- FL authored from `function_model` semantics; RTL authored from rtl todos —
  separate calls, separate artifact diets; cross-model authoring when
  available.
- Locked behavioral contracts' `pass_condition`s are evaluated against sim
  evidence independently of the oracle (VCM evidence ladder), so a co-wrong
  oracle+RTL pair still fails contract closure.

### Migration order

1. **FL first** (the watchdog blocker): add an LLM authoring path in
   `fl-model-gen` + gates 1–4. Deterministic emitter remains and feeds gate 3.
2. **CL second** (same gates; `cosim` lockstep gets the expressiveness it has
   been missing for multi-event flows).
3. **TB third** — the goal-runner template stays as harness, but per-IP
   stimulus/checking moves to LLM authorship (already proven manually in the
   mctp datapath-TB campaign), gated by the tb/sim evidence battery + mutation.

### Explicitly rejected alternative

Continuing to grow deterministic emitter semantics (e.g. the started-and-
abandoned `csr_write` transaction-side-effect extension). It fixes one idiom
per change, the idiom list is open-ended, and every addition risks the
regression matrix (three template regressions in one day: op/addr mirroring,
event-vs-resting assigns, last-write visibility). The deterministic layer's
durable value is as a *baseline oracle*, not the authoring path.

## Implemented: FL/CL semantic-conformance gate (gate 1, first slice — 2026-06-11)

User restated the principle directly (2026-06-11): **"Locked Truth 기준 LLM 이
작성 → Evidence Validation" — apply it to FL *and* CL uniformly.** First concrete
slice of gate 1 (SSOT semantic-conformance) now ships for both models:

- **FL**: `workflow/fl-model-gen/scripts/validate_fl_semantics.py` →
  fictional **state** (an FSM / `state_updates` / undeclared `state_variables`
  projected onto a `cycle_model_waiver=true` combinational IP).
- **CL**: `workflow/fl-model-gen/scripts/validate_cl_semantics.py` →
  fictional **timing** (a valid/ready handshake, FSM-terminal `ordering`,
  pipeline/backpressure, `outstanding>1`, or multi-cycle / unbounded
  `latency` on a cycle-waived IP). The cycle-domain twin of the FL gate.

Each gate has the same two layers and the same honesty contract:

1. **Deterministic FAST-PATH backstop** (no LLM): high-precision, zero
   false-positive. Fires only when *every* behavioral contract is explicitly
   `cycle_model_waiver=true`. Verified: flags `add8_cin_v1` (5 fictional-timing
   violations on CL; fictional FSM on FL); does **not** flag the genuinely
   sequential `cnt8_en_v1` / `mctp_assembler_v2`.
2. **LLM judge** (`gpt-5.4`, `ATLAS_{FL,CL}_SEMANTIC_JUDGE_MODEL`): per-contract
   decision-table-vs-model verdict for the cases the flag does not cover.
3. **Safe degradation**: when the real LLM is unavailable the judge records an
   explicit `llm_judge.status=not_run` — never a silent pass. The deterministic
   layer still gates.

Wiring: `emit_fl_model.py` / `emit_cycle_model.py` run the gate, fold the verdict
into `fl_model_check.json.semantic_validation` / `cl_model_check.json.
semantic_validation`, and AND it into the artifact's `passed` (so a fictional
model exits non-zero and never reaches sim). Flags: `--no-semantic`,
`--no-semantic-llm`. Evidence: `tests/test_validate_cl_semantics.py` (7 cases).

### Root fix — the criterion lives in the locked truth, not an optional flag

User direction (2026-06-11): **"명확한 기준이 truth에 있어야지"** — the
combinational/sequential criterion must be IN the locked truth. The first cut of
the backstop fired only on the **explicit** `cycle_model_waiver=true` flag, which
the normal req-gen path doesn't set, so `mux4_v1` (combinational, authored
without the flag) kept the same fictional timing as `add8` yet the no-LLM layer
stayed silent.

The naive structural inference ("no state ⇒ combinational") is **unusable**: the
generic SSOT template fabricates an FSM + `state_variables` on combinational IPs
too (`add8`, `mux4`, `cnt8` all carry a fictional FSM), so *absence of state* is
not a signal. The reliable signal is the **locked decision table's own
vocabulary**: a genuinely sequential contract cannot specify its behaviour
without clock/cycle/reset/handshake/state language (`cnt8`: "rising clk", "next
cycle", "async", "+="; the timer's `cmd_valid/cmd_ready` handshake), while a
combinational contract is a pure input→output function (`mux4`: "sel=0 ⇒ y=d0";
`add8`: "{cout,sum}==a+b+cin"). So `cycle_model_waiver` is now **derived
deterministically from the decision table** in the shared truth authority
(`behavioral_contracts._cycle_model_waived` / `_contract_is_combinational`): a
contract with a readable table, no `state_transitions`, and none of the
sequential vocabulary (`_SEQUENTIAL_TOKEN_RE`) is combinational — waived by the
truth itself, flag or no flag. The explicit flag remains an override, and a flag
that **contradicts** a clocked decision table is now a hard projection issue
(`compare_behavioral_to_function_cycle`), so the criterion stays consistent with
the truth.

Result: `mux4_v1` is now caught by the deterministic backstop with no LLM and no
flag; `cnt8_en_v1` / `mctp_assembler_v2` stay PASS (their decision tables carry
the sequential vocabulary). Safety direction is deliberate — over-tagging a
combinational contract as sequential just falls back to the LLM judge, whereas
mis-waiving a sequential contract (the dangerous case) requires *every* token to
be absent from a clocked spec, which does not happen. Closes
`OBL_TRUTH_COMBINATIONAL_WAIVER_AUTOSET`.

## Status

- Direction approved by user 2026-06-10. **Gate 1 first slice (FL+CL
  semantic-conformance, deterministic backstop + LLM judge) implemented
  2026-06-11**, with the waiver criterion **derived from the locked decision
  table** (root fix, same day). Gates 2–4 (mutation / dual-oracle / provenance)
  and the full LLM-authoring path still pending.
- hx3 (`apb_watchdog_v1`) intentionally left at 47/55 — its 8 remaining
  failures (KICK write-side-effect class + timeout strobe sampling + reset
  window) are the acceptance test for FL migration step 1.
- Phase-2 headless features (req-contracts stage, projection brief,
  stage retries) are orthogonal and remain.

Related: [[headless-stage-validation-phase2-20260610]],
[[verification-contract-model]], [[workflow-improvement-candidates]],
[[stage-validation-reflections-20260610]].
