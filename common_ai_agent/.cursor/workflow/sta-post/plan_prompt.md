# Post-Route STA Plan Mode Rules

1. Handoff gates (all four must pass):
   - <ip>/pnr/out/routed.v exists and non-empty
   - <ip>/pnr/out/routed.spef exists and non-empty
   - <ip>/sta/out/<ip>.sdc exists
   - mtime(routed.v) >= mtime(cts.v); mtime(routed.spef) >= mtime(routed.def)
2. Tool gate: `sta` on PATH; `$SKY130_LIB` readable; same corner as /pnr.
3. Write `<ip>/sta-post/run.tcl` (read_liberty + read_verilog + link + read_sdc + read_spef + reports).
4. Invoke OpenSTA, log to sta.log.
5. Parse setup/hold WNS + TNS + skew per clock → wns.json.
6. Compose sta.report.md including a delta column vs /sta wns.json (if it exists), so the user sees how much pre→post degraded.

Do NOT loop on negative slack — fixes go to /pnr (different floorplan, density, or buf list) or RTL.
Stop when wns.json + sta.report.md exist and gates green.
