# DFT Plan Mode Rules

1. First task: handoff gate — `<ip>/syn/out/synth.v` exists AND mtime ≥ all rtl/* mtimes. If not, STOP with `[DFT HANDOFF MISSING]` or `[DFT STALE NETLIST]`.
2. Second task: read SSOT `dft:` section. If `dft.enabled: false` or absent, run the passthrough branch (cp synth.v → scan.v) and skip steps 3-7.
3. Third task: verify `scan_enable_port` from SSOT exists as a port in synth.v. Fail-fast otherwise.
4. Fourth task: verify `$SKY130_LIB` and `openroad` binary.
5. Fifth task: write `<ip>/dft/run.tcl` (set_dft_config / preview_dft / insert_dft / write_verilog).
6. Sixth task: invoke OpenROAD, log to dft.log.
7. Seventh task: parse chain output → scan_chains.json. Sanity gate: total_ffs > 0, no unstitched.
8. (optional) Eighth task: if SSOT `dft.atpg.enabled: true`, run Fault, parse coverage.
9. Final task: dft.report.md with chain table + coverage if available + scan port summary.

Stop when scan.v + scan_chains.json exist and sanity gate is green.
