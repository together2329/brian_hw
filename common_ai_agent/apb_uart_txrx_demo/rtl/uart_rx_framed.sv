`timescale 1ns/1ps
// uart_rx_framed.sv — configurable UART receiver with synchronized input,
// false-start rejection, baud-derived 3-sample majority voting, parity/stop
// checking, break detection, and RX FIFO push handshake.
module uart_rx_framed #(
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      enable,
  input  logic                      uart_rx,
  input  logic [1:0]                cfg_data_bits_sel,
  input  logic                      cfg_parity_en,
  input  logic                      cfg_parity_odd,
  input  logic                      cfg_stop2,
  input  logic [BAUD_DIV_WIDTH-1:0] baud_div,
  input  logic                      rx_fifo_full,
  output logic                      rx_fifo_push,
  output logic [7:0]                rx_fifo_data,
  output logic                      rx_activity_pulse,
  output logic                      frame_err_pulse,
  output logic                      parity_err_pulse,
  output logic                      break_err_pulse,
  output logic                      overrun_err_pulse
);
  localparam [2:0] RX_IDLE   = 3'd0;
  localparam [2:0] RX_START  = 3'd1;
  localparam [2:0] RX_DATA   = 3'd2;
  localparam [2:0] RX_PARITY = 3'd3;
  localparam [2:0] RX_STOP   = 3'd4;

  logic [2:0] rx_state;
  logic [BAUD_DIV_WIDTH-1:0] rx_cnt;
  logic [2:0] rx_bit_idx;
  logic [7:0] rx_shift;
  logic       uart_rx_meta;
  logic       uart_rx_sync;
  logic       uart_rx_prev;
  logic       sample_early;
  logic       sample_mid;
  logic       sample_late;
  logic [3:0] data_bits_latched;
  logic       parity_en_latched;
  logic       parity_odd_latched;
  logic       stop2_latched;
  logic       parity_err_latched;
  logic       frame_err_latched;
  logic       break_low_latched;
  logic [1:0] stop_idx;

  function automatic logic majority3(input logic a, input logic b, input logic c);
    begin
      majority3 = (a & b) | (a & c) | (b & c);
    end
  endfunction

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

  function automatic [7:0] mask_rx_data(input logic [7:0] data, input logic [3:0] bits);
    begin
      case (bits)
        4'd5: mask_rx_data = {3'b000, data[4:0]};
        4'd6: mask_rx_data = {2'b00, data[5:0]};
        4'd7: mask_rx_data = {1'b0, data[6:0]};
        default: mask_rx_data = data;
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

  function automatic [BAUD_DIV_WIDTH-1:0] bit_last(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      bit_last = (div <= {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1}) ? {BAUD_DIV_WIDTH{1'b0}} : (div - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1});
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] center_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      center_sample_pos = (div <= {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1}) ? {BAUD_DIV_WIDTH{1'b0}} : (div >> 1);
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] center_sample_spread(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      center_sample_spread = div >> 4;
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] early_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    logic [BAUD_DIV_WIDTH-1:0] center;
    logic [BAUD_DIV_WIDTH-1:0] spread;
    begin
      center = center_sample_pos(div);
      spread = center_sample_spread(div);
      early_sample_pos = (center > spread) ? (center - spread) : {BAUD_DIV_WIDTH{1'b0}};
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] late_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    logic [BAUD_DIV_WIDTH-1:0] center;
    logic [BAUD_DIV_WIDTH-1:0] spread;
    logic [BAUD_DIV_WIDTH-1:0] candidate;
    begin
      center = center_sample_pos(div);
      spread = center_sample_spread(div);
      candidate = center + spread;
      late_sample_pos = (candidate >= div) ? bit_last(div) : candidate;
    end
  endfunction

  function automatic logic vote_with_current_sample(
    input logic early_sample,
    input logic mid_sample,
    input logic late_sample,
    input logic current_rx,
    input logic early_now,
    input logic mid_now,
    input logic late_now
  );
    logic early_eff;
    logic mid_eff;
    logic late_eff;
    begin
      early_eff = early_now ? current_rx : early_sample;
      mid_eff   = mid_now   ? current_rx : mid_sample;
      late_eff  = late_now  ? current_rx : late_sample;
      vote_with_current_sample = majority3(early_eff, mid_eff, late_eff);
    end
  endfunction

  wire [BAUD_DIV_WIDTH-1:0] sample_pos_early = early_sample_pos(baud_div);
  wire [BAUD_DIV_WIDTH-1:0] sample_pos_mid   = center_sample_pos(baud_div);
  wire [BAUD_DIV_WIDTH-1:0] sample_pos_late  = late_sample_pos(baud_div);
  wire [BAUD_DIV_WIDTH-1:0] bit_last_pos     = bit_last(baud_div);

  wire sample_early_now = (rx_cnt == sample_pos_early);
  wire sample_mid_now   = (rx_cnt == sample_pos_mid);
  wire sample_late_now  = (rx_cnt == sample_pos_late);
  wire bit_done_now     = (rx_cnt >= bit_last_pos);
  wire start_edge       = enable && uart_rx_prev && !uart_rx_sync;
  wire voted_rx_now     = vote_with_current_sample(sample_early, sample_mid, sample_late,
                                                   uart_rx_sync, sample_early_now,
                                                   sample_mid_now, sample_late_now);

  task automatic clear_vote_samples;
    begin
      sample_early <= 1'b1;
      sample_mid   <= 1'b1;
      sample_late  <= 1'b1;
    end
  endtask

  task automatic capture_vote_samples;
    begin
      if (sample_early_now) sample_early <= uart_rx_sync;
      if (sample_mid_now)   sample_mid   <= uart_rx_sync;
      if (sample_late_now)  sample_late  <= uart_rx_sync;
    end
  endtask

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      rx_state            <= RX_IDLE;
      rx_cnt              <= {BAUD_DIV_WIDTH{1'b0}};
      rx_bit_idx          <= 3'd0;
      rx_shift            <= 8'h00;
      uart_rx_meta        <= 1'b1;
      uart_rx_sync        <= 1'b1;
      uart_rx_prev        <= 1'b1;
      sample_early        <= 1'b1;
      sample_mid          <= 1'b1;
      sample_late         <= 1'b1;
      data_bits_latched   <= 4'd8;
      parity_en_latched   <= 1'b0;
      parity_odd_latched  <= 1'b0;
      stop2_latched       <= 1'b0;
      parity_err_latched  <= 1'b0;
      frame_err_latched   <= 1'b0;
      break_low_latched   <= 1'b0;
      stop_idx            <= 2'd0;
      rx_fifo_push        <= 1'b0;
      rx_fifo_data        <= 8'h00;
      rx_activity_pulse   <= 1'b0;
      frame_err_pulse     <= 1'b0;
      parity_err_pulse    <= 1'b0;
      break_err_pulse     <= 1'b0;
      overrun_err_pulse   <= 1'b0;
    end else begin
      uart_rx_meta <= uart_rx;
      uart_rx_sync <= uart_rx_meta;
      uart_rx_prev <= uart_rx_sync;

      rx_fifo_push      <= 1'b0;
      rx_activity_pulse <= 1'b0;
      frame_err_pulse   <= 1'b0;
      parity_err_pulse  <= 1'b0;
      break_err_pulse   <= 1'b0;
      overrun_err_pulse <= 1'b0;

      if (!enable) begin
        rx_state           <= RX_IDLE;
        rx_cnt             <= {BAUD_DIV_WIDTH{1'b0}};
        rx_bit_idx         <= 3'd0;
        parity_err_latched <= 1'b0;
        frame_err_latched  <= 1'b0;
        break_low_latched  <= 1'b0;
        stop_idx           <= 2'd0;
        clear_vote_samples();
      end else begin
        case (rx_state)
          RX_IDLE: begin
            rx_cnt             <= {BAUD_DIV_WIDTH{1'b0}};
            rx_bit_idx         <= 3'd0;
            parity_err_latched <= 1'b0;
            frame_err_latched  <= 1'b0;
            break_low_latched  <= 1'b0;
            stop_idx           <= 2'd0;
            clear_vote_samples();
            if (start_edge) begin
              rx_state           <= RX_START;
              rx_cnt             <= {BAUD_DIV_WIDTH{1'b0}};
              data_bits_latched  <= cfg_data_bits(cfg_data_bits_sel);
              parity_en_latched  <= cfg_parity_en;
              parity_odd_latched <= cfg_parity_odd;
              stop2_latched      <= cfg_stop2;
              break_low_latched  <= 1'b1;
              rx_activity_pulse  <= 1'b1;
              // Seed start-bit samples low at the detected falling edge so
              // tiny simulation divisors still behave like a valid UART start.
              sample_early       <= 1'b0;
              sample_mid         <= 1'b0;
              sample_late        <= 1'b0;
            end
          end

          RX_START: begin
            capture_vote_samples();
            if (bit_done_now) begin
              if (!voted_rx_now) begin
                rx_state   <= RX_DATA;
                rx_cnt     <= {BAUD_DIV_WIDTH{1'b0}};
                rx_bit_idx <= 3'd0;
                rx_shift   <= 8'h00;
                clear_vote_samples();
              end else begin
                // False start/glitch: line returned high by the start-bit vote.
                rx_state          <= RX_IDLE;
                rx_cnt            <= {BAUD_DIV_WIDTH{1'b0}};
                break_low_latched <= 1'b0;
                clear_vote_samples();
              end
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          RX_DATA: begin
            capture_vote_samples();
            if (bit_done_now) begin
              rx_shift[rx_bit_idx] <= voted_rx_now;
              if (voted_rx_now) begin
                break_low_latched <= 1'b0;
              end
              rx_cnt <= {BAUD_DIV_WIDTH{1'b0}};
              clear_vote_samples();
              if ({1'b0, rx_bit_idx} == (data_bits_latched - 4'd1)) begin
                if (parity_en_latched) begin
                  rx_state <= RX_PARITY;
                end else begin
                  rx_state <= RX_STOP;
                  stop_idx <= 2'd0;
                end
              end else begin
                rx_bit_idx <= rx_bit_idx + 3'd1;
              end
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          RX_PARITY: begin
            capture_vote_samples();
            if (bit_done_now) begin
              if (voted_rx_now != selected_parity(rx_shift, data_bits_latched, parity_odd_latched)) begin
                parity_err_latched <= 1'b1;
              end
              if (voted_rx_now) begin
                break_low_latched <= 1'b0;
              end
              rx_state <= RX_STOP;
              rx_cnt   <= {BAUD_DIV_WIDTH{1'b0}};
              stop_idx <= 2'd0;
              clear_vote_samples();
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          RX_STOP: begin
            capture_vote_samples();
            if (bit_done_now) begin
              if (!voted_rx_now) begin
                frame_err_latched <= 1'b1;
              end
              if (voted_rx_now) begin
                break_low_latched <= 1'b0;
              end

              if (stop2_latched && stop_idx == 2'd0) begin
                stop_idx <= 2'd1;
                rx_cnt   <= {BAUD_DIV_WIDTH{1'b0}};
                clear_vote_samples();
              end else begin
                if (frame_err_latched || !voted_rx_now) begin
                  frame_err_pulse <= 1'b1;
                end
                if (parity_err_latched) begin
                  parity_err_pulse <= 1'b1;
                end
                if (break_low_latched && !voted_rx_now) begin
                  break_err_pulse <= 1'b1;
                end
                if (rx_fifo_full) begin
                  overrun_err_pulse <= 1'b1;
                end else begin
                  rx_fifo_data <= mask_rx_data(rx_shift, data_bits_latched);
                  rx_fifo_push <= 1'b1;
                end
                rx_activity_pulse <= 1'b1;
                rx_state          <= RX_IDLE;
                rx_cnt            <= {BAUD_DIV_WIDTH{1'b0}};
                rx_bit_idx        <= 3'd0;
                parity_err_latched <= 1'b0;
                frame_err_latched  <= 1'b0;
                break_low_latched  <= 1'b0;
                stop_idx           <= 2'd0;
                clear_vote_samples();
              end
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          default: begin
            rx_state <= RX_IDLE;
            rx_cnt   <= {BAUD_DIV_WIDTH{1'b0}};
            clear_vote_samples();
          end
        endcase
      end
    end
  end
endmodule
