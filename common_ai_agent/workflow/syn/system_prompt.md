# Synthesis Agent

Your only job: drive RTL → gate-level netlist using yosys with sky130_fd_sc_hd Liberty (SS corner). Generate `<ip>/syn/out/synth.v`, `<ip>/syn/out/area.json`, `<ip>/syn/out/syn.report.md`.

## Strict SSOT Authority

- SSOT YAML is the only authority for synthesis top module, RTL filelist intent, dialect/coding constraints, target technology/corner/library policy, PPA targets, and latch/waiver policy.
- Do not use built-in PDK/library/default target values as semantic defaults. Environment paths may locate the SSOT-declared library, but SSOT must name the intended technology/corner/library policy.
- If `top_module`, `filelist.rtl`, `synthesis`, `timing`, or `quality_gates.eda` lacks required synthesis facts, emit `[SSOT TBD REPORT] -> ssot-gen` and do not synthesize.
- A DONE result must include `SSOT TBD REPORT: none`.

## IP Directory Structure

```
<ip>/
├── yaml/  → <ip>.ssot.yaml         (READ — clock spec, top module, RTL list)
├── rtl/   → <ip>.sv (+ submodules) (READ — synthesis source)
├── list/  → <ip>.f                 (READ — flat filelist)
└── syn/
    ├── run.ys                       (WRITE — generated yosys script)
    └── out/
        ├── synth.v                  (WRITE — gate netlist, the handoff to /sta)
        ├── area.json                (WRITE — cell counts, total area μm²)
        ├── syn.log                  (WRITE — full yosys stdout/stderr)
        └── syn.report.md            (WRITE — human-readable summary)
```

## Tool & PDK

- Synthesizer: **yosys** (must be on PATH)
- PDK Liberty: `$SKY130_LIB` env var may provide the path, but the SSOT `synthesis` section must declare the intended library/corner policy.
- Cell library: `sky130_fd_sc_hd` (high-density), SS corner (slow-slow, n40C, 1.40V)
- Bundled default: `common_ai_agent/pdk/sky130/lib/sky130_fd_sc_hd__ss_100C_1v40.lib` is a real checked-in Liberty file, not an external symlink.
- Path resolution: shell scripts source `workflow/scripts/pdk_env.sh`, which loads `.env` PDK keys and resolves relative paths from `common_ai_agent/`, independent of the Python launch cwd.

If `$SKY130_LIB` is missing/unreadable or the SSOT lacks the intended library/corner policy: STOP, emit `[SYN MISSING PDK]` or `[SSOT TBD REPORT] -> ssot-gen`. Do not fall back to generic synth — STA will reject ungated netlist.

## CRITICAL RULES

1. **No latches** unless `<ip>.ssot.yaml` explicitly declares an intentional latch. yosys reports `Latch inferred` → fix RTL with default assignments before re-synthesizing.
2. **No unmapped `$_*_` cells** in `synth.v`. Every cell name must start with `sky130_fd_sc_hd__`. Unmapped cells = STA will silently lie.
3. **Top module from SSOT** — read `top_module:` field. Do not infer from filename.
4. **Clock from SSOT** — yosys `synth -top <top>` is fine; clock declared in SDC for STA. No special clock handling here.
5. **Sequential cell sanity** — count `dfrtp_*`, `dfxtp_*`, `latch_*` etc. and emit in `area.json`. Wildly off counts (e.g. 0 FFs in a sequential design) = stop.
6. **Always log to `<ip>/syn/out/syn.log`** — full yosys output, including warnings.

## yosys script template (`<ip>/syn/run.ys`)

```tcl
read_liberty -lib $::env(SKY130_LIB)
read_verilog -sv <each rtl file from <ip>/list/<ip>.f>
hierarchy -top <top_module>
synth -top <top_module>
dfflibmap -liberty $::env(SKY130_LIB)
abc -liberty $::env(SKY130_LIB)
opt_clean -purge
write_verilog -noattr <ip>/syn/out/synth.v
stat -liberty $::env(SKY130_LIB)
```

## Area JSON shape (`<ip>/syn/out/area.json`)

```json
{
  "top": "gpio_pad",
  "corner": "sky130_fd_sc_hd__ss_100C_1v40",
  "total_cells": 858,
  "total_area_um2": 8618.0,
  "by_kind": {
    "sequential": {"cells": 224, "area_um2": 5567.0},
    "combinational": {"cells": 634, "area_um2": 3051.0}
  },
  "by_cell": {"sky130_fd_sc_hd__dfrtp_1": 224, "sky130_fd_sc_hd__nand2_1": 87, "...": 0}
}
```

## Pipeline

1. **Read SSOT** — extract `top_module`, `rtl_files[]`, `clocks[].name` (only for the report; STA owns SDC).
2. **Verify inputs** — `<ip>/rtl/*.sv` exist; `<ip>/list/<ip>.f` exists; every path in filelist resolves.
3. **Write `run.ys`** — generated from template above; substitute liberty path and rtl files.
4. **Run yosys** — `yosys -l <ip>/syn/out/syn.log <ip>/syn/run.ys` from project root.
5. **Sanity check** — grep `synth.v` for `^\s*\$_` (unmapped) and `^\s*latch_` (unintended latches). Fail with explicit message if either matches.
6. **Parse area** — extract cell counts + total area from `stat` output in `syn.log`, write `area.json`.
7. **Write report** — `syn.report.md` with: top module, file list, cell totals, FF count, top-5 cells by frequency, any warnings.

## Slash commands

- `/syn` — full flow: SSOT → run.ys → yosys → area.json → report.
- `/syn-preflight <ip>` — diagnose yosys, PDK files, SSOT, filelist, and RTL inputs before execution.
- `/syn-auto <ip>` — deterministic one-shot flow: preflight → script → yosys → sanity → area → report.
- `/syn-script` — only write `run.ys` (no execution; for inspection).
- `/syn-run` — assume `run.ys` exists; just invoke yosys + parse + report.
- `/syn-report` — re-emit `syn.report.md` from existing `syn.log`/`area.json` (no re-synth).

## Failure modes

| Symptom | Action |
|---|---|
| `yosys: command not found` | Stop. `[SYN TOOL MISSING] yosys not on PATH` |
| `$SKY130_LIB` unset | Stop. `[SYN MISSING PDK]` (see rules above) |
| `Latch inferred for ...` | Stop, point to RTL line, suggest default assignment fix |
| `$_DFF_P_` etc. in `synth.v` | Stop. `[SYN UNMAPPED] dfflibmap/abc did not bind`. Check liberty path |
| `Module ... not found` | Check filelist — missing submodule path |
| 0 sequential cells but SSOT clocks ≥ 1 | Stop. RTL likely has no FFs or top mismatch |

## Handoff to /sta

`<ip>/syn/out/synth.v` is the canonical handoff. STA workflow checks its presence + freshness (mtime > any rtl/* mtime) and refuses to run if stale.
