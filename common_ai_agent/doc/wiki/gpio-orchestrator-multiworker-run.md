# GPIO Orchestrator Multi-Worker Run

Status: active debug log for the `gpio_orch_scratch` scratch run on 2026-05-16.

Latest update: 2026-05-16 22:xx KST. Current run is using
`gpt-5.3-codex`, not `glm-5.1`; the active blocker is evidence routing and
stale generated artifacts, not model latency.

Related wiki:

- [[orchestrator-worker-handoff]] - orchestrator owns cross-worker scheduling.
- [[full-flow-pipeline]] - expected stage DAG.
- [[rtl-gen-ssot-contract]] - RTL must be generated from SSOT, not manually patched.
- [[golden-todo-evidence]] - PASS must be evidence-backed.
- [[gpio-serial-pipeline-run]] - prior serial GPIO evidence and repair-loop notes.

## Run Scope

| Item | Value |
|---|---|
| Scratch root | `/Users/brian/Desktop/Project/GPIO_ORCH_MULTIWORKER_TEST` |
| Source root | `/Users/brian/Desktop/Project/brian_hw/common_ai_agent` |
| IP | `gpio_orch_scratch` |
| UI | Atlas on `http://127.0.0.1:5421` |
| Workers | author `:5521`, verify `:5522` |
| Model | `gpt-5.3-codex`, medium effort |
| Policy | Do not manually patch generated RTL; fix common workflow/prompt/gate behavior and rerun |

## Current Evidence

Earlier pipeline `1c8741572c78` reached `rtl-gen` and stopped there.
That specific blocker has been improved by richer RTL gate packet context and
memory-owner inference.

Later pipelines reached `lint`, `tb`, and `sim`. RTL now compiles and lints
cleanly in the scratch run, but simulation still reports 37 scoreboard
mismatches. The latest evidence points to stale oracle artifacts, not a clean
RTL owner claim.

Positive progress:

- `rtl/rtl_compile.json`: `returncode=0`, `errors=0`, `diagnostics=0`.
- `lint/dut_lint.json`: `errors=0`; warnings remain.
- Manifest hierarchy and top/child port mismatch errors that appeared in
  earlier retries were reduced to zero compile/lint errors.

Current blockers:

- `sim/scoreboard_events.jsonl` reports 37 FL-vs-RTL mismatches.
- `model/functional_model.py`, `model/fl_model_check.json`, and
  `verify/equivalence_goals.json` are older than the current SSOT YAML.
- The current SSOT says APB write `pready` is always `1` for zero-wait
  handshake, while the stale generated FL/oracle path still expects `pready=0`
  for some write rows.
- `sim_debug` currently classifies all 37 failures as `rtl-gen` repair work,
  which is misleading when the oracle artifacts are stale.
- The Atlas UI server on `:5421` was started before the pipeline dependency
  fix, so a failed `sim` stage can still block `sim-debug` instead of allowing
  classification to run.

## Bugs To Fix

### BUG-001: Gate/tool-evidence packet has too little RTL context

Observed behavior:

- The `rtl_gate_tool_evidence` and `rtl_gate_evidence_closure` packets are
  owned by the top file, so the LLM mostly sees `rtl/gpio_orch_scratch.sv`.
- Actual diagnostics are in `rtl/gpio_orch_scratch_apb.sv`,
  `rtl/gpio_orch_scratch_irq.sv`, and sometimes sync/top interconnect.
- The packet asks the LLM to repair compile/lint/static evidence but does not
  provide enough full-file context for the files that must be edited.

Fix direction:

- Gate packets must include a current snapshot of all manifest RTL files.
- Gate packets must include an audit digest with open TODOs, static missing
  details, manifest signal-flow issues, and compile/lint summaries.
- Gate prompt rules must explicitly allow editing any implicated RTL file while
  keeping SSOT/FL/coverage authority locked.

### BUG-002: Tool-evidence closure is too coarse for lint warnings

Observed behavior:

- Compile/lint gates report only "not clean" in the TODO reason, while the
  actionable data lives inside `rtl_compile.json` and `dut_lint.json`.
- The LLM can miss style/warning-specific repairs unless those artifacts are
  injected directly into the packet prompt.

Fix direction:

- Preserve the tool artifact injection.
- Add an audit digest and all-file snapshot so warning ownership is visible.

### BUG-003: Unowned memory task remains after module mapping

Observed behavior:

- `memory.instances.gpio_in_prev_core` is still open with no RTL owner file.
- This is likely a derive-owner mapping weakness for memory/state items that
  are semantically owned by the sync/irq CDC path.

Fix direction:

- Do not invent manual RTL fixes.
- Improve owner inference or packet context so the LLM can place the memory
  state in the correct owner module from SSOT ownership refs.

Status:

- Fixed in `workflow/rtl-gen/scripts/derive_rtl_todos.py` by deriving memory
  owners from FunctionModel `state_update` ownership evidence.
- Covered by `test_derive_rtl_todos_assigns_memory_owner_from_function_state_update`.

### BUG-004: Worker result log path can be misleading during scratch testing

Observed behavior:

- The scratch HTTP worker reports a log path based on the run id before the
  file exists, and old worker logs can make status inspection confusing.

Fix direction:

- Treat this as scratch adapter hygiene.
- Source workflow correctness is still based on `logs/headless_run.json`,
  `rtl_compile.json`, `dut_lint.json`, and Atlas job state.

### BUG-005: UI state can show stale artifact summaries

Observed behavior:

- Pipeline screen can show the latest artifact summary even when the current
  pipeline stage is still queued/blocked.

Fix direction:

- UI should display run-scoped artifact version/run id when available.
- This belongs with the version/run-history work in [[rtl-version-run-history]].

### BUG-006: Failed sim blocks sim-debug classification in the pipeline DAG

Observed behavior:

- In a DAG run, `sim` can fail with scoreboard mismatches.
- `sim-debug` is the stage that should classify those mismatches and route the
  owner repair.
- The API dependency blocker treated failed `sim` as a hard stop for all
  downstream stages, so `sim-debug`, `coverage`, and `goal-audit` stayed
  blocked.

Fix direction:

- Pipeline mode must allow `sim-debug` to consume a failed `sim` artifact.
- CI mode may still stop immediately on `sim` failure.
- This distinction is required so pipeline mode can become an evidence-based
  repair loop.

Status:

- Fixed in `src/atlas_api_jobs.py` with an allowed failed-dependency edge:
  `sim -> sim-debug`.
- Covered by `test_sim_error_still_dispatches_sim_debug_for_classification`.
- Remaining operational note: the currently running Atlas UI process must be
  restarted before this API behavior is active in the live browser session.

### BUG-007: Fresh sim-debug evidence did not reopen closed RTL packets

Observed behavior:

- After `sim-debug` wrote `mismatch_classification.json`, a rerun of `rtl-gen`
  completed very quickly.
- The run did not reopen module packets because all previous RTL TODOs were
  already closed.
- That means a real repair loop could be skipped even when fresh downstream
  failure evidence exists.

Fix direction:

- When `sim/mismatch_classification.json` is newer than the RTL files and
  contains loopable `rtl-gen` classifications, reopen relevant module packets.
- Do not reopen human/contract-blocked packets automatically.

Status:

- Fixed in `src/headless_workflow.py` with fresh RTL repair evidence detection.
- Covered by
  `test_rtl_packet_work_batch_reopens_closed_module_packets_for_fresh_sim_debug_repair`.

### BUG-008: Stale FL/equivalence artifacts are misclassified as RTL bugs

Observed behavior:

- Current SSOT YAML is newer than `model/functional_model.py`,
  `model/fl_model_check.json`, and `verify/equivalence_goals.json`.
- The scoreboard mismatch rows are therefore comparing RTL against stale
  generated oracle artifacts.
- `sim_debug` still emits 37 `owner=rtl-gen` classifications, which sends the
  repair loop to the wrong workflow.

Fix direction:

- `workflow/sim_debug/scripts/compare_fl_rtl_results.py` must detect stale
  derived artifacts, not only stale sim result files.
- If FL/equivalence artifacts are older than SSOT, `sim-debug` should emit a
  stale-oracle classification owned by `fl-model-gen` or `equiv-goals`, then
  rerun downstream `tb-gen`, `sim`, `coverage`, and `goal-audit`.
- Do not let stale oracle evidence create 37 misleading RTL repair tickets.

Status:

- Fixed in `workflow/sim_debug/scripts/compare_fl_rtl_results.py`.
- Covered by
  `test_stale_derived_oracle_routes_to_fl_model_gen_instead_of_rtl`.
- Local replay on `gpio_orch_scratch` now reports:
  `status=stale`, one classification
  `classification=stale_oracle owner=fl-model-gen`, and zero `rtl-gen`
  classifications.
- Remaining validation: rerun the common pipeline from FL/equiv generation and
  verify whether regenerated oracle + TB + sim converges.

### BUG-008b: Headless pipeline stopped at sim before sim-debug

Observed behavior:

- The API DAG now allows `sim-debug` to consume a failed `sim` stage, but the
  direct headless pipeline loop returned immediately on `sim` failure.
- That prevents owner classification in the common headless path and makes the
  pipeline behave like CI mode.

Fix direction:

- In pipeline mode, a failed `sim` should continue directly to `sim-debug`.
- Intermediate downstream stages such as `coverage` should wait until
  `sim-debug` has classified the failed sim evidence.
- If `sim-debug` produces a loopable owner repair, route to that owner. If it
  cannot classify, return the original sim failure.

Status:

- Fixed in `src/headless_workflow.py`.
- Covered by
  `test_pipeline_continues_failed_sim_to_sim_debug_for_owner_routing`.

### BUG-009: TB stimulus/runtime has secondary gaps after oracle freshness

Observed behavior:

- The generated cocotb test starts the manifest clock only when it matches
  `pclk`; `core_clk` is an input but is not driven as a real independent clock.
- Some FunctionalModel goals such as `FM_READ_DATA_IN` miss APB setup signals
  because CSR detection is based on naming rather than transaction
  preconditions.
- Illegal-offset stimulus can still use `paddr=0`, which weakens negative-path
  evidence.

Fix direction:

- Fix stale oracle routing first.
- Then improve `tb-gen` runtime generation so stimulus comes from goal
  preconditions/constraints rather than transaction-name heuristics.
- Keep this as TB owner work, not manual test patching.

Status:

- Open secondary blocker. Validate after BUG-008 is fixed and FL/equiv artifacts
  are regenerated.

### BUG-010: Stage-filtered repair loop can skip the classified owner

Observed behavior:

- A focused rerun used
  `ATLAS_HEADLESS_PIPELINE_STAGES=fl-model-gen,equiv-goals,tb-gen,sim,coverage,sim-debug,goal-audit`
  to regenerate stale oracle artifacts.
- After regeneration, `sim-debug` correctly found real mismatches again:
  31 classifications, all `owner=rtl-gen`.
- The repair sequence was filtered by the debug stage list, so `rtl-gen` and
  `lint` were dropped and the next iteration started at `tb-gen`.
- The pipeline then stopped with repeated `rtl-gen` mismatch evidence even
  though the owner repair stage had not actually run.

Why it matters:

- This is a "pass/fail for the wrong reason" risk. A pipeline must never claim
  an owner repair was attempted when a stage filter excluded the owner.

Fix direction:

- When a repair owner is classified, the owner workflow and its required local
  verification prefix must be kept even if a debug-stage filter is active.
- For `rtl-gen`, this means at least `rtl-gen` and `lint` must precede
  downstream `tb-gen/sim/sim-debug`.

Status:

- Fixed in `src/headless_workflow.py`.
- Covered by
  `test_pipeline_repair_sequence_keeps_owner_when_stage_filter_excludes_it`.

## Latest Run Snapshot

Run at 2026-05-16 21:55 KST:

- `fl-model-gen`: PASS; regenerated `functional_model.py`,
  `fl_model_check.json`, `decomposition.json`, and `fcov_plan.json` from the
  current SSOT.
- `equiv-goals`: PASS; regenerated 54 required goals, 0 blocked.
- `tb-gen`: PASS; generated goal-driven cocotb/scoreboard.
- `sim`: FAIL with 31 scoreboard mismatches; cocotb itself passes but
  scoreboard emits `SOFT_EQ_MISMATCH`.
- `sim-debug`: PASS-as-router; writes 31 loopable classifications,
  all `classification=rtl_bug owner=rtl-gen`.
- `pipeline`: BLOCKED because the debug stage filter skipped actual `rtl-gen`
  repair before the repeated signature guard fired.

Next run should use the fixed repair sequence so `rtl-gen` and `lint` execute
before downstream TB/sim classification.

## Stop Rule

Do not call the run green until:

1. `rtl-gen` returns PASS from the common stage engine.
2. Downstream `lint`, `tb-gen`, `sim`, `coverage`, `sim-debug`, and
   `goal-audit` either pass or produce owner-routed repair evidence.
3. The Pipeline UI shows the same stage/run status as `/api/jobs` and disk
   artifacts.
