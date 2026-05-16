# simple_gpio_lite — Serial Pipeline Iteration (2026-05-16)

GPIO smoke run used to validate that the common engine blocks on real
evidence gaps instead of reporting a green result from a soft cocotb pass.

Related wiki:

- [[full-flow-pipeline]] — canonical stage order.
- [[workflow-ownership-and-boundaries]] — owner routing for failed evidence.
- [[golden-todo-evidence]] — approval must be evidence-based.
- [[rtl-gen-ssot-contract]] — RTL is generated from SSOT, not manually patched.
- [[deterministic-emit-stages]] — FL/CL emitters are deterministic and depend on SSOT quality.
- [[human-review-and-escalation]] — unresolved SSOT semantics become human/SSOT gates.

## Run Scope

| Item | Value |
|---|---|
| IP | `simple_gpio_lite` |
| Root | `gpio/simple_gpio_lite` |
| Surface | `src/headless_workflow.py --root gpio --ip simple_gpio_lite` |
| Model | `gpt-5.3-codex` for RTL LLM calls; deterministic stages use 0 LLM calls |
| Stop condition | Stop when a stage has evidence PASS, or when owner classification produces a blocker |

## Stage Roll-Up

| Stage | Result | Evidence |
|---|---|---|
| ssot repair/check | PASS | `check_ssot_disk.sh` passes; 36 sections, 0 TBDs; no auto-promoted `read_mux`/`reduction_or`/`edge_event` IO |
| fl-model-gen | PASS | `model/fl_model_check.json` `passed=true`; `cov/fcov_plan.json` 41 FL bins |
| cl-model-gen | PASS | `model/cycle_model.py`; `model/cl_model_check.json` `passed=true`; `cov/cl_fcov_plan.json` 21 CL bins |
| dual-fcov | PASS | FL+CL union emitted under `cov/` |
| equiv-goals | PASS | `verify/equivalence_goals.json` total 48, required 48, blocked 0 |
| rtl-gen | PASS | 4 SV files; `rtl/rtl_compile.json` errors=0; `lint/dut_lint.json` errors=0 warnings=0; required RTL todos closed |
| tb-gen | PASS | `tb/cocotb/test_runner.py`; scoreboard self-check `checked=48`, `contract_gaps=[]`, `ssot_questions=0` |
| sim | PASS_OR_ESCALATE | cocotb `TESTS=1 PASS=1`; `scoreboard_events.jsonl` has 48 rows, 25 failed FL-vs-RTL rows; `sim_report.txt` now emits `[SIM ESCALATE]` |
| coverage | BLOCKED | `cov/coverage.json` status=`blocked`; function coverage 12/19, cycle coverage 11/22; blocked by failed/missing passing RTL-observed scoreboard bins |
| sim-debug | FAIL / action required | `sim/fl_rtl_compare.json` total=48 checked=48 passed=23 failed=25; `mismatch_classification.json` has 25 routed classifications |
| goal-audit | FAIL / action required | `sim/fl_rtl_goal_audit.json` passed 12/16; blockers: `req`, `fl_rtl_compare`, `mismatch_classification`, `functional_coverage` |

## Key Findings

The earlier prose-only SSOT gap is closed for this GPIO iteration. SSOT now has
structured `output_rules`/`state_updates` for `FM1` through `FM6`, and TB
self-check reports no SSOT questions.

Two general workflow issues were found and fixed:

- `repair_ssot_schema.py` must not promote expression helpers or internal
  derived signals into top-level IO. `read_mux()`, `reduction_or()`, and
  `edge_event` were incorrectly treated as DUT inputs. The fix excludes call
  targets from expression-name extraction and prunes stale auto-derived ports.
- A soft cocotb PASS with failed FL-vs-RTL scoreboard rows must still create
  repair evidence. Generated `test_runner.py` now writes `[SIM ESCALATE]`
  lines when `scoreboard_events.jsonl` contains failed rows.

The current failure is therefore useful: simulator infrastructure is working,
but FL-vs-RTL equivalence and coverage closure are not green.

## Workflow Fix

`workflow/tb-gen/runtime/equivalence_scoreboard.py --self-check` now treats
embedded `ssot_question` and required-goal `unsupported_transaction` results as
contract blockers:

- returns non-zero instead of `passed=true`;
- writes `tb/cocotb/tb_blocked.json`;
- lets the common stage engine classify `/tb` as `human_gate`;
- prevents the misleading path `tb-gen PASS -> sim soft mismatch`.

Regression evidence:

- `pytest -q tests/test_fl_rtl_equivalence_loop.py::test_scoreboard_self_check_blocks_prose_only_ssot_questions`
- `python3 src/headless_workflow.py --root gpio --ip simple_gpio_lite --model gpt-5.3-codex --provider fake --stages tb-gen`

The same root cause is now gated earlier in ssot-gen. `check_ssot_disk.sh`
requires every non-reset `function_model.transactions[]` entry to carry
executable `output_rules` or `state_updates`, and
`repair_ssot_schema.py --strict-downstream` writes
`req/ssot_downstream_blockers.json` with `SSOT_FM_MACHINE_RULES_MISSING_*`
issues when a transaction is prose-only. A temp-copy GPIO validation produced
six blockers (`FM1` through `FM6`), so a fresh run should repair SSOT semantics
before spending tokens on FL/RTL/TB.

Regression evidence:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/test_headless_llm_contracts.py::test_ssot_downstream_readiness_blocks_prose_only_function_transactions`
- `python3 workflow/ssot-gen/scripts/repair_ssot_schema.py simple_gpio_lite --root <temp_gpio_root> --strict-downstream` returns 2 with 6 `SSOT_FM_MACHINE_RULES_MISSING_*` blockers.

Additional regression evidence from this iteration:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/test_headless_llm_contracts.py::test_repair_ssot_schema_does_not_promote_rule_helpers_to_io tests/test_fl_rtl_equivalence_loop.py::test_generated_runner_escalates_soft_scoreboard_mismatches`
- `python3 src/headless_workflow.py --root gpio --ip simple_gpio_lite --model gpt-5.3-codex --provider fake --stages tb-gen,sim,coverage` now reaches `PASS_OR_ESCALATE` for sim evidence and then blocks on real coverage/equivalence gaps.

## Next Owner

Owner is now `sim_debug` -> routed repair, not manual RTL/TB patching.
Use `mismatch_classification.json` to feed the owning workflow. Current
classifications route the failed goals to `rtl-gen`, but the first audit blocker
is still the weak requirement artifact (`req/*.md` is only 44 bytes), so a clean
signoff run should also capture a substantive requirement document.

After repair, rerun:

```bash
python3 src/headless_workflow.py --root gpio --ip simple_gpio_lite --model gpt-5.3-codex --provider fake --stages fl-model-gen,cl-model-gen,dual-fcov,equiv-goals,tb-gen,sim,coverage
python3 src/headless_workflow.py --root gpio --ip simple_gpio_lite --model gpt-5.3-codex --provider fake --stages sim-debug,goal-audit
```

Do not edit generated GPIO RTL/TB artifacts just to make the run pass.
