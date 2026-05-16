Updated rv32i_min_if IO contract slice to match SSOT io_list port ownership for this module packet.
- Added io_list data bus ports to rv32i_min_if: d_addr, d_wdata, d_rdata, d_we, d_be, d_valid.
- Added io_list exception port excpt_o as module output.
- Preserved prior fetch/PC sequencing logic and existing pipeline-valid tracking.
- Replaced previous internal-only d_valid/d_we/excpt_o nets with output-driving registered signals.
- Kept i_addr/i_valid/i_rdata/clk/rst_n declarations and behavior intact.
Todo plan hash context: 4524afbf00956040f093561ebadb2d5c2f92d4eb682a07c5e91aa427628b9243.