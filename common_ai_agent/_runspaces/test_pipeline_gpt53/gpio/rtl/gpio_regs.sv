module gpio_regs #(
    parameter integer WIDTH = 8
) (
    input  logic             clk,
    input  logic             rst_n,
    input  logic [WIDTH-1:0] dir_in,
    input  logic [WIDTH-1:0] dout_in,
    input  logic [WIDTH-1:0] pad_in,
    output logic [WIDTH-1:0] dir_q,
    output logic [WIDTH-1:0] dout_q,
    output logic [WIDTH-1:0] din_q
);

    // HR_INPUT_MASK_SAMPLE / S2_SAMPLE_INPUTS:
    // Use registered direction state to decide which din_q bits sample pad_in
    // and which bits hold previous state.
    logic [WIDTH-1:0] din_q_masked_next;

    // S3_DRIVE_OUTPUTS observability in this owner file:
    // gpio_regs owns registered state; top-level pad outputs are driven from this
    // state in gpio_pad_logic with oe_o=dir_q and pad_o=(dout_q & dir_q).
    // Keeping these stage wires local preserves cycle-model traceability while
    // leaving architectural ownership unchanged.
    logic [WIDTH-1:0] oe_o_s3;
    logic [WIDTH-1:0] pad_o_s3;

    assign din_q_masked_next = (din_q & dir_q) | (pad_in & (~dir_q));
    assign oe_o_s3           = dir_q;
    assign pad_o_s3          = dout_q & dir_q;

    // FM1 + FM2 + FM4 owner behavior with SSOT cycle semantics:
    // - HR_SYNC_SAMPLE: all sampling happens only on posedge clk
    // - S0_RESET: async assert reset clears architectural state
    // - S1_LATCH_CONTROL: latch dir_in/dout_in at cycle N
    // - S2_SAMPLE_INPUTS: update din_q using registered direction mask
    // Ordering rule: reset dominates non-reset logic.
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_q  <= {WIDTH{1'b0}};
            dout_q <= {WIDTH{1'b0}};
            din_q  <= {WIDTH{1'b0}};
        end else begin
            // S1_LATCH_CONTROL (latency=1 from control inputs to state outputs)
            dir_q  <= dir_in;
            dout_q <= dout_in;

            // HR_INPUT_MASK_SAMPLE / S2_SAMPLE_INPUTS (latency=1 pad_in->din_q)
            din_q  <= din_q_masked_next;
        end
    end

endmodule
