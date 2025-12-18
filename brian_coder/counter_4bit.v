// 4‑bit counter with synchronous reset
module counter_4bit (
    input  clk,
    input  reset,
    output reg [3:0] count
);

    // Sync reset (active high) and count increment logic
    always @(posedge clk) begin
        if (reset)
            count <= 4'b0;
        else
            count <= count + 1;
    end

endmodule
