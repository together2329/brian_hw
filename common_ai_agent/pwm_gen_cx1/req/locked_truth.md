# Locked Truth - pwm_gen_cx1

## Approval
- status: requirements_locked
- approved_by: cursor-agent
- approved_at_utc: 2026-06-10T14:00:00Z
- decision_note: ROCEV chain exercise: deterministic-only run

## Requirements

| requirement_id | title | status |
| --- | --- | --- |
| REQ_PWM_COUNTER_001 | 8-bit free-running counter | locked |
| REQ_PWM_DUTY_001 | DUTY register write | locked |
| REQ_PWM_OUT_001 | PWM output compare | locked |
| REQ_PWM_RESET_001 | Reset clears all state | locked |

## Obligations

| obligation_id | closure_stage | granularity |
| --- | --- | --- |
| OBL_PWM_COUNTER_001 | sim | temporal |
| OBL_PWM_DUTY_001 | sim | count |
| OBL_PWM_OUT_001 | sim | content |
| OBL_PWM_RESET_001 | sim | structural |
| OBL_PWM_LINT_001 | lint | structural |

## Contracts

### Structural
- SC_PWM_PORTS: ports clk, rst_n, duty_in, wr_en, pwm_out

### Behavioral
- BC_PWM_COUNT: counter_q increments each cycle; pwm_out = counter_q < duty_reg
- BC_PWM_DUTY: duty_reg latches duty_in when wr_en=1
- BC_PWM_RESET: async reset clears counter_q and duty_reg to 0
- BC_PWM_LINT: no inferred latches; single driver per register

### Contract Refs
- C_PWM_COUNTER: ssot_anchor=function_model.transactions.FM_TICK
- C_PWM_DUTY: ssot_anchor=function_model.transactions.FM_WRITE
- C_PWM_OUT: ssot_anchor=function_model.transactions.FM_TICK
- C_PWM_RESET: ssot_anchor=cycle_model.reset
- C_PWM_LINT: ssot_anchor=coding_rules

## Evidence Plan

| evidence_id | contract_ref | artifact | pass_condition |
| --- | --- | --- | --- |
| E_PWM_BC_COUNT | BC_PWM_COUNT | sim/scoreboard_events.jsonl | pwm_out matches FL expected each cycle |
| E_PWM_BC_DUTY | BC_PWM_DUTY | sim/scoreboard_events.jsonl | duty_reg matches duty_in one cycle after wr_en |
| E_PWM_BC_RESET | BC_PWM_RESET | sim/scoreboard_events.jsonl | counter_q=0 and duty_reg=0 during reset |
| E_PWM_BC_LINT | BC_PWM_LINT | lint/dut_lint.json | no latch findings |
| E_PWM_COUNTER | C_PWM_COUNTER | sim/scoreboard_events.jsonl | counter_q increments observed |
| E_PWM_DUTY | C_PWM_DUTY | sim/scoreboard_events.jsonl | duty_reg write observed |
| E_PWM_OUT | C_PWM_OUT | sim/scoreboard_events.jsonl | pwm_out = (counter_q < duty_reg) observed |
| E_PWM_RESET | C_PWM_RESET | sim/scoreboard_events.jsonl | pwm_out=0 during reset |
| E_PWM_LINT | C_PWM_LINT | lint/dut_lint.json | no latch/single-driver violations |
| E_PWM_SC_PORTS | SC_PWM_PORTS | rtl/pwm_gen_cx1.sv | top ports present with correct widths |
