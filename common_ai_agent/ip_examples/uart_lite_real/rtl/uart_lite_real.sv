// uart_lite_real.sv — Top-level wrapper
// SSOT: top_module (name: uart_lite_real, file: rtl/uart_lite_real.sv)

`include "uart_lite_real_param.vh"

module uart_lite_real (
    input  wire                   PCLK,
    input  wire                   PRESETn,
    // APB4 slave interface
    input  wire [APB_ADDR_WIDTH-1:0] PADDR,
    input  wire                   PSEL,
    input  wire                   PENABLE,
    input  wire                   PWRITE,
    input  wire [APB_DATA_WIDTH-1:0] PWDATA,
    input  wire [3:0]             PSTRB,
    output wire [APB_DATA_WIDTH-1:0] PRDATA,
    output wire                   PREADY,
    output wire                   PSLVERR,
    // UART serial
    output wire                   tx,
    input  wire                   rx,
    // Interrupt
    output wire                   uart_irq
);

    uart_lite_real_core u_core (
        .PCLK    (PCLK),
        .PRESETn (PRESETn),
        .PADDR   (PADDR),
        .PSEL    (PSEL),
        .PENABLE (PENABLE),
        .PWRITE  (PWRITE),
        .PWDATA  (PWDATA),
        .PSTRB   (PSTRB),
        .PRDATA  (PRDATA),
        .PREADY  (PREADY),
        .PSLVERR (PSLVERR),
        .tx      (tx),
        .rx      (rx),
        .uart_irq(uart_irq)
    );

endmodule
