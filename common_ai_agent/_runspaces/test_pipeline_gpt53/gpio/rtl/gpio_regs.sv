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

    // FM1 + FM2 + FM4 owner behavior:
    // - FM1: latch dir_in/dout_in each rising edge when not in reset
    // - FM2: sample pad_in only on input-configured bits (dir_q==0), hold output bits
    // - FM4: async reset clears all architectural state to zero
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            dir_q  <= {WIDTH{1'b0}};
            dout_q <= {WIDTH{1'b0}};
            din_q  <= {WIDTH{1'b0}};
        end else begin
            // FM1_LATCH_CONTROL: atomic control-state update per clock edge
            dir_q  <= dir_in;
            dout_q <= dout_in;

            // FM2_SAMPLE_INPUTS: preserve output-mode bits, sample input-mode bits
            // Uses current-cycle registered direction mask as required by SSOT expression:
            // din_q_next = (din_q & dir_q) | (pad_in & ~dir_q)
            din_q  <= (din_q & dir_q) | (pad_in & (~dir_q));
        end
    end

endmodule
