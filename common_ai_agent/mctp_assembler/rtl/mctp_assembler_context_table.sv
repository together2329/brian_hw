`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Track fragmented MCTP assemblies and drive payload writes.
module mctp_assembler_context_table #(
  parameter integer CONTEXT_COUNT = `MCTP_ASSEMBLER_CONTEXT_COUNT,
  parameter integer SRAM_ADDR_WIDTH = `MCTP_ASSEMBLER_SRAM_ADDR_WIDTH
) (
  input  logic                        axi_aclk,
  input  logic                        axi_aresetn,
  input  logic                        soft_reset,
  input  logic                        pkt_valid,
  output logic                        pkt_ready,
  output logic                        pkt_reject,
  input  logic [7:0]                  pkt_source_eid,
  input  logic [7:0]                  pkt_dest_eid,
  input  logic                        pkt_som,
  input  logic                        pkt_eom,
  input  logic [1:0]                  pkt_seq,
  input  logic                        pkt_tag_owner,
  input  logic [2:0]                  pkt_message_tag,
  input  logic [7:0]                  pkt_message_type,
  input  logic [15:0]                 pkt_payload_count,
  input  logic [15:0]                 pkt_requester_id,
  input  logic [7:0]                  payload_byte,
  input  logic                        payload_byte_valid,
  input  logic [15:0]                 max_message_bytes,
  input  logic [15:0]                 cfg_mtu_bytes,
  input  logic [SRAM_ADDR_WIDTH-1:0]  sram_base,
  input  logic [SRAM_ADDR_WIDTH-1:0]  sram_limit,
  input  logic [SRAM_ADDR_WIDTH-1:0]  sram_wr_ptr_in,
  output logic [SRAM_ADDR_WIDTH-1:0]  sram_wr_ptr_out,
  input  logic                        desc_fifo_full,
  output logic                        wr_byte_valid,
  output logic [7:0]                  wr_byte_data,
  output logic [SRAM_ADDR_WIDTH-1:0]  wr_byte_addr,
  output logic                        wr_flush,
  input  logic                        wr_byte_ready,
  input  logic                        writer_busy,
  output logic                        context_active_any,
  output logic [3:0]                  active_context_count,
  output logic                        evt_packet_drop,
  output logic                        evt_assembly_drop,
  output logic                        evt_desc_ready,
  output logic                        evt_sequence_error,
  output logic                        evt_context_error,
  output logic                        evt_overflow_error,
  output logic                        evt_unexpected_fragment,
  output logic                        evt_duplicate_som,
  output logic                        evt_seq_mismatch,
  output logic [7:0]                  desc_source_eid,
  output logic [7:0]                  desc_dest_eid,
  output logic                        desc_tag_owner,
  output logic [2:0]                  desc_message_tag,
  output logic [7:0]                  desc_message_type,
  output logic [15:0]                 desc_payload_byte_count,
  output logic [15:0]                 desc_requester_id,
  output logic [SRAM_ADDR_WIDTH-1:0]  desc_sram_start_addr,
  output logic [1:0]                  desc_final_sequence,
  output logic [3:0]                  desc_context_id,
  output logic                        desc_push
);
  localparam [2:0] ST_IDLE  = 3'd0;
  localparam [2:0] ST_WRITE = 3'd1;
  localparam [2:0] ST_FLUSH = 3'd2;
  localparam [2:0] ST_DESC  = 3'd3;

  logic [2:0] state_q;
  logic [15:0] byte_idx_q;
  logic [15:0] total_len_q;
  logic [SRAM_ADDR_WIDTH-1:0] start_addr_q;
  logic [SRAM_ADDR_WIDTH-1:0] wr_ptr_q;
  logic [3:0] ctx_slot_q;
  logic keep_context_q;
  logic [1:0] final_seq_q;
  logic [7:0] msg_type_q;
  logic [15:0] req_id_q;
  logic [7:0] src_eid_q;
  logic [7:0] dest_eid_q;
  logic tag_owner_q;
  logic [2:0] msg_tag_q;

  logic ctx_valid [0:CONTEXT_COUNT-1];
  logic [7:0] ctx_src [0:CONTEXT_COUNT-1];
  logic ctx_tag_owner [0:CONTEXT_COUNT-1];
  logic [2:0] ctx_msg_tag [0:CONTEXT_COUNT-1];
  logic [1:0] ctx_expected_seq [0:CONTEXT_COUNT-1];
  logic [15:0] ctx_len [0:CONTEXT_COUNT-1];
  logic [SRAM_ADDR_WIDTH-1:0] ctx_start [0:CONTEXT_COUNT-1];
  logic [7:0] ctx_msg_type [0:CONTEXT_COUNT-1];
  logic [15:0] ctx_req_id [0:CONTEXT_COUNT-1];
  logic [7:0] ctx_dest [0:CONTEXT_COUNT-1];

  logic key_match_0;
  logic key_match_1;
  logic key_match_2;
  logic key_match_3;
  logic key_match_4;
  logic key_match_5;
  logic key_match_6;
  logic key_match_7;
  logic key_match_8;
  logic key_match_9;
  logic key_match_10;
  logic key_match_11;
  logic key_match_12;
  logic key_match_13;
  logic key_match_14;
  logic match_found;
  logic [3:0] match_slot;
  logic free_found;
  logic [3:0] free_slot;
  logic duplicate_som;
  logic unexpected_fragment;
  logic seq_mismatch;

  assign key_match_0 = ctx_valid[0] && (ctx_src[0] == pkt_source_eid) && (ctx_tag_owner[0] == pkt_tag_owner) && (ctx_msg_tag[0] == pkt_message_tag);
  assign key_match_1 = ctx_valid[1] && (ctx_src[1] == pkt_source_eid) && (ctx_tag_owner[1] == pkt_tag_owner) && (ctx_msg_tag[1] == pkt_message_tag);
  assign key_match_2 = ctx_valid[2] && (ctx_src[2] == pkt_source_eid) && (ctx_tag_owner[2] == pkt_tag_owner) && (ctx_msg_tag[2] == pkt_message_tag);
  assign key_match_3 = ctx_valid[3] && (ctx_src[3] == pkt_source_eid) && (ctx_tag_owner[3] == pkt_tag_owner) && (ctx_msg_tag[3] == pkt_message_tag);
  assign key_match_4 = ctx_valid[4] && (ctx_src[4] == pkt_source_eid) && (ctx_tag_owner[4] == pkt_tag_owner) && (ctx_msg_tag[4] == pkt_message_tag);
  assign key_match_5 = ctx_valid[5] && (ctx_src[5] == pkt_source_eid) && (ctx_tag_owner[5] == pkt_tag_owner) && (ctx_msg_tag[5] == pkt_message_tag);
  assign key_match_6 = ctx_valid[6] && (ctx_src[6] == pkt_source_eid) && (ctx_tag_owner[6] == pkt_tag_owner) && (ctx_msg_tag[6] == pkt_message_tag);
  assign key_match_7 = ctx_valid[7] && (ctx_src[7] == pkt_source_eid) && (ctx_tag_owner[7] == pkt_tag_owner) && (ctx_msg_tag[7] == pkt_message_tag);
  assign key_match_8 = ctx_valid[8] && (ctx_src[8] == pkt_source_eid) && (ctx_tag_owner[8] == pkt_tag_owner) && (ctx_msg_tag[8] == pkt_message_tag);
  assign key_match_9 = ctx_valid[9] && (ctx_src[9] == pkt_source_eid) && (ctx_tag_owner[9] == pkt_tag_owner) && (ctx_msg_tag[9] == pkt_message_tag);
  assign key_match_10 = ctx_valid[10] && (ctx_src[10] == pkt_source_eid) && (ctx_tag_owner[10] == pkt_tag_owner) && (ctx_msg_tag[10] == pkt_message_tag);
  assign key_match_11 = ctx_valid[11] && (ctx_src[11] == pkt_source_eid) && (ctx_tag_owner[11] == pkt_tag_owner) && (ctx_msg_tag[11] == pkt_message_tag);
  assign key_match_12 = ctx_valid[12] && (ctx_src[12] == pkt_source_eid) && (ctx_tag_owner[12] == pkt_tag_owner) && (ctx_msg_tag[12] == pkt_message_tag);
  assign key_match_13 = ctx_valid[13] && (ctx_src[13] == pkt_source_eid) && (ctx_tag_owner[13] == pkt_tag_owner) && (ctx_msg_tag[13] == pkt_message_tag);
  assign key_match_14 = ctx_valid[14] && (ctx_src[14] == pkt_source_eid) && (ctx_tag_owner[14] == pkt_tag_owner) && (ctx_msg_tag[14] == pkt_message_tag);
  assign match_found = key_match_0 || key_match_1 || key_match_2 || key_match_3 || key_match_4 ||
                       key_match_5 || key_match_6 || key_match_7 || key_match_8 || key_match_9 ||
                       key_match_10 || key_match_11 || key_match_12 || key_match_13 || key_match_14;

  always @(*) begin
    match_slot = 4'd0;
    if (key_match_0) match_slot = 4'd0;
    else if (key_match_1) match_slot = 4'd1;
    else if (key_match_2) match_slot = 4'd2;
    else if (key_match_3) match_slot = 4'd3;
    else if (key_match_4) match_slot = 4'd4;
    else if (key_match_5) match_slot = 4'd5;
    else if (key_match_6) match_slot = 4'd6;
    else if (key_match_7) match_slot = 4'd7;
    else if (key_match_8) match_slot = 4'd8;
    else if (key_match_9) match_slot = 4'd9;
    else if (key_match_10) match_slot = 4'd10;
    else if (key_match_11) match_slot = 4'd11;
    else if (key_match_12) match_slot = 4'd12;
    else if (key_match_13) match_slot = 4'd13;
    else if (key_match_14) match_slot = 4'd14;
  end

  always @(*) begin
    free_slot = 4'd0;
    free_found = 1'b0;
    if (!ctx_valid[0]) begin free_slot = 4'd0; free_found = 1'b1; end
    else if (!ctx_valid[1]) begin free_slot = 4'd1; free_found = 1'b1; end
    else if (!ctx_valid[2]) begin free_slot = 4'd2; free_found = 1'b1; end
    else if (!ctx_valid[3]) begin free_slot = 4'd3; free_found = 1'b1; end
    else if (!ctx_valid[4]) begin free_slot = 4'd4; free_found = 1'b1; end
    else if (!ctx_valid[5]) begin free_slot = 4'd5; free_found = 1'b1; end
    else if (!ctx_valid[6]) begin free_slot = 4'd6; free_found = 1'b1; end
    else if (!ctx_valid[7]) begin free_slot = 4'd7; free_found = 1'b1; end
    else if (!ctx_valid[8]) begin free_slot = 4'd8; free_found = 1'b1; end
    else if (!ctx_valid[9]) begin free_slot = 4'd9; free_found = 1'b1; end
    else if (!ctx_valid[10]) begin free_slot = 4'd10; free_found = 1'b1; end
    else if (!ctx_valid[11]) begin free_slot = 4'd11; free_found = 1'b1; end
    else if (!ctx_valid[12]) begin free_slot = 4'd12; free_found = 1'b1; end
    else if (!ctx_valid[13]) begin free_slot = 4'd13; free_found = 1'b1; end
    else if (!ctx_valid[14]) begin free_slot = 4'd14; free_found = 1'b1; end
  end

  assign active_context_count =
      {3'd0, ctx_valid[0]} + {3'd0, ctx_valid[1]} + {3'd0, ctx_valid[2]} +
      {3'd0, ctx_valid[3]} + {3'd0, ctx_valid[4]} + {3'd0, ctx_valid[5]} +
      {3'd0, ctx_valid[6]} + {3'd0, ctx_valid[7]} + {3'd0, ctx_valid[8]} +
      {3'd0, ctx_valid[9]} + {3'd0, ctx_valid[10]} + {3'd0, ctx_valid[11]} +
      {3'd0, ctx_valid[12]} + {3'd0, ctx_valid[13]} + {3'd0, ctx_valid[14]};

  assign duplicate_som = pkt_valid && pkt_som && match_found;
  assign unexpected_fragment = pkt_valid && !pkt_som && !match_found;
  assign seq_mismatch = pkt_valid && !pkt_som && match_found && (ctx_expected_seq[match_slot] != pkt_seq);

  assign sram_wr_ptr_out = wr_ptr_q;
  assign wr_byte_data = payload_byte;
  assign pkt_ready = (state_q == ST_IDLE);
  assign pkt_reject = pkt_valid && (state_q == ST_IDLE) && (
      unexpected_fragment ||
      (pkt_som && (duplicate_som || !free_found ||
          (pkt_payload_count > max_message_bytes) || (pkt_payload_count > cfg_mtu_bytes))) ||
      seq_mismatch ||
      (!pkt_som && match_found && (
          ((ctx_len[match_slot] + pkt_payload_count) > max_message_bytes) ||
          ((ctx_len[match_slot] + pkt_payload_count) > cfg_mtu_bytes) ||
          ((ctx_start[match_slot] + ctx_len[match_slot] + pkt_payload_count) > sram_limit) ||
          desc_fifo_full))
  );
  assign context_active_any = (active_context_count != 4'd0);
  assign wr_byte_valid = (state_q == ST_WRITE) && payload_byte_valid && wr_byte_ready;
  assign wr_byte_addr = start_addr_q + byte_idx_q;
  assign wr_flush = (state_q == ST_FLUSH);
  assign desc_push = (state_q == ST_DESC) && !desc_fifo_full;
  assign evt_desc_ready = desc_push;

  assign desc_source_eid = src_eid_q;
  assign desc_dest_eid = dest_eid_q;
  assign desc_tag_owner = tag_owner_q;
  assign desc_message_tag = msg_tag_q;
  assign desc_message_type = msg_type_q;
  assign desc_payload_byte_count = total_len_q;
  assign desc_requester_id = req_id_q;
  assign desc_sram_start_addr = start_addr_q;
  assign desc_final_sequence = final_seq_q;
  assign desc_context_id = ctx_slot_q;

  always @(posedge axi_aclk) begin
    if (!axi_aresetn || soft_reset) begin
      state_q <= ST_IDLE;
      byte_idx_q <= 16'd0;
      total_len_q <= 16'd0;
      start_addr_q <= {SRAM_ADDR_WIDTH{1'b0}};
      wr_ptr_q <= {SRAM_ADDR_WIDTH{1'b0}};
      ctx_slot_q <= 4'd0;
      keep_context_q <= 1'b0;
      evt_packet_drop <= 1'b0;
      evt_assembly_drop <= 1'b0;
      evt_sequence_error <= 1'b0;
      evt_context_error <= 1'b0;
      evt_overflow_error <= 1'b0;
      evt_unexpected_fragment <= 1'b0;
      evt_duplicate_som <= 1'b0;
      evt_seq_mismatch <= 1'b0;
      ctx_valid[0] <= 1'b0; ctx_valid[1] <= 1'b0; ctx_valid[2] <= 1'b0; ctx_valid[3] <= 1'b0;
      ctx_valid[4] <= 1'b0; ctx_valid[5] <= 1'b0; ctx_valid[6] <= 1'b0; ctx_valid[7] <= 1'b0;
      ctx_valid[8] <= 1'b0; ctx_valid[9] <= 1'b0; ctx_valid[10] <= 1'b0; ctx_valid[11] <= 1'b0;
      ctx_valid[12] <= 1'b0; ctx_valid[13] <= 1'b0; ctx_valid[14] <= 1'b0;
    end else begin
      evt_packet_drop <= 1'b0;
      evt_assembly_drop <= 1'b0;
      evt_sequence_error <= 1'b0;
      evt_context_error <= 1'b0;
      evt_overflow_error <= 1'b0;
      evt_unexpected_fragment <= 1'b0;
      evt_duplicate_som <= 1'b0;
      evt_seq_mismatch <= 1'b0;

      if (state_q == ST_IDLE && pkt_valid) begin
        src_eid_q <= pkt_source_eid;
        dest_eid_q <= pkt_dest_eid;
        tag_owner_q <= pkt_tag_owner;
        msg_tag_q <= pkt_message_tag;
        req_id_q <= pkt_requester_id;
        final_seq_q <= pkt_seq;
        msg_type_q <= pkt_message_type;
        if (unexpected_fragment) begin
          evt_packet_drop <= 1'b1;
          evt_unexpected_fragment <= 1'b1;
          evt_sequence_error <= 1'b1;
        end else if (duplicate_som) begin
          evt_assembly_drop <= 1'b1;
          evt_duplicate_som <= 1'b1;
          evt_context_error <= 1'b1;
          ctx_valid[match_slot] <= 1'b0;
        end else if (seq_mismatch) begin
          evt_assembly_drop <= 1'b1;
          evt_seq_mismatch <= 1'b1;
          evt_sequence_error <= 1'b1;
          ctx_valid[match_slot] <= 1'b0;
        end         else if (pkt_som && pkt_eom) begin
          start_addr_q <= sram_wr_ptr_in;
          total_len_q <= pkt_payload_count;
          byte_idx_q <= 16'd0;
          keep_context_q <= 1'b0;
          ctx_slot_q <= 4'd0;
          wr_ptr_q <= sram_wr_ptr_in;
          if ((pkt_payload_count > max_message_bytes) ||
              (pkt_payload_count > cfg_mtu_bytes) ||
              ((sram_wr_ptr_in + pkt_payload_count) > sram_limit) ||
              (sram_wr_ptr_in < sram_base) || desc_fifo_full) begin
            evt_assembly_drop <= 1'b1;
            evt_overflow_error <= 1'b1;
          end else begin
            state_q <= ST_WRITE;
          end
        end else if (pkt_som) begin
          if (!free_found || (pkt_payload_count > max_message_bytes) || (pkt_payload_count > cfg_mtu_bytes) ||
              ((sram_wr_ptr_in + max_message_bytes) > sram_limit) ||
              (sram_wr_ptr_in < sram_base)) begin
            evt_packet_drop <= 1'b1;
            evt_context_error <= 1'b1;
          end else begin
            ctx_valid[free_slot] <= 1'b1;
            ctx_src[free_slot] <= pkt_source_eid;
            ctx_tag_owner[free_slot] <= pkt_tag_owner;
            ctx_msg_tag[free_slot] <= pkt_message_tag;
            ctx_expected_seq[free_slot] <= (pkt_seq + 2'd1) & 2'd3;
            ctx_len[free_slot] <= pkt_payload_count;
            ctx_start[free_slot] <= sram_wr_ptr_in;
            ctx_msg_type[free_slot] <= pkt_message_type;
            ctx_req_id[free_slot] <= pkt_requester_id;
            ctx_dest[free_slot] <= pkt_dest_eid;
            ctx_slot_q <= free_slot;
            start_addr_q <= sram_wr_ptr_in;
            total_len_q <= pkt_payload_count;
            byte_idx_q <= 16'd0;
            keep_context_q <= !pkt_eom;
            wr_ptr_q <= sram_wr_ptr_in + max_message_bytes;
            state_q <= ST_WRITE;
          end
        end else begin
          ctx_slot_q <= match_slot;
          start_addr_q <= ctx_start[match_slot];
          total_len_q <= ctx_len[match_slot] + pkt_payload_count;
          byte_idx_q <= ctx_len[match_slot];
          keep_context_q <= !pkt_eom;
          src_eid_q <= ctx_src[match_slot];
          dest_eid_q <= ctx_dest[match_slot];
          tag_owner_q <= ctx_tag_owner[match_slot];
          msg_tag_q <= ctx_msg_tag[match_slot];
          msg_type_q <= ctx_msg_type[match_slot];
          req_id_q <= ctx_req_id[match_slot];
          if (((ctx_len[match_slot] + pkt_payload_count) > max_message_bytes) ||
              ((ctx_len[match_slot] + pkt_payload_count) > cfg_mtu_bytes) ||
              ((ctx_start[match_slot] + ctx_len[match_slot] + pkt_payload_count) > sram_limit) ||
              desc_fifo_full) begin
            evt_assembly_drop <= 1'b1;
            evt_overflow_error <= 1'b1;
            ctx_valid[match_slot] <= 1'b0;
          end else begin
            state_q <= ST_WRITE;
          end
        end
      end else if (state_q == ST_WRITE && wr_byte_valid) begin
        if ((byte_idx_q + 16'd1) >= total_len_q) begin
          state_q <= ST_FLUSH;
        end else begin
          byte_idx_q <= byte_idx_q + 16'd1;
        end
      end else if (state_q == ST_FLUSH && !writer_busy && wr_byte_ready) begin
        if (keep_context_q) begin
          ctx_len[ctx_slot_q] <= total_len_q;
          ctx_expected_seq[ctx_slot_q] <= (final_seq_q + 2'd1) & 2'd3;
          state_q <= ST_IDLE;
        end else begin
          state_q <= ST_DESC;
        end
      end else if (state_q == ST_DESC && !desc_fifo_full) begin
        if (!keep_context_q) begin
          wr_ptr_q <= start_addr_q + total_len_q;
          ctx_valid[ctx_slot_q] <= 1'b0;
        end else begin
          ctx_len[ctx_slot_q] <= total_len_q;
          ctx_expected_seq[ctx_slot_q] <= (final_seq_q + 2'd1) & 2'd3;
        end
        state_q <= ST_IDLE;
      end
    end
  end
endmodule
