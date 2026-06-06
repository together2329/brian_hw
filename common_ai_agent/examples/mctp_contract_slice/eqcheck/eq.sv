module dut_eq(input clk, input [3:0] a, input [3:0] b, output reg [3:0] y);
  wire [3:0] t = a << 1;
  always @(posedge clk) y <= t + b;
endmodule
