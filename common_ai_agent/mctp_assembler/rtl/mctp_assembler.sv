`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Top-level mctp_assembler integration (SSOT wiring-only top).
module mctp_assembler #(
  parameter integer AXI_ADDR_WIDTH = `MCTP_ASSEMBLER_AXI_ADDR_WIDTH,
  parameter integer AXI_DATA_WIDTH = `MCTP_ASSEMBLER_AXI_DATA_WIDTH,
  parameter integer APB_ADDR_WIDTH = `MCTP_ASSEMBLER_APB_ADDR_WIDTH,
  parameter integer APB_DATA_WIDTH = `MCTP_ASSEMBLER_APB_DATA_WIDTH,
  parameter integer SRAM_ADDR_WIDTH = `MCTP_ASSEMBLER_SRAM_ADDR_WIDTH,
  parameter integer SRAM_DATA_WIDTH = `MCTP_ASSEMBLER_SRAM_DATA_WIDTH,
  parameter integer CONTEXT_COUNT = `MCTP_ASSEMBLER_CONTEXT_COUNT
) (
  input  logic                        axi_aclk,
  input  logic                        axi_aresetn,
  input  logic                        pclk,
  input  logic                        presetn,
  input  logic [AXI_ADDR_WIDTH-1:0]   s_axi_awaddr,
  input  logic [7:0]                  s_axi_awlen,
  input  logic [2:0]                  s_axi_awsize,
  input  logic [1:0]                  s_axi_awburst,
  input  logic                        s_axi_awvalid,
  output logic                        s_axi_awready,
  input  logic [AXI_DATA_WIDTH-1:0]   s_axi_wdata,
  input  logic [AXI_DATA_WIDTH/8-1:0] s_axi_wstrb,
  input  logic                        s_axi_wlast,
  input  logic                        s_axi_wvalid,
  output logic                        s_axi_wready,
  output logic [1:0]                  s_axi_bresp,
  output logic                        s_axi_bvalid,
  input  logic                        s_axi_bready,
  input  logic [APB_ADDR_WIDTH-1:0]   paddr,
  input  logic                        psel,
  input  logic                        penable,
  input  logic                        pwrite,
  input  logic [APB_DATA_WIDTH-1:0]   pwdata,
  input  logic [APB_DATA_WIDTH/8-1:0] pstrb,
  output logic [APB_DATA_WIDTH-1:0]   prdata,
  output logic                        pready,
  output logic                        pslverr,
  output logic                        sram_wr_valid,
  input  logic                        sram_wr_ready,
  output logic [SRAM_ADDR_WIDTH-1:0]  sram_wr_addr,
  output logic [SRAM_DATA_WIDTH-1:0]  sram_wr_data,
  output logic [SRAM_DATA_WIDTH/8-1:0] sram_wr_strb,
  output logic                        intr
);
  logic tlp_valid;
  logic tlp_ready;
  logic [15:0] tlp_byte_count;
  logic [7:0] tlp_byte0;
  logic [7:0] tlp_byte1;
  logic [7:0] tlp_byte2;
  logic [7:0] tlp_byte3;
  logic [7:0] tlp_byte4;
  logic [7:0] tlp_byte5;
  logic [7:0] tlp_byte6;
  logic [7:0] tlp_byte7;
  logic [7:0] tlp_byte8;
  logic [7:0] tlp_byte9;
  logic [7:0] tlp_byte10;
  logic [7:0] tlp_byte11;
  logic [7:0] tlp_byte12;
  logic [7:0] tlp_byte13;
  logic [7:0] tlp_byte14;
  logic [7:0] tlp_byte15;
  logic [7:0] tlp_payload_byte;
  logic [8:0] tlp_payload_index;
  logic tlp_payload_valid;
  logic ingress_busy;
  logic ingress_malformed;

  logic vdm_valid;
  logic vdm_malformed_tlp;
  logic vdm_unsupported;
  logic vdm_bad_vendor;
  logic vdm_bad_message_code;
  logic vdm_bad_mctp_vdm_code;
  logic [1:0] vdm_pad_len;
  logic [15:0] vdm_requester_id;
  logic [15:0] vdm_target_id;
  logic [15:0] vdm_vendor_id;
  logic [2:0] vdm_routing;

  logic mctp_valid;
  logic mctp_bad_hdr;
  logic mctp_bad_pad;
  logic mctp_dest_reject;
  logic [7:0] mctp_dest_eid;
  logic [7:0] mctp_source_eid;
  logic mctp_som;
  logic mctp_eom;
  logic [1:0] mctp_seq;
  logic mctp_tag_owner;
  logic [2:0] mctp_message_tag;
  logic [15:0] mctp_payload_byte_count;

  logic cfg_enable;
  logic cfg_drop_when_disabled;
  logic cfg_dest_filter_enable;
  logic cfg_accept_broadcast_eid;
  logic cfg_accept_null_eid;
  logic cfg_soft_reset;
  logic [7:0] cfg_local_eid;
  logic [15:0] cfg_max_message_bytes;
  logic [15:0] cfg_mtu_bytes;
  logic [23:0] cfg_timeout_cycles;
  logic [15:0] cfg_sram_base;
  logic [15:0] cfg_sram_limit;

  logic cfg_enable_apb;
  logic cfg_drop_when_disabled_apb;
  logic cfg_dest_filter_enable_apb;
  logic cfg_accept_broadcast_apb;
  logic cfg_accept_null_apb;
  logic cfg_soft_reset_apb;
  logic [7:0] cfg_local_eid_apb;
  logic [15:0] cfg_max_message_bytes_apb;
  logic [15:0] cfg_mtu_bytes_apb;
  logic [23:0] cfg_timeout_cycles_apb;
  logic [15:0] cfg_sram_base_apb;
  logic [15:0] cfg_sram_limit_apb;

  logic pkt_valid;
  logic pkt_ready;
  logic pkt_reject;
  logic wr_byte_valid;
  logic [7:0] wr_byte_data;
  logic [SRAM_ADDR_WIDTH-1:0] wr_byte_addr;
  logic wr_flush;
  logic wr_byte_ready;
  logic writer_busy;
  logic [SRAM_ADDR_WIDTH-1:0] sram_wr_ptr;
  logic desc_fifo_full;
  logic [3:0] desc_fifo_count;
  logic [31:0] desc_word0;
  logic [31:0] desc_word1;
  logic [31:0] desc_word2;
  logic [31:0] desc_word3;
  logic desc_pop_apb;
  logic desc_push;
  logic evt_desc_ready;
  logic evt_packet_drop;
  logic evt_assembly_drop;
  logic evt_desc_ready_apb;
  logic evt_packet_drop_apb;
  logic evt_assembly_drop_apb;
  logic evt_malformed_tlp;
  logic evt_unsupported_vdm;
  logic evt_bad_mctp_hdr;
  logic evt_dest_reject;
  logic evt_sequence_error;
  logic evt_context_error;
  logic evt_overflow_error;
  logic evt_unexpected_fragment;
  logic evt_duplicate_som;
  logic evt_seq_mismatch;
  logic context_active_any;
  logic [3:0] active_context_count;
  logic [7:0] desc_source_eid;
  logic [7:0] desc_dest_eid;
  logic desc_tag_owner;
  logic [2:0] desc_message_tag;
  logic [7:0] desc_message_type;
  logic [15:0] desc_payload_byte_count;
  logic [15:0] desc_requester_id;
  logic [15:0] desc_sram_start_addr;
  logic [1:0] desc_final_sequence;
  logic [3:0] desc_context_id;
  logic [2:0] desc_routing_axi;

  logic [15:0] payload_idx_q;
  logic process_active_q;
  logic pkt_accepted_q;
  logic [15:0] held_payload_count;
  logic parse_fail_pulse;
  logic held_packet_drop_evt;
  logic held_malformed_tlp_evt;
  logic held_unsupported_vdm_evt;
  logic held_bad_mctp_hdr_evt;
  logic held_dest_reject_evt;
  wire cfg_timeout_armed = |cfg_timeout_cycles;
  wire vdm_identity_ok = (vdm_vendor_id == `MCTP_ASSEMBLER_VENDOR_ID_DMTF) &&
                         (|vdm_target_id || |vdm_requester_id);

  wire parse_fail_cond = ingress_malformed || vdm_malformed_tlp || vdm_unsupported ||
      vdm_bad_vendor || vdm_bad_message_code || vdm_bad_mctp_vdm_code ||
      mctp_bad_hdr || mctp_bad_pad || mctp_dest_reject;
  wire parse_ok = mctp_valid && !parse_fail_cond;
  wire parse_fail = tlp_valid && parse_fail_cond;
  wire parse_fail_done = tlp_valid && tlp_ready && parse_fail;
  wire evt_packet_drop_parse = parse_fail_done && held_packet_drop_evt;
  wire evt_packet_drop_reject = tlp_valid && tlp_ready && pkt_reject;
  wire evt_packet_drop_combined = evt_packet_drop | evt_packet_drop_parse | evt_packet_drop_reject;
  wire payload_stream_done = (held_payload_count == 16'd0 && pkt_accepted_q) ||
      (payload_idx_q >= held_payload_count);

  assign tlp_payload_index = payload_idx_q[8:0];
  assign tlp_ready = process_active_q && (
      ((parse_fail || pkt_reject) && pkt_ready) ||
      (parse_ok && !pkt_reject && payload_stream_done && pkt_accepted_q)
  );
  assign pkt_valid = process_active_q && parse_ok && !pkt_accepted_q;

  assign evt_malformed_tlp = parse_fail_done && held_malformed_tlp_evt;
  assign evt_unsupported_vdm = parse_fail_done && held_unsupported_vdm_evt;
  assign evt_bad_mctp_hdr = parse_fail_done && held_bad_mctp_hdr_evt;
  assign evt_dest_reject = parse_fail_done && held_dest_reject_evt;

  always @(posedge axi_aclk) begin
    if (!axi_aresetn || cfg_soft_reset) begin
      process_active_q <= 1'b0;
      payload_idx_q <= 16'd0;
      pkt_accepted_q <= 1'b0;
      held_payload_count <= 16'd0;
      parse_fail_pulse <= 1'b0;
      held_packet_drop_evt <= 1'b0;
      held_malformed_tlp_evt <= 1'b0;
      held_unsupported_vdm_evt <= 1'b0;
      held_bad_mctp_hdr_evt <= 1'b0;
      held_dest_reject_evt <= 1'b0;
    end else begin
      parse_fail_pulse <= 1'b0;
      if (tlp_valid && tlp_ready) begin
        process_active_q <= 1'b0;
        payload_idx_q <= 16'd0;
        pkt_accepted_q <= 1'b0;
        held_packet_drop_evt <= 1'b0;
        held_malformed_tlp_evt <= 1'b0;
        held_unsupported_vdm_evt <= 1'b0;
        held_bad_mctp_hdr_evt <= 1'b0;
        held_dest_reject_evt <= 1'b0;
        if (parse_fail) begin
          parse_fail_pulse <= 1'b1;
        end
      end else if (tlp_valid && !process_active_q) begin
        process_active_q <= 1'b1;
        payload_idx_q <= 16'd0;
        pkt_accepted_q <= 1'b0;
        held_payload_count <= mctp_payload_byte_count;
        held_packet_drop_evt <= vdm_unsupported || vdm_bad_vendor || vdm_bad_message_code ||
            vdm_bad_mctp_vdm_code || mctp_bad_hdr || mctp_bad_pad || mctp_dest_reject;
        held_malformed_tlp_evt <= ingress_malformed || vdm_malformed_tlp;
        held_unsupported_vdm_evt <= vdm_unsupported || vdm_bad_vendor || vdm_bad_message_code ||
            vdm_bad_mctp_vdm_code || !vdm_identity_ok;
        held_bad_mctp_hdr_evt <= mctp_bad_hdr || mctp_bad_pad;
        held_dest_reject_evt <= mctp_dest_reject;
      end else if (pkt_valid && pkt_ready && !pkt_reject) begin
        pkt_accepted_q <= 1'b1;
      end else if (process_active_q && parse_ok && wr_byte_valid &&
                   (payload_idx_q < held_payload_count)) begin
        payload_idx_q <= payload_idx_q + 16'd1;
      end
    end
  end

  mctp_assembler_axi_write_ingress #(
    .AXI_ADDR_WIDTH(AXI_ADDR_WIDTH),
    .AXI_DATA_WIDTH(AXI_DATA_WIDTH)
  ) u_ingress (
    .axi_aclk(axi_aclk),
    .axi_aresetn(axi_aresetn),
    .enable(cfg_enable),
    .drop_when_disabled(cfg_drop_when_disabled),
    .s_axi_awaddr(s_axi_awaddr),
    .s_axi_awlen(s_axi_awlen),
    .s_axi_awsize(s_axi_awsize),
    .s_axi_awburst(s_axi_awburst),
    .s_axi_awvalid(s_axi_awvalid),
    .s_axi_awready(s_axi_awready),
    .s_axi_wdata(s_axi_wdata),
    .s_axi_wstrb(s_axi_wstrb),
    .s_axi_wlast(s_axi_wlast),
    .s_axi_wvalid(s_axi_wvalid),
    .s_axi_wready(s_axi_wready),
    .s_axi_bresp(s_axi_bresp),
    .s_axi_bvalid(s_axi_bvalid),
    .s_axi_bready(s_axi_bready),
    .soft_reset(cfg_soft_reset),
    .tlp_valid(tlp_valid),
    .tlp_ready(tlp_ready),
    .tlp_byte_count(tlp_byte_count),
    .tlp_byte0(tlp_byte0),
    .tlp_byte1(tlp_byte1),
    .tlp_byte2(tlp_byte2),
    .tlp_byte3(tlp_byte3),
    .tlp_byte4(tlp_byte4),
    .tlp_byte5(tlp_byte5),
    .tlp_byte6(tlp_byte6),
    .tlp_byte7(tlp_byte7),
    .tlp_byte8(tlp_byte8),
    .tlp_byte9(tlp_byte9),
    .tlp_byte10(tlp_byte10),
    .tlp_byte11(tlp_byte11),
    .tlp_byte12(tlp_byte12),
    .tlp_byte13(tlp_byte13),
    .tlp_byte14(tlp_byte14),
    .tlp_byte15(tlp_byte15),
    .tlp_payload_byte(tlp_payload_byte),
    .tlp_payload_index(tlp_payload_index),
    .tlp_payload_valid(tlp_payload_valid),
    .ingress_busy(ingress_busy),
    .ingress_malformed(ingress_malformed)
  );

  mctp_assembler_pcie_vdm_parser u_vdm (
    .tlp_valid(tlp_valid),
    .tlp_byte_count(tlp_byte_count),
    .tlp_byte0(tlp_byte0),
    .tlp_byte1(tlp_byte1),
    .tlp_byte2(tlp_byte2),
    .tlp_byte3(tlp_byte3),
    .tlp_byte4(tlp_byte4),
    .tlp_byte5(tlp_byte5),
    .tlp_byte6(tlp_byte6),
    .tlp_byte7(tlp_byte7),
    .tlp_byte8(tlp_byte8),
    .tlp_byte9(tlp_byte9),
    .tlp_byte10(tlp_byte10),
    .tlp_byte11(tlp_byte11),
    .vdm_valid(vdm_valid),
    .vdm_malformed_tlp(vdm_malformed_tlp),
    .vdm_unsupported(vdm_unsupported),
    .vdm_bad_vendor(vdm_bad_vendor),
    .vdm_bad_message_code(vdm_bad_message_code),
    .vdm_bad_mctp_vdm_code(vdm_bad_mctp_vdm_code),
    .vdm_pad_len(vdm_pad_len),
    .vdm_requester_id(vdm_requester_id),
    .vdm_target_id(vdm_target_id),
    .vdm_vendor_id(vdm_vendor_id),
    .vdm_routing(vdm_routing)
  );

  mctp_assembler_mctp_parser u_mctp (
    .vdm_valid(vdm_valid),
    .vdm_pad_len(vdm_pad_len),
    .tlp_byte_count(tlp_byte_count),
    .tlp_byte12(tlp_byte12),
    .tlp_byte13(tlp_byte13),
    .tlp_byte14(tlp_byte14),
    .tlp_byte15(tlp_byte15),
    .local_eid(cfg_local_eid),
    .dest_filter_enable(cfg_dest_filter_enable),
    .accept_broadcast_eid(cfg_accept_broadcast_eid),
    .accept_null_eid(cfg_accept_null_eid),
    .mctp_valid(mctp_valid),
    .mctp_bad_hdr(mctp_bad_hdr),
    .mctp_bad_pad(mctp_bad_pad),
    .mctp_dest_reject(mctp_dest_reject),
    .mctp_dest_eid(mctp_dest_eid),
    .mctp_source_eid(mctp_source_eid),
    .mctp_som(mctp_som),
    .mctp_eom(mctp_eom),
    .mctp_seq(mctp_seq),
    .mctp_tag_owner(mctp_tag_owner),
    .mctp_message_tag(mctp_message_tag),
    .mctp_payload_byte_count(mctp_payload_byte_count)
  );

  mctp_assembler_context_table #(
    .CONTEXT_COUNT(CONTEXT_COUNT),
    .SRAM_ADDR_WIDTH(SRAM_ADDR_WIDTH)
  ) u_context (
    .axi_aclk(axi_aclk),
    .axi_aresetn(axi_aresetn),
    .soft_reset(cfg_soft_reset),
    .pkt_valid(pkt_valid),
    .pkt_ready(pkt_ready),
    .pkt_reject(pkt_reject),
    .pkt_source_eid(mctp_source_eid),
    .pkt_dest_eid(mctp_dest_eid),
    .pkt_som(mctp_som),
    .pkt_eom(mctp_eom),
    .pkt_seq(mctp_seq),
    .pkt_tag_owner(mctp_tag_owner),
    .pkt_message_tag(mctp_message_tag),
    .pkt_message_type(tlp_payload_byte),
    .pkt_payload_count(held_payload_count),
    .pkt_requester_id(vdm_requester_id),
    .payload_byte(tlp_payload_byte),
    .payload_byte_valid(tlp_payload_valid && process_active_q && parse_ok),
    .max_message_bytes(cfg_max_message_bytes),
    .cfg_mtu_bytes(cfg_mtu_bytes),
    .sram_base(cfg_sram_base),
    .sram_limit(cfg_sram_limit),
    .sram_wr_ptr_in(sram_wr_ptr),
    .sram_wr_ptr_out(sram_wr_ptr),
    .desc_fifo_full(desc_fifo_full),
    .wr_byte_valid(wr_byte_valid),
    .wr_byte_data(wr_byte_data),
    .wr_byte_addr(wr_byte_addr),
    .wr_flush(wr_flush),
    .wr_byte_ready(wr_byte_ready),
    .writer_busy(writer_busy),
    .context_active_any(context_active_any),
    .active_context_count(active_context_count),
    .evt_packet_drop(evt_packet_drop),
    .evt_assembly_drop(evt_assembly_drop),
    .evt_desc_ready(evt_desc_ready),
    .evt_sequence_error(evt_sequence_error),
    .evt_context_error(evt_context_error),
    .evt_overflow_error(evt_overflow_error),
    .evt_unexpected_fragment(evt_unexpected_fragment),
    .evt_duplicate_som(evt_duplicate_som),
    .evt_seq_mismatch(evt_seq_mismatch),
    .desc_source_eid(desc_source_eid),
    .desc_dest_eid(desc_dest_eid),
    .desc_tag_owner(desc_tag_owner),
    .desc_message_tag(desc_message_tag),
    .desc_message_type(desc_message_type),
    .desc_payload_byte_count(desc_payload_byte_count),
    .desc_requester_id(desc_requester_id),
    .desc_sram_start_addr(desc_sram_start_addr),
    .desc_final_sequence(desc_final_sequence),
    .desc_context_id(desc_context_id),
    .desc_push(desc_push)
  );

  mctp_assembler_payload_writer #(
    .SRAM_ADDR_WIDTH(SRAM_ADDR_WIDTH),
    .SRAM_DATA_WIDTH(SRAM_DATA_WIDTH)
  ) u_writer (
    .axi_aclk(axi_aclk),
    .axi_aresetn(axi_aresetn),
    .soft_reset(cfg_soft_reset),
    .wr_byte_valid(wr_byte_valid),
    .wr_byte_data(wr_byte_data),
    .wr_byte_addr(wr_byte_addr),
    .wr_flush(wr_flush),
    .wr_byte_ready(wr_byte_ready),
    .sram_wr_valid(sram_wr_valid),
    .sram_wr_ready(sram_wr_ready),
    .sram_wr_addr(sram_wr_addr),
    .sram_wr_data(sram_wr_data),
    .sram_wr_strb(sram_wr_strb),
    .writer_busy(writer_busy)
  );

  mctp_assembler_cdc u_cdc (
    .axi_aclk(axi_aclk),
    .axi_aresetn(axi_aresetn),
    .pclk(pclk),
    .presetn(presetn),
    .cfg_enable_apb(cfg_enable_apb),
    .cfg_drop_when_disabled_apb(cfg_drop_when_disabled_apb),
    .cfg_dest_filter_enable_apb(cfg_dest_filter_enable_apb),
    .cfg_accept_broadcast_apb(cfg_accept_broadcast_apb),
    .cfg_accept_null_apb(cfg_accept_null_apb),
    .cfg_soft_reset_apb(cfg_soft_reset_apb),
    .cfg_local_eid_apb(cfg_local_eid_apb),
    .cfg_max_message_bytes_apb(cfg_max_message_bytes_apb),
    .cfg_mtu_bytes_apb(cfg_mtu_bytes_apb),
    .cfg_timeout_cycles_apb(cfg_timeout_cycles_apb),
    .cfg_sram_base_apb(cfg_sram_base_apb),
    .cfg_sram_limit_apb(cfg_sram_limit_apb),
    .cfg_enable(cfg_enable),
    .cfg_drop_when_disabled(cfg_drop_when_disabled),
    .cfg_dest_filter_enable(cfg_dest_filter_enable),
    .cfg_accept_broadcast_eid(cfg_accept_broadcast_eid),
    .cfg_accept_null_eid(cfg_accept_null_eid),
    .cfg_soft_reset(cfg_soft_reset),
    .cfg_local_eid(cfg_local_eid),
    .cfg_max_message_bytes(cfg_max_message_bytes),
    .cfg_mtu_bytes(cfg_mtu_bytes),
    .cfg_timeout_cycles(cfg_timeout_cycles),
    .cfg_sram_base(cfg_sram_base),
    .cfg_sram_limit(cfg_sram_limit),
    .evt_desc_ready_axi(evt_desc_ready),
    .evt_packet_drop_axi(evt_packet_drop_combined),
    .evt_assembly_drop_axi(evt_assembly_drop),
    .desc_source_eid_axi(desc_source_eid),
    .desc_dest_eid_axi(desc_dest_eid),
    .desc_tag_owner_axi(desc_tag_owner),
    .desc_message_tag_axi(desc_message_tag),
    .desc_message_type_axi(desc_message_type),
    .desc_payload_byte_count_axi(desc_payload_byte_count),
    .desc_requester_id_axi(desc_requester_id),
    .desc_sram_start_addr_axi(desc_sram_start_addr),
    .desc_final_sequence_axi(desc_final_sequence),
    .desc_context_id_axi(desc_context_id),
    .desc_routing_axi(desc_routing_axi),
    .desc_push_axi(desc_push),
    .desc_pop_apb(desc_pop_apb),
    .desc_fifo_full(desc_fifo_full),
    .desc_fifo_count(desc_fifo_count),
    .desc_word0(desc_word0),
    .desc_word1(desc_word1),
    .desc_word2(desc_word2),
    .desc_word3(desc_word3),
    .evt_desc_ready_apb(evt_desc_ready_apb),
    .evt_packet_drop_apb(evt_packet_drop_apb),
    .evt_assembly_drop_apb(evt_assembly_drop_apb)
  );

  assign desc_routing_axi = vdm_routing;

  mctp_assembler_apb_regfile u_apb (
    .pclk(pclk),
    .presetn(presetn),
    .psel(psel),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr),
    .pwdata(pwdata),
    .pstrb(pstrb),
    .prdata(prdata),
    .pready(pready),
    .pslverr(pslverr),
    .intr(intr),
    .cfg_enable_apb(cfg_enable_apb),
    .cfg_drop_when_disabled_apb(cfg_drop_when_disabled_apb),
    .cfg_dest_filter_enable_apb(cfg_dest_filter_enable_apb),
    .cfg_accept_broadcast_apb(cfg_accept_broadcast_apb),
    .cfg_accept_null_apb(cfg_accept_null_apb),
    .cfg_soft_reset_apb(cfg_soft_reset_apb),
    .cfg_local_eid_apb(cfg_local_eid_apb),
    .cfg_max_message_bytes_apb(cfg_max_message_bytes_apb),
    .cfg_mtu_bytes_apb(cfg_mtu_bytes_apb),
    .cfg_timeout_cycles_apb(cfg_timeout_cycles_apb),
    .cfg_sram_base_apb(cfg_sram_base_apb),
    .cfg_sram_limit_apb(cfg_sram_limit_apb),
    .ingress_busy(ingress_busy),
    .context_active_any(context_active_any),
    .active_context_count(active_context_count),
    .desc_fifo_count(desc_fifo_count),
    .desc_fifo_full(desc_fifo_full),
    .desc_word0(desc_word0),
    .desc_word1(desc_word1),
    .desc_word2(desc_word2),
    .desc_word3(desc_word3),
    .desc_pop_apb(desc_pop_apb),
    .sram_wr_ptr_shadow(sram_wr_ptr),
    .evt_desc_ready_apb(evt_desc_ready_apb),
    .evt_packet_drop_apb(evt_packet_drop_apb),
    .evt_assembly_drop_apb(evt_assembly_drop_apb),
    .evt_malformed_tlp(evt_malformed_tlp),
    .evt_unsupported_vdm(evt_unsupported_vdm),
    .evt_bad_mctp_hdr(evt_bad_mctp_hdr),
    .evt_dest_reject(evt_dest_reject),
    .evt_sequence_error(evt_sequence_error),
    .evt_context_error(evt_context_error),
    .evt_overflow_error(evt_overflow_error),
    .evt_unexpected_fragment(evt_unexpected_fragment),
    .evt_duplicate_som(evt_duplicate_som),
    .evt_seq_mismatch(evt_seq_mismatch),
    .cfg_timeout_armed(cfg_timeout_armed)
  );
endmodule
