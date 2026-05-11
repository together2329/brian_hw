# Synthesis Plan Mode Rules

1. First task: read SSOT and confirm `top_module`, `filelist.rtl`, `synthesis`, `timing`, and `quality_gates.eda` are present and substantive. If any required field is missing, STOP with `[SSOT TBD REPORT] -> ssot-gen`.
2. Second task: verify `$SKY130_LIB` is set and the file is readable. Stop the plan if not — there is no valid fallback.
3. Third task: verify the SSOT declares the intended technology/corner/library policy; environment paths only locate that declared policy.
4. Fourth task: write `<ip>/syn/run.ys` from template. Do NOT execute yet.
5. Fifth task: run yosys with logging to `<ip>/syn/out/syn.log`.
6. Sixth task: sanity gate — `synth.v` has no `$_*_` and no latches (unless declared in SSOT).
7. Seventh task: parse area, write `area.json`.
8. Final task: `syn.report.md` with cell totals + FF count + top-5 cells and `SSOT TBD REPORT: none`.

Group fixes by RTL latch / unmapped cause when remediation is needed. One re-synth per fix group, not per fix.

Stop the loop when `synth.v` exists, sanity gates green, and `area.json` written.
