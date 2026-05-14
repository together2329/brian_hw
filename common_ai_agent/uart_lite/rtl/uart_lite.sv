// uart_lite.sv — UART Lite top-level wrapper
// Instantiates uart_lite_regs (APB slave + register file + interrupt combiner)
// and uart_lite_core (TX/RX datapath, FIFOs, baud generator, debug counters).
// Provides APB4 slave, UART serial, and interrupt interfaces.
//
// SSOT: top_module, io_list, integration

`include "uart_lite_param.vh"

module uart_lite #(
    parameter integer DATA_WIDTH      = `UART_LITE_DATA_WIDTH,
    parameter integer FIFO_DEPTH      = `UART_LITE_FIFO_DEPTH,
    parameter integer OVERSAMPLE      = `UART_LITE_OVERSAMPLE,
    parameter integer APB_ADDR_WIDTH  = `UART_LITE_APB_ADDR_WIDTH,
    parameter integer APB_DATA_WIDTH  = `UART_LITE_APB_DATA_WIDTH
) (
    // Clock and reset
    input  logic                     PCLK,
    input  logic                     PRESETn,

    // APB4 slave interface — widths match SSOT io_list exactly
    input  logic [7:0]               PADDR,     // SSOT: width 8
    input  logic                     PSEL,
    input  logic                     PENABLE,
    input  logic                     PWRITE,
    input  logic [31:0]              PWDATA,    // SSOT: width 32
    input  logic [3:0]               PSTRB,
    output logic [31:0]              PRDATA,    // SSOT: width 32
    output logic                     PREADY,
    output logic                     PSLVERR,

    // UART serial interface
    output logic                     tx,
    input  logic                     rx,

    // Interrupt output
    output logic                     uart_irq
);

    // ---------- Interconnect signals: regs → core ----------
    logic                 tx_enable;
    logic                 rx_enable;
    logic                 loopback;
    logic                 break_send;
    logic                 parity_en;
    logic                 parity_odd;
    logic                 stop_bits;
    logic [15:0]          baud_div;

    // TXDATA write interface
    logic                 tx_fifo_wr_en;
    logic [DATA_WIDTH-1:0] tx_fifo_wr_data;

    // RXDATA read interface
    logic                 rx_fifo_rd_en;
    logic [DATA_WIDTH-1:0] rx_fifo_rd_data;

    // ---------- Interconnect signals: core → regs ----------
    logic                 tx_full;
    logic                 tx_empty;
    logic                 rx_empty;
    logic                 rx_full;
    logic                 tx_busy;
    logic                 rx_busy;
    logic                 frame_err;
    logic                 parity_err;
    logic                 overrun_err;
    logic                 underrun_err;

    // Debug counters
    logic [31:0]          bytes_tx;
    logic [31:0]          bytes_rx;
    logic [31:0]          frames_errored;
    logic [31:0]          parities_errored;

    // Baud tick (for break timer in regs)
    logic                 baud_tick;

    // ---------- Register block ----------
    uart_lite_regs #(
        .DATA_WIDTH      (DATA_WIDTH),
        .FIFO_DEPTH      (FIFO_DEPTH),
        .APB_ADDR_WIDTH  (APB_ADDR_WIDTH),
        .APB_DATA_WIDTH  (APB_DATA_WIDTH)
    ) u_regs (
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
        .parity_en_o      (parity_en),
        .parity_odd_o     (parity_odd),
        .stop_bits_o      (stop_bits),
        .baud_div_o       (baud_div),
        .baud_tick_i      (baud_tick),
        .break_send_o     (break_send),

        .tx_full_i        (tx_full),
        .tx_empty_i       (tx_empty),
        .rx_empty_i       (rx_empty),
        .rx_full_i        (rx_full),
        .tx_busy_i        (tx_busy),
        .rx_busy_i        (rx_busy),
        .frame_err_i      (frame_err),
        .parity_err_i     (parity_err),
        .overrun_err_i    (overrun_err),
        .underrun_err_i   (underrun_err),

        .tx_fifo_wr_en_o  (tx_fifo_wr_en),
        .tx_fifo_wr_data_o(tx_fifo_wr_data),
        .rx_fifo_rd_en_o  (rx_fifo_rd_en),
        .rx_fifo_rd_data_i(rx_fifo_rd_data),

        .bytes_tx_i       (bytes_tx),
        .bytes_rx_i       (bytes_rx),
        .frames_errored_i (frames_errored),
        .parities_errored_i(parities_errored),

        .uart_irq_o       (uart_irq)
    );

    // ---------- Core (TX/RX datapath + FIFOs) ----------
    uart_lite_core #(
        .DATA_WIDTH  (DATA_WIDTH),
        .FIFO_DEPTH  (FIFO_DEPTH),
        .OVERSAMPLE  (OVERSAMPLE)
    ) u_core (
        .PCLK              (PCLK),
        .PRESETn           (PRESETn),

        .tx_enable_i       (tx_enable),
        .rx_enable_i       (rx_enable),
        .loopback_i        (loopback),
        .break_send_i      (break_send),
        .parity_en_i       (parity_en),
        .parity_odd_i      (parity_odd),
        .stop_bits_i       (stop_bits),
        .baud_div_i        (baud_div),

        .tx_fifo_wr_en_i   (tx_fifo_wr_en),
        .tx_fifo_wr_data_i (tx_fifo_wr_data),
        .rx_fifo_rd_en_i   (rx_fifo_rd_en),
        .rx_fifo_rd_data_o (rx_fifo_rd_data),

        .tx_full_o         (tx_full),
        .tx_empty_o        (tx_empty),
        .rx_empty_o        (rx_empty),
        .rx_full_o         (rx_full),
        .tx_busy_o         (tx_busy),
        .rx_busy_o         (rx_busy),
        .frame_err_o       (frame_err),
        .parity_err_o      (parity_err),
        .overrun_err_o     (overrun_err),
        .underrun_err_o    (underrun_err),

        .bytes_tx_o        (bytes_tx),
        .bytes_rx_o        (bytes_rx),
        .frames_errored_o  (frames_errored),
        .parities_errored_o(parities_errored),

        .baud_tick_o       (baud_tick),

        .tx_o              (tx),
        .rx_i              (rx)
    );

endmodule
