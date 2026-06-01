# RTL To Signoff Runbook

This is a Cursor-facing mirror of the common_ai_agent workflow. It is not a second validator. DV stages call `WorkflowStageEngine`; EDA stages call the same `bash:auto_*` scripts exposed by workflow command JSON.

Machine-readable routing lives in `STAGE_MANIFEST.json`.

## Profiles

| Profile | Purpose | Stages |
| --- | --- | --- |
| `dv` | Common-engine DV and equivalence closure | FL model, cycle model, equivalence goals, RTL, lint, TB, sim, coverage, sim-debug, goal-audit |
| `eda` | Backend signoff after DV is already green | syn, sta, pnr, sta-post |
| `full` | DV plus EDA plus final goal audit | `dv` + `eda` + final goal-audit |
| `headless-dv` | Product/TDD-style pipeline convergence | `src/headless_workflow.py --stages pipeline`, then goal-audit |
| `ssot-to-signoff` | Greenfield flow from SSOT generation through signoff | `ssot-gen` + `full` |

## SSOT Track

`ssot-gen` is interactive in the runtime agent. Cursor uses the headless entrypoint when it needs to start before SSOT exists.

| Manifest ID | Invoke | Owner workflow | Surface | Evidence |
| --- | --- | --- | --- | --- |
| `ssot-gen` | `src/headless_workflow.py --stages ssot-gen` | `ssot-gen` | `/to-ssot <ip>`, `/grill-me`, `/verify-ssot` | `req/`, `req/approval_manifest.json`, `yaml/<ip>.ssot.yaml` |

Use `--req <path>` when starting from a requirement document.

## DV Track: Common Engine

These stages must run through `WorkflowStageEngine.run_stage()`. Do not replace them with raw disk-check scripts.

| Manifest ID | Engine stage | Owner workflow | Slash surface | Primary evidence |
| --- | --- | --- | --- | --- |
| `ssot-fl-model` | `ssot-fl-model` | `fl-model-gen` | `/ssot-fl-model <ip>` | `model/functional_model.py`, `model/fl_model_check.json`, `cov/fcov_plan.json` |
| `ssot-cycle-model` | `ssot-cycle-model` | `fl-model-gen` | `/ssot-cycle-model <ip>` | `model/cycle_model.py`, `model/cl_model_check.json` |
| `ssot-equiv-goals` | `ssot-equiv-goals` | `fl-model-gen` | `/ssot-equiv-goals <ip>` | `verify/equivalence_goals.json` |
| `ssot-rtl` | `ssot-rtl` | `rtl-gen` | `/ssot-rtl <ip>` | `rtl/rtl_todo_plan.json`, `rtl/rtl_compile.json`, `lint/dut_lint.json`, `logs/stage_engine/ssot-rtl.json` |
| `lint` | `lint` | `lint` | `/lint-ip <ip>` | `lint/dut_lint.json`, `lint/dut_lint.log` |
| `ssot-tb-cocotb` | `ssot-tb-cocotb` | `tb-gen` | `/ssot-tb-cocotb <ip>` | `tb/cocotb/tb_manifest.json`, `tb/cocotb/tb_generation.json`, `tb/tb_todo_plan.json` |
| `sim` | `sim` | `sim` | `/ssot-sim <ip>` | `sim/results.xml`, `sim/scoreboard_events.jsonl`, `sim/sim_report.txt`, `cov/coverage.json` |
| `coverage` | `coverage` | `coverage` | `/ssot-coverage <ip>` | `cov/coverage_functional.json`, `cov/coverage.json`, `cov/coverage_ssot.json` |
| `sim-debug` | `sim-debug` | `sim_debug` | `/sim-debug <ip>` | `sim/fl_rtl_compare.json`, `sim/mismatch_classification.json`, `sim/simulation_quality.json`, `sim/simulation_quality.md` |
| `goal-audit` | `goal-audit` | `sim_debug` | `/goal-audit <ip>` | `sim/fl_rtl_goal_audit.json` |

Every engine stage also writes:

```text
<ip>/logs/stage_engine/<engine_stage>.json
```

## EDA Track: Workflow Commands

EDA is not owned by `WorkflowStageEngine` today. Use the workflow command scripts.

| Manifest ID | Owner workflow | Slash surface | Script | Evidence |
| --- | --- | --- | --- | --- |
| `syn` | `syn` | `/syn-auto <ip>` | `workflow/syn/scripts/auto_syn.sh` | `syn/out/synth.v`, `syn/out/area.json`, `syn/out/syn.report.md` |
| `sta` | `sta` | `/sta-auto <ip>` | `workflow/sta/scripts/auto_sta.sh` | `sta/out/wns.json`, `sta/out/sta.report.md` |
| `pnr` | `pnr` | `/pnr-auto <ip>` | `workflow/pnr/scripts/auto_pnr.sh` | `pnr/out/pnr.report.md` |
| `sta-post` | `sta-post` | `/sta-post-auto <ip>` | `workflow/sta-post/scripts/auto_sta_post.sh` | `sta-post/out/wns.json`, `sta-post/out/sta-post.report.md` |
| `dft` | `dft` | `/dft-auto <ip>` | `workflow/dft/scripts/auto_dft.sh` | optional DFT reports |

## Human Gates

Stop and route instead of patching evidence when these appear:

- `rtl/rtl_blocked.json`: SSOT or RTL authoring blocker owned by `rtl-gen` or human.
- `tb/cocotb/tb_blocked.json`: TB generation blocker owned by `tb-gen` or human.
- `sim/mismatch_classification.json`: semantic mismatch; use `sim-debug` classification.
- `sim/simulation_quality.json`: failed or stale scoreboard quality evidence; rerun `sim-debug` or `workflow/sim_debug/scripts/check_simulation_quality.py`.
- `cov/coverage.json` limitations: coverage proof blocked or needs human review.
- EDA missing-tool/PDK failures: environment/setup blocker, not a report editing task.

## Commands

Plan with KPI dots and evidence paths:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --plan
```

Run DV only:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute
```

Run just sim-debug evidence refresh:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile dv --execute --from-stage sim-debug --until sim-debug
```

Run EDA only after DV is green:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile eda --execute
```

Run the full profile:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --execute
```

Resume from a failed owner:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile full --execute --from-stage ssot-rtl
```

Run product/TDD-style convergence through headless:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile headless-dv --provider fake --execute
```

Run from SSOT generation:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile ssot-to-signoff --provider fake --execute --req <req-file>
```

## Output

The runner writes:

```text
<ip>/verify/cursor_rtl_to_signoff_summary.json
```

That summary is generated evidence derived from engine results and bash command exits. Regenerate it by rerunning the workflow; do not hand-edit it.
