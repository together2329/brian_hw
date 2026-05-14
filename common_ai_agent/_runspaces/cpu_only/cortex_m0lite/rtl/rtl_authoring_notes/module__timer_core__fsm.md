# module__timer_core__fsm

Implemented explicit FSM state encoding and transitions in `rtl/cortex_m0lite.sv` while preserving prior function_model/cycle_model datapath behavior.

## Added state model
- `IDLE`, `RUN`, `DONE_PULSE` localparams.
- `state_q/state_next` with combinational transition logic and sequential update on `accept_txn`.

## Transition mapping to SSOT
- transition_0: `IDLE -> RUN` when `fetch_en && instr_data != 0`.
- transition_1: `RUN -> RUN` represented by hold in RUN when not terminal/flush.
- transition_2: `RUN -> DONE_PULSE` on terminal tick condition `step_en && busy_q && pc_q == 1`.
- transition_3: `DONE_PULSE -> IDLE` in next sampled control cycle when no new non-zero fetch starts.
- transition_4: `RUN -> IDLE` on `flush` (highest priority).

## Latency contract
No extra sampling stage added; architectural outputs remain registered on the same accepting edge (`latency=1` observable behavior retained).
