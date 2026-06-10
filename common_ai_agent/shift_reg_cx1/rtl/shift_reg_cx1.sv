`timescale 1ns/1ps
`default_nettype none

// 8-bit serial-in parallel-out shift register with synchronous active-low reset
// SSOT: shift_reg_cx1/yaml/shift_reg_cx1.ssot.yaml
// function_model.transactions: TR_RESET, TR_SHIFT
// Shift direction: left, si enters at bit 0 (LSB)
module shift_reg_cx1 #(
    parameter integer WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             si,
    output wire [WIDTH-1:0] po
);

    reg [WIDTH-1:0] shift_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            shift_reg <= {WIDTH{1'b0}};
        end else begin
            shift_reg <= {shift_reg[WIDTH-2:0], si};
        end
    end

    assign po = shift_reg;

endmodule

`default_nettype wire
