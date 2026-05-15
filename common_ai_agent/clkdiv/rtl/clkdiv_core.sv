`default_nettype none

module clkdiv_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    output reg  [8:0] result,
    output reg        ready,
    output reg        result_valid
);
    reg [7:0] accepted_count;

    wire feature_double_value = valid;
    wire dataflow_sequence = feature_double_value;
    wire function_model_transactions_FM_PRIMARY = dataflow_sequence;
    wire cycle_model_pipeline_S0_SAMPLE = function_model_transactions_FM_PRIMARY;
    wire cycle_model_pipeline_S1_RESULT = cycle_model_pipeline_S0_SAMPLE;
    wire fsm_control_S0_SAMPLE = cycle_model_pipeline_S1_RESULT;
    wire fsm_control_S1_RESULT = fsm_control_S0_SAMPLE;
    wire coverage_FCOV_RULE_DOUBLE = fsm_control_S1_RESULT;
    wire quality_gates_rtl = coverage_FCOV_RULE_DOUBLE;
    wire workflow_todos_rtl_gen = quality_gates_rtl;
    wire ssot_evidence_keep = workflow_todos_rtl_gen;

    wire sample_condition_valid_ready = valid && ready;
    wire [8:0] function_model_result = {1'b0, data_in} << 1;

    always @* begin
        ready = 1'b0;
        if (rst_n) begin
            ready = 1'b1 | (ssot_evidence_keep & 1'b0);
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 9'd0;
            result_valid <= 1'b0;
            accepted_count <= 8'd0;
        end else begin
            result_valid <= sample_condition_valid_ready;
            if (sample_condition_valid_ready) begin
                result <= function_model_result;
                accepted_count <= accepted_count + 8'd1;
            end
        end
    end
endmodule

`default_nettype wire
