module tb_equivalence_fresh_rule_ip;
    logic       clk;
    logic       rst_n;
    logic       valid;
    logic [7:0] data_in;
    logic [8:0] result;
    logic       ready;
    logic       result_valid;
    logic [7:0] accepted_count;

    logic [8:0] fl_expected_result;
    logic [7:0] fl_expected_count;

    fresh_rule_ip dut (
        .clk(clk),
        .rst_n(rst_n),
        .valid(valid),
        .data_in(data_in),
        .result(result),
        .ready(ready),
        .result_valid(result_valid),
        .accepted_count(accepted_count)
    );

    always #5 clk = ~clk;

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        valid = 1'b0;
        data_in = 8'd0;
        fl_expected_result = 9'd0;
        fl_expected_count = 8'd0;

        repeat (2) @(posedge clk);
        rst_n = 1'b1;
        @(posedge clk);

        data_in = 8'd13;
        valid = 1'b1;
        fl_expected_result = {1'b0, 8'd13} << 1;
        fl_expected_count = 8'd1;
        @(posedge clk);
        #1;

        $display("{\"goal_id\":\"EQ_MODULE_FRESH_RULE_IP\",\"scope\":{\"level\":\"module\",\"module\":\"fresh_rule_ip\"},\"fl_expected\":{\"model_api\":\"FunctionalModel.apply\",\"transaction\":\"FM_PRIMARY\",\"value\":13,\"result\":%0d,\"accepted_count\":%0d},\"rtl_observed\":{\"source\":\"dut module boundary ports\",\"result\":%0d,\"result_valid\":%0d,\"accepted_count\":%0d,\"ready\":%0d},\"pass\":%0d}", fl_expected_result, fl_expected_count, result, result_valid, accepted_count, ready, ((result == fl_expected_result) && (result_valid == 1'b1) && (accepted_count == fl_expected_count) && (ready == 1'b1)));

        if (result !== fl_expected_result) $fatal(1, "result mismatch");
        if (result_valid !== 1'b1) $fatal(1, "result_valid mismatch");
        if (accepted_count !== fl_expected_count) $fatal(1, "accepted_count mismatch");
        if (ready !== 1'b1) $fatal(1, "ready mismatch");

        valid = 1'b0;
        @(posedge clk);
        #1;
        $finish;
    end
endmodule
