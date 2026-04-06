//------------------------------------------------------------
// Simple 256-bit Up Counter
//------------------------------------------------------------
// Ports:
//   clk   - Clock input
//   rst   - Synchronous active-high reset
//   count - 256-bit counter output [255:0]
//------------------------------------------------------------

module counter (
    input  wire          clk,
    input  wire          rst,
    output reg  [255:0]  count
);

always @(posedge clk) begin
    if (rst)
        count <= 256'd0;
    else
        count <= count + 256'd1;
end

endmodule
