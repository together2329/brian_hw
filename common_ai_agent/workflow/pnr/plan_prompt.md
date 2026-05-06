# PnR Plan Mode Rules

For `/pnr` (full pipeline):

1. Handoff gate: input netlist (`scan.v` preferred, else `synth.v`) + `<ip>.sdc` both present and fresh.
2. Tool/PDK gate: `openroad` on PATH; `$SKY130_LEF`, `$SKY130_TLEF`, `$SKY130_LIB` all readable.
3. Floorplan stage: write floorplan.tcl from SSOT pnr: section → run → produce `floorplan.def`.
4. Placement stage: write place.tcl → run → produce `placed.def`. Sanity gate: no overlaps.
5. CTS stage: write cts.tcl → run → produce `cts.def` + `cts.v`. Report clock skew.
6. Route stage: write route.tcl → run → produce `routed.def` + `routed.v` + `routed.spef`. Surface DRC count.
7. Report stage: aggregate per-stage stats into `pnr.report.md`. Emit `[PNR HANDOFF] routed.spef ready — run /sta-post`.

For per-stage commands (`/pnr-fp`, `/pnr-place`, `/pnr-cts`, `/pnr-route`):

- Check prior-stage artifact freshness. Stop with `[PNR STALE <STAGE>]` if upstream is older.
- Each stage is one openroad invocation with a single tcl. Log to `<ip>/pnr/out/pnr.log` (append).
- Do NOT loop on DRC violations — surface them and stop. Fixes go to RTL or PnR config.

Stop the loop when the requested stage's output exists and the sanity gate is green.
