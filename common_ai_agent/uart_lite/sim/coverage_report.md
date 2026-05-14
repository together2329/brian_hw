# uart_lite SSOT coverage report

SSOT: `uart_lite/yaml/uart_lite.ssot.yaml`
Status: `blocked`

DV scenarios: 17
Scoreboard checks: 17
Functional bins: 55/86
Function coverage: 29/33 (87.88%) target=100.0
Cycle coverage: 26/53 (49.06%) target=100.0
RTL-observed coverage events: 30/68
Line coverage: 0/0 (None%) target=90.0
Branch coverage: 0/0 (None%) target=85.0
FSM-state coverage: 8/18 (44.44%) target=100.0

## Limitations
- rtl_observed_coverage: Functional bins are not covered until a passing scoreboard row with real rtl_observed signals hits them: ccov_perf_fifo_depth, ccov_rx_data, ccov_rx_start_confirm, ccov_tx_data, ccov_tx_idle, cycle_backpressure_0, cycle_backpressure_1, cycle_perf_depth, cycle_perf_frequency_mhz, cycle_perf_outstanding, cycle_pipeline_rx_data, cycle_pipeline_rx_idle, ... +19
- line: SSOT requests line/code coverage, but coverage.info has no DA records.
- branch: SSOT requests branch coverage, but coverage.info has no BRDA/BRF records for this tool flow.
