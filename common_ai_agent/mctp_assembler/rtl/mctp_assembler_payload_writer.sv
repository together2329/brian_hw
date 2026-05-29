`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Pack payload bytes into SRAM write beats.
module mctp_assembler_payload_writer #(
  parameter integer SRAM_ADDR_WIDTH = `MCTP_ASSEMBLER_SRAM_ADDR_WIDTH,
  parameter integer SRAM_DATA_WIDTH = `MCTP_ASSEMBLER_SRAM_DATA_WIDTH
) (
  input  logic                        axi_aclk,
  input  logic                        axi_aresetn,
  input  logic                        soft_reset,
  input  logic                        wr_byte_valid,
  input  logic [7:0]                  wr_byte_data,
  input  logic [SRAM_ADDR_WIDTH-1:0]  wr_byte_addr,
  input  logic                        wr_flush,
  output logic                        wr_byte_ready,
  output logic                        sram_wr_valid,
  input  logic                        sram_wr_ready,
  output logic [SRAM_ADDR_WIDTH-1:0]  sram_wr_addr,
  output logic [SRAM_DATA_WIDTH-1:0]  sram_wr_data,
  output logic [SRAM_DATA_WIDTH/8-1:0] sram_wr_strb,
  output logic                        writer_busy
);
  localparam integer SRAM_DATA_BYTES = SRAM_DATA_WIDTH / 8;
  localparam integer BEAT_SHIFT = (SRAM_DATA_BYTES <= 1) ? 0 : $clog2(SRAM_DATA_BYTES);
  localparam integer LANE_W = (BEAT_SHIFT == 0) ? 1 : BEAT_SHIFT;

  logic [SRAM_DATA_WIDTH-1:0] pack_data_q;
  logic [SRAM_DATA_BYTES-1:0] pack_strb_q;
  logic [SRAM_ADDR_WIDTH-1:0] pack_addr_q;
  logic hold_q;
  logic [SRAM_DATA_WIDTH-1:0] pack_data_next;

  wire [LANE_W-1:0] lane_base = wr_byte_addr[LANE_W-1:0];
  wire [SRAM_ADDR_WIDTH-1:0] beat_addr =
      {wr_byte_addr[SRAM_ADDR_WIDTH-1:BEAT_SHIFT], {BEAT_SHIFT{1'b0}}};
  wire beat_full = (lane_base == (SRAM_DATA_BYTES - 1));
  wire need_flush = wr_flush && (pack_strb_q != {SRAM_DATA_BYTES{1'b0}});

  assign writer_busy = hold_q || (pack_strb_q != {SRAM_DATA_BYTES{1'b0}});
  assign wr_byte_ready = !hold_q && sram_wr_ready;
  assign sram_wr_valid = hold_q;
  assign sram_wr_addr = pack_addr_q;
  assign sram_wr_data = pack_data_q;
  assign sram_wr_strb = pack_strb_q;

  always @(*) begin
    pack_data_next = pack_data_q;
    if (wr_byte_valid && wr_byte_ready) begin
      pack_data_next[8 * lane_base +: 8] = wr_byte_data;
    end
  end

  always @(posedge axi_aclk) begin
    if (!axi_aresetn || soft_reset) begin
      pack_data_q <= {SRAM_DATA_WIDTH{1'b0}};
      pack_strb_q <= {SRAM_DATA_BYTES{1'b0}};
      pack_addr_q <= {SRAM_ADDR_WIDTH{1'b0}};
      hold_q <= 1'b0;
    end else begin
      if (hold_q && sram_wr_ready) begin
        hold_q <= 1'b0;
        pack_data_q <= {SRAM_DATA_WIDTH{1'b0}};
        pack_strb_q <= {SRAM_DATA_BYTES{1'b0}};
      end else if (need_flush && !hold_q && sram_wr_ready) begin
        hold_q <= 1'b1;
        pack_addr_q <= beat_addr;
      end else if (wr_byte_valid && wr_byte_ready) begin
        pack_data_q <= pack_data_next;
        pack_addr_q <= beat_addr;
        pack_strb_q[lane_base] <= 1'b1;
        if (beat_full) begin
          hold_q <= 1'b1;
        end
      end
    end
  end
endmodule
