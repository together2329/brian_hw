# edge_det_cx1 Locked Truth Bundle

Status: requirements_locked
Approved by: cursor-agent
Locked at UTC: 2026-06-10T14:00:00Z

## Requirements

| ID | Title | Status |
|---|---|---|
| REQ_EDGE_SYNC_001  | 2-flop synchronizer       | locked |
| REQ_EDGE_RISE_001  | Rising edge detection     | locked |
| REQ_EDGE_FALL_001  | Falling edge detection    | locked |
| REQ_EDGE_RESET_001 | Reset clears all state    | locked |

## Obligations

| ID | Statement | Stage |
|---|---|---|
| OBL_EDGE_SYNC_001  | 2-flop sync chain captures sig_in into sync1 then sync2 | sim |
| OBL_EDGE_RISE_001  | rise_out = sync2 & ~prev_sync, 1-cycle pulse             | sim |
| OBL_EDGE_FALL_001  | fall_out = ~sync2 & prev_sync, 1-cycle pulse             | sim |
| OBL_EDGE_RESET_001 | All FFs clear to 0 on rst_n=0                           | sim |
| OBL_EDGE_LINT_001  | No inferred latches, single driver per register         | lint |

## Contract Refs

- C_EDGE_SYNC  → OBL_EDGE_SYNC_001
- C_EDGE_RISE  → OBL_EDGE_RISE_001
- C_EDGE_FALL  → OBL_EDGE_FALL_001
- C_EDGE_RESET → OBL_EDGE_RESET_001
- C_EDGE_LINT  → OBL_EDGE_LINT_001

## Structural Contract

SC_EDGE_PORTS: ports clk/rst_n/sig_in/rise_out/fall_out verified at rtl compile.

## Behavioral Contract

BC_EDGE_SYNC: FM_RISE/FM_FALL/FM_STABLE/FM_RESET transactions with cycle latency 3.

## Evidence Plan

- E_EDGE_SYNC, E_EDGE_RISE, E_EDGE_FALL, E_EDGE_RESET → sim/scoreboard_events.jsonl
- E_EDGE_LINT → lint/dut_lint.json
- E_EDGE_SC_PORTS → rtl/edge_det_cx1.sv
- E_EDGE_BC_SYNC → sim/scoreboard_events.jsonl
