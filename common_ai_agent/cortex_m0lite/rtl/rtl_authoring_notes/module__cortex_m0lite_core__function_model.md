Implemented owner file rtl/cortex_m0lite_core.sv for function_model packet.

Included SSOT-backed function_model elements in this slice:
- State owners: pc_q, rf storage (rf_mem_0..rf_mem_14), nzcv_q, trap_q.
- FM_CPU_STEP preconditions: execution gated by rst_n & hresetn deasserted, IF instruction valid staging, and d_hready/d_hresp gating for memory completion.
- Outputs: pc_dbg, retire pulse, trap pulse.
- Output rules: retire asserted only on non-trapped commit; trap asserted on illegal opcode, bus error, or misalignment at commit boundary.
- State updates: pc normal +2, branch target redirect, trap vector redirect; register writeback only on ALU/MOV/LDR commit; NZCV updates on arithmetic/compare/logical classes.
- Error cases: trap_code=1 illegal, 2 bus, 3 misalign.

Notes:
- This file is authored from SSOT packet constraints without using fixed templates.
- Remaining slices (parameters/registers/cycle_model/fsm/dataflow/etc.) can incrementally refine decode exactness and stage partitioning while preserving this owner logic baseline.