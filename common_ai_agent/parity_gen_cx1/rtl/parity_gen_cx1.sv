// parity_gen_cx1.sv
// 8-bit even/odd parity generator with registered output.
// SSOT: yaml/parity_gen_cx1.ssot.yaml
// Obligations: OBL_PAR_EVEN_001, OBL_PAR_ODD_001, OBL_PAR_REG_001, OBL_PAR_RESET_001

`timescale 1ns/1ps

module parity_gen_cx1 (
    input  wire       clk,      // System clock
    input  wire       rst_n,    // Active-low async assert / sync deassert reset
    input  wire [7:0] data_in,  // 8-bit input data
    output wire       even_par, // Even parity: XOR of all 8 bits (combinational)
    output wire       odd_par,  // Odd parity: ~even_par (combinational)
    output reg        par_reg   // Registered even parity (latched on rising clk)
);

    // Even parity: XOR reduction of all 8 data bits (OBL_PAR_EVEN_001)
    assign even_par = ^data_in;

    // Odd parity: inversion of even_par (OBL_PAR_ODD_001)
    assign odd_par  = ~even_par;

    // Registered parity: captures even_par on each rising edge (OBL_PAR_REG_001)
    // Reset clears par_reg to 0 (OBL_PAR_RESET_001)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            par_reg <= 1'b0;
        else
            par_reg <= even_par;
    end

endmodule
