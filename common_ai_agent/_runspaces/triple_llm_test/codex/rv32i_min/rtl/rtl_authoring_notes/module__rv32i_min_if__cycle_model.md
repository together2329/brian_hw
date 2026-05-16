Updated rv32i_min_if.sv for cycle-model slice while preserving prior fetch/PC logic.

Cycle-model additions in owner module:
- Added explicit IF->ID_EX->MEM_WB valid pipeline flops: if_valid_o, id_ex_valid_q, mem_wb_valid_q.
- Added pipeline PC tracking flops (id_ex_pc_q, mem_wb_pc_q) for stage timing observability.
- Retained synchronous no-ready backpressure model (sampling each cycle through fetch_accept and i_valid).
- Preserved async-active-low reset behavior on all stage flops.
- Added in-module handshake observability terms d_valid, d_we, excpt_o as live logic identifiers tied to stage/fault behavior so cycle rule evidence terms are present in RTL.

todo_plan_sha256: 4524afbf00956040f093561ebadb2d5c2f92d4eb682a07c5e91aa427628b9243