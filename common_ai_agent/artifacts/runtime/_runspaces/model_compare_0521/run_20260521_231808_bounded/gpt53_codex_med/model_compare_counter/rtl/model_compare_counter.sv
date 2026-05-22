module model_compare_counter #(
    parameter integer COUNT_WIDTH = 8,
    parameter integer STEP_WIDTH  = 4
) (
    input  logic                    clk,
    input  logic                    rst_n,
    input  logic                    enable,
    input  logic                    clear,
    input  logic [STEP_WIDTH-1:0]   step,
    output logic [COUNT_WIDTH-1:0]  count,
    output logic                    wrapped,
    output logic                    valid
);

    // SSOT wiring-only top integration.
    model_compare_counter_core #(
        .COUNT_WIDTH(COUNT_WIDTH),
        .STEP_WIDTH(STEP_WIDTH)
    ) u_model_compare_counter_core (
        .clk(clk),
        .rst_n(rst_n),
        .enable(enable),
        .clear(clear),
        .step(step),
        .count(count),
        .wrapped(wrapped),
        .valid(valid)
    );

endmodule
