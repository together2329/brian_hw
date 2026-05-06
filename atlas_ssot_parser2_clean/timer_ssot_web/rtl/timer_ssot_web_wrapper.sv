`default_nettype none

module timer_ssot_web_wrapper #(
    parameter integer DBITS = 32,
    parameter integer ABITS = 4
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire [ABITS-1:0]  paddr,
    input  wire              psel,
    input  wire              penable,
    input  wire              pwrite,
    input  wire [DBITS-1:0]  pwdata,
    input  wire [3:0]        pstrb,
    output wire [DBITS-1:0]  prdata,
    output wire              pready,
    output wire              pslverr,
    output wire              irq
);
    wire              ctrl_enable;
    wire              ctrl_irq_enable;
    wire [DBITS-1:0]  compare_value;
    wire              status_clear;
    wire [DBITS-1:0]  count_value;
    wire              irq_status;

    timer_ssot_web_regs #(
        .DBITS(DBITS),
        .ABITS(ABITS)
    ) regs_u (
        .clk(clk),
        .rst_n(rst_n),
        .paddr(paddr),
        .psel(psel),
        .penable(penable),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .pstrb(pstrb),
        .prdata(prdata),
        .pready(pready),
        .pslverr(pslverr),
        .count_value(count_value),
        .irq_status(irq_status),
        .ctrl_enable(ctrl_enable),
        .ctrl_irq_enable(ctrl_irq_enable),
        .compare_value(compare_value),
        .status_clear(status_clear)
    );

    timer_ssot_web_core #(
        .DBITS(DBITS)
    ) core_u (
        .clk(clk),
        .rst_n(rst_n),
        .enable(ctrl_enable),
        .irq_enable(ctrl_irq_enable),
        .compare_value(compare_value),
        .status_clear(status_clear),
        .count_value(count_value),
        .irq_status(irq_status),
        .irq(irq)
    );
endmodule

`default_nettype wire
