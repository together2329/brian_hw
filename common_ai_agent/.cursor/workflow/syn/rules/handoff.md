# Synthesis Handoff Contract

The `syn` workflow consumes RTL + filelist and produces the gate-level netlist that
both `/sta` (zero-delay) and `/dft` (scan insertion) consume.

## Required upstream artifacts

```
<ip>/yaml/<ip>.ssot.yaml   # top_module, optional latch_intended
<ip>/rtl/*.{sv,v}          # source
<ip>/list/<ip>.f           # flat filelist
$SKY130_LIB                # Liberty SS corner (env var or default path)
```

## Produced artifacts

```
<ip>/syn/run.ys                 # generated yosys script
<ip>/syn/out/synth.v            # gate netlist — handoff to /sta and /dft
<ip>/syn/out/area.json          # cell counts + total area
<ip>/syn/out/syn.log            # full yosys output
<ip>/syn/out/syn.report.md      # human summary
```

## Sanity gates that must pass before handoff

1. yosys rc=0 and `synth.v` non-empty.
2. 0 unmapped generic cells (`$_*_`) — every cell name starts with `sky130_fd_sc_hd__`.
3. 0 unintended latches — only allowed if SSOT declares `latch_intended: true`.
4. `area.json` has `total_cells > 0`. (For sequential designs, `by_kind.sequential.cells > 0`.)

If any gate fails, the netlist is NOT considered ready — `/sta`, `/dft`, and `/pnr-fp` will
all refuse the stale-or-broken handoff.

## Downstream consumers

| Consumer | Required from syn | Behavior on failure |
|---|---|---|
| `/sta` | `synth.v` exists, fresh vs `<ip>/rtl/*` | `[STA HANDOFF MISSING]` or `[STA STALE NETLIST]`, exit 5 or 6 |
| `/dft` | `synth.v` exists, fresh; scan_enable_port present | `[DFT HANDOFF MISSING]`, `[DFT PORT MISMATCH]`, exit 5 or 9 |
| `/pnr-fp` | `<ip>/dft/out/scan.v` if DFT ran, else `synth.v`; SDC from `/sta` | `[PNR HANDOFF MISSING]`, exit 5 |

## Re-synthesis triggers

Any of these invalidates `synth.v` and requires re-running `/syn`:

- `<ip>/rtl/*` modified (mtime > synth.v)
- `<ip>/list/<ip>.f` modified
- `$SKY130_LIB` corner changed
- SSOT `top_module` changed

The downstream tools' staleness gate detects (1) automatically. (2)-(4) require manual
attention — re-run `/syn` whenever the inputs upstream of it change.
