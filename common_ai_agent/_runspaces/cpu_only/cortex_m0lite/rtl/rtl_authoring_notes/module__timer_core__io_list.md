# Packet module__timer_core__io_list

Updated `rtl/cortex_m0lite.sv` as the owner file for timer_core and preserved existing function/cycle-model logic.

IO-list coverage in this packet:
- `clk` input, width 1, consumed by sequential state update.
- `rst_n` input, width 1, active-low reset in sequential state update.
- `fetch_en` input, width 1, consumed by sample condition and next-state priority logic.
- `step_en` input, width 1, consumed by sample condition and decrement/retire transitions.
- `flush` input, width 1, consumed with highest priority in all next-state/output rules.
- `instr_data` input, width `XLEN`, consumed by fetch load path.
- `pc` output, width `XLEN`, driven from architectural state `pc_q`.
- `busy` output, width 1, driven from architectural state `busy_q`.
- `retire` output, width 1, driven from architectural state `retire_q`.

This packet is RTL-authoring only; compile/lint/tool evidence is deferred to tool stages.