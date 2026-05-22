Implemented initial gpio_regs owner RTL for function_model slice.

Key implemented behavior:
- Async active-low reset clears dir_q/dout_q/din_q to zero (FM4).
- Rising-edge control latch of dir_in->dir_q and dout_in->dout_q (FM1).
- Rising-edge masked input sample din_q <= (din_q & dir_q) | (pad_in & ~dir_q) (FM2).

Design intent:
- Keep state-owner logic in one sequential block for atomic update visibility.
- Use WIDTH parameter for all vector sizing.
- Avoid loops/functions/packages per project RTL subset.

Follow-up integration consideration:
- If later packet enforces strict gpio_regs port contract without pad_in/din_q, move FM2 state update to gpio_input_sampler and keep gpio_regs focused on dir_q/dout_q only.