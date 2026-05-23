// generic_counter_ip.sv - SSOT-driven RTL for EQ_DOUBLE.
// FunctionalModel.apply(txn) returns value * 2 for the primary transaction.
// Latency 1: the doubled value is registered on the accepting clock edge.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);
    logic [8:0] fm_value_wide;
    logic [8:0] fm_value_doubled;

    // EQ_DOUBLE / function_model.transactions[0]: FunctionalModel.apply returns
    // value * 2.  The SSOT latency is 1, so register the exact doubled value
    // from the current input on this clock edge; no decrement/stale sample is
    // permitted by the FL-vs-RTL goal or scoreboard evidence.
    assign fm_value_wide    = {1'b0, data_in};
    assign fm_value_doubled = fm_value_wide << 1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= fm_value_doubled;
        end
    end
endmodule
