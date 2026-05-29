`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Parse MCTP transport header and compute payload bounds.
module mctp_assembler_mctp_parser (
  input  logic        vdm_valid,
  input  logic [1:0]  vdm_pad_len,
  input  logic [15:0] tlp_byte_count,
  input  logic [7:0]  tlp_byte12,
  input  logic [7:0]  tlp_byte13,
  input  logic [7:0]  tlp_byte14,
  input  logic [7:0]  tlp_byte15,
  input  logic [7:0]  local_eid,
  input  logic        dest_filter_enable,
  input  logic        accept_broadcast_eid,
  input  logic        accept_null_eid,
  output logic        mctp_valid,
  output logic        mctp_bad_hdr,
  output logic        mctp_bad_pad,
  output logic        mctp_dest_reject,
  output logic [7:0]  mctp_dest_eid,
  output logic [7:0]  mctp_source_eid,
  output logic        mctp_som,
  output logic        mctp_eom,
  output logic [1:0]  mctp_seq,
  output logic        mctp_tag_owner,
  output logic [2:0]  mctp_message_tag,
  output logic [15:0] mctp_payload_byte_count
);
  wire [3:0] hdr_version = tlp_byte12[3:0];
  wire [7:0] dest_eid = tlp_byte13;
  wire [7:0] source_eid = tlp_byte14;
  wire [7:0] flags = tlp_byte15;
  wire som = flags[7];
  wire eom = flags[6];
  wire [1:0] seq = flags[5:4];
  wire tag_owner = flags[3];
  wire [2:0] message_tag = flags[2:0];
  wire [15:0] raw_payload_bytes = (tlp_byte_count >= 16'd16) ? (tlp_byte_count - 16'd16) : 16'd0;
  wire [15:0] trimmed_payload_bytes = (raw_payload_bytes >= {14'd0, vdm_pad_len}) ?
                                      (raw_payload_bytes - {14'd0, vdm_pad_len}) : 16'd0;
  wire dest_local_ok = (dest_eid == local_eid);
  wire dest_bcast_ok = accept_broadcast_eid && (dest_eid == 8'hFF);
  wire dest_null_ok = accept_null_eid && (dest_eid == 8'h00);
  wire dest_ok = !dest_filter_enable || dest_local_ok || dest_bcast_ok || dest_null_ok;

  assign mctp_bad_hdr = vdm_valid &&
                        ((hdr_version != `MCTP_ASSEMBLER_MCTP_HDR_VERSION) || (tlp_byte12[7:4] != 4'd0));
  assign mctp_bad_pad = vdm_valid &&
                        (((vdm_pad_len != 2'd0) && !eom) ||
                         (raw_payload_bytes < {14'd0, vdm_pad_len}));
  assign mctp_dest_reject = vdm_valid && !mctp_bad_hdr && !mctp_bad_pad && !dest_ok;
  assign mctp_valid = vdm_valid && !mctp_bad_hdr && !mctp_bad_pad && dest_ok && (trimmed_payload_bytes != 16'd0 || (som && eom));
  assign mctp_dest_eid = dest_eid;
  assign mctp_source_eid = source_eid;
  assign mctp_som = som;
  assign mctp_eom = eom;
  assign mctp_seq = seq;
  assign mctp_tag_owner = tag_owner;
  assign mctp_message_tag = message_tag;
  assign mctp_payload_byte_count = trimmed_payload_bytes;
endmodule
