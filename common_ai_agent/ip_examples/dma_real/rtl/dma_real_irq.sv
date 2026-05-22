// dma_real_irq.sv — Interrupt aggregation in pclk domain with sticky latch
// v2: pulse synchronizer input from hclk domain
module dma_real_irq #(
    parameter integer N_CHANNELS = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    input  logic [N_CHANNELS-1:0] int_enable_wr,
    input  logic [N_CHANNELS-1:0] int_enable_wdata,
    input  logic [N_CHANNELS-1:0] int_clear_wr,
    output logic [N_CHANNELS-1:0] int_status,
    output logic [N_CHANNELS-1:0] int_enable_rd,
    output logic [N_CHANNELS-1:0] int_done,
    output logic [N_CHANNELS-1:0] int_error,
    output logic [N_CHANNELS-1:0] irq,
    output logic                  irq_combined
);

    logic [N_CHANNELS-1:0] done_q, error_q;
    logic [N_CHANNELS-1:0] int_enable_q;

    genvar ch;
    generate
        for (ch = 0; ch < N_CHANNELS; ch = ch + 1) begin : gen_irq_ch
            always @(posedge pclk or negedge presetn) begin
                if (!presetn) begin
                    done_q[ch]       <= 1'b0;
                    error_q[ch]      <= 1'b0;
                    int_enable_q[ch] <= 1'b0;
                end else begin
                    if (int_enable_wr[ch])
                        int_enable_q[ch] <= int_enable_wdata[ch];
                    if (int_clear_wr[ch])
                        done_q[ch] <= 1'b0;
                    else if (ch_done[ch])
                        done_q[ch] <= 1'b1;
                    if (int_clear_wr[ch])
                        error_q[ch] <= 1'b0;
                    else if (ch_error[ch])
                        error_q[ch] <= 1'b1;
                end
            end
        end
    endgenerate

    assign int_done   = done_q;
    assign int_error  = error_q;
    assign int_status = done_q | error_q;
    assign int_enable_rd = int_enable_q;
    assign irq = int_status & int_enable_q;
    assign irq_combined = |irq;

endmodule
