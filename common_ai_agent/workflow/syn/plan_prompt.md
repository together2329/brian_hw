# Synthesis Plan Mode Rules

1. First task: read SSOT and confirm `top_module`, `rtl_files[]` resolve on disk.
2. Second task: verify `$SKY130_LIB` is set and the file is readable. Stop the plan if not — there is no valid fallback.
3. Third task: write `<ip>/syn/run.ys` from template. Do NOT execute yet.
4. Fourth task: run yosys with logging to `<ip>/syn/out/syn.log`.
5. Fifth task: sanity gate — `synth.v` has no `$_*_` and no latches (unless declared in SSOT).
6. Sixth task: parse area, write `area.json`.
7. Final task: `syn.report.md` with cell totals + FF count + top-5 cells.

Group fixes by RTL latch / unmapped cause when remediation is needed. One re-synth per fix group, not per fix.

Stop the loop when `synth.v` exists, sanity gates green, and `area.json` written.
