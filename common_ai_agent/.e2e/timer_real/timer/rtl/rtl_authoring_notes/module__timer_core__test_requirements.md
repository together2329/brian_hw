# module__timer_core__test_requirements

Authored timer_core.sv because the owner file was missing. The module exposes reset-visible count_q and irq outputs for SC01, primary tick behavior for SC02, cycle-stable registered outputs for SC03, non-corrupting disabled/unmapped/APB-error-adjacent behavior through no APB-side state coupling for SC04/SC12, and committed SSOT-visible count_q/irq observability for SC05.

The core implements the SSOT timer transactions owned by timer_core: FM_TICK_DECREMENT decrements count_q once per pclk while enable_q is high and count_q is nonzero; FM_TICK_RELOAD_IRQ reloads count_q from load_q and pulses irq for one pclk when enable_q is high and count_q is zero; FM_DISABLED_HOLD holds count_q and deasserts irq while enable_q is low. APB register transactions SC06/SC07/SC08/SC12 remain observable through timer_regs plus the shared load_q, enable_q, count_q, and irq integration signals.

PASS is not claimed because the authoring plan pass_allowed flag is false and later packets/tool evidence must still run.