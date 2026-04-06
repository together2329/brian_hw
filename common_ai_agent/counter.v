//------------------------------------------------------------
// Simple 128-bit Up Counter
//------------------------------------------------------------
// Ports:
//   clk   - Clock input
//   rst   - Synchronous active-high reset
//   count - 128-bit counter output [127:0]
//------------------------------------------------------------

module counter (
    input  wire          clk,
    input  wire          rst,
    output reg  [127:0]  count
);

always @(posedge clk) begin
    if (rst)
        count <= 128'd0;
    else
        count <= count + 128'd1;
end

endmodule
