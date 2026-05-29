`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Accept one AXI write burst as one raw PCIe VDM TLP byte stream.
module mctp_assembler_axi_write_ingress #(
  parameter integer AXI_ADDR_WIDTH = `MCTP_ASSEMBLER_AXI_ADDR_WIDTH,
  parameter integer AXI_DATA_WIDTH = `MCTP_ASSEMBLER_AXI_DATA_WIDTH,
  parameter integer MAX_TLP_BYTES  = `MCTP_ASSEMBLER_MAX_TLP_BYTES
) (
  input  logic                        axi_aclk,
  input  logic                        axi_aresetn,
  input  logic                        enable,
  input  logic                        drop_when_disabled,
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
  input  logic                        soft_reset,
  output logic                        tlp_valid,
  input  logic                        tlp_ready,
  output logic [15:0]                 tlp_byte_count,
  output logic [7:0]                  tlp_byte0,
  output logic [7:0]                  tlp_byte1,
  output logic [7:0]                  tlp_byte2,
  output logic [7:0]                  tlp_byte3,
  output logic [7:0]                  tlp_byte4,
  output logic [7:0]                  tlp_byte5,
  output logic [7:0]                  tlp_byte6,
  output logic [7:0]                  tlp_byte7,
  output logic [7:0]                  tlp_byte8,
  output logic [7:0]                  tlp_byte9,
  output logic [7:0]                  tlp_byte10,
  output logic [7:0]                  tlp_byte11,
  output logic [7:0]                  tlp_byte12,
  output logic [7:0]                  tlp_byte13,
  output logic [7:0]                  tlp_byte14,
  output logic [7:0]                  tlp_byte15,
  output logic [7:0]                  tlp_payload_byte,
  input  logic [8:0]                  tlp_payload_index,
  output logic                        tlp_payload_valid,
  output logic                        ingress_busy,
  output logic                        ingress_malformed
);
  localparam integer TLP_IDX_WIDTH = 9;
  localparam integer AXI_DATA_BYTES = AXI_DATA_WIDTH / 8;
  localparam [2:0] EXPECTED_AWSIZE = $clog2(AXI_DATA_BYTES);

  localparam [2:0] ST_IDLE = 3'd0;
  localparam [2:0] ST_ADDR = 3'd1;
  localparam [2:0] ST_DATA = 3'd2;
  localparam [2:0] ST_RESP = 3'd3;

  logic [2:0] state_q;
  logic [7:0] beats_left_q;
  logic [TLP_IDX_WIDTH-1:0] byte_count_q;
  logic overflow_q;
  logic malformed_q;
  logic tlp_valid_q;
  logic enable_lat_q;
  logic accept_lat_q;
  logic [7:0] tlp_mem [0:MAX_TLP_BYTES-1];
  logic accept_burst;
  logic backpressure;
  logic capture_beat;
  logic [TLP_IDX_WIDTH-1:0] next_byte_count;
  logic beat_overflow;
  logic aw_phase_ok;
  logic [8:0] strb_pop_count;

  wire [10:0] next_byte_count_ext = {1'b0, byte_count_q} + {1'b0, strb_pop_count};

  wire [TLP_IDX_WIDTH-1:0] payload_mem_idx = 9'd16 + tlp_payload_index;

  integer lane_i;
  always @(*) begin
    strb_pop_count = 9'd0;
    for (lane_i = 0; lane_i < AXI_DATA_BYTES; lane_i = lane_i + 1) begin
      strb_pop_count = strb_pop_count + {8'd0, s_axi_wstrb[lane_i]};
    end
  end

  assign accept_burst = enable || drop_when_disabled;
  assign backpressure = (!enable && !drop_when_disabled) || (tlp_valid_q && !tlp_ready);
  assign ingress_busy = (state_q != ST_IDLE);
  assign ingress_malformed = malformed_q;
  assign tlp_byte_count = {7'd0, byte_count_q};
  assign tlp_valid = tlp_valid_q;
  assign capture_beat = (state_q == ST_DATA) && s_axi_wvalid && s_axi_wready;
  assign aw_phase_ok = (s_axi_awburst == 2'b01) &&
                       (s_axi_awsize == EXPECTED_AWSIZE) &&
                       (|s_axi_awaddr);

  assign tlp_byte0  = tlp_mem[9'd0];
  assign tlp_byte1  = tlp_mem[9'd1];
  assign tlp_byte2  = tlp_mem[9'd2];
  assign tlp_byte3  = tlp_mem[9'd3];
  assign tlp_byte4  = tlp_mem[9'd4];
  assign tlp_byte5  = tlp_mem[9'd5];
  assign tlp_byte6  = tlp_mem[9'd6];
  assign tlp_byte7  = tlp_mem[9'd7];
  assign tlp_byte8  = tlp_mem[9'd8];
  assign tlp_byte9  = tlp_mem[9'd9];
  assign tlp_byte10 = tlp_mem[9'd10];
  assign tlp_byte11 = tlp_mem[9'd11];
  assign tlp_byte12 = tlp_mem[9'd12];
  assign tlp_byte13 = tlp_mem[9'd13];
  assign tlp_byte14 = tlp_mem[9'd14];
  assign tlp_byte15 = tlp_mem[9'd15];
  assign tlp_payload_byte  = tlp_mem[payload_mem_idx];
  assign tlp_payload_valid = (payload_mem_idx < byte_count_q);

  assign s_axi_awready = (state_q == ST_ADDR) && accept_burst && !backpressure;
  assign s_axi_wready  = (state_q == ST_DATA) && accept_lat_q;
  assign s_axi_bvalid  = (state_q == ST_RESP);
  assign s_axi_bresp   = 2'b00;

  assign next_byte_count = next_byte_count_ext[TLP_IDX_WIDTH-1:0];
  assign beat_overflow = (next_byte_count_ext >= 11'd512);

  always @(posedge axi_aclk) begin
    if (!axi_aresetn || soft_reset) begin
      state_q <= ST_IDLE;
      beats_left_q <= 8'd0;
      byte_count_q <= {TLP_IDX_WIDTH{1'b0}};
      overflow_q <= 1'b0;
      malformed_q <= 1'b0;
      tlp_valid_q <= 1'b0;
      enable_lat_q <= 1'b0;
      accept_lat_q <= 1'b0;
    end else begin
      if (tlp_valid_q && tlp_ready) begin
        tlp_valid_q <= 1'b0;
        state_q <= ST_IDLE;
        byte_count_q <= {TLP_IDX_WIDTH{1'b0}};
        overflow_q <= 1'b0;
        malformed_q <= 1'b0;
      end else if (state_q == ST_IDLE && s_axi_awvalid && accept_burst && !backpressure) begin
        state_q <= ST_ADDR;
        byte_count_q <= {TLP_IDX_WIDTH{1'b0}};
        overflow_q <= 1'b0;
        malformed_q <= 1'b0;
      end else if (state_q == ST_ADDR && s_axi_awvalid && s_axi_awready) begin
        beats_left_q <= s_axi_awlen;
        enable_lat_q <= enable;
        accept_lat_q <= accept_burst;
        state_q <= ST_DATA;
        if (!aw_phase_ok) begin
          malformed_q <= 1'b1;
        end
      end else if (capture_beat) begin
        if (beat_overflow) begin
          overflow_q <= 1'b1;
        end else begin
          byte_count_q <= next_byte_count;
        end
        for (lane_i = 0; lane_i < AXI_DATA_BYTES; lane_i = lane_i + 1) begin
          if (s_axi_wstrb[lane_i] && !beat_overflow) begin
            tlp_mem[byte_count_q + lane_i[8:0]] <= s_axi_wdata[8 * lane_i +: 8];
          end
        end
        if (s_axi_wlast && (beats_left_q != 8'd0)) begin
          malformed_q <= 1'b1;
        end
        if (!s_axi_wlast && (beats_left_q == 8'd0)) begin
          malformed_q <= 1'b1;
        end
        if (beats_left_q != 8'd0) begin
          beats_left_q <= beats_left_q - 8'd1;
        end
        if (s_axi_wlast) begin
          state_q <= ST_RESP;
        end
      end else if (state_q == ST_RESP) begin
        if (enable_lat_q && !malformed_q && !overflow_q && (byte_count_q >= 9'd16)) begin
          tlp_valid_q <= 1'b1;
        end else if (s_axi_bready || !tlp_valid_q) begin
          state_q <= ST_IDLE;
        end
      end
    end
  end
endmodule
