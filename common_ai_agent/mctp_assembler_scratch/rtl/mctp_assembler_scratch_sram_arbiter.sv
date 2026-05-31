`include "mctp_assembler_scratch_param.vh"

module mctp_assembler_scratch_sram_arbiter (
    input  logic                                             axi_aclk,
    input  logic                                             axi_aresetn,
    input  logic                                             pack_wr_valid,
    output logic                                             pack_wr_ready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] pack_wr_addr,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] pack_wr_data,
    input  logic [31:0]                                      pack_wr_strb,
    input  logic                                             rd_req_valid,
    output logic                                             rd_req_ready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] rd_req_addr,
    output logic                                             rd_rsp_valid,
    input  logic                                             rd_rsp_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] rd_rsp_data,
    output logic                                             rd_rsp_error,
    output logic                                             sram_wr_valid,
    input  logic                                             sram_wr_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_wr_addr,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_wr_data,
    output logic [31:0]                                      sram_wr_strb,
    output logic                                             sram_rd_req_valid,
    input  logic                                             sram_rd_req_ready,
    output logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_ADDR_WIDTH-1:0] sram_rd_req_addr,
    input  logic                                             sram_rd_rsp_valid,
    output logic                                             sram_rd_rsp_ready,
    input  logic [`MCTP_ASSEMBLER_SCRATCH_SRAM_DATA_WIDTH-1:0] sram_rd_rsp_data,
    input  logic                                             sram_rd_rsp_error
);
    logic unused_inputs;

    assign unused_inputs = ^{axi_aclk, axi_aresetn};
    assign sram_wr_valid = pack_wr_valid;
    assign pack_wr_ready = sram_wr_ready;
    assign sram_wr_addr = pack_wr_addr;
    assign sram_wr_data = pack_wr_data;
    assign sram_wr_strb = pack_wr_strb | {31'd0, unused_inputs & 1'b0};
    assign sram_rd_req_valid = rd_req_valid & (~pack_wr_valid);
    assign rd_req_ready = sram_rd_req_ready & (~pack_wr_valid);
    assign sram_rd_req_addr = rd_req_addr;
    assign rd_rsp_valid = sram_rd_rsp_valid;
    assign sram_rd_rsp_ready = rd_rsp_ready;
    assign rd_rsp_data = sram_rd_rsp_data;
    assign rd_rsp_error = sram_rd_rsp_error;
endmodule
