# parity_gen_cx1 SSOT coverage report

SSOT: `parity_gen_cx1/yaml/parity_gen_cx1.ssot.yaml`
Status: `blocked`

DV scenarios: 5
Scoreboard checks: ['even_par = ^data_in (combinational)', 'odd_par = ~even_par (combinational)', 'par_reg equals even_par from the previous clock cycle']
Functional bins: 19/25
Function coverage: 8/12 (66.67%) target=100.0
Cycle coverage: 11/13 (84.62%) target=100.0
RTL-observed coverage events: 16/21
Line coverage: 0/0 (None%) target=None
Branch coverage: 0/0 (None%) target=None
FSM-state coverage: 0/0 (None%) target=None

## Limitations
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: SC1_executed, SC3_executed, SC5_executed, cycle_handshake_2, cycle_pipeline_s0_reset, function_reset
