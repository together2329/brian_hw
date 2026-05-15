// fifo_sync_flags.sv — SSOT-backed full/empty/almost flag generation.
module fifo_sync_flags #(
    parameter integer DEPTH = 16,
    parameter integer ALMOST_FULL_THRESHOLD = 15,
    parameter integer ALMOST_EMPTY_THRESHOLD = 1,
    parameter integer COUNT_WIDTH = $clog2(DEPTH+1)
) (
    input  logic [COUNT_WIDTH-1:0] count_i,
    input  logic [7:0]             almost_full_thresh_i,
    input  logic [7:0]             almost_empty_thresh_i,
    output logic                   full_o,
    output logic                   empty_o,
    output logic                   almost_full_o,
    output logic                   almost_empty_o,
    output logic [COUNT_WIDTH-1:0] count_o
);

    localparam [COUNT_WIDTH-1:0] COUNT_ZERO = {COUNT_WIDTH{1'b0}};
    localparam [COUNT_WIDTH-1:0] DEPTH_COUNT = DEPTH[COUNT_WIDTH-1:0];

    logic [COUNT_WIDTH-1:0] almost_full_threshold_value;
    logic [COUNT_WIDTH-1:0] almost_empty_threshold_value;

    // Dynamic CSR threshold zero means use the SSOT parameter defaults.
    assign almost_full_threshold_value = (almost_full_thresh_i == 8'h00) ?
                                         ALMOST_FULL_THRESHOLD[COUNT_WIDTH-1:0] :
                                         almost_full_thresh_i[COUNT_WIDTH-1:0];
    assign almost_empty_threshold_value = (almost_empty_thresh_i == 8'h00) ?
                                          ALMOST_EMPTY_THRESHOLD[COUNT_WIDTH-1:0] :
                                          almost_empty_thresh_i[COUNT_WIDTH-1:0];
    // FM1..FM6 output rules: flags are pure functions of the architectural
    // count after pointer update; overflow/underflow leave count unchanged.
    always @(*) begin
        count_o         = count_i;
        full_o          = (count_i == DEPTH_COUNT);
        empty_o         = (count_i == COUNT_ZERO);
        almost_full_o   = (count_i >= almost_full_threshold_value);
        almost_empty_o  = (count_i <= almost_empty_threshold_value);
    end

endmodule
