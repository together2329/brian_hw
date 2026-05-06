// =============================================================================
// uart_wrapper.v — Top Integration Wrapper
// =============================================================================
`default_nettype none
`include "uart_defines.vh"

/* verilator lint_off UNUSEDSIGNAL */
module uart_wrapper (
    input  wire                      uartclk,
    input  wire                      uartresetn,
    input  wire [`APB_ADDR_W-1:0]    paddr,
    input  wire                      psel,
    input  wire                      penable,
    input  wire                      pwrite,
    input  wire [`APB_DATA_W-1:0]    pwdata,
    input  wire [3:0]                pstrb,
    output wire [`APB_DATA_W-1:0]    prdata,
    output wire                      pready,
    output wire                      pslverr,
    output wire                      tx,
    input  wire                      rx,
    output wire                      rts_n,
    input  wire                      cts_n,  /*verilator lint_off UNUSEDSIGNAL*/
    output wire                      uart_irq
);

    // Internal wires
    wire [2:0]  data_bits;
    wire        stop_bits;
    wire        parity_en;
    wire        parity_odd;
    wire        loopback;
    wire        tx_en;
    wire        rx_en;
    wire [15:0] baud_divisor;
    wire [7:0]  tx_data;
    wire        tx_data_valid;
    wire [7:0]  rx_data_to_regs;
    wire        rx_data_valid;
    wire [5:0]  status_vec;
    wire        busy;
    wire [5:0]  int_en;
    wire [5:0]  int_status_flags;

    // Debug wires — exposed for test but unused at wrapper level
    /*verilator lint_off UNUSEDSIGNAL*/
    wire [3:0]  sample_count;
    wire        tx_fifo_not_empty;
    wire [7:0]  rx_data_byte;
    wire        rx_fifo_empty;
    wire        rx_active;
    /*verilator lint_on UNUSEDSIGNAL*/

    uart_regs u_regs (
        .clk           (uartclk),
        .rst_n         (uartresetn),
        .paddr         (paddr),
        .psel          (psel),
        .penable       (penable),
        .pwrite        (pwrite),
        .pwdata        (pwdata),
        .pstrb         (pstrb),
        .prdata        (prdata),
        .pready        (pready),
        .pslverr       (pslverr),
        .data_bits     (data_bits),
        .stop_bits     (stop_bits),
        .parity_en     (parity_en),
        .parity_odd    (parity_odd),
        .loopback      (loopback),
        .tx_en         (tx_en),
        .rx_en         (rx_en),
        .baud_divisor  (baud_divisor),
        .tx_data       (tx_data),
        .tx_data_valid (tx_data_valid),
        .rx_data       (rx_data_to_regs),
        .rx_data_valid (rx_data_valid),
        .status_vec    (status_vec),
        .busy          (busy),
        .int_en        (int_en),
        .int_status    (int_status_flags)
    );

    uart_core u_core (
        .clk             (uartclk),
        .rst_n           (uartresetn),
        .data_bits       (data_bits),
        .stop_bits       (stop_bits),
        .parity_en       (parity_en),
        .parity_odd      (parity_odd),
        .loopback        (loopback),
        .tx_en           (tx_en),
        .rx_en           (rx_en),
        .baud_divisor    (baud_divisor),
        .tx_data         (tx_data),
        .tx_data_valid   (tx_data_valid),
        .rx_data_to_regs (rx_data_to_regs),
        .rx_data_valid   (rx_data_valid),
        .status_vec      (status_vec),
        .busy            (busy),
        .int_en          (int_en),
        .int_status_flags(int_status_flags),
        .uart_irq        (uart_irq),
        .tx_out          (tx),
        .rx_in           (rx),
        .sample_count    (sample_count),
        .tx_fifo_not_empty(tx_fifo_not_empty),
        .rx_data_byte    (rx_data_byte),
        .rx_fifo_empty   (rx_fifo_empty),
        .rx_active       (rx_active)
    );

    assign rts_n = 1'b1;

endmodule

`default_nettype wire
