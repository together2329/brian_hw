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
    logic active_q;
    logic [12:0] remaining_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] next_addr_q;
    logic [`MCTP_ASSEMBLER_SCRATCH_AXI_DATA_WIDTH-1:0] data_q;
    logic [4:0] write_lane;
    logic [8:0] write_shift_bits;
    logic [12:0] emit_bytes;
    logic can_emit;

    assign write_lane = payload_write_addr[4:0];
    assign write_shift_bits = {1'b0, write_lane, 3'd0};
    assign emit_bytes = (payload_write_bytes >= 13'd32) ? 13'd32 : payload_write_bytes;
    assign can_emit = (~sram_wr_valid) | sram_wr_ready;

    function automatic [31:0] strobe_for_bytes(input logic [12:0] byte_count);
        begin
            if (byte_count >= 13'd32) begin
                strobe_for_bytes = 32'hffff_ffff;
            end else if (byte_count == 13'd0) begin
                strobe_for_bytes = 32'd0;
            end else begin
                strobe_for_bytes = (32'h0000_0001 << byte_count[4:0]) - 32'd1;
            end
        end
    endfunction

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
                    sram_wr_strb <= strobe_for_bytes(remaining_q);
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
                    sram_wr_addr <= {payload_write_addr[15:5], 5'd0};
                    sram_wr_data <= payload_write_data << write_shift_bits;
                    sram_wr_strb <= (payload_write_bytes >= 13'd32) ?
                        (32'hffff_ffff << write_lane) : ((payload_write_strb << write_lane) & 32'hffff_ffff);
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
