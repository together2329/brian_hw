# module__timer_core__function_model

Authored `timer_core` as the owner for FunctionalModel state variables referenced by this packet.

- `load_q` is consumed as the 32-bit reload value from the register block.
- `enable_q` is consumed as the 1-bit timer enable control from the register block.
- `count_q` is owned as a 32-bit registered output with active-low reset to zero.
- `irq` is registered and derived from the enabled zero-count reload event so it is a cycle-stable pulse.
- The conceptual FSM states `DISABLED`, `ENABLED_COUNT`, and `RELOAD_IRQ` are present for traceability to the SSOT FSM while the datapath implements the SSOT tick rules directly.

This packet does not claim rtl-gen PASS because the authoring plan marks pass_allowed=false and later packets/tool evidence remain open.
