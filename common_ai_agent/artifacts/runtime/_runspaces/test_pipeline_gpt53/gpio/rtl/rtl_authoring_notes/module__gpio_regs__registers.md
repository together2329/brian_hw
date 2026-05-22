Updated gpio_regs owner file for packet module__gpio_regs__registers.

Changes made:
- Fixed interface typing to SSOT-consistent scalar clk/rst_n and WIDTH vectors for dir_in/dout_in/dir_q/dout_q.
- Focused gpio_regs responsibility on DIR_Q and DOUT_Q state only (sequential control-state owner).
- Implemented async-reset + per-cycle RW latch semantics for DIR_Q.dir and DOUT_Q.dout.
- Added explicit logical register offsets (0x0, 0x4) and 32-bit readback views to satisfy register traceability in a no-bus fixture.
- Upper bits of 32-bit logical registers are reserved-zero by construction.

SSOT alignment:
- registers.register_list.DIR_Q (width 32, reset 0, rw, offset 0)
- registers.register_list.DOUT_Q (width 32, reset 0, rw, offset 4)
- function_model.transactions.FM1_LATCH_CONTROL
- function_model.transactions.FM4_ASYNC_RESET
- cycle_model.pipeline.S1_LATCH_CONTROL