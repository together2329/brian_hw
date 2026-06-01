# ATLAS Workflow Index

Reference these source files in place. Do not copy their logic into `.cursor/`.

## Entrypoints

- `python3 src/main.py -w <workspace>`: CLI ReAct agent.
- `python3 src/textual_main.py -w <workspace>`: Textual/Atlas UI launcher.
- `python3 src/atlas_ui.py --port 8765`: Atlas FastAPI/WebSocket UI.
- `python3 src/main.py --serve --all-workflows --port 5601`: all-workflows worker.
- `python3 src/headless_workflow.py --root <root> --ip <ip> --stages <stages>`: headless reproduction.
- `python3 src/progress_debug.py`: progress/debug summaries.

## Tests

- `scripts/run_tests.sh`: canonical smoke, quick, full, live, frontend, load, and mutation gates.
- `scripts/llm_cost_dryrun.py`: live LLM cost estimate.
- `scripts/cli_tests/*.py`: standalone CLI tests, run with `python3`.

## Workflow Workspaces

- `workflow/default/workspace.json`
- `workflow/orchestrator/workspace.json`
- `workflow/ssot-gen/workspace.json`
- `workflow/fl-model-gen/workspace.json`
- `workflow/rtl-gen/workspace.json`
- `workflow/tb-gen/workspace.json`
- `workflow/sim/workspace.json`
- `workflow/sim_debug/workspace.json`
- `workflow/coverage/workspace.json`
- `workflow/lint/workspace.json`
- `workflow/syn/workspace.json`
- `workflow/sta/workspace.json`
- `workflow/pnr/workspace.json`
- `workflow/sta-post/workspace.json`
- `workflow/dft/workspace.json`

## Stage Scripts

- SSOT: `workflow/ssot-gen/scripts/check_ssot_disk.sh`, `verify_ssot.py`, `validate_yaml.sh`, `approved_to_ssot.py`, `repair_ssot_schema.py`.
- FL/equiv: `workflow/fl-model-gen/scripts/emit_fl_model.py`, `emit_cycle_model.py`, `emit_equivalence_goals.py`.
- RTL: `workflow/rtl-gen/scripts/ssot_to_rtl.sh`, `derive_rtl_todos.py`, `build_gate.sh`, `lint.sh`.
- TB: `workflow/tb-gen/scripts/sim.sh`, `check_tb_disk.sh`, `check_sim_pass.sh`, `ssot_to_cocotb.sh`.
- Sim: `workflow/sim/scripts/sim.sh`, `compile.sh`, `check_sim_disk.sh`, `sim_capture.sh`.
- Debug: `workflow/sim_debug/scripts/wave_info.sh`, `sig_search.sh`, `compare_fl_rtl_results.py`, `mutation_guard.py`, `check_simulation_quality.py`, `audit_fl_rtl_equivalence_goal.py`.
- Coverage: `workflow/coverage/scripts/coverage_build.sh`, `coverage_merge.sh`, `coverage_report.sh`, `coverage_gaps.sh`.
- Lint: `workflow/lint/scripts/auto_lint.sh`, `run_full_lint.sh`, `lint_all.sh`.
- EDA: `workflow/scripts/pdk_env.sh`, `workflow/syn/scripts/auto_syn.sh`, `workflow/sta/scripts/auto_sta.sh`, `workflow/pnr/scripts/auto_pnr.sh`, `workflow/sta-post/scripts/auto_sta_post.sh`, `workflow/dft/scripts/auto_dft.sh`.

## Reference IP

- `apb_uart_txrx_demo/sim/run_sim.sh`
- `apb_uart_txrx_demo/sim/run_random_regression.sh`

Tracked demo evidence may be regenerated, but should not be hand-edited.
