# module__timer_regs__function_model_01 notes

Updated `timer_regs` to add a real one-bit `irq_q` FunctionalModel mirror owned by the register block for this slice. APB LOAD/CTRL/STATUS/unmapped accepted access decodes now drive explicit irq clear conditions, and timer tick irq-decrement/reload/disabled decode expressions are present as live RTL logic using existing `psel`, `enable_q`, and `count_q` inputs. The top-level interrupt remains owned by `timer_core`; this register-local `irq_q` is the SSOT FunctionalModel state evidence for APB transaction state updates and reset behavior.

No SSOT or locked-truth artifacts were modified. PASS is not claimed because the authoring plan still has open packets/gates.