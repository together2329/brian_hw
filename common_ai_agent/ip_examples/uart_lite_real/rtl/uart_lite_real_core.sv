// uart_lite_real_core.sv — Top integration: instantiates all sub-modules
// SSOT: function_model, decomposition, cycle_model, dataflow, features

`include "uart_lite_real_param.vh"

module uart_lite_real_core (
    input  wire                   PCLK,
    input  wire                   PRESETn,
    // APB interface
    input  wire [APB_ADDR_WIDTH-1:0] PADDR,
    input  wire                   PSEL,
    input  wire                   PENABLE,
    input  wire                   PWRITE,
    input  wire [APB_DATA_WIDTH-1:0] PWDATA,
    input  wire [3:0]             PSTRB,
    output wire [APB_DATA_WIDTH-1:0] PRDATA,
    output wire                   PREADY,
    output wire                   PSLVERR,
    // Serial
    output wire                   tx,
    input  wire                   rx,
    // Interrupt
    output wire                   uart_irq
);

    // ---- Register block outputs ----
    wire                    tx_enable;
    wire                    rx_enable;
    wire                    loopback;
    wire                    break_send;
    wire                    parity_en;
    wire                    parity_odd;
    wire                    stop_bits;
    wire [15:0]             baud_div;
    wire                    tx_fifo_wr;
    wire [DATA_WIDTH-1:0]   tx_fifo_wr_data;
    wire                    rx_fifo_rd;
    wire [DATA_WIDTH-1:0]   rx_fifo_rd_data;
    wire                    clear_errors;

    // ---- FIFO status ----
    wire                    tx_fifo_full;
    wire                    tx_fifo_empty;
    wire [FIFO_PTR_WIDTH:0] tx_fifo_count;
    wire [DATA_WIDTH-1:0]   tx_fifo_rd_data;

    wire                    rx_fifo_full;
    wire                    rx_fifo_empty;
    wire [FIFO_PTR_WIDTH:0] rx_fifo_count;

    // ---- Baud generator ----
    wire                    baud_tick;
    wire [15:0]             oversample_cnt;
    wire                    oversample_tick;
    wire                    mid_sample;

    // ---- TX outputs ----
    wire                    tx_active;
    wire                    tx_fifo_pop;
    wire [DATA_WIDTH-1:0]   tx_fifo_data;
    wire [31:0]             bytes_tx;

    // ---- RX outputs ----
    wire                    rx_active;
    wire                    rx_fifo_wr;
    wire [DATA_WIDTH-1:0]   rx_fifo_wr_data;
    wire                    frame_err;
    wire                    parity_err;
    wire                    overrun_err;
    wire [31:0]             bytes_rx;
    wire [31:0]             frames_errored;
    wire [31:0]             parities_errored;
    wire                    rx_start_detect;

    // Underrun not generated in this version
    wire underrun_err = 1'b0;

    // ============================================================
    // TX FIFO
    // ============================================================
    uart_lite_real_tx_fifo u_tx_fifo (
        .PCLK      (PCLK),
        .PRESETn   (PRESETn),
        .wr_en_i   (tx_fifo_wr),
        .wr_data_i (tx_fifo_wr_data),
        .rd_en_i   (tx_fifo_pop),
        .rd_data_o (tx_fifo_rd_data),
        .full_o    (tx_fifo_full),
        .empty_o   (tx_fifo_empty),
        .count_o   (tx_fifo_count)
    );

    // ============================================================
    // RX FIFO
    // ============================================================
    uart_lite_real_rx_fifo u_rx_fifo (
        .PCLK      (PCLK),
        .PRESETn   (PRESETn),
        .wr_en_i   (rx_fifo_wr),
        .wr_data_i (rx_fifo_wr_data),
        .rd_en_i   (rx_fifo_rd),
        .rd_data_o (rx_fifo_rd_data),
        .full_o    (rx_fifo_full),
        .empty_o   (rx_fifo_empty),
        .count_o   (rx_fifo_count)
    );

    // ============================================================
    // Baud rate generator
    // ============================================================
    uart_lite_real_baud_gen u_baud_gen (
        .PCLK             (PCLK),
        .PRESETn          (PRESETn),
        .baud_div_i       (baud_div),
        .rx_start_detect_i(rx_start_detect),
        .baud_tick_o      (baud_tick),
        .oversample_cnt_o (oversample_cnt),
        .oversample_tick_o(oversample_tick),
        .mid_sample_o     (mid_sample)
    );

    // ============================================================
    // TX FSM
    // ============================================================
    uart_lite_real_tx u_tx (
        .PCLK         (PCLK),
        .PRESETn      (PRESETn),
        .tx_enable_i  (tx_enable),
        .parity_en_i  (parity_en),
        .parity_odd_i (parity_odd),
        .stop_bits_i  (stop_bits),
        .fifo_data_i  (tx_fifo_rd_data),
        .fifo_empty_i (tx_fifo_empty),
        .fifo_pop_o   (tx_fifo_pop),
        .baud_tick_i  (baud_tick),
        .tx_o         (tx),
        .tx_active_o  (tx_active),
        .bytes_tx_o   (bytes_tx),
        .break_i      (break_send)
    );

    // ============================================================
    // RX FSM
    // ============================================================
    uart_lite_real_rx u_rx (
        .PCLK              (PCLK),
        .PRESETn           (PRESETn),
        .rx_enable_i       (rx_enable),
        .parity_en_i       (parity_en),
        .parity_odd_i      (parity_odd),
        .stop_bits_i       (stop_bits),
        .rx_i              (rx),
        .loopback_i        (loopback),
        .tx_loopback_i     (tx),
        .mid_sample_i      (mid_sample),
        .oversample_cnt_i  (oversample_cnt),
        .fifo_wr_o         (rx_fifo_wr),
        .fifo_data_o       (rx_fifo_wr_data),
        .fifo_full_i       (rx_fifo_full),
        .rx_active_o       (rx_active),
        .frame_err_o       (frame_err),
        .parity_err_o      (parity_err),
        .overrun_err_o     (overrun_err),
        .bytes_rx_o        (bytes_rx),
        .frames_errored_o  (frames_errored),
        .parities_errored_o(parities_errored),
        .clear_errors_i    (clear_errors),
        .start_detect_o    (rx_start_detect)
    );

    // ============================================================
    // APB Registers
    // ============================================================
    uart_lite_real_regs u_regs (
        .PCLK             (PCLK),
        .PRESETn          (PRESETn),
        .PADDR            (PADDR),
        .PSEL             (PSEL),
        .PENABLE          (PENABLE),
        .PWRITE           (PWRITE),
        .PWDATA           (PWDATA),
        .PSTRB            (PSTRB),
        .PRDATA           (PRDATA),
        .PREADY           (PREADY),
        .PSLVERR          (PSLVERR),
        .tx_enable_o      (tx_enable),
        .rx_enable_o      (rx_enable),
        .loopback_o       (loopback),
        .break_send_o     (break_send),
        .parity_en_o      (parity_en),
        .parity_odd_o     (parity_odd),
        .stop_bits_o      (stop_bits),
        .baud_div_o       (baud_div),
        .tx_fifo_wr_o     (tx_fifo_wr),
        .tx_fifo_wr_data_o(tx_fifo_wr_data),
        .tx_fifo_full_i   (tx_fifo_full),
        .tx_fifo_empty_i  (tx_fifo_empty),
        .rx_fifo_rd_o     (rx_fifo_rd),
        .rx_fifo_rd_data_i(rx_fifo_rd_data),
        .rx_fifo_empty_i  (rx_fifo_empty),
        .tx_busy_i        (tx_active),
        .rx_busy_i        (rx_active),
        .tx_active_i      (tx_active),
        .rx_active_i      (rx_active),
        .frame_err_i      (frame_err),
        .parity_err_i     (parity_err),
        .overrun_err_i    (overrun_err),
        .underrun_err_i   (underrun_err),
        .bytes_tx_i       (bytes_tx),
        .bytes_rx_i       (bytes_rx),
        .frames_errored_i (frames_errored),
        .parities_errored_i(parities_errored),
        .clear_errors_o   (clear_errors),
        .uart_irq_o       (uart_irq)
    );

endmodule
