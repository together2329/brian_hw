---
title: Coverage
type: reference
tags: [workflow, coverage, sim]
status: stable
---

# Coverage

`coverage` instruments the DUT with Verilator coverage flags, re-runs the [[tb-gen]] testbench, analyzes line/toggle/user coverage against SSOT goals, and iteratively closes gaps with directed tests until SSOT targets are met or precisely escalated. SSOT is the only acceptance source; it never silently lowers a threshold. See [[workflow-stages]] for the pipeline.

## Purpose

Measure and close the SSOT-declared coverage goals — `test_requirements.coverage_goals.function` (function_model-derived) and `.cycle` (cycle_model-derived) plus SSOT line/toggle thresholds — and emit `<ip>/cov/coverage.json` with measured metrics and explicit limitations.

## How to run

Run from the project root. One pass = "coverage iter":

```bash
verilator --cc --exe --coverage --coverage-line --coverage-toggle --trace ...   # build
make SIM=verilator MODULE=tests.tb                                              # run testcases
verilator_coverage logs/*.dat --write <ip>/cov/merged.dat                       # merge
verilator_coverage <ip>/cov/merged.dat --annotate <ip>/cov/annotated/ --write-info <ip>/cov/coverage.info
python3 workflow/coverage/scripts/ssot_coverage_summary.py <ip>                 # SSOT-aligned summary
```

## Scripts

| script | does |
| --- | --- |
| `coverage_build.sh` | Verilator build with line + toggle coverage flags; reads `<ip>/list/<ip>.f`, builds into `build_<ip>_cov/`. |
| `coverage_merge.sh` | Merge per-test `coverage.dat` files into `<ip>/cov/merged.dat`. |
| `coverage_report.sh` | Generate `<ip>/cov/annotated/` + `.info` from `merged.dat`. |
| `coverage_gaps.sh` | Identify top-N uncovered regions from the annotated output (zero-count coverage points). |
| `coverage_vcd_merge.sh` | Discover and concat-merge `*.vcd` under `<ip>/` into `<ip>/cov/merged.vcd`. |
| `coverage_vcd_toggle.sh` | Compute toggle coverage from `merged.vcd` (or first VCD found). |
| `ssot_coverage_summary.py` | Summarize SSOT-driven coverage evidence for any leaf IP into `<ip>/cov/coverage.json`. |

## Method / key rules

- **Strict SSOT authority.** SSOT alone defines function/cycle goals, code/toggle/FSM/assertion thresholds, waiver policy, and DONE criteria. Report `coverage_goals.function` and `coverage_goals.cycle` separately. Missing goals/waiver fields → `[SSOT TBD REPORT] -> ssot-gen`; DONE states `SSOT TBD REPORT: none`.
- **Tool scope.** Verilator supports line, toggle, and user-defined points (branch is partial, subsumed under line). It does **not** support SystemVerilog functional coverage (`covergroup`/`coverpoint`/cross), MC/DC, or full SVA coverage — for those, flag the limit and route to Questa/VCS.
- **Generic only.** No per-IP coverage harnesses/parsers under the IP tree; reuse the existing TB and `ssot_coverage_summary.py`. Unmeasurable metric → report a capability gap, never invent a number.
- **Evidence discipline.** Never claim a line "covered" without reading the annotated source in the same turn; quote `file:line` + hit-count in every approved reason. Self-written summaries are not trustworthy — re-read `.info`/`annotated/`. Coverage on a failing regression (`<failure>` in `results.xml`) is meaningless and not PASS.
- **Iteration loop.** build → run all tests → merge → annotate/report → read annotated source → pick top-N gaps → write directed test → re-run; log `{line%, toggle%, lines_added}` per iter.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml` (goals), `<ip>/tb/*` (existing TB), `<ip>/list/<ip>.f`, per-test `*.dat`, `<ip>/sim/results.xml`.
- **Outputs:** `<ip>/cov/merged.dat`, `<ip>/cov/coverage.info`, `<ip>/cov/annotated/`, `<ip>/cov/coverage.json` (naming SSOT scenarios, scoreboard checks, goals, measured metrics, and limitations).

## Structure — coverage iter

Each iteration builds instrumented, runs the regression, merges `.dat`, annotates source, identifies worst-coverage modules/lines, and adds a directed test for the top gap — repeating until SSOT line/toggle/function/cycle goals close or an evidence gap is escalated.

## Related

Upstream: [[sim]] (passing run), [[tb-gen]], [[fl-model-gen]] (`fcov_plan.json`). Authority: [[ssot-gen]]. Back to [[workflow-stages]].
