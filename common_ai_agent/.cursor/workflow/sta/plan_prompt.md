# STA Plan Mode Rules

1. First task: handoff gate — `<ip>/syn/out/synth.v` exists AND mtime ≥ all rtl/* mtimes. If not, STOP and surface `[STA HANDOFF MISSING]` or `[STA STALE NETLIST]`.
2. Second task: read SSOT timing clocks, IO delays, false_paths, multicycle paths, async resets, operating mode, and library/corner policy. If any required timing fact is missing, STOP with `[SSOT TBD REPORT] -> ssot-gen`.
3. Third task: write `<ip>/sta/out/<ip>.sdc` only from SSOT (clocks, IO delays, false_paths, multicycle, async resets). No implicit delay defaults.
4. Fourth task: verify `$SKY130_LIB` set/readable and matching SSOT policy.
5. Fifth task: write `<ip>/sta/run.tcl`.
6. Sixth task: invoke OpenSTA, log to sta.log.
7. Seventh task: parse setup/hold WNS+TNS per clock → wns.json.
8. Final task: sta.report.md with pass/fail per clock + WNS/TNS table + worst paths and `SSOT TBD REPORT: none`.

Do NOT loop on negative slack — STA reports the truth, fixes go in /syn or RTL. Just report cleanly and stop.
