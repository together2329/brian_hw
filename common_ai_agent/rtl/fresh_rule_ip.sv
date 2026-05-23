// fresh_rule_ip.sv — SSOT-authored RTL for the double_value rule
module fresh_rule_ip (
    input  logic       clk,
    input  logic       rst_n,
    input  logic       valid,
    input  logic [7:0] data_in,
    output logic [8:0] result,
    output logic       ready,
    output logic       result_valid,
    output logic [7:0] accepted_count
);
    localparam [8:0] RESULT_RESET_VALUE = 9'd0;
    localparam [7:0] ACCEPTED_COUNT_RESET_VALUE = 8'd0;

    logic       valid_sample;
    logic [7:0] value;
    logic [8:0] doubled_value;
    logic [7:0] accepted_count_next;

    assign valid_sample = valid & ready;
    assign value = data_in;
    // SSOT double_value: exact unsigned multiply by two uses a left shift; result widens to 9 bits with no rounding or saturation.
    assign doubled_value = {1'b0, value} << 1;
    assign accepted_count_next = accepted_count + 8'd1;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= RESULT_RESET_VALUE;
            result_valid <= 1'b0;
            ready <= 1'b0;
            accepted_count <= ACCEPTED_COUNT_RESET_VALUE;
        end else begin
            // Ready remains asserted after reset; valid_sample is the SSOT acceptance point for the transaction.
            ready <= 1'b1;
            result_valid <= valid_sample;
            if (valid_sample) begin
                result <= doubled_value;
                accepted_count <= accepted_count_next;
            end
        end
    end
endmodule
