---
title: Place & Route
type: reference
tags: [workflow, pnr, signoff]
status: stable
---

# Place & Route

`pnr` drives the post-synth netlist through OpenROAD's full physical pipeline (floorplan → place → CTS → route) and extracts a parasitic SPEF for sign-off timing. The triple `(routed.v, routed.spef, <ip>.sdc)` is the handoff to [[sta-post]]. See [[workflow-stages]] for the pipeline.

## Purpose

Turn the [[syn]] netlist (or [[sta]]-constrained design) into a routed layout with real interconnect parasitics, gating each stage on the previous stage's freshness, so post-route STA can report silicon-accurate timing.

## How to run

Run from the project root (OpenROAD + bundled sky130 PDK via `pdk_env.sh`):

```bash
bash workflow/pnr/scripts/preflight.sh <ip>   # validate tool/PDK/handoff/SDC/IO-layers
bash workflow/pnr/scripts/auto_pnr.sh <ip>    # floorplan → place → CTS → route → SPEF
```

Per-stage slash commands: `/pnr`, `/pnr-preflight`, `/pnr-fp`, `/pnr-place`, `/pnr-cts`, `/pnr-route`, `/pnr-report`, `/pnr-auto`.

## Scripts

| script | does |
| --- | --- |
| `auto_pnr.sh` | One-shot pipeline: floorplan → place → CTS → route in sequence. |
| `run_fp.sh` | Floorplan stage (one OpenROAD invocation) → `floorplan.def`. |
| `run_place.sh` | Global + detailed placement (reads `floorplan.def`) → `placed.def`. |
| `run_cts.sh` | Clock-tree synthesis (reads `placed.def`) → `cts.def` + `cts.v`. |
| `run_route.sh` | Global + detailed route + SPEF extraction (reads `cts.def`/`cts.v`) → `routed.def` + `routed.v` + `routed.spef`. |
| `preflight.sh` | Validate OpenROAD, PDK files, SSOT physical constraints, netlist, SDC, and IO-layer directions. |
| `_pnr_common.sh` | Sourced by every stage script: tool/PDK/handoff helper functions. |
| `write_report.sh` | Aggregate per-stage stats into `pnr.report.md`. |

## Method / key rules

- **Strict SSOT authority.** SSOT alone defines floorplan targets, utilization, aspect ratio, core margin, placement density, IO layers, CTS buffer policy, routing layers, DRC waiver policy, and sign-off handoff requirements. No built-in PnR defaults when SSOT omits `pnr` fields → `[SSOT TBD REPORT] -> ssot-gen`. DONE states `SSOT TBD REPORT: none`.
- **Handoff gates.** Input netlist priority `<ip>/dft/out/scan.v` > `<ip>/syn/out/synth.v`; neither → `[PNR HANDOFF MISSING]` (exit 5). SDC required → exit 5 if missing. Stage staleness: place needs fresh `floorplan.def`, CTS needs fresh `placed.def`, route needs fresh `cts.def` → `[PNR STALE <STAGE>]`. LEF/TLEF/Liberty/tracks/RCX must be readable.
- **DFT-aware / sky130 specifics.** When `scan.v` is the input, add `set_case_analysis 0 [get_ports scan_en]` for functional-mode optimization (scan-mode timing checked at [[sta-post]]). Use horizontal `met3` / vertical `met2` (met2 is vertical in the bundled TLEF). DRC errors are surfaced, not auto-fixed.
- **Stage tcl** sets up LEF/Liberty/netlist/SDC then per stage: `initialize_floorplan`+`place_pins` → `global_placement`/`detailed_placement`/`check_placement` → `clock_tree_synthesis` → `global_route`/`detailed_route`/`extract_parasitics`/`write_spef`.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml` (`pnr` section), `<ip>/dft/out/scan.v` or `<ip>/syn/out/synth.v`, `<ip>/sta/out/<ip>.sdc`, bundled sky130 LEF/TLEF/Liberty/tracks/RCX.
- **Outputs:** `<ip>/pnr/out/{floorplan.def, placed.def, cts.def, cts.v, routed.def, routed.v, routed.spef, density.json, drc.json, pnr.log, pnr.report.md}`. The `(routed.v, routed.spef, <ip>.sdc)` triple is the [[sta-post]] handoff.

## Structure — physical pipeline

floorplan (`floorplan.def`) → placement (`placed.def`, density check) → CTS (`cts.def`/`cts.v`, clock-skew report) → route (`routed.def`/`routed.v`, DRC) → parasitic extraction (`routed.spef`). Each stage gates on the prior stage's fresh output.

## Related

Upstream: [[syn]], [[sta]] (SDC). Authority: [[ssot-gen]]. Downstream: [[sta-post]]. Back to [[workflow-stages]].
