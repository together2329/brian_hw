`timescale 1ns/1ps
module uart_tx_8n1 #(
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      enable,
  input  logic                      tx_break,
  input  logic                      tx_start,
  input  logic [7:0]                tx_data,
  input  logic [BAUD_DIV_WIDTH-1:0] baud_div,
  output logic                      uart_tx,
  output logic                      tx_busy,
  output logic                      tx_empty,
  output logic                      tx_done_pulse
);
  localparam [1:0] TX_IDLE = 2'd0, TX_START = 2'd1, TX_DATA = 2'd2, TX_STOP = 2'd3;

  logic [1:0] tx_state;
  logic [BAUD_DIV_WIDTH-1:0] tx_cnt;
  logic [2:0] tx_bit_idx;
  logic [7:0] tx_shift;
  logic       tx_line_reg;

  assign tx_busy  = (tx_state != TX_IDLE);
  assign tx_empty = !tx_busy;
  assign uart_tx  = tx_break ? 1'b0 : tx_line_reg;

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      tx_state      <= TX_IDLE;
      tx_cnt        <= '0;
      tx_bit_idx    <= 3'd0;
      tx_shift      <= 8'h00;
      tx_line_reg   <= 1'b1;
      tx_done_pulse <= 1'b0;
    end else begin
      tx_done_pulse <= 1'b0;
      case (tx_state)
        TX_IDLE: begin
          tx_line_reg <= 1'b1;
          tx_cnt <= '0;
          tx_bit_idx <= 3'd0;
          if (tx_start && enable) begin
            tx_shift <= tx_data;
            tx_state <= TX_START;
            tx_line_reg <= 1'b0;
            tx_cnt <= baud_div - 1'b1;
          end
        end
        TX_START: begin
          tx_line_reg <= 1'b0;
          if (tx_cnt == 0) begin
            tx_state <= TX_DATA;
            tx_line_reg <= tx_shift[0];
            tx_bit_idx <= 3'd0;
            tx_cnt <= baud_div - 1'b1;
          end else tx_cnt <= tx_cnt - 1'b1;
        end
        TX_DATA: begin
          tx_line_reg <= tx_shift[tx_bit_idx];
          if (tx_cnt == 0) begin
            if (tx_bit_idx == 3'd7) begin
              tx_state <= TX_STOP;
              tx_line_reg <= 1'b1;
            end else begin
              tx_bit_idx <= tx_bit_idx + 1'b1;
              tx_line_reg <= tx_shift[tx_bit_idx + 1'b1];
            end
            tx_cnt <= baud_div - 1'b1;
          end else tx_cnt <= tx_cnt - 1'b1;
        end
        TX_STOP: begin
          tx_line_reg <= 1'b1;
          if (tx_cnt == 0) begin
            tx_state <= TX_IDLE;
            tx_done_pulse <= 1'b1;
          end else tx_cnt <= tx_cnt - 1'b1;
        end
        default: tx_state <= TX_IDLE;
      endcase
    end
  end
endmodule
