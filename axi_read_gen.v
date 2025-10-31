module axi_read_gen
(
// Clock
input i_clk,
// Reset
input i_reset_n,
// AXI I/F
// Read Address Channel
output reg [6:0] arid,
output reg [31:0] araddr,
output reg [7:0] arlen,
output reg [2:0] arsize. 
output reg [1:0] arburst,
output reg       arvalid,
input            arready,

// Read Data/Response Channel
input [6:0] rid,
input [255:0] rdata,
input [1:0] rresp,
input       rlast,
input       rvalid,
output reg  rready
);

endmodule
