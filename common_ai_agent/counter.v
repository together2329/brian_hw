//------------------------------------------------------------
// Simple 18-bit Up Counter
//------------------------------------------------------------
// Ports:
//   clk   - Clock input
//   rst   - Synchronous active-high reset
//   count - 18-bit counter output [17:0]
//------------------------------------------------------------

module counter (
    input  wire         clk,
    input  wire         rst,
    output reg  [17:0]  count
);

always @(posedge clk) begin
    if (rst)
        count <= 18'd0;
    else
        count <= count + 18'd1;
end

endmodule
