`default_nettype none

module simple_cpu (
    input wire clk,
    input wire rst_n,
    output reg [15:0] m_addr,
    output reg [31:0] m_wdata,
    input wire [31:0] m_rdata,
    output reg m_valid,
    output reg m_write,
    input wire m_ready
);

    reg [7:0] heartbeat_q;

    simple_cpu_fetch simple_cpu_fetch_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_cpu_decode simple_cpu_decode_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    simple_cpu_core simple_cpu_core_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            heartbeat_q <= 8'd0;
            m_addr <= 16'd0;
            m_wdata <= 32'd0;
            m_valid <= 1'b0;
            m_write <= 1'b0;
        end else begin
            heartbeat_q <= heartbeat_q + 8'd1;
            m_addr <= {2{heartbeat_q}};
            m_wdata <= {4{heartbeat_q}};
            m_valid <= heartbeat_q[0];
            m_write <= heartbeat_q[0];
        end
    end

endmodule

`default_nettype wire
