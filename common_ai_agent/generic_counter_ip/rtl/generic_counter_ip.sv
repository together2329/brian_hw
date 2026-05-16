// generic_counter_ip.sv - SSOT-driven RTL: value = data_in * 2
// EQ_DOUBLE goal: FunctionalModel.apply(txn) returns value * 2.
// Latency 1: value is registered on the clock edge after data_in is presented.
// Shift-left by 1 is equivalent to multiply-by-2 for unsigned values.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    // SSOT: value = input * 2; implemented as left-shift (no multiplier needed)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= {1'b0, data_in} << 1;
        end
    end
endmodule
