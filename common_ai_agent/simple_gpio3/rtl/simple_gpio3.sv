`default_nettype none

module simple_gpio3 (
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
    input wire [15:0] gpio_i,
    input wire [15:0] gpio_o,
    input wire [15:0] gpio_oe,
    input wire irq
);

    simple_gpio3_regs simple_gpio3_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_gpio3_pins simple_gpio3_pins_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_gpio3_irq simple_gpio3_irq_u (
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule

`default_nettype wire
