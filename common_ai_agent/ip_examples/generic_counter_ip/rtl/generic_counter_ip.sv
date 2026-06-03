// generic_counter_ip.sv - SSOT-driven RTL for EQ_DOUBLE.
// FunctionalModel.apply(txn) returns value * 2 for the primary transaction.
// Latency 1: the doubled value is registered on the accepting clock edge.
module generic_counter_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic [7:0] data_in,
    output logic [8:0] value
);

    // EQ_DOUBLE / function_model.transactions[0]: FunctionalModel.apply
    // computes value * 2.  Multiply-by-2 is implemented by appending a zero
    // LSB to the 8-bit input, yielding a 9-bit result directly.
    // {data_in, 1'b0} == data_in * 2 for unsigned 8-bit data_in.
    // cycle_model.latency=1: registered result from current input on the
    // accepting edge, matching the FL expected value 10 -> 20.
    // Repair: replaced {1'b0, data_in} << 1 with {data_in, 1'b0} to fix
    // off-by-one observed (19 instead of 20) under simulation.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            value <= 9'h000;
        end else begin
            value <= {data_in, 1'b0};
        end
    end
endmodule
