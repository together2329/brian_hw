// bad_syntax.v — deliberately malformed Verilog for fail-path testing
// Missing semicolon, undeclared wire, and missing endmodule

module bad_counter
    input wire clk,
    input wire rst_n,
    output reg [3:0] count  // MISSING SEMICOLON here

    always @(posedge clk) begin
        count <= count + 1
    end
// MISSING endmodule
