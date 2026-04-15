`timescale 1ns/1ps

module counter #(
    parameter integer WIDTH = 8
) (
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic                  en,
    input  logic                  load,
    input  logic [WIDTH-1:0]      load_value,
    output logic [WIDTH-1:0]      count
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= '0;
        end else if (load) begin
            count <= load_value;
        end else if (en) begin
            count <= count + 1'b1;
        end
    end

endmodule
