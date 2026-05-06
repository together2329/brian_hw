`default_nettype none

module simple_uart3 (
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
    input wire rx,
    input wire tx,
    input wire irq
);

    simple_uart3_regs simple_uart3_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_uart3_baud simple_uart3_baud_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_uart3_rx simple_uart3_rx_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_uart3_tx simple_uart3_tx_u (
        .clk(clk),
        .rst_n(rst_n)
    );

endmodule

`default_nettype wire
