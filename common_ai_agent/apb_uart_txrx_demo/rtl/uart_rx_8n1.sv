`timescale 1ns/1ps
// uart_rx_8n1.sv — fixed 8N1 UART receiver with synchronized input,
// false-start rejection, and baud-derived 3-sample majority voting.
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
  localparam [1:0] RX_IDLE  = 2'd0;
  localparam [1:0] RX_START = 2'd1;
  localparam [1:0] RX_DATA  = 2'd2;
  localparam [1:0] RX_STOP  = 2'd3;

  logic [1:0] rx_state;
  logic [BAUD_DIV_WIDTH-1:0] rx_cnt;
  logic [2:0] rx_bit_idx;
  logic [7:0] rx_shift;
  logic       uart_rx_meta, uart_rx_sync, uart_rx_prev;
  logic       sample_early, sample_mid, sample_late;

  function automatic logic majority3(input logic a, input logic b, input logic c);
    majority3 = (a & b) | (a & c) | (b & c);
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] bit_last(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      bit_last = (div <= {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1}) ? '0 : (div - {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1});
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] center_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      center_sample_pos = (div <= {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1}) ? '0 : (div >> 1);
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] center_sample_spread(input [BAUD_DIV_WIDTH-1:0] div);
    begin
      // One 16x-UART sample tick for production divisors, collapsed to zero
      // for tiny simulation divisors that cannot represent distinct samples.
      center_sample_spread = div >> 4;
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] early_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    reg [BAUD_DIV_WIDTH-1:0] center;
    reg [BAUD_DIV_WIDTH-1:0] spread;
    begin
      center = center_sample_pos(div);
      spread = center_sample_spread(div);
      early_sample_pos = (center > spread) ? (center - spread) : '0;
    end
  endfunction

  function automatic [BAUD_DIV_WIDTH-1:0] late_sample_pos(input [BAUD_DIV_WIDTH-1:0] div);
    reg [BAUD_DIV_WIDTH-1:0] center;
    reg [BAUD_DIV_WIDTH-1:0] spread;
    reg [BAUD_DIV_WIDTH-1:0] candidate;
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
      rx_state          <= RX_IDLE;
      rx_cnt            <= '0;
      rx_bit_idx        <= 3'd0;
      rx_shift          <= 8'h00;
      rx_data           <= 8'h00;
      uart_rx_meta      <= 1'b1;
      uart_rx_sync      <= 1'b1;
      uart_rx_prev      <= 1'b1;
      sample_early      <= 1'b1;
      sample_mid        <= 1'b1;
      sample_late       <= 1'b1;
      rx_valid_pulse    <= 1'b0;
      frame_err_pulse   <= 1'b0;
      overrun_err_pulse <= 1'b0;
    end else begin
      uart_rx_meta <= uart_rx;
      uart_rx_sync <= uart_rx_meta;
      uart_rx_prev <= uart_rx_sync;

      rx_valid_pulse    <= 1'b0;
      frame_err_pulse   <= 1'b0;
      overrun_err_pulse <= 1'b0;

      if (!enable) begin
        rx_state <= RX_IDLE;
        rx_cnt <= '0;
        rx_bit_idx <= 3'd0;
        clear_vote_samples();
      end else begin
        case (rx_state)
          RX_IDLE: begin
            rx_cnt <= '0;
            rx_bit_idx <= 3'd0;
            clear_vote_samples();
            if (start_edge) begin
              rx_state <= RX_START;
              rx_cnt <= '0;
              // Seed start-bit samples low at the detected falling edge so
              // minimum simulation divisors still behave as a valid 8N1 RX.
              sample_early <= 1'b0;
              sample_mid   <= 1'b0;
              sample_late  <= 1'b0;
            end
          end

          RX_START: begin
            capture_vote_samples();
            if (bit_done_now) begin
              if (!voted_rx_now) begin
                rx_state <= RX_DATA;
                rx_cnt <= '0;
                rx_bit_idx <= 3'd0;
                clear_vote_samples();
              end else begin
                // False start/glitch: line returned high by the start-bit center.
                rx_state <= RX_IDLE;
                rx_cnt <= '0;
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
              rx_cnt <= '0;
              clear_vote_samples();
              if (rx_bit_idx == 3'd7) begin
                rx_state <= RX_STOP;
              end else begin
                rx_bit_idx <= rx_bit_idx + 3'd1;
              end
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          RX_STOP: begin
            capture_vote_samples();
            if (bit_done_now) begin
              if (!voted_rx_now) begin
                frame_err_pulse <= 1'b1;
              end else if (rx_full) begin
                overrun_err_pulse <= 1'b1;
              end else begin
                rx_data <= rx_shift;
                rx_valid_pulse <= 1'b1;
              end
              rx_state <= RX_IDLE;
              rx_cnt <= '0;
              clear_vote_samples();
            end else begin
              rx_cnt <= rx_cnt + {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1};
            end
          end

          default: begin
            rx_state <= RX_IDLE;
            rx_cnt <= '0;
            clear_vote_samples();
          end
        endcase
      end
    end
  end
endmodule
