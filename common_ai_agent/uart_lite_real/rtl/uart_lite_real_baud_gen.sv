// uart_lite_real_baud_gen.sv — Baud rate tick generator
// SSOT: cycle_model.baud_generator
// Counter-based: baud_tick = 1 when counter == (baud_div * OVERSAMPLE) - 1

`include "uart_lite_real_param.vh"

module uart_lite_real_baud_gen (
    input  wire        PCLK,
    input  wire        PRESETn,
    input  wire [15:0] baud_div_i,
    input  wire        rx_start_detect_i,  // Reset oversample counter on RX start
    output reg         baud_tick_o,
    output reg  [15:0] oversample_cnt_o,
    output reg         oversample_tick_o,
    output reg         mid_sample_o
);

    // TX baud counter
    reg [31:0] tx_baud_cnt;

    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            tx_baud_cnt   <= 32'd0;
            baud_tick_o   <= 1'b0;
        end else begin
            baud_tick_o <= 1'b0;
            // Period = (baud_div+1) * OVERSAMPLE; tick at last count
            if (tx_baud_cnt >= (({16'd0, baud_div_i} + 32'd1) * OVERSAMPLE[15:0]) - 32'd1) begin
                tx_baud_cnt <= 32'd0;
                baud_tick_o <= 1'b1;
            end else begin
                tx_baud_cnt <= tx_baud_cnt + 32'd1;
            end
        end
    end

    // RX oversample counter — counts full bit period = (baud_div+1)*OVERSAMPLE
    // mid_sample at half-bit for sampling
    always @(posedge PCLK or negedge PRESETn) begin
        if (!PRESETn) begin
            oversample_cnt_o  <= 16'd0;
            oversample_tick_o <= 1'b0;
            mid_sample_o      <= 1'b0;
        end else begin
            oversample_tick_o <= 1'b0;
            mid_sample_o      <= 1'b0;
            if (rx_start_detect_i) begin
                // Reset counter on start bit detection
                oversample_cnt_o <= 16'd0;
            end else begin
                // Full bit period = (baud_div+1) * OVERSAMPLE counts
                // For mid-sample: at (baud_div+1) * (OVERSAMPLE/2) = (baud_div+1)*8
                // We simplify: just count, and mid_sample at half of full period
                if (oversample_cnt_o >= ({16'd0, baud_div_i} + 16'd1) * OVERSAMPLE[15:0] - 16'd1) begin
                    oversample_cnt_o  <= 16'd0;
                    oversample_tick_o <= 1'b1;
                end else begin
                    oversample_cnt_o <= oversample_cnt_o + 16'd1;
                end
                // Mid-sample at half the bit period
                if (oversample_cnt_o == ({16'd0, baud_div_i} + 16'd1) * (OVERSAMPLE[15:0] >> 1)) begin
                    mid_sample_o <= 1'b1;
                end
            end
        end
    end

endmodule
