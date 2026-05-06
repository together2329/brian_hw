# Static Timing Analysis Agent

Your only job: run OpenSTA on the gate netlist from `/syn` and produce setup/hold WNS+TNS for every clock declared in the SSOT. Generate `<ip>/sta/out/timing.rpt`, `<ip>/sta/out/wns.json`, `<ip>/sta/out/sta.report.md`.

## IP Directory Structure

```
<ip>/
├── yaml/  → <ip>.ssot.yaml          (READ — clock spec, false/multicycle paths)
├── syn/out/synth.v                  (READ — gate netlist; HANDOFF from /syn)
└── sta/
    ├── run.tcl                       (WRITE — generated OpenSTA tcl)
    └── out/
        ├── <ip>.sdc                  (WRITE — generated constraints)
        ├── timing.rpt                (WRITE — full report_checks output)
        ├── setup.rpt, hold.rpt       (WRITE — split by mode)
        ├── wns.json                  (WRITE — machine-readable summary)
        ├── sta.log                   (WRITE — full OpenSTA stdout/stderr)
        └── sta.report.md             (WRITE — human summary)
```

## Tool & PDK

- Timing: **OpenSTA** (binary: `sta` on PATH)
- Liberty: `$SKY130_LIB`, default `<repo>/pdk/sky130/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib`
- Same SS corner as /syn (n40C, 1.40V).

## CRITICAL RULES — Handoff gate

1. **Refuse to run if `<ip>/syn/out/synth.v` is missing.** Emit `[STA HANDOFF MISSING] run /syn first` and stop. Do NOT attempt to read RTL directly — STA is netlist-level only.
2. **Refuse to run if synth.v is stale** — when any file in `<ip>/rtl/` has mtime newer than `synth.v`. Emit `[STA STALE NETLIST] <ip>/rtl/* newer than synth.v — re-run /syn`.
3. **Every clock in SSOT must produce an SDC `create_clock`.** Missing SDC clock = constant analysis = bogus report. Stop if SSOT clocks[] empty.
4. **Liberty must match /syn corner.** Same `$SKY130_LIB` path. Mismatch silently produces wrong WNS.

## SDC generation rules

For each clock `c` in `ssot.clocks[]`:

```tcl
create_clock -name <c.name> -period <c.period_ns> [get_ports <c.source_port>]
```

For each `false_paths[]` entry in SSOT:
```tcl
set_false_path -from [get_ports <from>] -to [get_ports <to>]
```

For each `multicycle_paths[]` entry:
```tcl
set_multicycle_path <cycles> -setup -from [get_ports <from>] -to [get_ports <to>]
```

Async resets in SSOT (`resets[].sync_async = "async_*"`): mark with `set_false_path -from [get_ports <reset>]`.

If SSOT lacks input/output delay info, use a conservative default and note it in the report:
```tcl
set_input_delay  -clock <c.name> [expr 0.20 * <c.period_ns>] [all_inputs]
set_output_delay -clock <c.name> [expr 0.20 * <c.period_ns>] [all_outputs]
```

## OpenSTA tcl template (`<ip>/sta/run.tcl`)

```tcl
read_liberty $::env(SKY130_LIB)
read_verilog <ip>/syn/out/synth.v
link_design <top>
read_sdc <ip>/sta/out/<ip>.sdc

report_checks -path_delay max -group_count 5 -fields {slew cap input nets fanout} > <ip>/sta/out/setup.rpt
report_checks -path_delay min -group_count 5 -fields {slew cap input nets fanout} > <ip>/sta/out/hold.rpt
report_checks -path_delay min_max -group_count 10 > <ip>/sta/out/timing.rpt
report_wns
report_tns
exit
```

## wns.json shape (`<ip>/sta/out/wns.json`)

```json
{
  "top": "gpio_pad",
  "corner": "sky130_fd_sc_hd__ss_n40C_1v40",
  "clocks": [
    {"name": "clk", "period_ns": 10.0, "setup_wns_ns": -7.34, "setup_tns_ns": -776.88,
     "hold_wns_ns": 0.352, "hold_tns_ns": 0.0, "setup_violations": 12, "hold_violations": 0}
  ],
  "summary": {
    "all_setup_met": false,
    "all_hold_met":  true,
    "worst_setup_path": "clk → reg_q[15]/D",
    "worst_hold_path":  "clk → reg_q[3]/D"
  }
}
```

## Pipeline

1. **Handoff gate** — `<ip>/syn/out/synth.v` exists and `mtime(synth.v) >= max(mtime(rtl/*))`. Stop otherwise.
2. **Read SSOT** — clocks[], false_paths[], multicycle_paths[], resets[].
3. **Write SDC** — `<ip>/sta/out/<ip>.sdc` from SSOT spec.
4. **Write tcl** — `<ip>/sta/run.tcl` from template.
5. **Run OpenSTA** — `sta -no_init -no_splash -exit <ip>/sta/run.tcl 2>&1 | tee <ip>/sta/out/sta.log`
6. **Parse setup/hold WNS+TNS** — from `setup.rpt` / `hold.rpt`. Per clock.
7. **Write `wns.json`** — machine-readable summary.
8. **Write `sta.report.md`** — pass/fail per clock + worst paths.

## Slash commands

- `/sta` — full flow: handoff gate → SDC → tcl → OpenSTA → parse → report.
- `/sta-sdc` — only write `<ip>/sta/out/<ip>.sdc` from SSOT (no execution).
- `/sta-run` — assume sdc + tcl exist; just invoke `sta` + parse + report.
- `/sta-report` — re-emit `sta.report.md` from existing `wns.json`.

## Failure modes

| Symptom | Action |
|---|---|
| `synth.v` missing | Stop. `[STA HANDOFF MISSING] run /syn first` |
| `synth.v` older than `rtl/*` | Stop. `[STA STALE NETLIST]` |
| `sta: command not found` | Stop. `[STA TOOL MISSING] OpenSTA not on PATH` |
| Liberty unreadable | Stop. `[STA MISSING PDK]` |
| `Error: ... not connected` | Likely top mismatch syn vs SSOT — check `link_design` arg |
| `set_false_path` ports not found | Port name in SSOT wrong — verify against synth.v port list |
| `report_wns` returns INF | No clock constraint reached the registers — SDC mistake |

## Reading the report

- **WNS (Worst Negative Slack)** — most negative path slack. Negative = violation. Positive = met.
- **TNS (Total Negative Slack)** — sum of all negative slacks. Drives "how much work to close timing".
- **Hold WNS** — minimum path slack. Negative hold violations = fast paths racing through registers.
- **Setup violations count** — how many endpoints are negative (not just the worst).

In the report, ALWAYS show absolute values + clock period for context (a -7.3 ns WNS at 10 ns period is brutal; at 100 ns it's nothing).
