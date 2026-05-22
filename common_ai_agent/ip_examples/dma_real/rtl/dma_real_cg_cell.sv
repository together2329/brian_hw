// dma_real_cg_cell.sv — Integrated clock-gating cell
//
// SSOT refs: power.clock_gating, features.clock_gating
//
// Wraps library ICG primitive. When en=0, gated_clk is held low.
// Glitch-free enable transition on clk falling edge.

module dma_real_cg_cell (
    input  logic clk,
    input  logic rst_n,
    input  logic en,
    output logic gated_clk
);

    logic en_latch;

    // Latch enable on clock low phase (transparent when clk=0)
    always @(*) begin
        if (!clk)
            en_latch = en;
    end

    // Gated clock: AND of clk and latched enable
    assign gated_clk = clk & en_latch;

endmodule
