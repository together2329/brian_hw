`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// APB control, status, descriptor, interrupt, and counter register block.
module mctp_assembler_apb_regfile #(
  parameter integer APB_ADDR_WIDTH = `MCTP_ASSEMBLER_APB_ADDR_WIDTH
) (
  input  logic                        pclk,
  input  logic                        presetn,
  input  logic                        psel,
  input  logic                        penable,
  input  logic                        pwrite,
  input  logic [APB_ADDR_WIDTH-1:0]   paddr,
  input  logic [31:0]                   pwdata,
  input  logic [3:0]                    pstrb,
  output logic [31:0]                   prdata,
  output logic                        pready,
  output logic                        pslverr,
  output logic                        intr,
  output logic                        cfg_enable_apb,
  output logic                        cfg_drop_when_disabled_apb,
  output logic                        cfg_dest_filter_enable_apb,
  output logic                        cfg_accept_broadcast_apb,
  output logic                        cfg_accept_null_apb,
  output logic                        cfg_soft_reset_apb,
  output logic [7:0]                  cfg_local_eid_apb,
  output logic [15:0]                 cfg_max_message_bytes_apb,
  output logic [15:0]                 cfg_mtu_bytes_apb,
  output logic [23:0]                 cfg_timeout_cycles_apb,
  output logic [15:0]                 cfg_sram_base_apb,
  output logic [15:0]                 cfg_sram_limit_apb,
  input  logic                        ingress_busy,
  input  logic                        context_active_any,
  input  logic [3:0]                  active_context_count,
  input  logic [3:0]                  desc_fifo_count,
  input  logic                        desc_fifo_full,
  input  logic [31:0]                 desc_word0,
  input  logic [31:0]                 desc_word1,
  input  logic [31:0]                 desc_word2,
  input  logic [31:0]                 desc_word3,
  output logic                        desc_pop_apb,
  input  logic [15:0]                 sram_wr_ptr_shadow,
  input  logic                        evt_desc_ready_apb,
  input  logic                        evt_packet_drop_apb,
  input  logic                        evt_assembly_drop_apb,
  input  logic                        evt_malformed_tlp,
  input  logic                        evt_unsupported_vdm,
  input  logic                        evt_bad_mctp_hdr,
  input  logic                        evt_dest_reject,
  input  logic                        evt_sequence_error,
  input  logic                        evt_context_error,
  input  logic                        evt_overflow_error,
  input  logic                        evt_unexpected_fragment,
  input  logic                        evt_duplicate_som,
  input  logic                        evt_seq_mismatch,
  input  logic                        cfg_timeout_armed
);
  localparam [11:0] A_CONTROL = 12'h000;
  localparam [11:0] A_STATUS = 12'h004;
  localparam [11:0] A_LOCAL_EID = 12'h008;
  localparam [11:0] A_MTU_TIMEOUT = 12'h00C;
  localparam [11:0] A_MAX_MSG = 12'h010;
  localparam [11:0] A_SRAM_BASE = 12'h014;
  localparam [11:0] A_SRAM_LIMIT = 12'h018;
  localparam [11:0] A_SRAM_WR_PTR = 12'h01C;
  localparam [11:0] A_INTR_ENABLE = 12'h020;
  localparam [11:0] A_INTR_STATUS = 12'h024;
  localparam [11:0] A_ERROR_STATUS = 12'h028;
  localparam [11:0] A_DROP_STATUS = 12'h02C;
  localparam [11:0] A_DESC_STATUS = 12'h030;
  localparam [11:0] A_DESC_POP = 12'h034;
  localparam [11:0] A_DESC_WORD0 = 12'h038;
  localparam [11:0] A_DESC_WORD1 = 12'h03C;
  localparam [11:0] A_DESC_WORD2 = 12'h040;
  localparam [11:0] A_DESC_WORD3 = 12'h044;
  localparam [11:0] A_PACKET_DROP_COUNT = 12'h118;
  localparam [11:0] A_ASSEMBLY_DROP_COUNT = 12'h11C;

  logic [31:0] reg_control;
  logic [31:0] reg_local_eid;
  logic [31:0] reg_mtu_timeout;
  logic [31:0] reg_max_msg;
  logic [31:0] reg_sram_base;
  logic [31:0] reg_sram_limit;
  logic [31:0] reg_intr_enable;
  logic [31:0] reg_intr_status;
  logic [31:0] reg_error_status;
  logic [31:0] reg_drop_status;
  logic [31:0] reg_packet_drop_count;
  logic [31:0] reg_assembly_drop_count;

  wire access = psel && penable;
  wire write_xfer = access && pwrite;
  wire read_xfer = access && !pwrite;
  wire [11:0] addr = paddr[11:0];

  assign pready = 1'b1;
  assign pslverr = access && !(
      (addr == A_CONTROL) || (addr == A_STATUS) || (addr == A_LOCAL_EID) ||
      (addr == A_MTU_TIMEOUT) || (addr == A_MAX_MSG) || (addr == A_SRAM_BASE) ||
      (addr == A_SRAM_LIMIT) || (addr == A_SRAM_WR_PTR) || (addr == A_INTR_ENABLE) ||
      (addr == A_INTR_STATUS) || (addr == A_ERROR_STATUS) || (addr == A_DROP_STATUS) ||
      (addr == A_DESC_STATUS) || (addr == A_DESC_POP) || (addr == A_DESC_WORD0) ||
      (addr == A_DESC_WORD1) || (addr == A_DESC_WORD2) || (addr == A_DESC_WORD3) ||
      (addr == A_PACKET_DROP_COUNT) || (addr == A_ASSEMBLY_DROP_COUNT));

  assign cfg_enable_apb = reg_control[0];
  assign cfg_soft_reset_apb = reg_control[1];
  assign cfg_dest_filter_enable_apb = reg_control[2];
  assign cfg_drop_when_disabled_apb = reg_control[3];
  assign cfg_accept_broadcast_apb = reg_control[4];
  assign cfg_accept_null_apb = reg_control[5];
  assign cfg_local_eid_apb = reg_local_eid[7:0];
  assign cfg_mtu_bytes_apb = reg_mtu_timeout[15:0];
  assign cfg_timeout_cycles_apb = {8'd0, reg_mtu_timeout[31:16]};
  assign cfg_max_message_bytes_apb = reg_max_msg[15:0];
  assign cfg_sram_base_apb = reg_sram_base[15:0];
  assign cfg_sram_limit_apb = reg_sram_limit[15:0];
  assign desc_pop_apb = write_xfer && (addr == A_DESC_POP) && pwdata[0] && (&pstrb[3:0]);

  wire [31:0] status_read = {
      1'b0,
      21'd0,
      cfg_timeout_armed,
      active_context_count,
      desc_fifo_full,
      (desc_fifo_count != 4'd0),
      (|reg_error_status),
      context_active_any,
      ingress_busy
  };
  wire [31:0] desc_status_read = {
      25'd0,
      (desc_fifo_count == 4'd0),
      desc_fifo_full,
      1'b0,
      desc_fifo_count
  };

  assign intr = |(reg_intr_status & reg_intr_enable);

  always @(*) begin
    prdata = 32'd0;
    if (read_xfer) begin
      case (addr)
        A_CONTROL: prdata = reg_control;
        A_STATUS: prdata = status_read;
        A_LOCAL_EID: prdata = reg_local_eid;
        A_MTU_TIMEOUT: prdata = reg_mtu_timeout;
        A_MAX_MSG: prdata = reg_max_msg;
        A_SRAM_BASE: prdata = reg_sram_base;
        A_SRAM_LIMIT: prdata = reg_sram_limit;
        A_SRAM_WR_PTR: prdata = {16'd0, sram_wr_ptr_shadow};
        A_INTR_ENABLE: prdata = reg_intr_enable;
        A_INTR_STATUS: prdata = reg_intr_status;
        A_ERROR_STATUS: prdata = reg_error_status;
        A_DROP_STATUS: prdata = reg_drop_status;
        A_DESC_STATUS: prdata = desc_status_read;
        A_DESC_WORD0: prdata = desc_word0;
        A_DESC_WORD1: prdata = desc_word1;
        A_DESC_WORD2: prdata = desc_word2;
        A_DESC_WORD3: prdata = desc_word3;
        A_PACKET_DROP_COUNT: prdata = reg_packet_drop_count;
        A_ASSEMBLY_DROP_COUNT: prdata = reg_assembly_drop_count;
        default: prdata = 32'd0;
      endcase
    end
  end

  always @(posedge pclk) begin
    if (!presetn) begin
      reg_control <= 32'h0000_0004;
      reg_local_eid <= 32'd0;
      reg_mtu_timeout <= 32'h0000_0040;
      reg_max_msg <= 32'd4096;
      reg_sram_base <= 32'd0;
      reg_sram_limit <= 32'h0000_FFFF;
      reg_intr_enable <= 32'd0;
      reg_intr_status <= 32'd0;
      reg_error_status <= 32'd0;
      reg_drop_status <= 32'd0;
      reg_packet_drop_count <= 32'd0;
      reg_assembly_drop_count <= 32'd0;
    end else begin
      if (write_xfer && (addr == A_CONTROL)) begin
        reg_control <= (reg_control & ~32'h0000_003F) | (pwdata & 32'h0000_003F);
        if (pwdata[1]) begin
          reg_control[1] <= 1'b0;
        end
      end
      if (write_xfer && (addr == A_LOCAL_EID)) reg_local_eid <= pwdata;
      if (write_xfer && (addr == A_MTU_TIMEOUT)) reg_mtu_timeout <= pwdata;
      if (write_xfer && (addr == A_MAX_MSG)) reg_max_msg <= pwdata;
      if (write_xfer && (addr == A_SRAM_BASE)) reg_sram_base <= pwdata;
      if (write_xfer && (addr == A_SRAM_LIMIT)) reg_sram_limit <= pwdata;
      if (write_xfer && (addr == A_INTR_ENABLE)) reg_intr_enable <= pwdata;
      if (write_xfer && (addr == A_INTR_STATUS)) reg_intr_status <= reg_intr_status & ~pwdata;
      if (write_xfer && (addr == A_ERROR_STATUS)) reg_error_status <= reg_error_status & ~pwdata;

      if (evt_desc_ready_apb) reg_intr_status[0] <= 1'b1;
      if (evt_malformed_tlp) begin reg_intr_status[1] <= 1'b1; reg_error_status[0] <= 1'b1; end
      if (evt_unsupported_vdm) begin reg_intr_status[2] <= 1'b1; reg_error_status[1] <= 1'b1; end
      if (evt_bad_mctp_hdr) begin reg_intr_status[3] <= 1'b1; reg_error_status[4] <= 1'b1; end
      if (evt_dest_reject) begin reg_intr_status[4] <= 1'b1; reg_error_status[0] <= 1'b1; end
      if (evt_sequence_error) reg_intr_status[5] <= 1'b1;
      if (evt_context_error) begin reg_intr_status[6] <= 1'b1; reg_error_status[8] <= 1'b1; end
      if (evt_overflow_error) begin reg_intr_status[7] <= 1'b1; reg_error_status[9] <= 1'b1; end
      if (evt_unexpected_fragment) reg_error_status[5] <= 1'b1;
      if (evt_duplicate_som) reg_error_status[6] <= 1'b1;
      if (evt_seq_mismatch) reg_error_status[7] <= 1'b1;
      if (evt_packet_drop_apb) begin
        reg_intr_status[9] <= 1'b1;
        reg_error_status[13] <= 1'b1;
        reg_drop_status <= {reg_drop_status[31:6], 2'd1, reg_drop_status[3:0]};
        reg_packet_drop_count <= reg_packet_drop_count + 32'd1;
      end
      if (evt_assembly_drop_apb) begin
        reg_intr_status[10] <= 1'b1;
        reg_error_status[14] <= 1'b1;
        reg_drop_status <= {reg_drop_status[31:6], 2'd2, reg_drop_status[3:0]};
        reg_assembly_drop_count <= reg_assembly_drop_count + 32'd1;
      end
    end
  end
endmodule
