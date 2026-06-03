# PnR Plan Mode Rules

For `/pnr` (full pipeline):

1. Handoff gate: input netlist (`scan.v` preferred, else `synth.v`) + `<ip>.sdc` both present and fresh.
2. SSOT gate: `pnr` section exists and declares utilization, aspect_ratio, core_space, global_density, IO layers, CTS buffer policy, routing layers, and technology/corner/library policy. Missing fields STOP with `[SSOT TBD REPORT] -> ssot-gen`.
3. Tool/PDK gate: `openroad` on PATH; `$SKY130_LEF`, `$SKY130_TLEF`, `$SKY130_LIB` all readable and matching the SSOT-declared policy.
4. Floorplan stage: write floorplan.tcl from SSOT pnr: section → run → produce `floorplan.def`.
5. Placement stage: write place.tcl → run → produce `placed.def`. Sanity gate: no overlaps.
6. CTS stage: write cts.tcl → run → produce `cts.def` + `cts.v`. Report clock skew.
7. Route stage: write route.tcl → run → produce `routed.def` + `routed.v` + `routed.spef`. Surface DRC count.
8. Report stage: aggregate per-stage stats into `pnr.report.md`, include `SSOT TBD REPORT: none`, and emit `[PNR HANDOFF] routed.spef ready — run /sta-post`.

For per-stage commands (`/pnr-fp`, `/pnr-place`, `/pnr-cts`, `/pnr-route`):

- Check prior-stage artifact freshness. Stop with `[PNR STALE <STAGE>]` if upstream is older.
- Each stage is one openroad invocation with a single tcl. Log to `<ip>/pnr/out/pnr.log` (append).
- Do NOT loop on DRC violations — surface them and stop. Fixes go to RTL or PnR config.

Stop the loop when the requested stage's output exists and the sanity gate is green.
