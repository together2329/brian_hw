`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Synchronize APB configuration into AXI domain and AXI events/descriptors into APB domain.
module mctp_assembler_cdc #(
  parameter integer DESCRIPTOR_FIFO_DEPTH = `MCTP_ASSEMBLER_DESCRIPTOR_FIFO_DEPTH
) (
  input  logic        axi_aclk,
  input  logic        axi_aresetn,
  input  logic        pclk,
  input  logic        presetn,
  input  logic        cfg_enable_apb,
  input  logic        cfg_drop_when_disabled_apb,
  input  logic        cfg_dest_filter_enable_apb,
  input  logic        cfg_accept_broadcast_apb,
  input  logic        cfg_accept_null_apb,
  input  logic        cfg_soft_reset_apb,
  input  logic [7:0]  cfg_local_eid_apb,
  input  logic [15:0] cfg_max_message_bytes_apb,
  input  logic [15:0] cfg_mtu_bytes_apb,
  input  logic [23:0] cfg_timeout_cycles_apb,
  input  logic [15:0] cfg_sram_base_apb,
  input  logic [15:0] cfg_sram_limit_apb,
  output logic        cfg_enable,
  output logic        cfg_drop_when_disabled,
  output logic        cfg_dest_filter_enable,
  output logic        cfg_accept_broadcast_eid,
  output logic        cfg_accept_null_eid,
  output logic        cfg_soft_reset,
  output logic [7:0]  cfg_local_eid,
  output logic [15:0] cfg_max_message_bytes,
  output logic [15:0] cfg_mtu_bytes,
  output logic [23:0] cfg_timeout_cycles,
  output logic [15:0] cfg_sram_base,
  output logic [15:0] cfg_sram_limit,
  input  logic        evt_desc_ready_axi,
  input  logic        evt_packet_drop_axi,
  input  logic        evt_assembly_drop_axi,
  input  logic [7:0]  desc_source_eid_axi,
  input  logic [7:0]  desc_dest_eid_axi,
  input  logic        desc_tag_owner_axi,
  input  logic [2:0]  desc_message_tag_axi,
  input  logic [7:0]  desc_message_type_axi,
  input  logic [15:0] desc_payload_byte_count_axi,
  input  logic [15:0] desc_requester_id_axi,
  input  logic [15:0] desc_sram_start_addr_axi,
  input  logic [1:0]  desc_final_sequence_axi,
  input  logic [3:0]  desc_context_id_axi,
  input  logic [2:0]  desc_routing_axi,
  input  logic        desc_push_axi,
  input  logic        desc_pop_apb,
  output logic        desc_fifo_full,
  output logic [3:0]  desc_fifo_count,
  output logic [31:0] desc_word0,
  output logic [31:0] desc_word1,
  output logic [31:0] desc_word2,
  output logic [31:0] desc_word3,
  output logic        evt_desc_ready_apb,
  output logic        evt_packet_drop_apb,
  output logic        evt_assembly_drop_apb
);
  localparam integer DESC_PTR_WIDTH = 3;

  logic [1:0] enable_sync;
  logic [1:0] drop_sync;
  logic [1:0] filter_sync;
  logic [1:0] bcast_sync;
  logic [1:0] null_sync;
  logic [1:0] soft_sync;
  logic [7:0] local_eid_sync [0:1];
  logic [15:0] max_msg_sync [0:1];
  logic [15:0] mtu_sync [0:1];
  logic [23:0] timeout_sync [0:1];
  logic [15:0] base_sync [0:1];
  logic [15:0] limit_sync [0:1];

  logic [31:0] desc0_mem [0:DESCRIPTOR_FIFO_DEPTH-1];
  logic [31:0] desc1_mem [0:DESCRIPTOR_FIFO_DEPTH-1];
  logic [31:0] desc2_mem [0:DESCRIPTOR_FIFO_DEPTH-1];
  logic [31:0] desc3_mem [0:DESCRIPTOR_FIFO_DEPTH-1];
  logic [DESC_PTR_WIDTH-1:0] desc_wr_ptr;
  logic [DESC_PTR_WIDTH-1:0] desc_rd_ptr;
  logic [DESC_PTR_WIDTH:0] desc_count_axi;
  logic [DESC_PTR_WIDTH:0] desc_count_sync [0:1];
  logic [1:0] desc_pop_sync;
  wire desc_pop_axi = desc_pop_sync[1] & ~desc_pop_sync[0];

  logic [1:0] desc_ready_sync;
  logic [1:0] packet_drop_sync;
  logic [1:0] assembly_drop_sync;
  logic [2:0] desc_ready_stretch;
  logic [2:0] packet_drop_stretch;
  logic [2:0] assembly_drop_stretch;
  wire evt_desc_ready_axi_hold = |desc_ready_stretch;
  wire evt_packet_drop_axi_hold = |packet_drop_stretch;
  wire evt_assembly_drop_axi_hold = |assembly_drop_stretch;

  assign cfg_enable = enable_sync[1];
  assign cfg_drop_when_disabled = drop_sync[1];
  assign cfg_dest_filter_enable = filter_sync[1];
  assign cfg_accept_broadcast_eid = bcast_sync[1];
  assign cfg_accept_null_eid = null_sync[1];
  assign cfg_soft_reset = soft_sync[1];
  assign cfg_local_eid = local_eid_sync[1];
  assign cfg_max_message_bytes = max_msg_sync[1];
  assign cfg_mtu_bytes = mtu_sync[1];
  assign cfg_timeout_cycles = timeout_sync[1];
  assign cfg_sram_base = base_sync[1];
  assign cfg_sram_limit = limit_sync[1];

  assign desc_fifo_count = desc_count_sync[1][3:0];
  assign desc_fifo_full = (desc_count_axi >= 4'd8);
  assign desc_word0 = desc0_mem[desc_rd_ptr];
  assign desc_word1 = desc1_mem[desc_rd_ptr];
  assign desc_word2 = desc2_mem[desc_rd_ptr];
  assign desc_word3 = desc3_mem[desc_rd_ptr];

  wire [31:0] push_word0 = {
      desc_message_type_axi,
      4'd0,
      desc_tag_owner_axi,
      desc_message_tag_axi,
      desc_dest_eid_axi,
      desc_source_eid_axi
  };
  wire [31:0] push_word1 = {desc_requester_id_axi, desc_payload_byte_count_axi};
  wire [31:0] push_word2 = {16'd0, desc_sram_start_addr_axi};
  wire [31:0] push_word3 = {
      15'd0,
      desc_context_id_axi,
      desc_routing_axi,
      desc_final_sequence_axi,
      8'd0
  };

  always @(posedge axi_aclk) begin
    if (!axi_aresetn) begin
      enable_sync <= 2'b00;
      drop_sync <= 2'b00;
      filter_sync <= 2'b00;
      bcast_sync <= 2'b00;
      null_sync <= 2'b00;
      soft_sync <= 2'b00;
      local_eid_sync[0] <= 8'd0;
      local_eid_sync[1] <= 8'd0;
      max_msg_sync[0] <= 16'd4096;
      max_msg_sync[1] <= 16'd4096;
      mtu_sync[0] <= 16'd64;
      mtu_sync[1] <= 16'd64;
      timeout_sync[0] <= 24'd0;
      timeout_sync[1] <= 24'd0;
      base_sync[0] <= 16'd0;
      base_sync[1] <= 16'd0;
      limit_sync[0] <= 16'hFFFF;
      limit_sync[1] <= 16'hFFFF;
      desc_wr_ptr <= {DESC_PTR_WIDTH{1'b0}};
      desc_rd_ptr <= {DESC_PTR_WIDTH{1'b0}};
      desc_count_axi <= {(DESC_PTR_WIDTH + 1){1'b0}};
      desc_pop_sync <= 2'b00;
      desc_ready_stretch <= 3'b000;
      packet_drop_stretch <= 3'b000;
      assembly_drop_stretch <= 3'b000;
    end else begin
      enable_sync <= {enable_sync[0], cfg_enable_apb};
      drop_sync <= {drop_sync[0], cfg_drop_when_disabled_apb};
      filter_sync <= {filter_sync[0], cfg_dest_filter_enable_apb};
      bcast_sync <= {bcast_sync[0], cfg_accept_broadcast_apb};
      null_sync <= {null_sync[0], cfg_accept_null_apb};
      soft_sync <= {soft_sync[0], cfg_soft_reset_apb};
      local_eid_sync[0] <= cfg_local_eid_apb;
      local_eid_sync[1] <= local_eid_sync[0];
      max_msg_sync[0] <= cfg_max_message_bytes_apb;
      max_msg_sync[1] <= max_msg_sync[0];
      mtu_sync[0] <= cfg_mtu_bytes_apb;
      mtu_sync[1] <= mtu_sync[0];
      timeout_sync[0] <= cfg_timeout_cycles_apb;
      timeout_sync[1] <= timeout_sync[0];
      base_sync[0] <= cfg_sram_base_apb;
      base_sync[1] <= base_sync[0];
      limit_sync[0] <= cfg_sram_limit_apb;
      limit_sync[1] <= limit_sync[0];
      desc_pop_sync <= {desc_pop_sync[0], desc_pop_apb};
      if (evt_desc_ready_axi) begin
        desc_ready_stretch <= 3'b111;
      end else if (|desc_ready_stretch) begin
        desc_ready_stretch <= desc_ready_stretch - 3'd1;
      end
      if (evt_packet_drop_axi) begin
        packet_drop_stretch <= 3'b111;
      end else if (|packet_drop_stretch) begin
        packet_drop_stretch <= packet_drop_stretch - 3'd1;
      end
      if (evt_assembly_drop_axi) begin
        assembly_drop_stretch <= 3'b111;
      end else if (|assembly_drop_stretch) begin
        assembly_drop_stretch <= assembly_drop_stretch - 3'd1;
      end
      if (desc_push_axi && !desc_fifo_full) begin
        desc0_mem[desc_wr_ptr] <= push_word0;
        desc1_mem[desc_wr_ptr] <= push_word1;
        desc2_mem[desc_wr_ptr] <= push_word2;
        desc3_mem[desc_wr_ptr] <= push_word3;
        desc_wr_ptr <= desc_wr_ptr + 3'd1;
        desc_count_axi <= desc_count_axi + 4'd1;
      end else if (desc_pop_axi && (desc_count_axi != 4'd0)) begin
        desc_rd_ptr <= desc_rd_ptr + 3'd1;
        desc_count_axi <= desc_count_axi - 4'd1;
      end
    end
  end

  always @(posedge pclk) begin
    if (!presetn) begin
      desc_count_sync[0] <= {(DESC_PTR_WIDTH + 1){1'b0}};
      desc_count_sync[1] <= {(DESC_PTR_WIDTH + 1){1'b0}};
      desc_ready_sync <= 2'b00;
      packet_drop_sync <= 2'b00;
      assembly_drop_sync <= 2'b00;
      evt_desc_ready_apb <= 1'b0;
      evt_packet_drop_apb <= 1'b0;
      evt_assembly_drop_apb <= 1'b0;
    end else begin
      desc_count_sync[0] <= desc_count_axi;
      desc_count_sync[1] <= desc_count_sync[0];
      desc_ready_sync <= {desc_ready_sync[0], evt_desc_ready_axi_hold};
      packet_drop_sync <= {packet_drop_sync[0], evt_packet_drop_axi_hold};
      assembly_drop_sync <= {assembly_drop_sync[0], evt_assembly_drop_axi_hold};
      evt_desc_ready_apb <= desc_ready_sync[1] & ~desc_ready_sync[0];
      evt_packet_drop_apb <= packet_drop_sync[1] & ~packet_drop_sync[0];
      evt_assembly_drop_apb <= assembly_drop_sync[1] & ~assembly_drop_sync[0];
    end
  end
endmodule
