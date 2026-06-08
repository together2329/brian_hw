# module__timer_core__cycle_model attempt 2

Updated timer_core to close the three open cycle_model.handshake_rules evidence gaps for pready, pslverr, and prdata without adding evidence-only aliases.

The added APB phase inputs and monitor outputs implement the SSOT expressions directly at the timer_core owner boundary:
- pready = psel & penable
- pslverr = psel & penable & unmapped address
- prdata = count_q during STATUS read, otherwise zero

Timer decrement/reload state, one-cycle irq pulse, reset behavior, and prior FSM/count-path logic are preserved.

This packet does not claim PASS because the authoring plan pass_allowed field is false and the runner must refresh integration, compile, lint, and audit evidence after applying the RTL.
