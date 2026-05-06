// =============================================================================
// uart_wrapper.sv — Top-level APB4 integration wrapper for UART
// =============================================================================
// This module exposes the external port interface (APB4 slave, UART serial
// pins, interrupt) and instantiates the uart_core integration module.
// All parameters are passed down to uart_core.
// =============================================================================

module uart_wrapper #(
    parameter integer DATA_WIDTH     = 8,
    parameter integer BAUD_DIV       = 16,
    parameter integer FIFO_DEPTH     = 16,
    parameter integer APB_ADDR_WIDTH = 4,
    parameter integer CLOCK_FREQ_MHZ = 100,
    parameter bit     HAS_IRQ        = 1'b1
) (
    // System clock and reset
    input  logic                          clk,
    input  logic                          rst_n,

    // APB4 slave interface
    input  logic [APB_ADDR_WIDTH-1:0]     paddr,
    input  logic                          psel,
    input  logic                          penable,
    input  logic                          pwrite,
    input  logic [31:0]                   pwdata,
    output logic [31:0]                   prdata,
    output logic                          pready,
    output logic                          pslverr,

    // UART serial pins
    output logic                          tx,
    input  logic                          rx,

    // Interrupt output (gated by HAS_IRQ parameter)
    output logic                          irq
);

    // ========================================================================
    // Instantiate the core integration module
    // ========================================================================
    uart_core #(
        .DATA_WIDTH     (DATA_WIDTH),
        .BAUD_DIV       (BAUD_DIV),
        .FIFO_DEPTH     (FIFO_DEPTH),
        .APB_ADDR_WIDTH (APB_ADDR_WIDTH),
        .HAS_IRQ        (HAS_IRQ)
    ) u_core (
        .clk      (clk),
        .rst_n    (rst_n),

        .paddr    (paddr),
        .psel     (psel),
        .penable  (penable),
        .pwrite   (pwrite),
        .pwdata   (pwdata),
        .prdata   (prdata),
        .pready   (pready),
        .pslverr  (pslverr),

        .tx_o     (tx),
        .rx_i     (rx),

        .irq_o    (irq)
    );

endmodule
