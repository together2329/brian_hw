# caa_timer_ds Engineering Requirement

Create a small APB timer IP named `caa_timer_ds`.

The IP has one clock and one active-low asynchronous reset. It exposes an APB3-style slave interface with `paddr[7:0]`, `psel`, `penable`, `pwrite`, `pwdata[31:0]`, `prdata[31:0]`, `pready`, and `pslverr`.

Registers:
- `0x00 CONTROL`: bit 0 enables counting. Reset value is 0.
- `0x04 COMPARE`: bits 7:0 hold the compare value. Reset value is 3.
- `0x08 VALUE`: read-only current counter value, bits 7:0.
- `0x0c IRQ_STATUS`: bit 0 is the pending interrupt. Writing 1 clears it.

Behavior:
- While enabled, the 8-bit counter increments once per clock.
- When the counter equals COMPARE while enabled, `irq` becomes 1 and remains set until IRQ_STATUS bit 0 is written with 1.
- APB legal accesses complete in one access phase with `pready=1`.
- Illegal addresses assert `pslverr=1`, return read data 0, and do not change state.
- Writes to VALUE are ignored and do not raise an error.

Engineering run requirements:
- Use Engineering mode.
- The SSOT must lock all behavior above, with no optional behavior.
- `top_module.name` must be `caa_timer_ds`, but `sub_modules[]` must not contain another module named exactly `caa_timer_ds`.
- If a top wrapper is listed in `sub_modules[]`, name it `caa_timer_ds_top` and mark `wiring_only: true`.
- Keep YAML scalar conditions quoted when they include brackets or comparison syntax.
- RTL must be authored by the common_ai_agent `rtl-gen` workflow using real LLM calls, not deterministic fixed-template fallback.
- Produce RTL, filelist, lint evidence, testbench/simulation evidence, and enough model/equivalence/coverage artifacts for wiki graph closure.
