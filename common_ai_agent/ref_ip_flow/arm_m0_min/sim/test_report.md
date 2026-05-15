# arm_m0_min Simulation Report

## Run Evidence
- Command: `COCOTB_TESTCASE=fl_rtl_equivalence_goals python3 tb/cocotb/test_runner.py`
- Simulator: iverilog/vvp via cocotb
- Tests discovered: 1
- Scoreboard rows: 37
- FL/RTL mismatches: 0

## Artifacts
- `sim/results.xml`
- `sim/scoreboard_events.jsonl`
- `sim/fl_rtl_compare.json`
- `sim/fl_rtl_goal_audit.json`
- `sim/arm_m0_min.vcd`

## Goal Status
- FL-vs-RTL exact match goal (mismatch_count==0): **PASSED** (actual 0)
- FCOV plan bins all hit: **PASSED** (35/35)
