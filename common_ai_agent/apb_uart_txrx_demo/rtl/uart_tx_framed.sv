`timescale 1ns/1ps
module uart_tx_framed #(
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      enable,
  input  logic                      tx_break,
  input  logic [1:0]                cfg_data_bits_sel,
  input  logic                      cfg_parity_en,
  input  logic                      cfg_parity_odd,
  input  logic                      cfg_stop2,
  input  logic [BAUD_DIV_WIDTH-1:0] baud_div,
  input  logic [7:0]                fifo_data,
  input  logic                      fifo_empty,
  output logic                      fifo_pop,
  output logic                      uart_tx,
  output logic                      tx_busy,
  output logic                      tx_idle,
  output logic                      tx_done_pulse
);
  localparam [2:0] TX_IDLE   = 3'd0;
  localparam [2:0] TX_START  = 3'd1;
  localparam [2:0] TX_DATA   = 3'd2;
  localparam [2:0] TX_PARITY = 3'd3;
  localparam [2:0] TX_STOP   = 3'd4;

  logic [2:0] tx_state;
  logic [BAUD_DIV_WIDTH-1:0] bit_cnt;
  logic [3:0] data_bits_latched;
  logic       parity_en_latched;
  logic       parity_odd_latched;
  logic       stop2_latched;
  logic [7:0] shifter;
  logic [2:0] bit_idx;
  logic       parity_bit;
  logic [1:0] stop_idx;
  logic       tx_line_reg;

  assign tx_busy = (tx_state != TX_IDLE);
  assign tx_idle = (tx_state == TX_IDLE);
  assign uart_tx = tx_break ? 1'b0 : tx_line_reg;

  function automatic [3:0] cfg_data_bits(input logic [1:0] sel);
    begin
      case (sel)
        2'd0: cfg_data_bits = 4'd5;
        2'd1: cfg_data_bits = 4'd6;
        2'd2: cfg_data_bits = 4'd7;
        default: cfg_data_bits = 4'd8;
      endcase
    end
  endfunction

  function automatic logic selected_parity(input logic [7:0] data, input logic [3:0] bits, input logic odd);
    logic parity_xor;
    begin
      parity_xor = 1'b0;
      if (bits > 4'd0) parity_xor = parity_xor ^ data[0];
      if (bits > 4'd1) parity_xor = parity_xor ^ data[1];
      if (bits > 4'd2) parity_xor = parity_xor ^ data[2];
      if (bits > 4'd3) parity_xor = parity_xor ^ data[3];
      if (bits > 4'd4) parity_xor = parity_xor ^ data[4];
      if (bits > 4'd5) parity_xor = parity_xor ^ data[5];
      if (bits > 4'd6) parity_xor = parity_xor ^ data[6];
      if (bits > 4'd7) parity_xor = parity_xor ^ data[7];
      selected_parity = odd ? ~parity_xor : parity_xor;
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] bit_reload(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      bit_reload = (div <= {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1}) ? {BAUD_DIV_WIDTH{1'b0}} : (div - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1});
    end
  endfunction

  wire bit_done = (bit_cnt == {BAUD_DIV_WIDTH{1'b0}});
  wire [BAUD_DIV_WIDTH-1:0] reload_value = bit_reload(baud_div);

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      tx_state <= TX_IDLE;
      bit_cnt <= {BAUD_DIV_WIDTH{1'b0}};
      data_bits_latched <= 4'd8;
      parity_en_latched <= 1'b0;
      parity_odd_latched <= 1'b0;
      stop2_latched <= 1'b0;
      shifter <= 8'h00;
      bit_idx <= 3'd0;
      parity_bit <= 1'b0;
      stop_idx <= 2'd0;
      tx_line_reg <= 1'b1;
      fifo_pop <= 1'b0;
      tx_done_pulse <= 1'b0;
    end else begin
      fifo_pop <= 1'b0;
      tx_done_pulse <= 1'b0;

      if (!enable) begin
        tx_state <= TX_IDLE;
        bit_cnt <= {BAUD_DIV_WIDTH{1'b0}};
        bit_idx <= 3'd0;
        stop_idx <= 2'd0;
        tx_line_reg <= 1'b1;
      end else begin
        case (tx_state)
          TX_IDLE: begin
            tx_line_reg <= 1'b1;
            bit_cnt <= {BAUD_DIV_WIDTH{1'b0}};
            bit_idx <= 3'd0;
            stop_idx <= 2'd0;
            if (!tx_break && !fifo_empty) begin
              fifo_pop <= 1'b1;
              shifter <= fifo_data;
              data_bits_latched <= cfg_data_bits(cfg_data_bits_sel);
              parity_en_latched <= cfg_parity_en;
              parity_odd_latched <= cfg_parity_odd;
              stop2_latched <= cfg_stop2;
              parity_bit <= selected_parity(fifo_data, cfg_data_bits(cfg_data_bits_sel), cfg_parity_odd);
              tx_state <= TX_START;
              tx_line_reg <= 1'b0;
              bit_cnt <= reload_value;
            end
          end

          TX_START: begin
            tx_line_reg <= 1'b0;
            if (bit_done) begin
              tx_state <= TX_DATA;
              bit_idx <= 3'd0;
              tx_line_reg <= shifter[0];
              bit_cnt <= reload_value;
            end else begin
              bit_cnt <= bit_cnt - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          TX_DATA: begin
            tx_line_reg <= shifter[bit_idx];
            if (bit_done) begin
              if ({1'b0, bit_idx} == (data_bits_latched - 4'd1)) begin
                if (parity_en_latched) begin
                  tx_state <= TX_PARITY;
                  tx_line_reg <= parity_bit;
                end else begin
                  tx_state <= TX_STOP;
                  tx_line_reg <= 1'b1;
                  stop_idx <= 2'd0;
                end
              end else begin
                bit_idx <= bit_idx + 3'd1;
                tx_line_reg <= shifter[bit_idx + 3'd1];
              end
              bit_cnt <= reload_value;
            end else begin
              bit_cnt <= bit_cnt - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          TX_PARITY: begin
            tx_line_reg <= parity_bit;
            if (bit_done) begin
              tx_state <= TX_STOP;
              tx_line_reg <= 1'b1;
              stop_idx <= 2'd0;
              bit_cnt <= reload_value;
            end else begin
              bit_cnt <= bit_cnt - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          TX_STOP: begin
            tx_line_reg <= 1'b1;
            if (bit_done) begin
              if (stop2_latched && stop_idx == 2'd0) begin
                stop_idx <= 2'd1;
                bit_cnt <= reload_value;
              end else begin
                tx_state <= TX_IDLE;
                tx_done_pulse <= 1'b1;
                stop_idx <= 2'd0;
              end
            end else begin
              bit_cnt <= bit_cnt - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          default: begin
            tx_state <= TX_IDLE;
            tx_line_reg <= 1'b1;
          end
        endcase
      end
    end
  end
endmodule
