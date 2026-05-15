# Wiki Log

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
