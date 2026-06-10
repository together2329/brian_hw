`timescale 1ns/1ps
`default_nettype none

// 8-bit up-counter with synchronous active-low reset and enable
// SSOT: counter8_cx1/yaml/counter8_cx1.ssot.yaml
// function_model.transactions: TR_RESET, TR_COUNT, TR_HOLD
module counter8_cx1 #(
    parameter integer WIDTH = 8
) (
    input  wire             clk,
    input  wire             rst_n,
    input  wire             en,
    output wire [WIDTH-1:0] count
);

    reg [WIDTH-1:0] count_reg;

    always @(posedge clk) begin
        if (!rst_n) begin
            count_reg <= {WIDTH{1'b0}};
        end else if (en) begin
            count_reg <= count_reg + {{WIDTH-1{1'b0}}, 1'b1};
        end
    end

    assign count = count_reg;

endmodule

`default_nettype wire
