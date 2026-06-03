`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_sram_arbiter (
    input  wire                                             axi_aclk,
    input  wire                                             axi_aresetn,
    input  wire                                             pack_wr_valid,
    output wire                                             pack_wr_ready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] pack_wr_addr,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] pack_wr_data,
    input  wire [31:0]                                      pack_wr_strb,
    input  wire                                             rd_req_valid,
    output wire                                             rd_req_ready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] rd_req_addr,
    output reg                                             rd_rsp_valid,
    input  wire                                             rd_rsp_ready,
    output reg [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] rd_rsp_data,
    output reg                                             rd_rsp_error,
    output wire                                             sram_wr_valid,
    input  wire                                             sram_wr_ready,
    output wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_wr_addr,
    output wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_wr_data,
    output wire [31:0]                                      sram_wr_strb,
    output wire                                             sram_rd_req_valid,
    input  wire                                             sram_rd_req_ready,
    output wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_rd_req_addr,
    input  wire                                             sram_rd_rsp_valid,
    output reg                                             sram_rd_rsp_ready,
    input  wire [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_rd_rsp_data,
    input  wire                                             sram_rd_rsp_error
);
    reg read_rsp_wait_q;
    wire unused_inputs;

    assign unused_inputs = ^{axi_aclk, axi_aresetn};
    assign sram_wr_valid = pack_wr_valid;
    assign pack_wr_ready = sram_wr_ready;
    assign sram_wr_addr = pack_wr_addr;
    assign sram_wr_data = pack_wr_data;
    assign sram_wr_strb = pack_wr_strb | {31'd0, unused_inputs & 1'b0};
    assign sram_rd_req_valid = rd_req_valid & (~pack_wr_valid);
    assign rd_req_ready = sram_rd_req_ready & (~pack_wr_valid);
    assign sram_rd_req_addr = rd_req_addr;

    always @(posedge axi_aclk or negedge axi_aresetn) begin
        if (!axi_aresetn) begin
            read_rsp_wait_q <= 1'b0;
            rd_rsp_valid <= 1'b0;
            sram_rd_rsp_ready <= 1'b0;
            rd_rsp_data <= 256'd0;
            rd_rsp_error <= 1'b0;
        end else begin
            sram_rd_rsp_ready <= (~rd_rsp_valid) | rd_rsp_ready;
            if (rd_req_valid & rd_req_ready) begin
                read_rsp_wait_q <= 1'b1;
            end
            if (rd_rsp_valid & rd_rsp_ready) begin
                rd_rsp_valid <= 1'b0;
            end
            if (sram_rd_rsp_valid & sram_rd_rsp_ready) begin
                read_rsp_wait_q <= 1'b0;
                rd_rsp_valid <= read_rsp_wait_q | sram_rd_rsp_valid;
                rd_rsp_data <= sram_rd_rsp_data;
                rd_rsp_error <= sram_rd_rsp_error;
            end
        end
    end
endmodule
