`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Filter and decode PCIe VDM header fields for MCTP-over-PCIe-VDM.
module mctp_assembler_pcie_vdm_parser (
  input  logic        tlp_valid,
  input  logic [15:0] tlp_byte_count,
  input  logic [7:0]  tlp_byte0,
  input  logic [7:0]  tlp_byte1,
  input  logic [7:0]  tlp_byte2,
  input  logic [7:0]  tlp_byte3,
  input  logic [7:0]  tlp_byte4,
  input  logic [7:0]  tlp_byte5,
  input  logic [7:0]  tlp_byte6,
  input  logic [7:0]  tlp_byte7,
  input  logic [7:0]  tlp_byte8,
  input  logic [7:0]  tlp_byte9,
  input  logic [7:0]  tlp_byte10,
  input  logic [7:0]  tlp_byte11,
  output logic        vdm_valid,
  output logic        vdm_malformed_tlp,
  output logic        vdm_unsupported,
  output logic        vdm_bad_vendor,
  output logic        vdm_bad_message_code,
  output logic        vdm_bad_mctp_vdm_code,
  output logic [1:0]  vdm_pad_len,
  output logic [15:0] vdm_requester_id,
  output logic [15:0] vdm_target_id,
  output logic [15:0] vdm_vendor_id,
  output logic [2:0]  vdm_routing
);
  wire [7:0] fmt_type = tlp_byte0;
  wire [7:0] tag_byte = tlp_byte6;
  wire [7:0] message_code = tlp_byte7;
  wire [15:0] requester_id = {tlp_byte4, tlp_byte5};
  wire [15:0] target_id = {tlp_byte8, tlp_byte9};
  wire [15:0] vendor_id = {tlp_byte10, tlp_byte11};
  wire [3:0] mctp_vdm_code = tag_byte[3:0];
  wire [1:0] pad_len = tag_byte[5:4];
  wire hdr_prefix_ok = (tlp_byte1 == 8'd0) && (tlp_byte2 == 8'd0) && (tlp_byte3 == 8'd0);
  wire tag_rsv_ok = (tag_byte[7:6] == 2'd0);
  wire fmt_ok = ((fmt_type & 8'h70) == 8'h70) && hdr_prefix_ok && tag_rsv_ok;

  assign vdm_malformed_tlp = tlp_valid && (tlp_byte_count < 16'd16);
  assign vdm_bad_message_code = tlp_valid && fmt_ok && (message_code != `MCTP_ASSEMBLER_MSG_CODE_VDM);
  assign vdm_bad_vendor = tlp_valid && fmt_ok && (vendor_id != `MCTP_ASSEMBLER_VENDOR_ID_DMTF);
  assign vdm_bad_mctp_vdm_code = tlp_valid && fmt_ok && (mctp_vdm_code != 4'd0);
  assign vdm_unsupported = tlp_valid && !fmt_ok;
  assign vdm_valid = tlp_valid &&
                     (tlp_byte_count >= 16'd16) &&
                     fmt_ok &&
                     (message_code == `MCTP_ASSEMBLER_MSG_CODE_VDM) &&
                     (vendor_id == `MCTP_ASSEMBLER_VENDOR_ID_DMTF) &&
                     (mctp_vdm_code == 4'd0);

  assign vdm_pad_len = pad_len;
  assign vdm_requester_id = requester_id;
  assign vdm_target_id = target_id;
  assign vdm_vendor_id = vendor_id;
  assign vdm_routing = fmt_type[2:0];
endmodule
