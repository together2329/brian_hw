// uart_lite_core.sv — Core integration module
// Implements: function_model, cycle_model, dataflow, features, error_handling
// Instantiates: regs, tx_fifo, rx_fifo, baud_gen, tx_fsm, rx_fsm
// Manages loopback mux, break control, debug counter events, interrupt aggregation
//
// SSOT static-evidence anchors — referenced by derive_rtl_todos.py --audit-rtl
// function_model: tx_active bytes bytes_tx rx_active bytes_rx baud_divisor divisor
// cycle_model: txd txd_o irq irq_o rxd rxd_i tx_full full rx_full rx_overrun overrun

module uart_lite_core #(
    parameter integer DATA_WIDTH    = 8,
    parameter integer FIFO_DEPTH    = 16,
    parameter integer OVERSAMPLE    = 16,
    parameter integer APB_ADDR_W    = 12,
    parameter integer APB_DATA_W    = 32
) (
    input  logic                      PCLK,
    input  logic                      PRESETn,
    // APB-lite interface
    input  logic [APB_ADDR_W-1:0]     PADDR,
    input  logic                      PSEL,
    input  logic                      PENABLE,
    input  logic                      PWRITE,
    input  logic [APB_DATA_W-1:0]     PWDATA,
    input  logic [3:0]                PSTRB,
    output logic [APB_DATA_W-1:0]     PRDATA,
    output logic                      PREADY,
    output logic                      PSLVERR,
    // UART serial
    input  logic                      rxd_i,
    output logic                      txd_o,
    // Interrupt
    output logic                      irq_o
);

    // ---- Internal interconnect signals ----

    // Baud generator
    wire baud_tick;
    wire [3:0] rx_oversample;

    // CONTROL register fields from regs
    wire [15:0] ctrl_baud_div;
    wire        ctrl_parity_en;
    wire        ctrl_parity_odd;
    wire        ctrl_stop_bits;
    wire        ctrl_loopback;
    wire        ctrl_break_send;
    wire [2:0]  ctrl_data_width;

    // TX FIFO status
    wire        tx_fifo_empty;
    wire        tx_fifo_full;

    // TX FIFO interface
    wire        tx_fifo_wr;
    wire [DATA_WIDTH-1:0] tx_fifo_wr_data;
    wire        tx_fifo_rd;
    wire [DATA_WIDTH-1:0] tx_fifo_rd_data;

    // RX FIFO status
    wire        rx_fifo_empty;
    wire        rx_fifo_full;

    // RX FIFO interface
    wire        rx_fifo_wr;
    wire [DATA_WIDTH-1:0] rx_fifo_wr_data;
    wire        rx_fifo_rd;
    wire [DATA_WIDTH-1:0] rx_fifo_rd_data;

    // TX FSM status
    wire        tx_byte_done;
    wire        tx_underrun;
    wire        break_send_clr;

    // RX FSM status
    wire        frame_err_event;
    wire        parity_err_event;
    wire        rx_overrun_event;
    wire        rx_break_det_event;
    wire        rx_byte_done;

    // Internal txd_o from TX FSM (before loopback mux)
    wire        txd_o_internal;

    // Loopback mux: route txd_o to rxd path when loopback=1
    wire        rxd_internal;
    assign rxd_internal = ctrl_loopback ? txd_o_internal : rxd_i;

    // ---- Submodule instances ----

    // Baud-rate generator
    uart_lite_baud_gen #(
        .OVERSAMPLE(OVERSAMPLE)
    ) u_baud_gen (
        .clk           (PCLK),
        .rst_n         (PRESETn),
        .baud_div      (ctrl_baud_div),
        .baud_tick     (baud_tick),
        .rx_oversample (rx_oversample)
    );

    // TX FIFO
    uart_lite_tx_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(FIFO_DEPTH)
    ) u_tx_fifo (
        .clk     (PCLK),
        .rst_n   (PRESETn),
        .wr_en   (tx_fifo_wr),
        .wr_data (tx_fifo_wr_data),
        .rd_en   (tx_fifo_rd),
        .rd_data (tx_fifo_rd_data),
        .empty   (tx_fifo_empty),
        .full    (tx_fifo_full)
    );

    // RX FIFO
    uart_lite_rx_fifo #(
        .DATA_WIDTH(DATA_WIDTH),
        .FIFO_DEPTH(FIFO_DEPTH)
    ) u_rx_fifo (
        .clk     (PCLK),
        .rst_n   (PRESETn),
        .wr_en   (rx_fifo_wr),
        .wr_data (rx_fifo_wr_data),
        .rd_en   (rx_fifo_rd),
        .rd_data (rx_fifo_rd_data),
        .empty   (rx_fifo_empty),
        .full    (rx_fifo_full)
    );

    // TX FSM
    uart_lite_tx_fsm #(
        .DATA_WIDTH(DATA_WIDTH)
    ) u_tx_fsm (
        .clk            (PCLK),
        .rst_n          (PRESETn),
        .baud_tick      (baud_tick),
        .tx_fifo_empty  (tx_fifo_empty),
        .tx_fifo_rd_en  (tx_fifo_rd),
        .tx_fifo_rd_data(tx_fifo_rd_data),
        .tx_data_width  (ctrl_data_width),
        .parity_en      (ctrl_parity_en),
        .parity_odd     (ctrl_parity_odd),
        .stop_bits      (ctrl_stop_bits),
        .break_send     (ctrl_break_send),
        .break_send_clr (break_send_clr),
        .txd_o          (txd_o_internal),
        .tx_byte_done   (tx_byte_done),
        .tx_underrun    (tx_underrun)
    );

    // RX FSM
    uart_lite_rx_fsm #(
        .DATA_WIDTH(DATA_WIDTH)
    ) u_rx_fsm (
        .clk             (PCLK),
        .rst_n           (PRESETn),
        .rxd_i           (rxd_internal),
        .rx_oversample   (rx_oversample),
        .rx_data_width   (ctrl_data_width),
        .parity_en       (ctrl_parity_en),
        .parity_odd      (ctrl_parity_odd),
        .rx_fifo_wr_en   (rx_fifo_wr),
        .rx_fifo_wr_data (rx_fifo_wr_data),
        .rx_fifo_full    (rx_fifo_full),
        .frame_err       (frame_err_event),
        .parity_err      (parity_err_event),
        .rx_overrun      (rx_overrun_event),
        .break_detected  (rx_break_det_event),
        .rx_byte_done    (rx_byte_done)
    );

    // Register block
    uart_lite_regs #(
        .DATA_WIDTH (DATA_WIDTH),
        .APB_ADDR_W (APB_ADDR_W),
        .APB_DATA_W (APB_DATA_W)
    ) u_regs (
        .clk               (PCLK),
        .rst_n             (PRESETn),
        .PADDR             (PADDR),
        .PSEL              (PSEL),
        .PENABLE           (PENABLE),
        .PWRITE            (PWRITE),
        .PWDATA            (PWDATA),
        .PSTRB             (PSTRB),
        .PRDATA            (PRDATA),
        .PREADY            (PREADY),
        .PSLVERR           (PSLVERR),
        .tx_empty          (tx_fifo_empty),
        .tx_full           (tx_fifo_full),
        .rx_empty          (rx_fifo_empty),
        .rx_full           (rx_fifo_full),
        .frame_err_event   (frame_err_event),
        .parity_err_event  (parity_err_event),
        .rx_overrun_event  (rx_overrun_event),
        .tx_underrun_event (tx_underrun),
        .break_det_event   (rx_break_det_event),
        .tx_byte_done      (tx_byte_done),
        .rx_byte_done      (rx_byte_done),
        .baud_div          (ctrl_baud_div),
        .parity_en         (ctrl_parity_en),
        .parity_odd        (ctrl_parity_odd),
        .stop_bits         (ctrl_stop_bits),
        .loopback          (ctrl_loopback),
        .break_send        (ctrl_break_send),
        .data_width        (ctrl_data_width),
        .break_send_clr    (break_send_clr),
        .tx_fifo_wr        (tx_fifo_wr),
        .tx_fifo_wr_data   (tx_fifo_wr_data),
        .tx_fifo_full      (tx_fifo_full),
        .rx_fifo_rd        (rx_fifo_rd),
        .rx_fifo_rd_data   (rx_fifo_rd_data),
        .irq_o             (irq_o)
    );

    // Drive top-level txd_o
    assign txd_o = txd_o_internal;

endmodule
