
`default_nettype none

module gpio_pad #(
    parameter int NUM_PADS        = 32,
    parameter int APB_ADDR_WIDTH  = 12,
    parameter int APB_DATA_WIDTH  = 32
) (
    // Clock and Reset
    input  logic                             pclk,
    input  logic                             presetn,       // active-low async

    // APB Slave Interface
    input  logic [APB_ADDR_WIDTH-1:0]        paddr,
    input  logic                             psel,
    input  logic                             penable,
    input  logic                             pwrite,
    input  logic [APB_DATA_WIDTH-1:0]        pwdata,
    input  logic [(APB_DATA_WIDTH/8)-1:0]    pstrb,
    output logic [APB_DATA_WIDTH-1:0]        prdata,
    output logic                             pready,
    output logic                             pslverr,

    // GPIO Pad Interface
    input  logic [NUM_PADS-1:0]              gpio_in,
    output logic [NUM_PADS-1:0]              gpio_out,
    output logic [NUM_PADS-1:0]              gpio_oe,

    // Interrupt
    output logic                             gpio_irq
);

    // =========================================================================
    // Internal signals between regs and core
    // =========================================================================
    logic [NUM_PADS-1:0] dir;
    logic [NUM_PADS-1:0] out_val;
    logic [NUM_PADS-1:0] inten;        // unused in core, registered internally
    logic [NUM_PADS-1:0] in_sync;
    logic [NUM_PADS-1:0] edge_pulse;

    // =========================================================================
    // gpio_pad_regs — APB register block + interrupt controller
    // =========================================================================
    gpio_pad_regs #(
        .NUM_PADS        (NUM_PADS),
        .APB_ADDR_WIDTH  (APB_ADDR_WIDTH),
        .APB_DATA_WIDTH  (APB_DATA_WIDTH)
    ) u_regs (
        .pclk        (pclk),
        .presetn     (presetn),
        .paddr       (paddr),
        .psel        (psel),
        .penable     (penable),
        .pwrite      (pwrite),
        .pwdata      (pwdata),
        .pstrb       (pstrb),
        .prdata      (prdata),
        .pready      (pready),
        .pslverr     (pslverr),
        .dir         (dir),
        .out_val     (out_val),
        .inten       (inten),
        .in_sync     (in_sync),
        .edge_pulse  (edge_pulse),
        .gpio_irq    (gpio_irq)
    );

    // =========================================================================
    // gpio_pad_core — pad synchronizer + edge detect + output drive
    // =========================================================================
    gpio_pad_core #(
        .NUM_PADS (NUM_PADS)
    ) u_core (
        .pclk       (pclk),
        .presetn    (presetn),
        .gpio_in    (gpio_in),
        .gpio_out   (gpio_out),
        .gpio_oe    (gpio_oe),
        .dir        (dir),
        .out_val    (out_val),
        .in_sync    (in_sync),
        .edge_pulse (edge_pulse)
    );

endmodule : gpio_pad

`default_nettype wire
