`default_nettype none

module qa_visible_09182 (
    input wire clk,
    input wire rst_n,
    input wire [5:0] paddr,
    input wire psel,
    input wire penable,
    input wire pwrite,
    input wire [31:0] pwdata,
    input wire [3:0] pstrb,
    output reg [31:0] prdata,
    output reg pready,
    output reg pslverr,
    input wire [15:0] gpio_i,
    output reg [15:0] gpio_o,
    output reg [15:0] gpio_oe,
    output reg irq
);

    reg [7:0] heartbeat_q;

    qa_visible_09182_regs qa_visible_09182_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    qa_visible_09182_core qa_visible_09182_core_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    qa_visible_09182_irq qa_visible_09182_irq_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    qa_visible_09182_wrapper qa_visible_09182_wrapper_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            heartbeat_q <= 8'd0;
            prdata <= 32'd0;
            pready <= 1'b0;
            pslverr <= 1'b0;
            gpio_o <= 16'd0;
            gpio_oe <= 16'd0;
            irq <= 1'b0;
        end else begin
            heartbeat_q <= heartbeat_q + 8'd1;
            prdata <= {4{heartbeat_q}};
            pready <= heartbeat_q[0];
            pslverr <= heartbeat_q[0];
            gpio_o <= {2{heartbeat_q}};
            gpio_oe <= {2{heartbeat_q}};
            irq <= heartbeat_q[0];
        end
    end

endmodule

`default_nettype wire
