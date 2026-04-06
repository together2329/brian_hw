module counter (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,
    output reg  [31:0]  count
);

always @(posedge clk or negedge rst_n) begin
    if (!rst_n)
        count <= 32'd0;
    else if (en)
        count <= count + 32'd1;
end

endmodule
