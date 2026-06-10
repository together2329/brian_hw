# parity_gen_cx1 Locked Truth Bundle

Status: requirements_locked
Approved by: cursor-agent
Locked at UTC: 2026-06-10T14:00:00Z

## Requirements

| ID | Title | Status |
|---|---|---|
| REQ_PAR_EVEN_001  | Even parity (combinational)   | locked |
| REQ_PAR_ODD_001   | Odd parity (combinational)    | locked |
| REQ_PAR_REG_001   | Registered parity             | locked |
| REQ_PAR_RESET_001 | Reset clears registered parity| locked |

## Obligations

| ID | Statement | Stage |
|---|---|---|
| OBL_PAR_EVEN_001  | even_par = ^data_in, combinational              | sim  |
| OBL_PAR_ODD_001   | odd_par = ~even_par, combinational              | sim  |
| OBL_PAR_REG_001   | par_reg = even_par delayed 1 clock              | sim  |
| OBL_PAR_RESET_001 | par_reg=0 on rst_n=0                            | sim  |
| OBL_PAR_LINT_001  | No inferred latches, single driver per register | lint |

## Contract Refs

- C_PAR_EVEN  → OBL_PAR_EVEN_001
- C_PAR_ODD   → OBL_PAR_ODD_001
- C_PAR_REG   → OBL_PAR_REG_001
- C_PAR_RESET → OBL_PAR_RESET_001
- C_PAR_LINT  → OBL_PAR_LINT_001

## Structural Contract

SC_PAR_PORTS: ports clk/rst_n/data_in/even_par/odd_par/par_reg verified at RTL compile.

## Behavioral Contract

BC_PAR_FUNC: FM_PARITY/FM_RESET transactions; combinational even_par/odd_par (0-cycle), registered par_reg (1-cycle).

## Evidence Plan

- E_PAR_EVEN, E_PAR_ODD, E_PAR_REG, E_PAR_RESET → sim/scoreboard_events.jsonl
- E_PAR_LINT → lint/dut_lint.json
- E_PAR_SC_PORTS → rtl/parity_gen_cx1.sv
