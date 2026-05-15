# Wiki Log

## 2026-05-16

- New top-level ATLAS screen: [[atlas-pipeline-screen]] (`◫ Pipeline`,
  branch `feature_pipeline_ui`). Replaces the mock `◫ Architect`
  screen. Each of the 14 canonical stages becomes a click on a stage
  card with a 3-5 dot KPI scoresheet read from on-disk evidence JSON;
  the DAG MAP at the top shows token-flow animation along edges from
  running stages. Failed cards offer `[ go fix <owner> ]`, never
  `[ retry ]`, per [[workflow-ownership-and-boundaries]]. Live state
  served from a new `GET /api/pipeline/state?ip=<ip>` endpoint that
  composes `_job_artifact_recovery` + the existing `/api/jobs` poll +
  per-stage evidence JSON readers.
- New wiki page [[ui-design-references]] documents external UI
  checkouts under `~/Desktop/Project/brian_hw/external_refs/`.
  First entry: `nexu-io/open-design` (Apache-2.0). Pattern map: their
  `Theater/ScoreTicker` → our `MiniScoresheet`, `PanelistLane`
  `data-role` borders → our phase-band tints, `runtime/todos.ts`
  reverse-walk → our running-card mini-todo list, `InterruptButton`
  Esc keybind → our running-card `⏹`, `LiveArtifactBadges` → our
  state badges. Conceptual borrowing only — no code copied, no
  CSS / fonts / OKLch palettes / Next.js machinery imported.
- New IP run captured: [[arm-m0-min-pipeline-run]] — first CPU-class IP
  driven end-to-end through `ssot-gen → fl-model-gen → rtl-gen → tb-gen →
  sim → lint` with green compile/lint/sim/coverage on the headless
  surface (`gpt-5.3-codex`, `/mode pipeline`). 8 SV files (22 KB),
  scoreboard 37/37 with 0 mismatches, 35/35 fcov bins hit, lint clean.
  Detailed report at `arm_m0_min/PIPELINE_SUMMARY.md`. Open ledger
  items (8) classified as: 1 self-counter, 3 out-of-plan-scope
  (cl-model-gen / formal / production governance), 4 derive-tool
  false positives (same family as the uart_lite trial's "30 owner-file
  mismatches as tool bug"). Three workflow improvement candidates
  surfaced:
  1. `repair_ssot_schema.py` should normalize C/Verilog ternary and
     bit literals (`cond ? a : b`, `32'h0`, `1'b1`) inside `expr`
     strings — `emit_fl_model.py` crashes on these with SyntaxError.
  2. `rtl-gen` system prompt should require
     `rtl/rtl_authoring_provenance.json` emission as a closing artifact
     (schema: agent, workflow, surface, model_profile, ssot,
     rtl_files, todo_plan, todo_plan_sha256, toolchain).
  3. `react_loop` should stop on idle once the agent declares done,
     not run out the iteration cap doing nothing — ~50 min of the
     ~3 h wall-time on this run was post-completion idle.
- Updated [[rtl-version-run-history]] with the arm_m0_min row.
- New wiki page [[deterministic-emit-stages]] documents why fl-model-gen / cl-model-gen run with 0 LLM calls, what SSOT contract this places on the upstream ssot-gen LLM, and what failure modes (`SyntaxError`, helper unknown, etc.) mean for ownership. Also captures the cl-model-gen entry point: `/ssot-cycle-model <ip>` lives inside the `fl-model-gen` workspace (no separate `workflow/cl-model-gen/` directory).
- New wiki page [[karpathy-llm-wiki-pattern]] captures Andrej Karpathy's LLM Wiki concept (3-layer markdown architecture, frontmatter schema, ingest/query/lint/log operations, no RAG / no vector DB) and the gap analysis against the current `doc/wiki/`. Frontmatter rollout and lint extension are parked as follow-ups; the discussion itself is now searchable.
- New script `workflow/wiki/build_graph.py` emits `doc/wiki/_graph.json` (schema `wiki_graph.v1`) by parsing every wiki `.md`, optional YAML frontmatter, and `[[refs]]`. Initial index: nodes=15, edges=58, broken_refs=0. `--check` exits non-zero on broken refs so CI/lint can catch dangling wiki links.
- Addressed the three workflow improvement candidates surfaced by the arm_m0_min run:
  1. Confirmed `repair_ssot_schema.py` already normalizes C ternary (`cond ? a : b` → `(a if cond else b)`), full Verilog bit literals (`32'h0`, `1'b1`, `8'hff`), and SystemVerilog unsized fills (`'0`, `'1`, `'x`, `'z`) inside `expr` strings. Verified with a regression matrix; no further patch needed.
  2. `workflow/rtl-gen/system_prompt.md` now states the provenance JSON schema explicitly and tells the LLM rtl-gen agent NOT to write `rtl/rtl_authoring_provenance.json` directly — the engine (`src/headless_workflow.py`, `workflow/rtl-gen/scripts/ssot_to_rtl.py`) already auto-emits it at end of every rtl-gen run.
  3. `lib/iteration_control.detect_completion_signal` now recognizes narrative-end phrases ("pipeline complete", "all tasks finished", "everything is done", "nothing more to do", "✓ loop ended", "all workflows complete", "all stages passed", "run finished", …) in addition to the strict sentinel tokens. The react_loop's existing completion path at `core/react_loop.py:1266` now exits on the same plain-English declarations the LLM emitted on the arm_m0_min run, removing the ~50 min post-completion idle.

## 2026-05-15

- Created the tracked project wiki map for common_ai_agent under `doc/wiki/`.
- Added cross-linked pages for flow, ownership, todo evidence, provider call accounting, and human escalation.
- Captured the no-direct-generated-artifact-edit rule for pipeline tests.
- Pipeline smoke test (`gray_counter`, gpt-5.3-codex) under `_runspaces/test_pipeline_gpt53/`:
  - PASS: ssot-gen, fl-model-gen (after helper fix), cl-model-gen, dual-fcov, equiv-goals.
  - FAIL: rtl-gen audit. compile/lint clean, but `GC_TXN_ADVANCE.outputs.output_0` missed `bin`/`bin_state` static evidence (RTL-0062). owner = `rtl-gen` repair, no manual patch.
- Workflow source fix in `workflow/fl-model-gen/scripts/emit_fl_model.py`: registered canonical bit helpers (`gray_to_bin`, `bin_to_gray`, `popcount`, `parity`, `clog2`, `min`, `max`, `abs`) in the rule env and in `known_names`, so SSOT expressions may reference them without `run_self_check` shadowing the callable with a stub integer.
- Workflow source fix in `workflow/tb-gen/runtime/equivalence_scoreboard.py`: `_seed_rule_fields` now pulls helper names from the generated `FunctionalModel._default_rule_helpers()` and adds them to `known`, so the scoreboard does not stub callable helpers as integer stimulus fields.
- Pipeline smoke test continued — rtl-gen repair iteration passed, but sim FL-vs-RTL produced 11 SOFT_EQ_MISMATCH cases. Initial sim-debug classification attributed all 11 to `rtl-gen`.
- Workflow source fix in `workflow/sim_debug/scripts/compare_fl_rtl_results.py`: added a stimulus-vs-transaction-kind consistency check (`_stimulus_contract_violation`) that resolves to `tb-gen` when the TB drives control signals inconsistent with the named transaction kind (e.g., kind=`synchronous_clear` but `clear=0` and `enable=1`). After the patch the classification became 9 `tb-gen` / 2 `rtl-gen`, matching the true root cause: the deterministic TB stimulus generator does not encode transaction-kind preconditions.
- Confirmed limitation worth recording: `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py` is a deterministic generator (not an LLM), so re-running tb-gen reproduces the same stimulus pattern. The proper repair is to teach the generator (or its prompt for LLM-generated sequences) to honor transaction preconditions when driving control signals.
- Q&A history scope fix: an `mctp_assembler` grill-me session showed old GPIO entries in the UI even though `.session/2076604/mctp_assembler/ssot-gen/qa.json` did not contain GPIO. The backend QA board was scoped correctly; the browser ask_user history migration accepted legacy localStorage entries with no `session`/`ip` metadata. `workspace.jsx` now rejects scope-less legacy history when a real session/IP is active. Verified with `tests/test_atlas_qa_history_scope.py` and `tests/test_atlas_multiuser_session_scope.py` (`12 passed`).
- gpio pipeline smoke test (gpt-5.3-codex): ssot-gen / fl-model-gen / cl-model-gen / dual-fcov passed; equiv-goals blocked (sub_module `gpio_input_sampler` had no function_model_refs); rtl-gen returned `human_gate` from preflight (cyclic output dependency on `din_q_masked_next`, sample_condition not in DSL).
- Workflow source fix in `workflow/ssot-gen/scripts/repair_ssot_schema.py`: normalize SystemVerilog unsized fill literals (`'0` → `0`, `'1` → `1`, `'x`/`'z` → `0`) in rule expressions so the FL evaluator does not hit `EOL while scanning string literal`.
- Downstream readiness validator added to `repair_ssot_schema.py`: detects (a) cyclic same-cycle output_rule dependencies per transaction, (b) `sample_condition` strings that are not DSL-parseable, (c) `sub_modules[]` entries with no ownership refs. Writes `<ip>/req/ssot_downstream_blockers.json` after canonicalization; `--strict-downstream` makes the script exit non-zero so the ssot-gen stage gates instead of pushing the problem to fl/cl/equiv/rtl.
- `workflow/ssot-gen/system_prompt.md` now has a "DOWNSTREAM READINESS" section that tells the ssot-gen LLM the DSL rules, the no-output-cycle rule, the SV fill literal rule, the sub_module ownership refs rule, and the helper reserved names. Goal: catch the same gaps during authoring instead of waiting for rtl-gen preflight.
- SSOT Q&A Workbench UI contract added: `ssot-gen` now starts on Q&A Session, hides the old QA history panel, uses the full center card for ask_user, exposes Import / Deep Interview(`/grill-me`) / To SSOT(`/to-ssot`) buttons, and shows remaining SSOT requirement decisions. Verified by targeted pytest and ATLAS browser smoke.
- RTL-GEN split-workspace guidance fix: `rtl-gen` now treats `workflow/` as source-repo tooling under `ATLAS_SOURCE_ROOT`, not as an IP-workspace artifact that must exist in CWD. This prevents UI ask_user cards that ask the user to mount/copy `workflow/rtl-gen/scripts/derive_rtl_todos.py` when the source root is already injected.
