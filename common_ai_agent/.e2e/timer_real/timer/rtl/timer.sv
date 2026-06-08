module timer #(
    parameter integer DATA_WIDTH = 32,
    parameter integer ADDR_WIDTH = 4
) (
    input  logic                  pclk,
    input  logic                  presetn,
    input  logic [ADDR_WIDTH-1:0] paddr,
    input  logic                  psel,
    input  logic                  penable,
    input  logic                  pwrite,
    input  logic [DATA_WIDTH-1:0] pwdata,
    output logic [DATA_WIDTH-1:0] prdata,
    output logic                  pready,
    output logic                  pslverr,
    output logic                  irq
);

    logic [DATA_WIDTH-1:0] load_q;
    logic                  enable_q;
    logic [DATA_WIDTH-1:0] count_q;
    logic                  irq_q;

    // The top-level timer is the SSOT wiring owner: the parent supplies pclk,
    // presetn, APB setup/access phase controls, and a 0x10-byte register window.
    // APB inputs are consumed by timer_regs, while load_q/enable_q/count_q carry
    // live architectural state between the register file and timer_core.
    timer_regs #(
        .DATA_WIDTH(DATA_WIDTH),
        .ADDR_WIDTH(ADDR_WIDTH)
    ) u_timer_regs (
        .pclk    (pclk),
        .presetn (presetn),
        .paddr   (paddr),
        .psel    (psel),
        .penable (penable),
        .pwrite  (pwrite),
        .pwdata  (pwdata),
        .count_q (count_q),
        .irq_q   (irq_q),
        .prdata  (prdata),
        .pready  (pready),
        .pslverr (pslverr),
        .load_q  (load_q),
        .enable_q(enable_q)
    );

    // The core owns the one-cycle decrement/reload decision and drives irq as
    // the externally observable TIMER_ZERO pulse. The register file provides
    // LOAD/CTRL state, and STATUS observes the core count_q feedback.
    timer_core #(
        .DATA_WIDTH(DATA_WIDTH)
    ) u_timer_core (
        .pclk    (pclk),
        .presetn (presetn),
        .load_q  (load_q),
        .enable_q(enable_q),
        .count_q (count_q),
        .irq     (irq),
        .irq_q   (irq_q)
    );

endmodule
