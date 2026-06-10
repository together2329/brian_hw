---
title: Static Timing Analysis (Pre-Route)
type: reference
tags: [workflow, sta, signoff]
status: stable
---

# Static Timing Analysis (Pre-Route)

`sta` runs OpenSTA on the [[syn]] gate netlist and produces setup/hold WNS+TNS for every SSOT-declared clock, writing `<ip>/sta/out/wns.json` and the generated `<ip>.sdc`. This is the optimistic, zero-net-delay timing view — the silicon-accurate truth comes later from [[sta-post]]. See [[workflow-stages]] for the pipeline.

## Purpose

Constrain the synthesized netlist from SSOT clocks/exceptions/IO-delays and report per-clock worst negative slack, so timing health is known before place & route — and so [[pnr]] has a valid SDC.

## How to run

Run from the project root (OpenSTA `sta` + `$SKY130_LIB` resolved via `pdk_env.sh`):

```bash
bash workflow/sta/scripts/auto_sta.sh <ip>     # handoff gate → SDC → tcl → OpenSTA → parse → report
sta -no_init -no_splash -exit <ip>/sta/run.tcl 2>&1 | tee <ip>/sta/out/sta.log
```

Slash equivalents: `/sta`, `/sta-auto`, `/sta-sdc`, `/sta-run`, `/sta-report`.

## Scripts

| script | does |
| --- | --- |
| `auto_sta.sh` | End-to-end driver (`/sta` entry point): handoff gate → SDC → tcl → OpenSTA → parse WNS/TNS → report. |
| `write_sdc.sh` | Generate `<ip>/sta/out/<ip>.sdc` from the SSOT yaml. |
| `write_sta_tcl.sh` | Generate `<ip>/sta/run.tcl` driving OpenSTA. |
| `run_opensta.sh` | Invoke OpenSTA on `run.tcl`, capture all output to `sta.log`. |
| `parse_wns.sh` | Extract per-clock setup/hold WNS+TNS from `sta.log` + `setup.rpt` + `hold.rpt` into `wns.json`. |
| `write_report.sh` | Compose `sta.report.md` from `wns.json` + `sta.log`. |

## Method / key rules

- **Strict SSOT authority.** SSOT alone defines clocks, generated clocks, false/multicycle paths, async-reset exceptions, IO delays, operating mode, PDK/corner/library policy, and timing pass/fail targets. No implicit delay defaults — every input/output delay in SDC must come from SSOT; unknown delays/exceptions → `[SSOT TBD REPORT] -> ssot-gen`. DONE states `SSOT TBD REPORT: none`.
- **Handoff gates.** Refuse if `<ip>/syn/out/synth.v` is missing (`[STA HANDOFF MISSING] run /syn first`) or stale (any `rtl/*` newer → `[STA STALE NETLIST]`). STA is netlist-level only — never read RTL directly. Liberty must match the [[syn]] corner.
- **SDC rules.** Each SSOT clock → `create_clock`; each `false_paths[]` → `set_false_path`; each `multicycle_paths[]` → `set_multicycle_path`; async resets → `set_false_path -from [get_ports <reset>]`. Every clock must yield a `create_clock` or analysis is constant/bogus.
- **Report reading.** WNS = worst (most negative) path slack; TNS = sum of negative slacks; hold WNS = fast-path races; always show absolute slack + clock period for context.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml` (clocks, exceptions, delays), `<ip>/syn/out/synth.v` (handoff from [[syn]]).
- **Outputs:** `<ip>/sta/out/<ip>.sdc`, `<ip>/sta/run.tcl`, `<ip>/sta/out/{timing.rpt, setup.rpt, hold.rpt, sta.log}`, `<ip>/sta/out/wns.json` (per-clock setup/hold WNS/TNS + violation counts + worst paths), `<ip>/sta/out/sta.report.md`.

## Structure — STA pipeline

handoff gate (synth.v fresh) → read SSOT clocks/exceptions → write SDC → write tcl (`read_liberty` → `read_verilog synth.v` → `link_design` → `read_sdc` → `report_checks` setup/hold → `report_wns`/`report_tns`) → run OpenSTA → parse per-clock WNS/TNS → write `wns.json` + report. The generated `<ip>.sdc` is reused by [[pnr]] and [[sta-post]].

## Related

Upstream: [[syn]]. Authority: [[ssot-gen]]. Downstream: [[pnr]] (uses the SDC), [[sta-post]] (compares against this optimistic view). Back to [[workflow-stages]].
