`default_nettype none

module simple_bus (
    input wire clk,
    input wire rst_n,
    input wire [15:0] s_addr,
    input wire [31:0] s_wdata,
    output reg [31:0] s_rdata,
    input wire s_valid,
    input wire s_write,
    output reg s_ready,
    output reg [15:0] m_addr,
    output reg [31:0] m_wdata,
    input wire [31:0] m_rdata,
    output reg m_valid,
    output reg m_write,
    input wire m_ready
);

    reg [7:0] heartbeat_q;

    simple_bus_route simple_bus_route_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            heartbeat_q <= 8'd0;
            s_rdata <= 32'd0;
            s_ready <= 1'b0;
            m_addr <= 16'd0;
            m_wdata <= 32'd0;
            m_valid <= 1'b0;
            m_write <= 1'b0;
        end else begin
            heartbeat_q <= heartbeat_q + 8'd1;
            s_rdata <= {4{heartbeat_q}};
            s_ready <= heartbeat_q[0];
            m_addr <= {2{heartbeat_q}};
            m_wdata <= {4{heartbeat_q}};
            m_valid <= heartbeat_q[0];
            m_write <= heartbeat_q[0];
        end
    end

endmodule

`default_nettype wire
