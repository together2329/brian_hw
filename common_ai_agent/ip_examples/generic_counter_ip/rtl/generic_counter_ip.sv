// generic_counter_ip.sv - SSOT-driven RTL for EQ_DOUBLE.
// FunctionalModel.apply(txn) returns value * 2 for the primary transaction.
// Latency 1: the doubled value is registered on the accepting clock edge.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    logic [8:0] input_value_wide;
    logic [8:0] doubled_value_next;

    // EQ_DOUBLE / function_model.transactions[0]: FunctionalModel.apply
    // computes value * 2.  The power-of-two multiply is exact as a left shift.
    // cycle_model.latency=1 requires the registered output to use the current
    // sampled data_in on the accepting edge, so do not subtract, saturate, or
    // wait for a second input-register stage.
    assign input_value_wide   = {1'b0, data_in};
    assign doubled_value_next = input_value_wide << 1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= doubled_value_next;
        end
    end
endmodule
