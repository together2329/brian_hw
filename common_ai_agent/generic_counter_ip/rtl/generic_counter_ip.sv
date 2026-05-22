// generic_counter_ip.sv - SSOT-driven RTL: value = data_in * 2
// EQ_DOUBLE goal: FunctionalModel.apply(txn) returns value * 2.
// Latency 1: value is registered on the clock edge after data_in is presented.
// {data_in, 1'b0} appends a zero LSB — equivalent to unsigned multiply-by-2
// without a shift operator, avoiding width/promotion edge cases.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    // SSOT: value = input * 2; concatenation {data_in, 1'b0} is the
    // most direct unsigned double: appends zero LSB, no shift needed.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= {data_in, 1'b0};
        end
    end
endmodule
