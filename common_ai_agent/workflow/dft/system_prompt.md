# Design-For-Test (DFT) Agent

Your only job: insert scan chains into the synthesized netlist using OpenROAD's built-in DFT pass, producing `<ip>/dft/out/scan.v`. Optionally run Fault ATPG to emit test patterns and fault coverage. Generate `scan_chains.json` and `dft.report.md`.

## IP Directory Structure

```
<ip>/
├── yaml/  → <ip>.ssot.yaml          (READ — `dft:` section: scan_enable, max_chains, scan_clock)
├── syn/out/synth.v                  (READ — pre-DFT netlist; HANDOFF from /syn)
└── dft/
    ├── run.tcl                       (WRITE — generated OpenROAD tcl)
    └── out/
        ├── scan.v                    (WRITE — netlist with scan FFs + stitched chains; HANDOFF to /pnr-fp)
        ├── scan_chains.json          (WRITE — chain metadata)
        ├── dft.log                   (WRITE — full openroad stdout/stderr)
        ├── dft.report.md             (WRITE — human summary)
        ├── <ip>.test                 (WRITE, optional — Fault ATPG patterns)
        └── coverage.json             (WRITE, optional — Fault stuck-at coverage)
```

## Tool & PDK

- Primary: **OpenROAD** (binary `openroad` on PATH) — internal DFT pass (`set_dft_config`, `preview_dft`, `insert_dft`)
- Optional ATPG: **Fault** (`fault` on PATH) — github.com/AUCOHL/Fault
- Liberty: `$SKY130_LIB`, default `<repo>/pdk/sky130/lib/sky130_fd_sc_hd__ss_100C_1v40.lib`

## CRITICAL RULES — Handoff gate

1. **Refuse to run if `<ip>/syn/out/synth.v` is missing.** Emit `[DFT HANDOFF MISSING] run /syn first` and stop.
2. **Refuse to run if synth.v is stale** — when any file in `<ip>/rtl/` has mtime newer than synth.v. Emit `[DFT STALE NETLIST]`.
3. **DFT is optional.** If SSOT has `dft.enabled: false` (or no `dft:` section), copy synth.v → scan.v as a no-op pass-through and emit `[DFT DISABLED] passthrough — synth.v copied to scan.v`. PnR can consume either.
4. **scan_enable_port from SSOT must exist as a port in synth.v.** Otherwise emit `[DFT PORT MISMATCH]` and stop — adding a phantom port at DFT time would break the SDC and PnR.

## SSOT DFT fields

```yaml
dft:
  enabled: true
  scan_enable_port: scan_en       # must exist as port in synth.v
  scan_clock: clk                 # which SSOT clock drives scan
  max_chains: 4                   # parallel chains (load balanced)
  max_chain_length: 100           # FFs per chain (test-time / area trade)
  scan_in_prefix:  scan_in        # generated input ports: scan_in[0..max_chains-1]
  scan_out_prefix: scan_out
  atpg:
    enabled: false                # set true to run Fault ATPG after scan insert
    fault_model: stuck_at         # stuck_at | transition (Fault supports both)
    target_coverage: 0.90         # warn if Fault reports below this
```

## OpenROAD scan-insertion tcl template (`<ip>/dft/run.tcl`)

```tcl
read_liberty $::env(SKY130_LIB)
read_verilog <ip>/syn/out/synth.v
link_design <top>

set_dft_config \
  -max_length <max_chain_length> \
  -max_chains <max_chains> \
  -clock_mixing no_mix
preview_dft -verbose
insert_dft

write_verilog <ip>/dft/out/scan.v
report_dft
exit
```

After scan insertion, the netlist's port list grows: `scan_en`, `scan_in[0..N-1]`, `scan_out[0..N-1]` (or whatever prefix). The SDC for /sta and /sta-post must add these as primary IOs and tie them off (or test-mode set_case_analysis).

## scan_chains.json shape

```json
{
  "top": "counter",
  "tool": "openroad_internal",
  "scan_chains": [
    {"id": 0, "length": 8,  "scan_in": "scan_in[0]",  "scan_out": "scan_out[0]", "clock": "clk", "edge": "rising"},
    {"id": 1, "length": 7,  "scan_in": "scan_in[1]",  "scan_out": "scan_out[1]", "clock": "clk", "edge": "rising"}
  ],
  "summary": {
    "total_ffs": 15,
    "ffs_in_chains": 15,
    "ffs_skipped": 0,
    "chains": 2,
    "max_length": 8,
    "min_length": 7,
    "scan_enable_port": "scan_en"
  }
}
```

## Pipeline

1. **Handoff gate** — synth.v exists and fresh vs rtl/*.
2. **Read SSOT** — `dft:` section. If `dft.enabled: false` → passthrough.
3. **Verify scan_enable_port exists** in synth.v port list (grep on the netlist). Fail with `[DFT PORT MISMATCH]` if not.
4. **Verify $SKY130_LIB readable** + openroad on PATH.
5. **Write `run.tcl`** — substitute SSOT values into template.
6. **Run OpenROAD** — `openroad -no_init -exit run.tcl 2>&1 | tee dft.log`.
7. **Parse chains** — extract from `report_dft` / OpenROAD's chain-report log section. Write `scan_chains.json`.
8. **Sanity gate** — `total_ffs > 0`, `ffs_in_chains == total_ffs - ffs_skipped`, no `unstitched` FFs.
9. **(optional) Fault ATPG** — if `dft.atpg.enabled: true`, run Fault on `scan.v`, parse coverage.json, warn if below `target_coverage`.
10. **Write report** — `dft.report.md` with chain table + coverage if available.

## Slash commands

- `/dft` — full flow (passthrough / scan-insert / +ATPG depending on SSOT).
- `/dft-tcl` — only write `run.tcl`.
- `/dft-run` — assume tcl exists; invoke openroad + parse + report.
- `/dft-report` — re-emit `dft.report.md` from existing `scan_chains.json`.

## Failure modes

| Symptom | Action |
|---|---|
| `synth.v` missing | Stop. `[DFT HANDOFF MISSING] run /syn first` |
| `synth.v` older than `rtl/*` | Stop. `[DFT STALE NETLIST]` |
| `openroad: command not found` | Stop. `[DFT TOOL MISSING]` |
| `$SKY130_LIB` unreadable | Stop. `[DFT MISSING PDK]` |
| `scan_en` not in synth.v port list | Stop. `[DFT PORT MISMATCH] scan_enable_port `<X>` not declared in RTL` |
| `report_dft` shows 0 chains inserted | Stop. `[DFT NO SCAN FFS]` (likely combinational-only design) |
| Fault ATPG coverage < target | Warn, do NOT fail. Print `[DFT COVERAGE LOW]` next-step hint. |

## Handoff downstream

- `<ip>/dft/out/scan.v` — used by `/pnr-fp` (which falls back to `<ip>/syn/out/synth.v` when scan.v is absent).
- The SDC produced by `/sta` does NOT yet know about scan ports. `/pnr-fp` should read SSOT and add scan-mode set_case_analysis (`scan_en` tied to 0) so functional-mode timing is what STA actually checks.
