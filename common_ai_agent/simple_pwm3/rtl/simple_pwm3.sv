`default_nettype none

module simple_pwm3 (
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
    input wire [3:0] pwm_o,
    input wire irq
);

    simple_pwm3_regs simple_pwm3_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_pwm3_counter simple_pwm3_counter_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_pwm3_compare simple_pwm3_compare_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_pwm3_irq simple_pwm3_irq_u (
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule

`default_nettype wire
