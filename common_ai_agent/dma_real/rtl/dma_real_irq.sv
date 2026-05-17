// dma_real_irq.sv — Interrupt aggregation with per-channel mask and combined output
//
// SSOT refs: interrupts, io_list.interfaces.irq_outputs, registers.register_list.INT_ENABLE,
//   registers.register_list.INT_CLEAR, registers.register_list.INT_STATUS
//
// FIX: Export separate int_done / int_error for APB STATUS readback.

module dma_real_irq #(
    parameter integer N_CHANNELS = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    // Per-channel done/error inputs from channel modules
    input  logic [N_CHANNELS-1:0] ch_done,
    input  logic [N_CHANNELS-1:0] ch_error,
    // APB register interface (from apb_cfg)
    input  logic [N_CHANNELS-1:0] int_enable_wr,
    input  logic [N_CHANNELS-1:0] int_enable_wdata,
    input  logic [N_CHANNELS-1:0] int_clear_wr,
    // Status readback
    output logic [N_CHANNELS-1:0] int_status,
    output logic [N_CHANNELS-1:0] int_enable_rd,
    // NEW: separate done/error for APB CHx_STATUS readback
    output logic [N_CHANNELS-1:0] int_done,
    output logic [N_CHANNELS-1:0] int_error,
    // IRQ outputs
    output logic [N_CHANNELS-1:0] irq,
    output logic                  irq_combined
);

    // Latched done and error per channel (set by channel pulse, cleared by INT_CLEAR)
    // Priority: INT_CLEAR > ch_done/ch_error (clear wins so SC008 IRQ deassert works)
    logic [N_CHANNELS-1:0] done_q;
    logic [N_CHANNELS-1:0] error_q;

    // Interrupt enable register
    logic [N_CHANNELS-1:0] int_enable_q;

    genvar ch;
    generate
        for (ch = 0; ch < N_CHANNELS; ch++) begin : gen_irq_ch
            always @(posedge pclk or negedge presetn) begin
                if (!presetn) begin
                    done_q[ch]       <= 1'b0;
                    error_q[ch]      <= 1'b0;
                    int_enable_q[ch] <= 1'b0;
                end else begin
                    // INT_ENABLE register
                    if (int_enable_wr[ch])
                        int_enable_q[ch] <= int_enable_wdata[ch];

                    // Done latch — clear takes priority so IRQ deasserts on INT_CLEAR
                    if (int_clear_wr[ch])
                        done_q[ch] <= 1'b0;
                    else if (ch_done[ch])
                        done_q[ch] <= 1'b1;

                    // Error latch — same priority
                    if (int_clear_wr[ch])
                        error_q[ch] <= 1'b0;
                    else if (ch_error[ch])
                        error_q[ch] <= 1'b1;
                end
            end
        end
    endgenerate

    // Separate done / error outputs for APB STATUS register readback
    assign int_done   = done_q;
    assign int_error  = error_q;

    // Combined status (OR of done and error latches)
    assign int_status = done_q | error_q;

    // Interrupt enable readback
    assign int_enable_rd = int_enable_q;

    // Per-channel IRQ: asserted when (done OR error) AND enable
    assign irq = int_status & int_enable_q;

    // Combined IRQ
    assign irq_combined = |irq;

endmodule
