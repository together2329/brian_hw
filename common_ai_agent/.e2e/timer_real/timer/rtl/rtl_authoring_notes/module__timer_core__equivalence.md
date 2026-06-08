# module__timer_core__equivalence

Authored `timer_core` from the locked SSOT timer core behavior so module-boundary observations can be compared against `FunctionalModel.apply` for `sub_modules.timer_core.module_equivalence`.

Implemented behavior:
- `count_q` reset to zero and held while disabled.
- Enabled nonzero ticks decrement by one per `pclk`.
- Enabled zero ticks reload from `load_q` and assert `irq` for exactly one cycle.
- Conceptual FSM states `DISABLED`, `ENABLED_COUNT`, and `RELOAD_IRQ` are present as live state/control logic.

This packet does not claim PASS because equivalence goals and scoreboard artifacts are tool/DV evidence generated outside this RTL-owned packet.