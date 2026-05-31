`timescale 1ns/1ps
`include "mctp_assembler_param.vh"
// Separate AXI read-slave path for burst SRAM payload readback.
module mctp_assembler_axi_read_egress #(
  parameter integer AXI_ADDR_WIDTH = `MCTP_ASSEMBLER_AXI_ADDR_WIDTH,
  parameter integer AXI_DATA_WIDTH = `MCTP_ASSEMBLER_AXI_DATA_WIDTH,
  parameter integer SRAM_ADDR_WIDTH = `MCTP_ASSEMBLER_SRAM_ADDR_WIDTH,
  parameter integer SRAM_DATA_WIDTH = `MCTP_ASSEMBLER_SRAM_DATA_WIDTH
) (
  input  logic                        axi_aclk,
  input  logic                        axi_aresetn,
  input  logic                        soft_reset,
  input  logic [15:0]                 sram_base,
  input  logic [15:0]                 sram_limit,
  input  logic [AXI_ADDR_WIDTH-1:0]   s_axi_araddr,
  input  logic [7:0]                  s_axi_arlen,
  input  logic [2:0]                  s_axi_arsize,
  input  logic [1:0]                  s_axi_arburst,
  input  logic                        s_axi_arvalid,
  output logic                        s_axi_arready,
  output logic [AXI_DATA_WIDTH-1:0]   s_axi_rdata,
  output logic [1:0]                  s_axi_rresp,
  output logic                        s_axi_rlast,
  output logic                        s_axi_rvalid,
  input  logic                        s_axi_rready,
  output logic                        sram_rd_valid,
  input  logic                        sram_rd_ready,
  output logic [SRAM_ADDR_WIDTH-1:0]  sram_rd_addr,
  input  logic [SRAM_DATA_WIDTH-1:0]  sram_rd_data,
  output logic                        read_busy
);
  localparam integer AXI_DATA_BYTES = AXI_DATA_WIDTH / 8;
  localparam [2:0] EXPECTED_ARSIZE = $clog2(AXI_DATA_BYTES);

  localparam [2:0] ST_IDLE = 3'd0;
  localparam [2:0] ST_SRAM_REQ = 3'd1;
  localparam [2:0] ST_RDATA = 3'd2;
  localparam [2:0] ST_ERROR = 3'd3;

  logic [2:0] state_q;
  logic [7:0] beats_left_q;
  logic [AXI_ADDR_WIDTH-1:0] cursor_q;
  logic [1:0] burst_q;
  logic [2:0] size_q;
  logic [SRAM_DATA_WIDTH-1:0] read_data_q;
  logic rvalid_q;
  logic rlast_q;
  logic [1:0] rresp_q;

  wire [7:0] beat_count = s_axi_arlen + 8'd1;
  wire [2:0] req_bytes_shift = (s_axi_arsize > EXPECTED_ARSIZE) ? EXPECTED_ARSIZE : s_axi_arsize;
  wire [15:0] bytes_per_beat = 16'd1 << req_bytes_shift;
  wire [16:0] end_addr_ext =
      {1'b0, s_axi_araddr[15:0]} + ({9'd0, beat_count} * bytes_per_beat) - 17'd1;
  wire ar_burst_ok = (s_axi_arburst == 2'b01) || (s_axi_arburst == 2'b00);
  wire ar_size_ok = s_axi_arsize <= EXPECTED_ARSIZE;
  wire ar_addr_ok = (s_axi_araddr[15:0] >= sram_base) &&
                    (end_addr_ext[16:0] <= {1'b0, sram_limit});
  wire ar_phase_ok = ar_burst_ok && ar_size_ok && ar_addr_ok;

  wire [2:0] active_bytes_shift = (size_q > EXPECTED_ARSIZE) ? EXPECTED_ARSIZE : size_q;
  wire [15:0] active_bytes_per_beat = 16'd1 << active_bytes_shift;
  wire final_beat = (beats_left_q == 8'd0);
  wire [AXI_ADDR_WIDTH-1:0] next_cursor =
      (burst_q == 2'b01) ? (cursor_q + active_bytes_per_beat[AXI_ADDR_WIDTH-1:0]) : cursor_q;

  assign read_busy = (state_q != ST_IDLE) || rvalid_q;
  assign s_axi_arready = (state_q == ST_IDLE) && !soft_reset;
  assign sram_rd_valid = (state_q == ST_SRAM_REQ);
  assign sram_rd_addr = cursor_q[SRAM_ADDR_WIDTH-1:0];

  assign s_axi_rdata = read_data_q[AXI_DATA_WIDTH-1:0];
  assign s_axi_rresp = rresp_q;
  assign s_axi_rlast = rlast_q;
  assign s_axi_rvalid = rvalid_q;

  always @(posedge axi_aclk) begin
    if (!axi_aresetn || soft_reset) begin
      state_q <= ST_IDLE;
      beats_left_q <= 8'd0;
      cursor_q <= {AXI_ADDR_WIDTH{1'b0}};
      burst_q <= 2'b01;
      size_q <= EXPECTED_ARSIZE;
      read_data_q <= {SRAM_DATA_WIDTH{1'b0}};
      rvalid_q <= 1'b0;
      rlast_q <= 1'b0;
      rresp_q <= 2'b00;
    end else begin
      case (state_q)
        ST_IDLE: begin
          if (s_axi_arvalid && s_axi_arready) begin
            beats_left_q <= s_axi_arlen;
            cursor_q <= s_axi_araddr;
            burst_q <= s_axi_arburst;
            size_q <= s_axi_arsize;
            if (ar_phase_ok) begin
              state_q <= ST_SRAM_REQ;
            end else begin
              state_q <= ST_ERROR;
              rvalid_q <= 1'b1;
              rlast_q <= final_beat;
              rresp_q <= 2'b10;
            end
          end
        end
        ST_SRAM_REQ: begin
          if (sram_rd_valid && sram_rd_ready) begin
            read_data_q <= sram_rd_data;
            state_q <= ST_RDATA;
            rvalid_q <= 1'b1;
            rlast_q <= final_beat;
            rresp_q <= 2'b00;
          end
        end
        ST_RDATA: begin
          if (rvalid_q && s_axi_rready) begin
            rvalid_q <= 1'b0;
            if (final_beat) begin
              state_q <= ST_IDLE;
            end else begin
              beats_left_q <= beats_left_q - 8'd1;
              cursor_q <= next_cursor;
              state_q <= ST_SRAM_REQ;
            end
          end
        end
        ST_ERROR: begin
          if (rvalid_q && s_axi_rready) begin
            rvalid_q <= 1'b0;
            if (final_beat) begin
              state_q <= ST_IDLE;
            end else begin
              beats_left_q <= beats_left_q - 8'd1;
              rvalid_q <= 1'b1;
              rlast_q <= (beats_left_q == 8'd1);
              rresp_q <= 2'b10;
            end
          end
        end
        default: state_q <= ST_IDLE;
      endcase
    end
  end
endmodule
