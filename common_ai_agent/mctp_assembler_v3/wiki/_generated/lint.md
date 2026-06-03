---
title: Lint
type: reference
tags: [workflow, lint, lint]
status: stable
---

# Lint

`lint` drives the DUT RTL files to 0 lint errors, 0 warnings and writes `<ip>/lint/dut_lint.json` + `dut_lint.log`. It is the DUT-only quality gate for [[rtl-gen]] — sim/TB logs are not lint approval, and warnings are fixed at the root cause, never suppressed. See [[workflow-stages]] for the pipeline.

## Purpose

Produce canonical DUT-only lint evidence (zero unwaived errors/warnings/style diagnostics) that gates RTL acceptance before [[tb-gen]] and the EDA stages.

## How to run

Run from the project root:

```bash
# canonical DUT-only report (writes lint/dut_lint.json + log)
python3 workflow/lint/scripts/dut_lint_report.py <ip> --top <top_module>
# equivalent explicit forms
cd <ip> && verilator --lint-only -Wall -Irtl -f list/<ip>.f --top-module <top>
cd <ip> && iverilog -Wall -g2012 -Irtl -f list/<ip>.f -s <top> -o lint/<ip>_dut_lint.vvp
```

Tool priority: Verilator `--lint-only -Wall` on macOS/Linux when available, else Icarus `iverilog -Wall -g2012`.

## Scripts

| script | does |
| --- | --- |
| `dut_lint_report.py` | Run DUT-only RTL lint and write `<ip>/lint/dut_lint.json` — the canonical ATLAS progress evidence for lint approval (records command, tool, return code, error/warning counts, RTL filelist). |
| `lint_all.sh` | Lint all `.sv`/`.v` files (excluding `tb_`/`tc_`). |
| `lint_file.sh` | Lint a single file. |
| `auto_lint.sh` | Hook: quick lint of a changed file, auto-triggered after every `.sv`/`.v` write. |
| `run_full_lint.sh` | Verilator `-Wall` lint with the project waiver file. |
| `write_report.sh` | Generate `lint_report.txt` from the `.benchmark` log. |
| `check_lint_disk.sh` | Disk-truth validator for lint tasks. |
| `error_log.sh` | Hook: capture lint errors into the session log. |

## Method / key rules

- **Anti-hallucination.** No "lint clean" without a real lint `run_command` whose output contains the metrics; no "report written" without a real DUT-only `dut_lint_report.py` (or equivalent) recording command/tool/return-code/counts/filelist in JSON.
- **Never suppress.** No `-Wno-*` flags or inline `verilator lint_off`; a waiver is valid only when SSOT `coding_rules.lint_waivers` names the exact warning code, file, signal, and rationale.
- **Artifacts stay in `lint/`.** `.vvp`/check-logs/scratch land under `<ip>/lint/`, never in `rtl/` (synthesizable source only); delete stray `.vvp` in `rtl/`.
- **One module per file** — filename must match module name; split multi-module files (fix `%Warning-DECLFILENAME`) and update the filelist.
- **Fix-priority table.** Undeclared signal → declare; multiple drivers → remove duplicate; latch → default assignment at top of comb block; width mismatch → correct-width constant; implicit net → declare explicitly; unused port/signal → remove or wire to real logic. Always re-run lint to confirm 0/0.
- **Done.** 0 errors, 0 warnings; emit `METRICS: lint.errors=N, lint.warnings=N` and `[LINT PASS]`. Work only within CWD.

## Inputs → Outputs

- **Inputs:** `<ip>/rtl/*.sv` (source), `<ip>/list/<ip>.f` (filelist).
- **Outputs:** `<ip>/lint/dut_lint.json` (`{type, scope:"dut", dut_only:true, tool, command, rtl_files, errors, warnings, passed}`) and `<ip>/lint/dut_lint.log`.

## Structure — lint gate flow

run lint → read diagnostics → fix root cause (declare / single-driver / default-assign / correct width / split module) → re-run → confirm 0 errors, 0 warnings → write `dut_lint.json` (`passed: true`). The JSON is the gate artifact [[rtl-gen]] must close before DONE.

## Related

Gates [[rtl-gen]]. Upstream source from [[rtl-gen]]; consumed by [[syn]] and the build graph's lint node. Back to [[workflow-stages]].
