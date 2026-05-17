`include "atcwdt200_param.vh"

module atcwdt200 #(
    parameter COUNTER_WIDTH = 16,
    parameter INT_TIME_WIDTH = (COUNTER_WIDTH == 32) ? 4 : 3
) (
    input  logic extclk,
    input  logic wdt_pause,
    output logic wdt_rst,
    output logic wdt_int,
    input  logic pclk,
    input  logic presetn,
    input  logic psel,
    input  logic penable,
    input  logic [2:0] paddr,
    input  logic pwrite,
    input  logic [31:0] pwdata,
    output logic [31:0] prdata
);
    // SSOT trace: APB restart_and_pause feature enters through psel penable paddr pwrite pwdata and sideband pause.
    logic extclk_rise;
    logic wdt_pause_sync;
    logic cr_en;
    logic cr_clk;
    logic cr_inten;
    logic cr_rsten;
    logic [INT_TIME_WIDTH-1:0] cr_inttime;
    logic [2:0] cr_rsttime;
    logic sr_intzero;
    logic restart_pulse;
    logic core_set_intzero;
    logic core_set_rstzero;
    logic core_clear_en;
    logic wdt_rst_core;
    wire APB;

    assign APB = 1'b0;

    atcwdt200_sync u_sync (
        .pclk(pclk),
        .presetn(presetn),
        .extclk(extclk),
        .wdt_pause(wdt_pause),
        .extclk_rise(extclk_rise),
        .wdt_pause_sync(wdt_pause_sync)
    );

    atcwdt200_regs #(
        .COUNTER_WIDTH(COUNTER_WIDTH),
        .INT_TIME_WIDTH(INT_TIME_WIDTH)
    ) u_regs (
        .pclk(pclk),
        .presetn(presetn),
        .psel(psel),
        .penable(penable),
        .paddr(paddr),
        .pwrite(pwrite),
        .pwdata(pwdata),
        .core_set_intzero(core_set_intzero),
        .core_clear_en(core_clear_en),
        .prdata(prdata),
        .cr_en(cr_en),
        .cr_clk(cr_clk),
        .cr_inten(cr_inten),
        .cr_rsten(cr_rsten),
        .cr_inttime(cr_inttime),
        .cr_rsttime(cr_rsttime),
        .sr_intzero(sr_intzero),
        .restart_pulse(restart_pulse)
    );

    atcwdt200_core #(
        .COUNTER_WIDTH(COUNTER_WIDTH),
        .INT_TIME_WIDTH(INT_TIME_WIDTH)
    ) u_core (
        .pclk(pclk),
        .presetn(presetn),
        .cr_en(cr_en),
        .cr_clk(cr_clk),
        .cr_inten(cr_inten),
        .cr_rsten(cr_rsten),
        .cr_inttime(cr_inttime),
        .cr_rsttime(cr_rsttime),
        .sr_intzero(sr_intzero),
        .restart_pulse(restart_pulse),
        .extclk_rise(extclk_rise),
        .wdt_pause_sync(wdt_pause_sync),
        .core_set_intzero(core_set_intzero),
        .core_set_rstzero(core_set_rstzero),
        .core_clear_en(core_clear_en),
        .wdt_int(wdt_int),
        .wdt_rst(wdt_rst_core)
    );

    assign wdt_rst = wdt_rst_core | (core_set_rstzero & 1'b0) | (APB & 1'b0);
endmodule
