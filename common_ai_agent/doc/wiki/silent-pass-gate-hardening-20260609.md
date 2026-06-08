# Silent-PASS Gate Hardening

Date: 2026-06-09

Branch: `fix/silent-pass-gate-hardening` (off `main`, not yet merged)

This page records the silent-PASS hardening effort and — most importantly — the
**remaining TODO** so the next session can continue.

## Why

The recurring failure mode in this repo is **content-blind gates**: a workflow
check passes on *existence / keyword / key-presence* instead of *content*, so a
hollow artifact turns green. See `[[log]]` history and the
`project_silent_pass_exposure` / `project_contract_mutation_gate` memories.

## What landed (done)

### A — per-gate fixes (symptoms), each guarded by mutation/negative tests
- **tb contract-ledger** (`workflow/tb-gen/scripts/derive_tb_todos.py`): substring
  `"EquivalenceScoreboard"` → real `ast` import/usage; empty-stub body floor;
  reject empty scoreboard rows + empty `scenario_id` (validate all rows, dropped
  the 32-row cap); `coverage.json` status-missing now fails.
- **resume matcher** (`core/chat_loop.py::_is_execution_resume_request`):
  unanchored substring → negation/`"진행 상황"` guards first + word-boundary cues
  + length cap, so `"don't continue"` / `"discontinue"` no longer hijack a STOP.
- **req gate** (`src/workflow_stage_engine.py`): manifest-absent skip is now a
  **visible** `contract_authority_gate_skipped` run (was a silent `None`, then a
  same-label rc-0 run indistinguishable from a pass); coverage stage now
  auto-runs `derive_tb_todos.py --audit-evidence` (was hand-run only).

### B — the meta-gate (process fix): `tests/test_gate_self_test.py`
A gate is not trusted until it proves it rejects bad input.
- `GateSelfTest` harness: known-good fixture must pass; every mutation must be
  rejected (kill-all).
- `GATE_REGISTRY` is the single source of truth.
- **Ratchet** (`test_every_manifest_gate_is_registered`): any gate-shaped command
  in `workflow/STAGE_MANIFEST.json` that is not registered fails the suite — a new
  hollow gate cannot ship unacknowledged. Proven killable.
- `UNCOVERED_GATES` is an explicit, FROZEN backlog (printed each run); it can only
  shrink by a reviewed change. Goal: `UNCOVERED_GATES == {}`.

### Covered gates (4)
| gate | script | notes |
|---|---|---|
| tb_contract_ledger | `derive_tb_todos.py` | was actually broken; fixed in A |
| req_contract_authority | `check_contract_bundle.py` | already enforcing; anchor-only + tamper-without-rehash |
| scoreboard_events | `check_scoreboard_events.py` | already enforcing; empty/vacuous/FL-copy/no-model_api |
| ip_signoff | `check_ip_signoff.py` | already enforcing; missing ip_contract/truth_coverage/stale provenance/missing observable |

Observation: only the tb gate was genuinely broken. req/scoreboard/signoff were
already content-enforcing — the meta-gate *proves and locks* that.

## Remaining TODO — retire the 7-gate backlog

Each item = write a `GateSelfTest` (good fixture + mutation battery that the gate
must reject), move it from `UNCOVERED_GATES` to `COVERED_GATES`, and update the
frozen set in `test_uncovered_backlog_is_explicit_and_frozen`.

Priority — content gates first (higher silent-PASS risk):
1. `check_truth_coverage.py` — locked-truth obligation coverage. Fixture source:
   `tests/test_truth_coverage_gate.py::_write_direct_ssot_ip` (passing case at rc 0).
2. `run_contract_check.py` — contract-reflection closure (+ `--require-contract-closure`
   strict). Fixture source: `tests/test_contract_reflection_gate.py` / `test_contract_check_command.py`.
3. `derive_rtl_todos.py --enforce` — RTL final static/todo closure gate.

Lower value — structural / tool gates (silent-PASS risk low; do last or skip):
4. `ssot_coverage_summary.py` — functional coverage summary. Fixture: `tests/test_coverage_summary.py`.
5. `check_tb_python_compile.py` — pre-sim TB python compile gate.
6. `dut_lint_report.py` — DUT lint/suppression gate.
7. `rtl_compile_report.py` — DUT RTL compile gate.

Recipe for one item:
1. Find an existing test that builds a *passing* fixture for the gate (grep the
   gate script name under `tests/`); reuse its `_write_*`/`_make_*` helper.
2. `build_good` → invoke the gate exactly as `STAGE_MANIFEST` does (same flags).
3. Mutations: degrade one enforced property each (prefer mutations already proven
   to fail by that gate's existing negative tests). Watch for non-idempotent
   fixtures (e.g. `_make_ip` needs an `rmtree` before rebuild).
4. Register `COVERED_GATES`, remove from `UNCOVERED_GATES`, update the frozen set.
5. `pytest tests/test_gate_self_test.py -q` → green.

## Residual / notes
- skip≠pass was resolved (distinct `contract_authority_gate_skipped` label).
- The tb ledger gate is engine-internal (not a `STAGE_MANIFEST` stage command), so
  the manifest is not the complete gate list — the registry holds the truth.
- `mutation_guard.py` is `ADVISORY_NOT_GATE` (advisory kill-rate, no pass/fail
  contract) — no self-test required.

## Next operational step
Merge `fix/silent-pass-gate-hardening` to `main` (8 commits) when ready, then
resume the backlog from item 1.
