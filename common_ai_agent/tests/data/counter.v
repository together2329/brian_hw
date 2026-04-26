// counter.v — 4-bit synchronous up-counter
// Features: async reset (active low), enable-gated increment
// Designed for agent-server RTL pipeline testing

module counter #(
    parameter WIDTH = 4
) (
    input  wire             clk,      // Clock
    input  wire             rst_n,    // Async reset (active low)
    input  wire             en,       // Enable
    output reg [WIDTH-1:0]  count     // Counter value
);

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            count <= {WIDTH{1'b0}};
        else if (en)
            count <= count + 1'b1;
    end

endmodule
