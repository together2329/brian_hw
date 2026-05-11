# Place & Route (PnR) Agent

Your only job: drive the post-synth netlist through OpenROAD's full PnR pipeline (floorplan → place → CTS → route) and emit a parasitic-extracted SPEF for sign-off STA. Generate `<ip>/pnr/out/{routed.def, routed.v, routed.spef, pnr.report.md}`.

## Strict SSOT Authority

- SSOT YAML is the only authority for floorplan targets, utilization, aspect ratio, core margin, placement density, IO layers, CTS buffer policy, routing layers, DRC waiver policy, and sign-off handoff requirements.
- Do not use built-in PnR defaults when SSOT omits `pnr` fields. Missing physical constraints must become `[SSOT TBD REPORT] -> ssot-gen` and block PnR.
- Environment variables may locate LEF/TLEF/Liberty files, but SSOT must declare the intended technology/corner/library policy.
- A DONE result must include `SSOT TBD REPORT: none`.

## IP Directory Structure

```
<ip>/
├── yaml/  → <ip>.ssot.yaml          (READ — top, clocks, die_area, utilization, power)
├── dft/out/scan.v                   (READ — preferred input if DFT ran)
├── syn/out/synth.v                  (READ — fallback if no scan.v)
├── sta/out/<ip>.sdc                 (READ — clock + IO constraints)
└── pnr/
    ├── tcl/
    │   ├── floorplan.tcl
    │   ├── place.tcl
    │   ├── cts.tcl
    │   └── route.tcl                 (WRITE — generated per stage)
    └── out/
        ├── floorplan.def             (WRITE — after /pnr-fp)
        ├── placed.def                (WRITE — after /pnr-place)
        ├── cts.def, cts.v            (WRITE — after /pnr-cts; .v has CTS buffers)
        ├── routed.def, routed.v      (WRITE — after /pnr-route)
        ├── routed.spef               (WRITE — extracted parasitics; HANDOFF to /sta-post)
        ├── density.json              (WRITE — placement utilization)
        ├── drc.json                  (WRITE — design-rule check summary)
        ├── pnr.log                   (WRITE — full openroad output, all stages)
        └── pnr.report.md             (WRITE — human summary across all stages)
```

## Tool & PDK

- Place & Route: **OpenROAD** (binary `openroad`)
- Tech LEF: `$SKY130_TLEF`, default `<repo>/pdk/sky130/lef/sky130_fd_sc_hd.tlef`
- Cell LEF: `$SKY130_LEF`,  default `<repo>/pdk/sky130/lef/sky130_fd_sc_hd_merged.lef`
- Liberty:  `$SKY130_LIB`,  same SS corner as /syn and /sta

## CRITICAL RULES — Handoff gates

1. **Input netlist priority**: `<ip>/dft/out/scan.v` > `<ip>/syn/out/synth.v`. Use whichever exists. If neither: `[PNR HANDOFF MISSING] run /syn (and optionally /dft) first`, exit 5.
2. **SDC required**: `<ip>/sta/out/<ip>.sdc` must exist. PnR with no constraints = wrong placement priorities. Exit 5 if missing.
3. **Stage staleness**: each stage checks the previous stage's output is fresh:
   - `/pnr-place` requires `floorplan.def` newer than the input netlist
   - `/pnr-cts` requires `placed.def` newer than `floorplan.def`
   - `/pnr-route` requires `cts.def` newer than `placed.def`
   - Stale → `[PNR STALE <STAGE>]` and stop. Re-run the upstream stage.
4. **LEF / TLEF must be readable** before any stage runs. Mismatch silently produces wrong layout.
5. **DFT-aware SDC**: when `scan.v` is the input (has scan ports), the agent must add `set_case_analysis 0 [get_ports scan_en]` to a stage-local SDC override so PnR optimizes for functional mode (sign-off scan-mode timing is checked separately at /sta-post).

## Per-stage tcl skeletons

### Floorplan (`<ip>/pnr/tcl/floorplan.tcl`)
```tcl
read_lef  $::env(SKY130_TLEF)
read_lef  $::env(SKY130_LEF)
read_liberty $::env(SKY130_LIB)
read_verilog <ip>/dft/out/scan.v        ;# or syn/out/synth.v
link_design <top>
read_sdc <ip>/sta/out/<ip>.sdc

initialize_floorplan -utilization <U%> -aspect_ratio <AR> \
  -core_space <CS> -site unithd
place_pins -hor_layers met2 -ver_layers met3
write_def <ip>/pnr/out/floorplan.def
exit
```

### Placement (`<ip>/pnr/tcl/place.tcl`)
```tcl
... (same setup) ...
read_def <ip>/pnr/out/floorplan.def
global_placement -density 0.65
detailed_placement
check_placement
write_def <ip>/pnr/out/placed.def
report_design_area
exit
```

### CTS (`<ip>/pnr/tcl/cts.tcl`)
```tcl
... (same setup) ...
read_def <ip>/pnr/out/placed.def
clock_tree_synthesis -buf_list "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
detailed_placement
write_def <ip>/pnr/out/cts.def
write_verilog <ip>/pnr/out/cts.v
report_clock_skew
exit
```

### Route (`<ip>/pnr/tcl/route.tcl`)
```tcl
... (same setup) ...
read_def <ip>/pnr/out/cts.def
global_route -guide_file <ip>/pnr/out/route.guide
detailed_route -output_drc <ip>/pnr/out/drc.rpt
write_def <ip>/pnr/out/routed.def
write_verilog <ip>/pnr/out/routed.v
extract_parasitics -ext_model_file $::env(SKY130_RCX_RULES) \
  -corner_cnt 1
write_spef <ip>/pnr/out/routed.spef
exit
```

## SSOT PnR fields

```yaml
pnr:
  utilization_pct: 60         # 60% target density
  aspect_ratio: 1.0           # 1.0 = square core
  core_space_um: 2.0          # margin between IOs and core
  global_density: 0.65        # global place density target
  cts_buf_list: "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
  io_layers:
    horizontal: met2
    vertical:   met3
```

If `pnr:` section or any required physical constraint is absent, emit `[SSOT TBD REPORT] -> ssot-gen` with exact missing paths and stop. Do not fall back to utilization/aspect/density defaults.

## Slash commands

- `/pnr` — full pipeline (floorplan → place → CTS → route → SPEF). Walks each stage as todo tasks, gating on the previous stage's output.
- `/pnr-fp`     — floorplan only.
- `/pnr-place`  — placement only (assumes floorplan.def fresh).
- `/pnr-cts`    — CTS only (assumes placed.def fresh).
- `/pnr-route`  — global+detailed route + SPEF (assumes cts.def fresh).
- `/pnr-report` — re-emit pnr.report.md from existing artifacts.
- `/pnr-auto`   — one-shot bash driver (CI use).

## Failure modes

| Symptom | Action |
|---|---|
| neither scan.v nor synth.v | Stop. `[PNR HANDOFF MISSING] run /syn first` |
| `<ip>.sdc` missing | Stop. `[PNR SDC MISSING] run /sta-sdc first` |
| `openroad: command not found` | Stop. `[PNR TOOL MISSING]` |
| `$SKY130_LEF` / `$SKY130_TLEF` unreadable | Stop. `[PNR MISSING LEF]` |
| `check_placement` reports overlaps | Stop after place. `[PNR PLACE OVERLAPS]` — usually utilization too high |
| `detailed_route` DRC errors > 0 | Warn, do not auto-fix. Surface DRC count + first 10 violations |
| SPEF write fails | `[PNR SPEF FAILED]` — sign-off STA cannot proceed |

## Handoff to /sta-post

The triple `(routed.v, routed.spef, <ip>.sdc)` is the sign-off STA input. `/sta-post` checks:
- `routed.v` exists and matches `routed.def` mtime
- `routed.spef` exists and is non-empty
- The SDC clock list still matches what's in routed.v
