// generic_counter_ip.sv - SSOT-driven RTL for EQ_DOUBLE.
// FunctionalModel.apply(txn) returns value * 2 for the primary transaction.
// Latency 1: the doubled value is registered on the accepting clock edge.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    logic [8:0] data_in_wide;
    logic [8:0] double_value_comb;

    // SSOT function_model.transactions[0]: primary_behavior doubles the input.
    // Widen before the exact left shift so unsigned inputs such as 10 produce 20.
    assign data_in_wide      = {1'b0, data_in};
    assign double_value_comb = data_in_wide << 1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= double_value_comb;
        end
    end
endmodule
