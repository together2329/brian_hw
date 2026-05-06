# PnR Handoff Contract

`pnr` consumes (scan.v OR synth.v) + SDC and produces routed netlist + SPEF for sign-off STA.

## Required upstream artifacts

```
<ip>/dft/out/scan.v       # preferred — DFT-inserted netlist with scan ports
   OR
<ip>/syn/out/synth.v      # fallback when DFT didn't run

<ip>/sta/out/<ip>.sdc     # required — clock + IO constraints
$SKY130_TLEF              # tech LEF (metal stack)
$SKY130_LEF               # cell LEF (placement footprint)
$SKY130_LIB               # Liberty (timing)
```

## Stage outputs (the per-stage handoff contract)

| Stage | Slash | Reads | Writes |
|---|---|---|---|
| Floorplan | `/pnr-fp` | netlist + SDC + LEFs | `floorplan.def` |
| Place | `/pnr-place` | `floorplan.def` (must be fresh) | `placed.def` |
| CTS | `/pnr-cts` | `placed.def` (fresh) | `cts.def`, `cts.v` |
| Route | `/pnr-route` | `cts.def` (fresh) | `routed.def`, `routed.v`, `routed.spef` |

Each stage gate-checks its upstream input via mtime comparison. A stale upstream
emits `[PNR STALE <STAGE>]` and refuses to proceed — the user re-runs the upstream
stage or `/pnr` (full pipeline) to rebuild from the right point.

## DFT-aware constraints

When the input is `scan.v`, the netlist has `scan_en`, `scan_in[*]`, `scan_out[*]`
ports added by `/dft`. PnR must:

1. Add `set_case_analysis 0 [get_ports scan_en]` to a stage-local SDC override so
   functional-mode timing drives placement (scan-mode timing is checked at
   `/sta-post`).
2. Place scan ports on perimeter — typically using the same place_pins call,
   OpenROAD treats them as ordinary primary IOs.
3. Stitch scan chains as routing constraints — OpenROAD detects scan_in→FF.SI→...
   →scan_out paths as combinational chains and routes them as such.

## Output artifact contract for /sta-post

```
<ip>/pnr/out/routed.v       # post-route netlist (with CTS buffers + post-route opt)
<ip>/pnr/out/routed.spef    # parasitic R/C — feeds OpenSTA read_spef
<ip>/sta/out/<ip>.sdc       # same SDC /sta used (or scan-mode override)
```

`/sta-post` checks:
- All three exist and are mutually consistent (same top module, same clocks)
- `routed.v` mtime ≥ `cts.v` mtime ≥ `synth.v` mtime
- `routed.spef` non-empty (a 0-byte SPEF means parasitic extraction silently failed)

## What PnR does NOT cover

- **Sign-off DRC** — `detailed_route` DRC count is reported but not blockingly
  fixed. Some sky130 DRC errors require Magic + KLayout sign-off; that's a
  separate `dr-signoff/` workflow (not yet implemented).
- **Antenna check** — OpenROAD has `check_antennas` but it's a separate stage
  not chained here. Add manually if needed.
- **EM / IR drop** — OpenROAD-based PI sign-off is an open problem; out of scope.
- **GDS write** — `routed.def` is the deliverable here; GDS via Magic
  `def2gds`-equivalent is also out of scope for v1.
