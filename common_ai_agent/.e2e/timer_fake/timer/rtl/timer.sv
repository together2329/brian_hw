`default_nettype none

module timer (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    output wire [8:0] result,
    output wire       ready,
    output wire       result_valid
);
    wire valid_sample = valid && ready;

    timer_core u_core (
        .clk(clk),
        .rst_n(rst_n),
        .valid(valid),
        .data_in(data_in),
        .valid_sample(valid_sample),
        .result(result),
        .ready(ready),
        .result_valid(result_valid)
    );
endmodule

`default_nettype wire
