# DFT Handoff Contract

The `dft` workflow consumes the synthesized netlist from `/syn` and produces a scan-inserted netlist that `/pnr-fp` consumes. DFT is **optional** — when SSOT does not opt in, the workflow runs in passthrough mode.

## Required upstream artifact

`<ip>/syn/out/synth.v` — must exist and be **fresh**:

```
mtime(synth.v) >= max(mtime(<ip>/rtl/*.{sv,v}))
```

If stale, the netlist no longer reflects current RTL — DFT refuses to run rather than insert scan into the wrong design.

## Optional vs required

DFT is opt-in via SSOT:

```yaml
dft:
  enabled: true            # default false → passthrough
  scan_enable_port: scan_en
  scan_clock: clk
  max_chains: 4
  max_chain_length: 100
  scan_in_prefix:  scan_in
  scan_out_prefix: scan_out
  atpg:
    enabled: false
    fault_model: stuck_at
    target_coverage: 0.90
```

If `dft.enabled: false` or the section is missing entirely:
- The workflow copies `synth.v` → `scan.v` verbatim.
- `scan_chains.json` records `{"tool": "passthrough", "scan_chains": [], "summary": {...}}`.
- No port additions, no log noise. Downstream PnR consumes scan.v identically.

## scan_enable_port must exist in RTL

The port has to be declared in the RTL (typically as `input logic scan_en`). The DFT workflow does not synthesize a phantom port — that would break SDC, PnR pin assignment, and the test bench. RTL author owns the port; DFT just wires it through.

## Two open-source backends

| Backend | What it does | Where it runs | Selected by |
|---|---|---|---|
| `openroad_internal` (default) | scan flop replacement + chain stitching | OpenROAD's `insert_dft` pass | always (default) |
| `fault` (optional) | ATPG: stuck-at / transition pattern generation, fault simulation | github.com/AUCOHL/Fault | `dft.atpg.enabled: true` |

Fault is invoked AFTER OpenROAD scan insertion, on the resulting `scan.v`. It does not redo the scan stitching — only generates `.test` patterns and a coverage number.

## What DFT does NOT cover (open-source gaps)

- **MBIST** (memory BIST insertion) — no robust open tool. RTL must include MBIST manually if needed.
- **JTAG / IEEE 1149.1 boundary scan** — no auto-generation. Add via RTL boilerplate.
- **Logic BIST / PRPG / MISR** — no tool.
- **Test compression** (chain compaction) — not in OpenROAD's pass.

These are documented gaps. The `dft.report.md` should call them out when the SSOT configures features that fall outside open-source coverage.

## Handoff to /pnr-fp

`/pnr-fp` reads `<ip>/dft/out/scan.v` if it exists; otherwise `<ip>/syn/out/synth.v`. So:
- DFT enabled + ran → PnR uses scan.v (with new scan ports).
- DFT disabled / not run → PnR uses synth.v.

`/pnr-fp` must also reconcile the SDC: when scan.v has scan ports, add `set_case_analysis 0 [get_ports scan_en]` so PnR optimizes for functional mode (scan-mode timing is checked at sign-off via a separate scan-mode SDC).
