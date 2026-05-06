// =============================================================================
// uart_core.v — Core Datapath, Interrupt OR, Loopback (LLM-written)
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

/* verilator lint_off UNUSEDSIGNAL */
module uart_core (
    input  wire        clk,
    input  wire        rst_n,
    // Register interface
    input  wire [2:0]  data_bits,
    input  wire        stop_bits,
    input  wire        parity_en,
    input  wire        parity_odd,
    input  wire        loopback,
    input  wire        tx_en,
    input  wire        rx_en,
    input  wire [15:0] baud_divisor,
    input  wire [7:0]  tx_data,
    input  wire        tx_data_valid,
    output wire [7:0]  rx_data_to_regs,
    output wire        rx_data_valid,
    output wire [5:0]  status_vec,
    output wire        busy,
    input  wire [5:0]  int_en,
    output wire [5:0]  int_status_flags,
    output wire        uart_irq,
    // Serial pins
    output wire        tx_out,
    input  wire        rx_in,
    // Debug wires
    output wire [3:0]  sample_count,
    output wire        tx_fifo_not_empty,
    output wire [7:0]  rx_data_byte,
    output wire        rx_fifo_empty,
    output wire        rx_active
);

    // Baud rate generator
    wire baud_tick;

    uart_baud u_baud (
        .clk          (clk),
        .rst_n        (rst_n),
        .divisor      (baud_divisor),
        .baud_tick    (baud_tick),
        .sample_count (sample_count)
    );

    // TX path
    wire       tx_done_w;
    wire       tx_fifo_full;
    wire       tx_fifo_not_empty_w;
    wire [7:0] tx_loopback_data; /*verilator lint_off UNUSEDSIGNAL*/

    uart_tx u_tx (
        .clk           (clk),
        .rst_n         (rst_n),
        .tx_en         (tx_en),
        .data_bits     (data_bits),
        .stop_bits     (stop_bits),
        .parity_en     (parity_en),
        .parity_odd    (parity_odd),
        .loopback_en   (loopback),
        .baud_tick     (baud_tick),
        .fifo_wdata    (tx_data),
        .fifo_wr_en    (tx_data_valid),
        .fifo_full     (tx_fifo_full),
        .fifo_not_empty(tx_fifo_not_empty_w),
        .tx_out        (tx_out),
        .tx_done       (tx_done_w),
        .loopback_data (tx_loopback_data)
    );

    assign tx_fifo_not_empty = tx_fifo_not_empty_w;

    // RX path — loopback mux
    wire rx_src = loopback ? tx_out : rx_in;

    // 2-stage synchronizer
    reg rx_sync_0, rx_sync_1;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_sync_0 <= 1'b1;
            rx_sync_1 <= 1'b1;
        end else begin
            rx_sync_0 <= rx_src;
            rx_sync_1 <= rx_sync_0;
        end
    end

    wire rx_fe_w, rx_pe_w, rx_oe_w;
    wire [7:0]  rx_fifo_data;
    wire        rx_fifo_not_empty_w;
    wire        rx_active_w;

    uart_rx u_rx (
        .clk           (clk),
        .rst_n         (rst_n),
        .rx_en         (rx_en),
        .data_bits     (data_bits),
        .parity_en     (parity_en),
        .parity_odd    (parity_odd),
        .baud_tick     (baud_tick),
        .rx_in         (rx_sync_1),
        .rx_data       (rx_fifo_data),
        .fifo_empty    (rx_fifo_empty),
        .fifo_not_empty(rx_fifo_not_empty_w),
        .rx_active     (rx_active_w),
        .framing_err   (rx_fe_w),
        .parity_err    (rx_pe_w),
        .overrun_err   (rx_oe_w)
    );

    assign rx_data_byte   = rx_fifo_data;
    assign rx_active      = rx_active_w;
    assign rx_data_to_regs = rx_fifo_data;
    assign rx_data_valid  = rx_fifo_not_empty_w;

    // RX timeout counter
    reg [7:0] rx_timeout_cnt;
    reg       rx_timeout_flag;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_timeout_cnt  <= 8'd0;
            rx_timeout_flag <= 1'b0;
        end else begin
            rx_timeout_flag <= 1'b0;
            if (rx_fifo_not_empty_w) begin
                if (rx_timeout_cnt >= 8'd255)
                    rx_timeout_flag <= 1'b1;
                else
                    rx_timeout_cnt <= rx_timeout_cnt + 8'd1;
            end else begin
                rx_timeout_cnt <= 8'd0;
            end
        end
    end

    // Status vector: {fe, pe, oe, rxdv, txnf, txe}
    assign status_vec = {rx_fe_w, rx_pe_w, rx_oe_w,
                         rx_fifo_not_empty_w,
                         ~tx_fifo_full,
                         ~tx_fifo_not_empty_w};

    assign busy = tx_fifo_not_empty_w | rx_active_w;

    // Interrupt flags (sticky)
    assign int_status_flags = {rx_fe_w | rx_timeout_flag,
                               rx_pe_w,
                               rx_oe_w,
                               rx_fifo_not_empty_w,
                               tx_done_w,
                               ~tx_fifo_not_empty_w};

    // IRQ = |(status & enable)
    assign uart_irq = |(int_status_flags & int_en);

endmodule

`default_nettype wire
