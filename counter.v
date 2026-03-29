module counter #(
    parameter WIDTH = 8,
    parameter MAX_VAL = 8'hFF
)(
    input  wire             clk,
    input  wire             rst_n,
    input  wire             enable,
    output reg  [WIDTH-1:0] count
);

    // Counter logic with asynchronous active-low reset
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            count <= {WIDTH{1'b0}};
        end else if (enable) begin
            if (count >= MAX_VAL) begin
                count <= {WIDTH{1'b0}};
            end else begin
                count <= count + 1'b1;
            end
        end
    end

endmodule
