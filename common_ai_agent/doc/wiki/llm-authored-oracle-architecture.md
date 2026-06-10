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

## Status

- Direction approved by user 2026-06-10; not yet implemented.
- hx3 (`apb_watchdog_v1`) intentionally left at 47/55 — its 8 remaining
  failures (KICK write-side-effect class + timeout strobe sampling + reset
  window) are the acceptance test for FL migration step 1.
- Phase-2 headless features (req-contracts stage, projection brief,
  stage retries) are orthogonal and remain.

Related: [[headless-stage-validation-phase2-20260610]],
[[verification-contract-model]], [[workflow-improvement-candidates]],
[[stage-validation-reflections-20260610]].
