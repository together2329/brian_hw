# cortex_m0lite SSOT coverage report

SSOT: `cortex_m0lite/yaml/cortex_m0lite.ssot.yaml`
Status: `blocked`

DV scenarios: 6
Scoreboard checks: 6
Functional bins: 30/45
Function coverage: 9/14 (64.29%) target=95.0
Cycle coverage: 21/31 (67.74%) target=90.0
RTL-observed coverage events: 25/27
Line coverage: 0/0 (None%) target=90.0
Branch coverage: 0/0 (None%) target=85.0
FSM-state coverage: 5/5 (100.0%) target=100.0

## Limitations
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: alu_flag_update_matrix, alu_ops_all, branch_flush_cycles, branch_taken_not_taken, core_bus_frequency_ratio, cpi_nominal_stream, dmem_wait_cycles, hazard_stall_cycles, if_wait_cycles, load_store_word, outstanding_data_depth, outstanding_instruction_depth, ... +3
- line: SSOT requests line/code coverage, but coverage.info has no DA records.
- branch: SSOT requests branch coverage, but coverage.info has no BRDA/BRF records for this tool flow.
