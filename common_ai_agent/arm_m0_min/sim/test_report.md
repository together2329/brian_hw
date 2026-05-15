# arm_m0_min Simulation Report

## Run Evidence
- Command: `COCOTB_TESTCASE=fl_rtl_equivalence_goals python3 tb/cocotb/test_runner.py`
- Simulator: iverilog/vvp via cocotb
- Tests discovered: 1
- Scoreboard rows: 37
- FL/RTL mismatches: 37

## Artifacts
- `sim/results.xml`
- `sim/scoreboard_events.jsonl`
- `sim/fl_rtl_compare.json`
- `sim/fl_rtl_goal_audit.json`
- `sim/arm_m0_min.vcd`

## Goal Status
- FL-vs-RTL exact match goal (mismatch_count==0): **FAILED** (actual 37)
- FCOV plan bins all hit: **PASSED** (35/35)

## First mismatches
- EQ_TRANSACTION_TX_DECODE_EXEC @cycle 1: i_haddr: expected=16 observed=0; d_hwdata: expected=18 observed=0
- EQ_TRANSACTION_TX_LOAD_STORE @cycle 2: d_haddr: expected=39 observed=13; d_hwrite: expected=1 observed=0
- EQ_SCENARIO_SC_ALU @cycle 3: i_haddr: expected=16 observed=0; d_hwdata: expected=18 observed=0
- EQ_SCENARIO_SC_CMP_BRANCH @cycle 4: i_haddr: expected=16 observed=0; d_hwdata: expected=18 observed=0
- EQ_SCENARIO_SC_LOAD_STORE @cycle 5: d_haddr: expected=39 observed=13; d_hwrite: expected=1 observed=0
