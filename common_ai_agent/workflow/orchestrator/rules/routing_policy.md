# Orchestrator Routing Policy

Authoritative routing table. The orchestrator agent consults this file before every dispatch decision.

## Owner → Workflow Map

| `sim_debug` owner | Dispatch | Payload hints |
|---|---|---|
| `rtl_bug` | `rtl-gen` | `{scope: [failing_modules], reason: "owner=rtl_bug", goal_ids: [...]}` |
| `tb_bug` | `tb-gen` | `{scope: ["scoreboard"], reason: "owner=tb_bug · observable missing", goal_ids: [...]}` |
| `stale_oracle` / `owner=fl-model-gen` | `fl-model-gen` with `stages=["equivalence"]` | Regenerate derived FL/equivalence/coverage oracle artifacts from current SSOT before RTL/TB repair |
| stale `fl_rtl_compare.json` or stale `mismatch_classification.json` | `sim_debug` | Refresh compare/classification first; do not route from an artifact older than fresh sim/equivalence evidence |
| `frontier` | escalate to human | Write `<ip>/review/frontier_<n>.json` — do not auto-dispatch |
| `coverage_gap` | `tb-gen` → `sim` → `coverage` | Loop; budget 2 |
| `lint_violation` | `rtl-gen` | `{scope: ["style"], lint_rules: [...]}` |
| `compile_error` | `rtl-gen` | `{scope: [bad_module], replay_packets: true}` |

## Stage → Downstream Map (canonical DAG)

| Just passed | Next dispatch candidates (parallel if independent) |
|---|---|
| `ssot-gen` | `fl-model-gen` with `stages=["fl-model", "cl-model"]` (parallel/DAG), then `stages=["equivalence"]` after both pass |
| `fl-model` ∧ `cl-model` | `fl-model-gen` with `stages=["equivalence"]` |
| `equivalence` | `rtl-gen` |
| `rtl-gen` | `lint`, `tb-gen` (parallel); `syn` only if Run Mode = signoff |
| `lint` | (gate only — no dispatch unless lint failed) |
| `tb-gen` | `sim` |
| `sim` (passed all goals) | `coverage` |
| `sim` (mismatches) | `sim_debug` |
| `sim_debug` | route by owner (see Owner → Workflow Map) |
| `coverage` (gaps) | `tb-gen` (loop) |
| `coverage` (full) | `contract-reflection` |
| `contract-reflection` (pass) | `goal-audit` |
| `contract-reflection` (blocked/fail) | route by `contract_owner_routing.json` |
| `goal-audit` | escalate to human for sign-off |
| `syn` | `sta`, `pnr` (parallel) |
| `pnr` | `sta-post` |
| `sta-post` | `goal-audit` |

## Parallelism Rules

- Two stages may run in parallel only if neither depends on the other.
- RTL todos within `rtl-gen` use packet-parallel (`ATLAS_HEADLESS_RTL_PACKET_PARALLEL=1`, default 3 sub-agents).
- Never run `sim` while `rtl-gen` for the same scope is still authoring — wait.

## Gate Rules

- `contract-reflection` is deterministic validation. It reads requirements, obligations, contract refs, stage reflection, scoreboard evidence, and wave/static artifacts. On fail/block, dispatch the reported owner workflow.
- `goal-audit` does not dispatch — it reads. Run only when every required upstream stage is `passed` with fresh evidence.
- `human-review-escalation` does not have a worker — write a review card and pause.
- `goal-audit` failure → escalate; do not auto-retry the whole pipeline.

## Stop Conditions

The orchestrator must stop the loop and surface to the user when:

1. Retry budget exhausted (see `retry_budget.md`)
2. `sim_debug` reports `frontier` owner
3. `goal-audit` fails with `unresolved_review_decisions > 0`
4. User typed `freeze` / `stop` in chat
5. A worker returns HTTP 403 (workflow binding guard) — surfaces multi-user conflict
6. SSOT structural invariant fails (`require_top_sub_module_consistency`) — escalate to ssot-gen with `/grill-me`

## Run Mode Filter

Before dispatching any stage, check `state.run_mode`:

- `starter` — skip `syn`, `sta`, `pnr`, `sta-post`, `coverage` (full), `goal-audit`. Stop at first green `sim`.
- `engineering` — full DAG up to `goal-audit`, including `contract-reflection`, skip EDA sign-off chain unless asked.
- `signoff` — full DAG including EDA sign-off. Require human approval on every escalation.
