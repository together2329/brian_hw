`default_nettype none
module dma_int_ctrl #(
    parameter int NUM_CHANNELS = 8
)(
    input  logic                    clk,
    input  logic                    rst_n,

    // Per-channel interrupt sources
    input  logic [NUM_CHANNELS-1:0] ch_irq_done,
    input  logic [NUM_CHANNELS-1:0] ch_irq_err,

    // Global interrupt enable register
    input  logic [31:0]             dma_ier,

    // W1C clear from reg_block (bits to clear in ISR)
    input  logic [31:0]             isr_w1c,

    // Status outputs (to reg_block for read access)
    output logic [31:0]             dma_isr,

    // Interrupt output
    output logic [NUM_CHANNELS-1:0] irq
);

    // ========================================================================
    // ISR register: SET on events, cleared by W1C from reg_block
    // ========================================================================
    logic [31:0] reg_isr;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            reg_isr <= 32'd0;
        end else begin
            // W1C clear first
            reg_isr <= reg_isr & ~isr_w1c;

            // Then set on events
            for (int i = 0; i < NUM_CHANNELS; i++) begin
                // irq_status [7:0] — any interrupt source for channel i
                if (ch_irq_done[i] || ch_irq_err[i])
                    reg_isr[i] <= 1'b1;

                // irq_done [15:8] — transfer complete
                if (ch_irq_done[i])
                    reg_isr[8 + i] <= 1'b1;

                // irq_err [23:16] — error interrupt
                if (ch_irq_err[i])
                    reg_isr[16 + i] <= 1'b1;
            end
        end
    end

    // ========================================================================
    // ERR register — managed by reg_block from channel status inputs
    // ========================================================================

    // ========================================================================
    // Output assignments
    // ========================================================================
    assign dma_isr = reg_isr;

    // ========================================================================
    // IRQ output: active-high level, gated by DMA_IER.irq_enable[7:0]
    // Level-sensitive: irq[i] = 1 when ISR[i] is set AND IER[i] is enabled
    // ========================================================================
    for (genvar i = 0; i < NUM_CHANNELS; i++) begin : gen_irq
        assign irq[i] = reg_isr[i] & dma_ier[i];
    end

endmodule
