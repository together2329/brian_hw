`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_sram_packer (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             payload_write_valid,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] payload_write_data,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_AXI_STRB_WIDTH-1:0] payload_write_strb,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] payload_write_addr,
    input  logic [12:0]                                      payload_write_bytes,
    output logic                                             sram_wr_valid,
    input  logic                                             sram_wr_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_wr_addr,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_wr_data,
    output logic [31:0]                                      sram_wr_strb,
    output logic [4:0]                                       pack_next_lane,
    output logic                                             pack_partial_valid
);
    logic [4:0] write_lane;
    logic [8:0] write_shift_bits;
    logic unused_inputs;

    assign write_lane = payload_write_addr[4:0];
    assign write_shift_bits = {1'b0, write_lane, 3'd0};
    assign unused_inputs = ^payload_write_bytes;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            sram_wr_valid <= 1'b0;
            sram_wr_addr <= 16'd0;
            sram_wr_data <= 256'd0;
            sram_wr_strb <= 32'd0;
            pack_next_lane <= 5'd0;
            pack_partial_valid <= 1'b0;
        end else begin
            if (sram_wr_valid & sram_wr_ready) begin
                sram_wr_valid <= 1'b0;
            end
            if (payload_write_valid & (~sram_wr_valid | sram_wr_ready)) begin
                sram_wr_valid <= 1'b1;
                sram_wr_addr <= {payload_write_addr[15:5], 5'd0};
                sram_wr_data <= payload_write_data << write_shift_bits;
                sram_wr_strb <= (payload_write_strb << write_lane) | {31'd0, unused_inputs & 1'b0};
                pack_next_lane <= write_lane + payload_write_bytes[4:0];
                pack_partial_valid <= |payload_write_bytes[4:0];
            end
        end
    end
endmodule
