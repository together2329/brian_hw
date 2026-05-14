// uart_lite.sv — Top-level UART Lite IP
// Implements: top_module — Simple parameterized UART transceiver with APB-lite CSR interface
// TX/RX FIFOs, configurable baud/parity/stop/framing, oversampling RX, loopback, break, debug counters, per-source masked interrupts

module uart_lite #(
    parameter integer DATA_WIDTH    = 8,
    parameter integer FIFO_DEPTH    = 16,
    parameter integer OVERSAMPLE    = 16,
    parameter integer APB_ADDR_W    = 12,
    parameter integer APB_DATA_W    = 32
) (
    // Clock and reset
    input  logic                      PCLK,
    input  logic                      PRESETn,
    // APB-lite slave interface
    input  logic [APB_ADDR_W-1:0]     PADDR,
    input  logic                      PSEL,
    input  logic                      PENABLE,
    input  logic                      PWRITE,
    input  logic [APB_DATA_W-1:0]     PWDATA,
    input  logic [3:0]                PSTRB,
    output logic [APB_DATA_W-1:0]     PRDATA,
    output logic                      PREADY,
    output logic                      PSLVERR,
    // UART serial interface
    input  logic                      rxd_i,
    output logic                      txd_o,
    // Interrupt
    output logic                      irq_o
);
    uart_lite_core #(
        .DATA_WIDTH (DATA_WIDTH),
        .FIFO_DEPTH (FIFO_DEPTH),
        .OVERSAMPLE (OVERSAMPLE),
        .APB_ADDR_W (APB_ADDR_W),
        .APB_DATA_W (APB_DATA_W)
    ) u_core (
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
        .rxd_i   (rxd_i),
        .txd_o   (txd_o),
        .irq_o   (irq_o)
    );

endmodule
