`timescale 1ns/1ps
module baud_div_eff #(
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic [BAUD_DIV_WIDTH-1:0] baud_div_reg,
  output logic [BAUD_DIV_WIDTH-1:0] baud_eff
);
  assign baud_eff = (baud_div_reg == {BAUD_DIV_WIDTH{1'b0}}) ? {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1} : baud_div_reg;
endmodule
