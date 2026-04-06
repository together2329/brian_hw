//------------------------------------------------------------
// Simple 8-bit Up Counter
//------------------------------------------------------------
// Ports:
//   clk   - Clock input
//   rst   - Synchronous active-high reset
//   count - 8-bit counter output [7:0]
//------------------------------------------------------------

module counter (
    input  wire        clk,
    input  wire        rst,
    output reg  [7:0]  count
);

always @(posedge clk) begin
    if (rst)
        count <= 8'd0;
    else
        count <= count + 8'd1;
end

endmodule
