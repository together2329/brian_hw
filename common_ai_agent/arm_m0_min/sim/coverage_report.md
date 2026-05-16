# arm_m0_min SSOT coverage report

SSOT: `arm_m0_min/yaml/arm_m0_min.ssot.yaml`
Status: `blocked`

DV scenarios: 5
Scoreboard checks: 20
Functional bins: 35/38
Function coverage: 21/21 (100.0%) target=100.0
Cycle coverage: 14/17 (82.35%) target=100.0
RTL-observed coverage events: 32/37
Line coverage: 0/0 (None%) target=90.0
Branch coverage: 0/0 (None%) target=90.0
FSM-state coverage: 8/8 (100.0%) target=None

## Limitations
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: latency_alu_instr_lt_min, latency_fetch_accept_lt_min, latency_load_store_instr_lt_min
- line: SSOT requests line/code coverage, but coverage.info has no DA records.
- branch: SSOT requests branch coverage, but coverage.info has no BRDA/BRF records for this tool flow.
