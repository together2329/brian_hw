---
title: Testbench Generation
type: reference
tags: [workflow, tb-gen, tb]
status: stable
---

# Testbench Generation

`tb-gen` builds the SSOT-driven verification environment — a layered pyuvm/cocotb testbench whose scoreboard compares RTL observations against the [[fl-model-gen]] FunctionalModel for every equivalence goal. It owns SSOT-derived tests, scoreboards, functional bins, results XML, and waveform setup, but never invents expected behavior. See [[workflow-stages]] for the pipeline.

## Purpose

Produce a UVM-style cocotb environment (transactions, sequences, drivers, monitors, scoreboard, coverage, env, tests) plus `sim/scoreboard_events.jsonl` rows keyed by `goal_id`, so [[sim]] can run it and prove FL-vs-RTL equivalence with no hidden failures.

## How to run

Run from the project root. `/ssot-tb <ip>` defaults to the `ssot-tb-cocotb` backend (`ssot-tb-uvm` and `ssot-tb-verilog` are explicit alternatives). The production path is AI-driven authoring; the goal-scoreboard generator emits the reusable FL-vs-RTL environment:

```bash
# generic FL-vs-RTL cocotb scoreboard environment
python3 workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py <ip> --root .
# prove goals + FunctionalModel are loadable before signoff
python3 workflow/tb-gen/runtime/equivalence_scoreboard.py <ip> --root . --self-check
# bounded run (from <ip>/tb/cocotb)
cd <ip>/tb/cocotb && python3 test_runner.py
```

Cocotb runs must be **bounded and staged**: prove the runner with one reset scenario (`COCOTB_TESTCASE=<test>`), then one transfer, then the full set (`FULL_REGRESSION_OK=1`). Never launch unbounded `make`/`tail`/`head` pipelines.

## Scripts

| script | does |
| --- | --- |
| `emit_goal_scoreboard_cocotb.py` | Emit a generic SSOT/equivalence-goal-driven cocotb/pyuvm FL-vs-RTL scoreboard environment; refuses to fabricate expected behavior. |
| `emit_axi_lite_memory_cocotb.py` | Emit and run SSOT-derived pyuvm/cocotb tests for AXI4-Lite memory IPs. |
| `emit_timing_header.py` | Emit `<ip>/tb/cocotb/<ip>_timing.py` constants from `SSOT.timing_constraints` (no magic timing literals). |
| `ssot_to_cocotb.py` / `ssot_to_cocotb.sh` | Deprecated fixed-shape APB/CPU/BUS template helper; disabled by default. |
| `check_pyuvm_structure.sh` | Verify the cocotb backend is a layered UVM-style TB, not a flat test / partial drop. |
| `check_scoreboard_events.py` | Validate the generic FL-vs-RTL scoreboard evidence contract (each event points back to an equivalence goal). |
| `check_scoreboard_events… / check_tb_magic_numbers.py` | Lint cocotb TB for unjustified bare timing literals encoding RTL assumptions. |
| `check_no_ip_coverage_workarounds.sh` | Reject per-IP coverage workaround artifacts (static coverage belongs to [[coverage]]). |
| `check_tb_sim_evidence.sh` | tb-gen validator: TB artifacts + assertion paths + sim evidence → PASS or precise escalation. |
| `check_sim_pass.sh` / `check_tb_disk.sh` | SV/cocotb sim-output validator; disk-truth validator for tb-gen tasks. |
| `check_pyuvm_structure… / sim.sh / gen_tc.sh / coverage.sh` | Layered-structure check; compile+run sim; tc skeleton from DUT; grep-based branch-coverage hint. |
| `emit_timing… / post_write.sh / sim_result_capture.sh / disk_diff.sh` | Hook helpers: post-write logging, sim-result capture, disk-diff injection. |

## Method / key rules

- **Strict SSOT authority.** SSOT YAML (`test_requirements`, `function_model`, `cycle_model`, `coverage_goals`, registers/memory/interrupts) is the only pass/fail source. RTL is read only as DUT structure to instantiate/observe. Missing facts → `[SSOT TBD REPORT] -> ssot-gen`; DONE states `SSOT TBD REPORT: none`.
- **Layered cocotb.** Prefer real `pyuvm`; otherwise cocotb-native classes with the same layered architecture. Files under `<ip>/tb/cocotb/`: `transactions.py`, `sequences.py`, `agents.py`, `scoreboard.py`, `coverage.py`, `uvm_env.py`, `test_<ip>.py`, `test_runner.py`. No flat monolithic test unless the SSOT is trivial.
- **Scoreboard contract.** Use the reusable `workflow/tb-gen/runtime/equivalence_scoreboard.py` (`EquivalenceScoreboard`) — it loads `verify/equivalence_goals.json`, imports `model/functional_model.py`, calls `FunctionalModel.apply`, and writes `sim/scoreboard_events.jsonl` rows with `goal_id`, `scenario_id`, `cycle`, `stimulus`, `fl_expected`, `rtl_observed`, `passed`, `mismatch`, `coverage_refs`. Don't reimplement expected behavior per IP.
- **Anti-hallucination.** No "done" without `write_file`; no "N/N PASS" without the documented `run_command` + `results.xml`. Any `[FAIL]`/failed-check must `raise AssertionError` — a PASS summary over a log containing `[FAIL]` is invalid.
- **Ownership.** DUT bug → `[SIM ESCALATE] -> rtl-gen` (never edit RTL or weaken/relabel a checker to match observed output). SSOT unclear → `[SSOT QUESTION] -> ssot-gen`.
- **Coverage split.** Functional bins from SSOT `coverage_goals`; static line/branch/FSM coverage comes from the [[coverage]] workflow, not a per-IP harness under `tb/`. One test + ≥1 scoreboard assertion + ≥1 functional bin per `test_requirements.scenarios[]`.
- **Done evidence.** Fresh TB files, runner output, `results.xml`/`sim_report.txt`, inspectable ASCII VCD, functional coverage JSON, and no failing markers.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml`, `<ip>/verify/equivalence_goals.json`, `<ip>/model/functional_model.py`, `<ip>/rtl/*.sv` (DUT structure only).
- **Outputs:** `<ip>/tb/cocotb/*` (env + `results.xml`), `<ip>/sim/scoreboard_events.jsonl`, `<ip>/sim/<ip>.vcd`, `<ip>/cov/coverage_functional.json`, `<ip>/sim/sim_report.txt`.

## Structure — SSOT → TB mapping

`io_list` → DUT instantiation + clock/reset gen; `registers` → R/W tasks + scoreboard checks; `function_model` → scoreboard/reference model; `cycle_model` → cycle checks, waveform expectations, timeout bounds; `test_requirements.scenarios[]` → one test each (stimulus from `stimulus_machine_spec`, expected from the FunctionalModel); `coverage_goals` → functional bins; `error_handling`/`security` → fault/negative scenarios. Build a verification ledger before writing, then author in bounded passes (`py_compile` after each).

## Related

Upstream: [[ssot-gen]], [[fl-model-gen]], [[rtl-gen]]. Downstream: [[sim]], [[coverage]]. Back to [[workflow-stages]].
