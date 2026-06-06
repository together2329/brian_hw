module dut_gold(input clk, input [3:0] a, input [3:0] b, output reg [3:0] y);
  always @(posedge clk) y <= a + a + b;
endmodule
