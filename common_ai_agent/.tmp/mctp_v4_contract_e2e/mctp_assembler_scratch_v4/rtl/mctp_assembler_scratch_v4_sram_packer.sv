`include "mctp_assembler_scratch_v4_param.vh"

module mctp_assembler_scratch_v4_sram_packer (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             payload_write_valid,
    output wire                                             payload_write_ready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_write_data,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_write_strb,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_write_addr,
    input  wire [12:0]                                      payload_write_bytes,
    output reg                                             sram_wr_valid,
    input  wire                                             sram_wr_ready,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_wr_addr,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_wr_data,
    output reg [31:0]                                      sram_wr_strb,
    output reg [4:0]                                       pack_next_lane,
    output reg                                             pack_partial_valid
);
    reg active_q;
    reg [12:0] remaining_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q;
    reg [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] data_q;
    wire [4:0] write_lane;
    wire [12:0] emit_bytes;
    wire [31:0] remaining_strobe;
    wire can_emit;

    assign write_lane = payload_write_addr[4:0];
    assign emit_bytes = (payload_write_bytes >= 13'd32) ? 13'd32 : payload_write_bytes;
    assign can_emit = (~sram_wr_valid) | sram_wr_ready;
    assign payload_write_ready = can_emit & (~active_q);
    assign remaining_strobe = (remaining_q >= 13'd32) ? 32'hffff_ffff :
        ((remaining_q == 13'd0) ? 32'd0 : ((32'h0000_0001 << remaining_q[4:0]) - 32'd1));

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            active_q <= 1'b0;
            remaining_q <= 13'd0;
            next_addr_q <= 16'd0;
            data_q <= 256'd0;
            sram_wr_valid <= 1'b0;
            sram_wr_addr <= 16'd0;
            sram_wr_data <= 256'd0;
            sram_wr_strb <= 32'd0;
            pack_next_lane <= 5'd0;
            pack_partial_valid <= 1'b0;
        end else begin
            if (can_emit) begin
                sram_wr_valid <= 1'b0;
                if (active_q) begin
                    sram_wr_valid <= 1'b1;
                    sram_wr_addr <= next_addr_q;
                    sram_wr_data <= data_q;
                    sram_wr_strb <= remaining_strobe;
                    pack_next_lane <= next_addr_q[4:0] + remaining_q[4:0];
                    pack_partial_valid <= |(next_addr_q[4:0] + remaining_q[4:0]);
                    if (remaining_q <= 13'd32) begin
                        active_q <= 1'b0;
                        remaining_q <= 13'd0;
                    end else begin
                        remaining_q <= remaining_q - 13'd32;
                        next_addr_q <= next_addr_q + 16'd32;
                    end
                end else if (payload_write_valid) begin
                    sram_wr_valid <= 1'b1;
                    sram_wr_addr <= payload_write_addr;
                    sram_wr_data <= payload_write_data;
                    sram_wr_strb <= payload_write_strb;
                    pack_next_lane <= write_lane + payload_write_bytes[4:0];
                    pack_partial_valid <= |(write_lane + payload_write_bytes[4:0]);
                    if (payload_write_bytes > emit_bytes) begin
                        active_q <= 1'b1;
                        remaining_q <= payload_write_bytes - emit_bytes;
                        next_addr_q <= {payload_write_addr[15:5], 5'd0} + 16'd32;
                        data_q <= payload_write_data;
                    end
                end
            end
        end
    end
endmodule
