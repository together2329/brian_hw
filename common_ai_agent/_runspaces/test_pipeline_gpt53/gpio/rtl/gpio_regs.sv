module gpio_regs #(
    parameter integer WIDTH = 8
) (
    input  logic [WIDTH-1:0] clk,
    input  logic [WIDTH-1:0] rst_n,
    input  logic [WIDTH-1:0] dir_in,
    input  logic [WIDTH-1:0] dout_in,
    input  logic [WIDTH-1:0] pad_in,
    output logic [WIDTH-1:0] dir_q,
    output logic [WIDTH-1:0] dout_q,
    output logic [WIDTH-1:0] din_q
);

    // Direction masks used by FM2 sampling rule:
    // - input_mask bit=1 means the corresponding GPIO is configured as input
    // - output_mask bit=1 means hold prior sampled din_q bit
    logic [WIDTH-1:0] input_mask;
    logic [WIDTH-1:0] output_mask;
    logic [WIDTH-1:0] din_q_masked_next;

    assign input_mask       = ~dir_q;
    assign output_mask      = dir_q;
    assign din_q_masked_next = (din_q & output_mask) | (pad_in & input_mask);

    // FM1 + FM2 + FM4 behavior with cycle-model ordering:
    // S0_RESET (async assert): clear architectural state
    // S1_LATCH_CONTROL (cycle N): sample dir_in/dout_in
    // S2_SAMPLE_INPUTS (cycle N): sample pad_in only for input-configured bits
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_q  <= {WIDTH{1'b0}};
            dout_q <= {WIDTH{1'b0}};
            din_q  <= {WIDTH{1'b0}};
        end else begin
            dir_q  <= dir_in;
            dout_q <= dout_in;
            din_q  <= din_q_masked_next;
        end
    end

endmodule
