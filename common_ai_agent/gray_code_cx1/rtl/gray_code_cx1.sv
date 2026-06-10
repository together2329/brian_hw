// gray_code_cx1 - 4-bit binary-to-Gray + Gray-to-binary converter (registered).
// SSOT: gray_code_cx1/yaml/gray_code_cx1.ssot.yaml
// function_model.transactions.FM_PRIMARY:
//   gray_out <= bin_in ^ (bin_in >> 1)      [binary-to-Gray, BC_GC_ENCODE]
//   bin_out  <= cascaded XOR of gray_in     [Gray-to-binary, BC_GC_DECODE]
// cycle_model: latency=1, sampled on valid, sync active-low reset.
// mode port: informational (both outputs computed every valid cycle).

module gray_code_cx1 (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire       mode,
    input  wire [3:0] bin_in,
    input  wire [3:0] gray_in,
    output reg  [3:0] gray_out,
    output reg  [3:0] bin_out
);

    // Binary-to-Gray: gray_comb = bin_in XOR (bin_in >> 1)  [BC_GC_ENCODE]
    wire [3:0] gray_comb;
    assign gray_comb = bin_in ^ (bin_in >> 1);

    // Gray-to-binary: cascaded XOR from MSB downward  [BC_GC_DECODE]
    //   b[3] = g[3]
    //   b[2] = g[2] ^ b[3]
    //   b[1] = g[1] ^ b[2]
    //   b[0] = g[0] ^ b[1]
    wire [3:0] bin_comb;
    assign bin_comb[3] = gray_in[3];
    assign bin_comb[2] = gray_in[2] ^ bin_comb[3];
    assign bin_comb[1] = gray_in[1] ^ bin_comb[2];
    assign bin_comb[0] = gray_in[0] ^ bin_comb[1];

    // mode_unused: mode is an informational port; both outputs register every cycle.
    wire mode_unused;
    assign mode_unused = mode;

    // Registered outputs - both update on valid, cleared on sync active-low reset.
    always @(posedge clk) begin
        if (!rst_n) begin
            gray_out <= 4'h0;
            bin_out  <= 4'h0;
        end else if (valid) begin
            gray_out <= gray_comb;
            bin_out  <= bin_comb;
        end
    end

endmodule
