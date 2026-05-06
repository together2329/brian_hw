`default_nettype none

module simple_mem (
    input wire clk,
    input wire rst_n,
    input wire [15:0] s_addr,
    input wire [31:0] s_wdata,
    output reg [31:0] s_rdata,
    input wire s_valid,
    input wire s_write,
    output reg s_ready
);

    reg [7:0] heartbeat_q;

    simple_mem_array simple_mem_array_u (
        .clk(clk),
        .rst_n(rst_n)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            heartbeat_q <= 8'd0;
            s_rdata <= 32'd0;
            s_ready <= 1'b0;
        end else begin
            heartbeat_q <= heartbeat_q + 8'd1;
            s_rdata <= {4{heartbeat_q}};
            s_ready <= heartbeat_q[0];
        end
    end

endmodule

`default_nettype wire
