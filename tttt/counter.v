//--------------------------------------------------------------
// 8-Bit Synchronous Up-Counter
//--------------------------------------------------------------
module counter (
    input  wire       clk,      // Clock
    input  wire       rst,      // Active-high synchronous reset
    output reg  [7:0] count     // 8-bit counter output
);

always @(posedge clk) begin
    if (rst)
        count <= 8'b0;
    else
        count <= count + 1;
end

endmodule
