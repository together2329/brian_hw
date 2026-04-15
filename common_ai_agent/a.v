// a simple Verilog module
module a (
    input  logic clk,
    input  logic rst_n,
    input  logic [7:0] in_data,
    output logic [7:0] out_data
);

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            out_data <= 8'd0;
        else
            out_data <= in_data;
    end

endmodule
