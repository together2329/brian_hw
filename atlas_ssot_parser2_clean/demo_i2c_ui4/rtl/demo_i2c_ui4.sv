`default_nettype none

module demo_i2c_ui4 (
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
    output reg scl,
    input wire scl_i,
    output reg sda,
    input wire sda_i,
    output reg irq
);

    reg [7:0] heartbeat_q;

    demo_i2c_ui4_regs demo_i2c_ui4_regs_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    demo_i2c_ui4_bit_ctrl demo_i2c_ui4_bit_ctrl_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    demo_i2c_ui4_byte_ctrl demo_i2c_ui4_byte_ctrl_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    demo_i2c_ui4_fifo demo_i2c_ui4_fifo_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    demo_i2c_ui4_core demo_i2c_ui4_core_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    demo_i2c_ui4_wrapper demo_i2c_ui4_wrapper_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            heartbeat_q <= 8'd0;
            prdata <= 32'd0;
            pready <= 1'b0;
            pslverr <= 1'b0;
            scl <= 1'b0;
            sda <= 1'b0;
            irq <= 1'b0;
        end else begin
            heartbeat_q <= heartbeat_q + 8'd1;
            prdata <= {4{heartbeat_q}};
            pready <= heartbeat_q[0];
            pslverr <= heartbeat_q[0];
            scl <= heartbeat_q[0];
            sda <= heartbeat_q[0];
            irq <= heartbeat_q[0];
        end
    end

endmodule

`default_nettype wire
