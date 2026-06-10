---
title: Simulation
type: reference
tags: [workflow, sim, sim]
status: stable
---

# Simulation

`sim` compiles and runs the [[tb-gen]] testbench against the [[rtl-gen]] DUT until it reaches 0 errors, 0 warnings with all checks PASS, then writes `sim/sim_report.txt`. It accepts handoffs from tb-gen (SSOT or legacy MAS) and is the executable verification step where FL-vs-RTL equivalence is exercised. See [[workflow-stages]] for the pipeline.

## Purpose

Drive compile → run → scoreboard → report on the SSOT-derived RTL+TB, classify any failure by owner (TB / DUT / SSOT), and emit fresh, inspectable evidence (report, `results.xml`, VCD) for downstream sim-debug and [[coverage]].

## How to run

Run from the project root. Simulator is selected from `test_requirements.simulator` (default Icarus):

```bash
# Icarus (default)
iverilog -g2012 -f <ip>/list/<ip>.f -o <ip>/sim/<ip>.out
vvp <ip>/sim/<ip>.out
# VCS
vcs -full64 -sverilog -f <ip>/list/<ip>.f -o <ip>/sim/<ip>_simv && ./<ip>/sim/<ip>_simv
# helper scripts
bash workflow/sim/scripts/sim.sh tb_<ip>.sv      # compile + run
bash workflow/sim/scripts/compile.sh tb_<ip>.sv  # compile only
bash workflow/sim/scripts/wave_info.sh <ip>.vcd  # inspect VCD signals
```

## Scripts

| script | does |
| --- | --- |
| `compile.sh` | Compile only (check for compile errors) and log to `.benchmark`. |
| `sim.sh` | Compile + run the testbench. |
| `sim_capture.sh` | Hook: capture simulator stdout/stderr into the session log. |
| `write_report.sh` | Generate `sim_report.txt` from the `.benchmark` log. |
| `wave_info.sh` | List signals in a `.vcd` waveform (debug aid). |
| `starter_preview_sim.py` | Run a deterministic Starter RTL preview smoke simulation (narrower than production tb-gen). |
| `check_sim_pass.sh` | Validator for SV and cocotb simulation output (delegates to `check_sim_disk.sh`). |
| `check_sim_disk.sh` | Disk-truth validator for sim tasks (artifacts exist, size > 0, metrics match). |
| `post_write.sh` | Hook: post-write logging. |

## Method / key rules

- **Anti-hallucination.** No "PASS"/"0 errors"/"N/N PASS" without real `iverilog`+`vvp` (or VCS) `run_command` whose output contains the cited metrics verbatim. Confirm artifacts with `ls -la <ip>/sim/` (size > 0) before claiming them. No metric fabrication.
- **Filelist handling.** If `<ip>/list/<ip>.f` is missing, build it from `rtl/` + `tb/`; verify paths.
- **Debug protocol.** File-not-found → fix filelist; compile error → fix signal/port mismatch; `[FAIL] got=X expected=Y` → grep RTL for the driver; X-prop → check reset; hang → missing `$finish`; Z value → undriven TB input.
- **Fix ownership.** TB bug → fix `tc_*/tb_*`; DUT bug → fix `<ip>_core.sv` or escalate to [[rtl-gen]]; SSOT unclear → ask [[ssot-gen]].
- **Done.** 0 errors, 0 warnings, all `[PASS]`; write `<ip>/sim/sim_report.txt`; output `[SIM PASS]`. Work only within CWD.

## Inputs → Outputs

- **Inputs:** `<ip>/list/<ip>.f`, `<ip>/rtl/*.sv`, `<ip>/tb/*` (or `tb/cocotb/*`), `<ip>/yaml/<ip>.ssot.yaml` (for simulator selection).
- **Outputs:** `<ip>/sim/sim_report.txt`, `<ip>/sim/results.xml` (cocotb), `<ip>/sim/<ip>.vcd`, `<ip>/sim/scoreboard_events.jsonl` (via the scoreboard).

## Structure — compile → run → scoreboard → report

1. **Compile** the filelist into a sim binary (`iverilog`/`vcs`); fix port/signal mismatches.
2. **Run** the binary (`vvp`/`simv`) or the bounded cocotb runner.
3. **Scoreboard** — FL-expected vs RTL-observed rows are emitted to `scoreboard_events.jsonl`; any mismatch is a real failure routed to its owner.
4. **Report** — write `sim_report.txt` with metrics and per-check PASS/FAIL; downstream sim-debug reads VCD + report.

## Related

Upstream: [[rtl-gen]], [[tb-gen]], [[fl-model-gen]]. Downstream: [[coverage]] (coverage on a passing run only). Back to [[workflow-stages]].
