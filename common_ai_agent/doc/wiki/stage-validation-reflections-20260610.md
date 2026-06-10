# Stage-Validation Reflections — Design Inputs for the Headless Worker (2026-06-10)

Personal retrospective from walking pulse_counter_v1 through req→ssot→fl/cl→
rtl→tb→sim by hand (every gate executed, [[stage-validation-pulse-counter-20260610]])
and then fixing the machinery to an honest 31/31 full-pipeline PASS. Written
as design inputs for the phase-2 headless worker, not as a run log.

## 1. The gates are real — design around being caught

The most convincing moments were the ones where the gates caught *me*:
direct-edit RTL caught by the provenance gate, literal waits caught by the
magic-number gate, a `passed: true`-only check file rejected for lacking
per-contract rows. Seven stages produced zero silent passes. Implication for
the headless worker: do NOT build bypasses or "temporary" overrides — build
the worker to *expect* rejection and route every rejection back to the owning
artifact. The gate message is the work queue.

## 2. The expensive bugs are the silent ones

Actionable gate errors cost minutes ("add stage_contracts[]" → fixed).
What cost hours was code that silently did nothing:

- `_apb_write_one` compared port names against literal uppercase `"PSEL"` —
  lowercase-port DUTs got a multi-cycle no-op, no error, no log. Only VCD
  archaeology (psel never toggled) cracked it.
- `emit_timing_header` silently skipped `cycles:` keys → empty header →
  ImportError much later.
- `ssot_to_rtl` preflight silently skipped the rtl_contract write on
  soft-question runs → SSOT rule renames never propagated, forever.

Rule of thumb that held all session: **code that rejects is cheap; code that
stays silent is expensive.** When adding machinery, prefer a loud error or a
logged skip over a quiet fallthrough. (Also: my own `| tail` pipe masked a
gate's exit code — measurement bugs look exactly like system bugs; check the
measurement first.)

## 3. Generality comes from the second concrete case, not from abstraction

Mid-campaign I drifted into tuning the testbed IP; the question "왜 특정 IP를
위한 것을 만들고 있어?" reset the discipline. The operative test became: *can
this change be justified on mctp too?* Concretely, I tried kind-based
machine_spec inheritance twice and was wrong in both directions (under- and
over-inheriting). The correct rule appeared only when I stopped guessing
categories and mirrored what the oracle actually does: a goal inherits the
spec of the transaction the FL resolves for it. Generality = mirror the
authoritative mechanism + regression on a second IP; never category
heuristics.

## 4. Freshness is the dominant failure mode, and that IS the headless worker's job

Roughly half of all debugging was staleness, not logic: stale rtl_contract
after SSOT rule renames, stale repair-mirrored copies *inside* the SSOT,
provenance todo_plan_sha drift, FL signature drift after SSOT edits, TB
regeneration clobbering the timing patch. The dependency-ordered regeneration
chain that a human reliably forgets is exactly what the worker must encode:

```
SSOT edited →
  repair_ssot_schema → verify_ssot/design_spec_trace
  → emit_fl_model → emit_cycle_model → (contract-evidence join) →
    emit_model_signature → emit_equivalence_goals → check_model_contract_trace
  → ssot_to_rtl preflight (contract refresh) → derive_rtl_todos →
    refresh_rtl_provenance → --audit-rtl
  → emit_goal_scoreboard_cocotb → emit_timing_header → (timing-constant patch)
    → tb gates → sim → sim gates
```

The worker's essence is not LLM calls; it is running this chain in order and
never skipping a link.

## 5. Claims and observations live at different layers — descend the ladder

Logs said "timeline executed 6 steps"; the VCD said the APB bus never moved.
Both were true. scoreboard row → cocotb log → VCD is a ladder, and root cause
lived at the bottom every time. The worker should keep the ladder cheap:
always emit scoreboard_events.jsonl AND the VCD, and on escalation hand
sim_debug the signal list it needs rather than prose.

## 6. Semantics that must move from wiki into error messages/templates

Authoring contracts a new IP author WILL trip over, currently documented but
not enforced:

- FL `output_rules` evaluate against PRE-transaction state ("read-back shows
  the post-edge count" is authored as `count + 1`).
- Timelines that verify read-data must end with `csr_read` so the DUT's
  read-data is fresh at the sample point.
- Scenario `transaction:` must name the FM transaction explicitly (alias text
  matching mis-binds).
- per_goal_reset implies the FL oracle resets per goal (now automatic) and
  fl_apply_count must match the timeline's event count.

Each of these deserves a validator message or a scaffold comment, not just a
wiki line. The two pytest regressions this session were caught only because
someone had pinned tests — the new emitter behaviors still owe that debt.

## One line

The system already works as a machine that *forces honesty*; what remains is
eliminating silence and automating freshness — which is precisely the headless
worker's charter, and the manual walk produced its blueprint.

Related: [[stage-validation-pulse-counter-20260610]],
[[workflow-improvement-candidates]] (CAND-06..11),
[[orchestrator-headless-worker-feedback]].
