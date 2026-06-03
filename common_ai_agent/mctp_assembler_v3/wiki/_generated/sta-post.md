---
title: Post-Route Sign-Off STA
type: reference
tags: [workflow, sta-post, signoff]
status: stable
---

# Post-Route Sign-Off STA

`sta-post` runs OpenSTA on the [[pnr]] post-route netlist with extracted parasitics (SPEF) to produce silicon-accurate, sign-off-grade setup/hold + clock-skew timing. Unlike the optimistic zero-net-delay [[sta]], this view includes real interconnect R/C — it is the timing truth. See [[workflow-stages]] for the pipeline.

## Purpose

Re-time the routed design with `read_spef` so the reported WNS/TNS reflect actual layout parasitics, and compose the sign-off report with the pre-route-vs-sign-off delta — the final timing evidence in the EDA tail.

## How to run

Run from the project root (OpenSTA `sta` + `$SKY130_LIB` via `pdk_env.sh`):

```bash
bash workflow/sta-post/scripts/preflight.sh <ip>   # validate tool/PDK/PnR handoff/freshness
bash workflow/sta-post/scripts/auto_sta_post.sh <ip>
```

Slash equivalents: `/sta-post`, `/sta-post-preflight`, `/sta-post-tcl`, `/sta-post-run`, `/sta-post-report`, `/sta-post-auto`.

## Scripts

| script | does |
| --- | --- |
| `auto_sta_post.sh` | End-to-end sign-off STA driver. |
| `write_sta_post_tcl.sh` | Generate `<ip>/sta-post/run.tcl` with `read_spef`. |
| `run_sta_post.sh` | Invoke OpenSTA on `run.tcl`. |
| `parse_wns.sh` | Reuse the `/sta` parser, output `wns.json` with `mode=post_route` + per-clock skew from `skew.rpt`. |
| `preflight.sh` | Validate post-route STA tool, PDK, and PnR handoff inputs. |
| `write_report.sh` | Compose `sta.report.md`, including the pre-vs-post delta when `/sta` `wns.json` exists. |

## Method / key rules

- **Strict SSOT authority.** SSOT alone defines sign-off clocks, IO delays, false/multicycle paths, scan/functional-mode case analysis, PDK/corner/library policy, and pass/fail targets. No invented scan case analysis / delay defaults / exceptions; missing post-route fact → `[SSOT TBD REPORT] -> ssot-gen`. DONE states `SSOT TBD REPORT: none`.
- **Handoff gates.** Refuse if `routed.v` missing (`[STA-POST HANDOFF MISSING]`, exit 5), if `routed.spef` missing or 0 bytes (`[STA-POST SPEF MISSING]`, exit 5 — without SPEF this collapses to zero-delay STA), or if SDC missing (exit 5). Staleness: `routed.v` older than `cts.v` (exit 6), `routed.spef` older than `routed.def` (exit 6). Liberty must match the [[pnr]] corner.
- **tcl** = `read_liberty` → `read_verilog routed.v` → `link_design` → `read_sdc` → `read_spef routed.spef` → optional `set_case_analysis 0 [get_ports scan_en]` → `report_checks` setup/hold/min_max → `report_clock_skew` → `report_wns`/`report_tns`.
- **Reading.** Setup numbers degrade vs [[sta]] because real net delays now count — that delta is the key sign-off reading. WNS suddenly *better* post-route is suspicious (SDC didn't load or extraction failed silently) → log a warning.

## Inputs → Outputs

- **Inputs:** `<ip>/yaml/<ip>.ssot.yaml` (clocks/exceptions), `<ip>/pnr/out/routed.v`, `<ip>/pnr/out/routed.spef`, `<ip>/sta/out/<ip>.sdc`, `$SKY130_LIB`.
- **Outputs:** `<ip>/sta-post/run.tcl`, `<ip>/sta-post/out/{timing.rpt, setup.rpt, hold.rpt, skew.rpt, sta.log}`, `<ip>/sta-post/out/wns.json` (`mode: post_route`, per-clock setup/hold WNS/TNS + violations + `max_skew_ps`/`max_latency_ps`), `<ip>/sta-post/out/sta.report.md` (PASS/FAIL + delta vs [[sta]]).

## Structure — sign-off STA pipeline

handoff gate (routed.v + non-empty routed.spef + SDC, all fresh) → Liberty/tool preflight → write `run.tcl` (with `read_spef`) → run OpenSTA → parse per-clock setup/hold WNS+TNS + skew → write `wns.json` → compose report with pre-route-vs-sign-off delta.

## Related

Upstream: [[pnr]] (routed netlist + SPEF), [[sta]] (SDC + pre-route comparison). Authority: [[ssot-gen]]. The terminal EDA stage — back to [[workflow-stages]].
