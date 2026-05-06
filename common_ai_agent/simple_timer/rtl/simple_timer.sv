`default_nettype none

module simple_timer (
    input wire clk,
    input wire rst_n,
    input wire psel,
    input wire penable,
    input wire pwrite,
    input wire [11:0] paddr,
    input wire [31:0] pwdata,
    input wire [31:0] prdata,
    input wire pready,
    input wire pslverr,
    input wire irq
);

    simple_timer_regs simple_timer_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_timer_counter simple_timer_counter_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_timer_irq simple_timer_irq_u (
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule

`default_nettype wire
