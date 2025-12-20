// 4‑bit up‑counter with async reset
module counter4 (
    input  wire        clk,
    input  wire        rst_n,   // active low reset
    output reg  [3:0]  count
);
    // Synchronous reset, count increments on each rising edge
    // Async reset (active low) and count increment logic
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= 4'd0;
        else
            count <= count + 4'd1;
    end
endmodule
