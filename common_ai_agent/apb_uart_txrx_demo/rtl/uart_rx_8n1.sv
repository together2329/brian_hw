`timescale 1ns/1ps
module uart_rx_8n1 #(
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      enable,
  input  logic                      uart_rx,
  input  logic [BAUD_DIV_WIDTH-1:0] baud_div,
  input  logic                      rx_full,
  output logic                      rx_valid_pulse,
  output logic [7:0]                rx_data,
  output logic                      frame_err_pulse,
  output logic                      overrun_err_pulse
);
  localparam [1:0] RX_IDLE = 2'd0, RX_START = 2'd1, RX_DATA = 2'd2, RX_STOP = 2'd3;

  logic [1:0] rx_state;
  logic [BAUD_DIV_WIDTH-1:0] rx_cnt;
  logic [2:0] rx_bit_idx;
  logic [7:0] rx_shift;
  logic       uart_rx_q1, uart_rx_q2;

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      rx_state          <= RX_IDLE;
      rx_cnt            <= '0;
      rx_bit_idx        <= 3'd0;
      rx_shift          <= 8'h00;
      rx_data           <= 8'h00;
      uart_rx_q1        <= 1'b1;
      uart_rx_q2        <= 1'b1;
      rx_valid_pulse    <= 1'b0;
      frame_err_pulse   <= 1'b0;
      overrun_err_pulse <= 1'b0;
    end else begin
      uart_rx_q1 <= uart_rx;
      uart_rx_q2 <= uart_rx_q1;
      rx_valid_pulse    <= 1'b0;
      frame_err_pulse   <= 1'b0;
      overrun_err_pulse <= 1'b0;

      case (rx_state)
        RX_IDLE: begin
          rx_cnt <= '0;
          rx_bit_idx <= 3'd0;
          if (enable && uart_rx_q2 && !uart_rx_q1) begin
            rx_state <= RX_START;
            rx_cnt <= (baud_div >> 1);
          end
        end
        RX_START: begin
          if (rx_cnt == 0) begin
            if (!uart_rx_q2) begin
              rx_state <= RX_DATA;
              rx_cnt <= baud_div - 1'b1;
              rx_bit_idx <= 3'd0;
            end else begin
              rx_state <= RX_IDLE;
            end
          end else rx_cnt <= rx_cnt - 1'b1;
        end
        RX_DATA: begin
          if (rx_cnt == 0) begin
            rx_shift[rx_bit_idx] <= uart_rx_q2;
            if (rx_bit_idx == 3'd7) begin
              rx_state <= RX_STOP;
            end else begin
              rx_bit_idx <= rx_bit_idx + 1'b1;
            end
            rx_cnt <= baud_div - 1'b1;
          end else rx_cnt <= rx_cnt - 1'b1;
        end
        RX_STOP: begin
          if (rx_cnt == 0) begin
            if (!uart_rx_q2) begin
              frame_err_pulse <= 1'b1;
            end else if (rx_full) begin
              overrun_err_pulse <= 1'b1;
            end else begin
              rx_data <= rx_shift;
              rx_valid_pulse <= 1'b1;
            end
            rx_state <= RX_IDLE;
          end else rx_cnt <= rx_cnt - 1'b1;
        end
        default: rx_state <= RX_IDLE;
      endcase
    end
  end
endmodule
