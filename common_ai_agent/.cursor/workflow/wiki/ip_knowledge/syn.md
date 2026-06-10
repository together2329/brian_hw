---
title: Synthesis
type: reference
tags: [workflow, syn, signoff]
status: stable
---

# Synthesis

`syn` drives RTL → gate-level netlist with yosys against the sky130_fd_sc_hd Liberty (SS corner), producing `<ip>/syn/out/synth.v` plus area stats and a report. The mapped netlist is the canonical handoff to [[sta]]; an ungated or unmapped netlist makes timing silently lie. See [[workflow-stages]] for the pipeline.

## Purpose

Map the [[rtl-gen]] DUT to standard cells, verify no unmapped `$_*_` cells and no unintended latches, and emit `synth.v` + `area.json` so downstream timing/physical stages have a real gate netlist.

## How to run

Run from the project root (yosys + `$SKY130_LIB` must resolve via `workflow/scripts/pdk_env.sh`):

```bash
bash workflow/syn/scripts/auto_syn.sh <ip>          # full flow: run.ys → yosys → sanity → area → report
bash workflow/syn/scripts/preflight.sh <ip>         # diagnose tool/PDK/SSOT/filelist/RTL first
yosys -l <ip>/syn/out/syn.log <ip>/syn/run.ys       # manual invoke
```

Slash equivalents: `/syn`, `/syn-preflight`, `/syn-auto`, `/syn-script`, `/syn-run`, `/syn-report`.

## Scripts

| script | does |
| --- | --- |
| `auto_syn.sh` | End-to-end driver (single `/syn` entry point): write `run.ys` → yosys → sanity gate → `area.json` → `syn.report.md`. |
| `write_yosys_script.sh` | Generate `<ip>/syn/run.ys` from SSOT `top_module` + filelist. |
| `run_yosys.sh` | Invoke yosys on `run.ys`, capture stdout/stderr to `syn.log`. |
| `run_synth.sh` | yosys generic synthesis + area/cell statistics. |
| `check_unmapped.sh` | Fail-fast sanity on `synth.v` (exit 7 = unmapped `$_*_` cells, exit 8 = unintended latches). |
| `parse_area.sh` | Parse `syn.log` + `synth.v` into `<ip>/syn/out/area.json`. |
| `emit_sdc.py` | Emit SDC from SSOT `timing` + `timing_constraints` + `synthesis` sections. |
| `preflight.sh` | Diagnose yosys, PDK files, SSOT, filelist, and RTL inputs before running. |
| `write_report.sh` | Compose `syn.report.md` from `area.json` + `syn.log`. |
| `run_openroad.sh` / `run_sta.sh` | Auxiliary OpenROAD floorplan/placement+STA and OpenSTA-on-netlist helpers. |

## Method / key rules

- **Strict SSOT authority.** SSOT names the synthesis top module, RTL filelist intent, dialect/coding constraints, target technology/corner/library policy, PPA targets, and latch/waiver policy. Env vars may *locate* the library but SSOT must name the policy. Missing `top_module`/`filelist.rtl`/`synthesis`/`timing`/`quality_gates.eda` facts → `[SSOT TBD REPORT] -> ssot-gen`; DONE states `SSOT TBD REPORT: none`.
- **Critical gates.** No latches unless SSOT declares an intentional one; no unmapped `$_*_` cells (every cell must start with `sky130_fd_sc_hd__`); top module from SSOT (not filename); sequential-cell sanity (0 FFs in a sequential design = stop). Always log full yosys output to `syn.log`.
- **No fallback synth.** If `$SKY130_LIB` is missing or SSOT lacks library/corner policy: stop with `[SYN MISSING PDK]` / `[SSOT TBD REPORT]` — [[sta]] rejects an ungated netlist.
- **yosys script** `read_liberty -lib` → `read_verilog -sv` (each filelist file) → `hierarchy -top` → `synth -top` → `dfflibmap` → `abc -liberty` → `opt_clean` → `write_verilog -noattr synth.v` → `stat`.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml` (top, clocks, synthesis policy), `<ip>/rtl/*.sv`, `<ip>/list/<ip>.f`.
- **Outputs:** `<ip>/syn/run.ys`, `<ip>/syn/out/synth.v` (handoff), `<ip>/syn/out/area.json` (cell counts, total μm², by_kind/by_cell), `<ip>/syn/out/syn.log`, `<ip>/syn/out/syn.report.md`.

## Structure — synthesis pipeline

read SSOT → verify inputs resolve → write `run.ys` → run yosys → sanity-check `synth.v` (grep for `$_` unmapped and unintended `latch_`) → parse area → write report. `synth.v` freshness (mtime ≥ any `rtl/*`) is checked by [[sta]].

## Related

Upstream: [[rtl-gen]], [[lint]]. Authority: [[ssot-gen]]. Downstream: [[sta]], [[pnr]]. Back to [[workflow-stages]].
