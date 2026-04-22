`timescale 1ns/1ps

module counter (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       en,
    output logic [7:0] count
);
    timeunit 1ns;
    timeprecision 1ps;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 8'h00;
        else if (en)
            count <= count + 8'h01;
    end

endmodule
