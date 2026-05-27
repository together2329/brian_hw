`timescale 1ns/1ps
module apb_uart_regs #(
  parameter integer APB_ADDR_WIDTH  = 8,
  parameter integer BAUD_DIV_WIDTH  = 16,
  parameter integer FIFO_LEVEL_WIDTH = 3
) (
  input  logic                         pclk,
  input  logic                         preset_n,
  input  logic                         psel,
  input  logic                         penable,
  input  logic                         pwrite,
  input  logic [APB_ADDR_WIDTH-1:0]    paddr,
  input  logic [31:0]                  pwdata,
  output logic [31:0]                  prdata,
  output logic                         pready,
  output logic                         pslverr,

  input  logic                         tx_busy,
  input  logic                         tx_empty,
  input  logic                         tx_fifo_empty,
  input  logic                         tx_fifo_full,
  input  logic [FIFO_LEVEL_WIDTH-1:0]  tx_fifo_level,
  input  logic                         tx_done_hw_set,
  input  logic                         rx_fifo_empty,
  input  logic                         rx_fifo_full,
  input  logic [FIFO_LEVEL_WIDTH-1:0]  rx_fifo_level,
  input  logic [7:0]                   rx_fifo_data,
  input  logic                         rx_valid_hw_set,
  input  logic [7:0]                   rx_data_hw,
  input  logic                         rx_activity_pulse,
  input  logic                         frame_err_hw_set,
  input  logic                         parity_err_hw_set,
  input  logic                         break_err_hw_set,
  input  logic                         overrun_err_hw_set,
  input  logic                         irq_pending,

  output logic                         ctrl_enable,
  output logic                         ctrl_tx_irq_en,
  output logic                         ctrl_rx_irq_en,
  output logic                         ctrl_err_irq_en,
  output logic                         ctrl_tx_break,
  output logic                         ctrl_loopback_en,
  output logic                         ctrl_timeout_irq_en,
  output logic                         ctrl_fifo_irq_en,
  output logic [BAUD_DIV_WIDTH-1:0]    baud_div_reg,
  output logic [1:0]                   cfg_data_bits_sel,
  output logic                         cfg_parity_en,
  output logic                         cfg_parity_odd,
  output logic                         cfg_stop2,
  output logic                         tx_start,
  output logic [7:0]                   tx_data,
  output logic                         tx_fifo_push,
  output logic [7:0]                   tx_fifo_wdata,
  output logic                         tx_fifo_clear,
  output logic                         rx_fifo_pop,
  output logic                         rx_fifo_clear,
  output logic [7:0]                   tx_threshold,
  output logic [7:0]                   rx_threshold,
  output logic [15:0]                  rx_timeout_cycles,
  output logic [31:0]                  scratch_reg,
  output logic                         rx_valid,
  output logic [7:0]                   rx_data,
  output logic                         frame_err,
  output logic                         parity_err,
  output logic                         overrun_err,
  output logic                         break_err,
  output logic                         rx_timeout,
  output logic                         irq_tx_done,
  output logic                         irq_error,
  output logic                         irq_rx_timeout,
  output logic                         irq_tx_threshold,
  output logic                         irq_rx_threshold
);
  localparam [7:0] A_CTRL        = 8'h00;
  localparam [7:0] A_STATUS      = 8'h04;
  localparam [7:0] A_BAUD_DIV    = 8'h08;
  localparam [7:0] A_TXDATA      = 8'h0c;
  localparam [7:0] A_RXDATA      = 8'h10;
  localparam [7:0] A_IRQ_STATUS  = 8'h14;
  localparam [7:0] A_FRAME_CFG   = 8'h18;
  localparam [7:0] A_FIFO_CTRL   = 8'h1c;
  localparam [7:0] A_FIFO_STATUS = 8'h20;
  localparam [7:0] A_FIFO_THRESH = 8'h24;
  localparam [7:0] A_RX_TIMEOUT  = 8'h28;
  localparam [7:0] A_SCRATCH     = 8'h2c;

  wire access     = psel && penable;
  wire write_xfer = access && pwrite;
  wire read_xfer  = access && !pwrite;
  wire [7:0] addr8 = paddr[7:0];

  function automatic logic valid_addr(input [7:0] a);
    begin
      valid_addr = (a == A_CTRL)        || (a == A_STATUS)      ||
                   (a == A_BAUD_DIV)    || (a == A_TXDATA)      ||
                   (a == A_RXDATA)      || (a == A_IRQ_STATUS)  ||
                   (a == A_FRAME_CFG)   || (a == A_FIFO_CTRL)   ||
                   (a == A_FIFO_STATUS) || (a == A_FIFO_THRESH) ||
                   (a == A_RX_TIMEOUT)  || (a == A_SCRATCH);
    end
  endfunction

  function automatic [7:0] level_to_u8(input [FIFO_LEVEL_WIDTH-1:0] level_in);
    begin
      level_to_u8 = {{(8-FIFO_LEVEL_WIDTH){1'b0}}, level_in};
    end
  endfunction

  logic [15:0] rx_timeout_counter;
  logic        legacy_rx_valid_hold;
  logic [7:0]  legacy_rx_data_hold;

  wire [7:0] tx_level_u8 = level_to_u8(tx_fifo_level);
  wire [7:0] rx_level_u8 = level_to_u8(rx_fifo_level);
  wire       rx_fifo_nonempty = !rx_fifo_empty;
  wire       rx_valid_status = rx_fifo_nonempty || legacy_rx_valid_hold;
  wire [7:0] rx_read_data = rx_fifo_nonempty ? rx_fifo_data :
                            (legacy_rx_valid_hold ? legacy_rx_data_hold : 8'h00);
  wire       tx_threshold_level = (tx_level_u8 <= tx_threshold);
  wire       rx_threshold_level = rx_fifo_nonempty && (rx_level_u8 >= rx_threshold);
  wire       txdata_write = write_xfer && (addr8 == A_TXDATA);
  wire       fifo_status_write = write_xfer && (addr8 == A_FIFO_STATUS);
  wire       rxdata_write = write_xfer && (addr8 == A_RXDATA);
  wire       txdata_unsupported = txdata_write && (!ctrl_enable || tx_fifo_full);
  wire       unsupported = rxdata_write || fifo_status_write || txdata_unsupported;
  wire       accepted_write = write_xfer && !pslverr;
  wire       accepted_read = read_xfer && !pslverr;
  wire       rx_pop_accept = accepted_read && (addr8 == A_RXDATA) && rx_fifo_nonempty;
  wire       legacy_rx_pop_accept = accepted_read && (addr8 == A_RXDATA) && !rx_fifo_nonempty && legacy_rx_valid_hold;
  wire       timeout_disabled = (rx_timeout_cycles == 16'h0000);
  wire       timeout_reset_event = rx_fifo_empty || rx_pop_accept || legacy_rx_pop_accept ||
                                   rx_fifo_clear || rx_valid_hw_set || rx_activity_pulse;
  wire       timeout_limit_reached = (rx_timeout_counter >= (rx_timeout_cycles - 16'h0001));

  assign pready = 1'b1;
  assign pslverr = access && (!valid_addr(addr8) || unsupported);
  assign rx_valid = rx_valid_status;
  assign rx_data = rx_read_data;
  assign irq_tx_threshold = tx_threshold_level;
  assign irq_rx_threshold = rx_threshold_level;

  always_comb begin
    case (addr8)
      A_CTRL: begin
        prdata = {23'b0, ctrl_fifo_irq_en, ctrl_timeout_irq_en, ctrl_loopback_en,
                  ctrl_tx_break, 1'b0, ctrl_err_irq_en, ctrl_rx_irq_en,
                  ctrl_tx_irq_en, ctrl_enable};
      end
      A_STATUS: begin
        prdata = {19'b0, rx_threshold_level, tx_threshold_level, rx_timeout,
                  break_err, parity_err, rx_fifo_full, tx_fifo_full,
                  irq_pending, overrun_err, frame_err, tx_busy, tx_empty,
                  rx_valid_status};
      end
      A_BAUD_DIV: begin
        prdata = {{(32-BAUD_DIV_WIDTH){1'b0}}, baud_div_reg};
      end
      A_TXDATA: begin
        prdata = 32'h0000_0000;
      end
      A_RXDATA: begin
        prdata = {24'h0, rx_read_data};
      end
      A_IRQ_STATUS: begin
        prdata = {26'b0, rx_threshold_level, tx_threshold_level, irq_rx_timeout,
                  irq_error, rx_valid_status, irq_tx_done};
      end
      A_FRAME_CFG: begin
        prdata = {27'b0, cfg_stop2, cfg_parity_odd, cfg_parity_en, cfg_data_bits_sel};
      end
      A_FIFO_CTRL: begin
        prdata = 32'h0000_0000;
      end
      A_FIFO_STATUS: begin
        prdata = {10'b0, rx_threshold_level, tx_threshold_level, rx_fifo_full,
                  rx_fifo_empty, tx_fifo_full, tx_fifo_empty, rx_level_u8,
                  tx_level_u8};
      end
      A_FIFO_THRESH: begin
        prdata = {16'h0000, rx_threshold, tx_threshold};
      end
      A_RX_TIMEOUT: begin
        prdata = {16'h0000, rx_timeout_cycles};
      end
      A_SCRATCH: begin
        prdata = scratch_reg;
      end
      default: begin
        prdata = 32'h0000_0000;
      end
    endcase
  end

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      ctrl_enable          <= 1'b1;
      ctrl_tx_irq_en       <= 1'b0;
      ctrl_rx_irq_en       <= 1'b0;
      ctrl_err_irq_en      <= 1'b0;
      ctrl_tx_break        <= 1'b0;
      ctrl_loopback_en     <= 1'b0;
      ctrl_timeout_irq_en  <= 1'b0;
      ctrl_fifo_irq_en     <= 1'b0;
      baud_div_reg         <= {{(BAUD_DIV_WIDTH-3){1'b0}}, 3'd4};
      cfg_data_bits_sel    <= 2'd3;
      cfg_parity_en        <= 1'b0;
      cfg_parity_odd       <= 1'b0;
      cfg_stop2            <= 1'b0;
      tx_start             <= 1'b0;
      tx_data              <= 8'h00;
      tx_fifo_push         <= 1'b0;
      tx_fifo_wdata        <= 8'h00;
      tx_fifo_clear        <= 1'b0;
      rx_fifo_pop          <= 1'b0;
      rx_fifo_clear        <= 1'b0;
      tx_threshold         <= 8'h01;
      rx_threshold         <= 8'h01;
      rx_timeout_cycles    <= 16'h0000;
      scratch_reg          <= 32'h0000_0000;
      frame_err            <= 1'b0;
      parity_err           <= 1'b0;
      overrun_err          <= 1'b0;
      break_err            <= 1'b0;
      rx_timeout           <= 1'b0;
      irq_tx_done          <= 1'b0;
      irq_error            <= 1'b0;
      irq_rx_timeout       <= 1'b0;
      rx_timeout_counter   <= 16'h0000;
      legacy_rx_valid_hold <= 1'b0;
      legacy_rx_data_hold  <= 8'h00;
    end else begin
      tx_start      <= 1'b0;
      tx_fifo_push  <= 1'b0;
      tx_fifo_clear <= 1'b0;
      rx_fifo_pop   <= 1'b0;
      rx_fifo_clear <= 1'b0;

      if (tx_done_hw_set) begin
        irq_tx_done <= 1'b1;
      end
      if (frame_err_hw_set) begin
        frame_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (parity_err_hw_set) begin
        parity_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (overrun_err_hw_set) begin
        overrun_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (break_err_hw_set) begin
        break_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (rx_valid_hw_set) begin
        legacy_rx_valid_hold <= 1'b1;
        legacy_rx_data_hold  <= rx_data_hw;
      end

      if (timeout_disabled || timeout_reset_event) begin
        rx_timeout_counter <= 16'h0000;
      end else if (rx_fifo_nonempty) begin
        if (timeout_limit_reached) begin
          rx_timeout <= 1'b1;
          irq_rx_timeout <= 1'b1;
          rx_timeout_counter <= rx_timeout_counter;
        end else begin
          rx_timeout_counter <= rx_timeout_counter + 16'h0001;
        end
      end

      if (accepted_write) begin
        case (addr8)
          A_CTRL: begin
            ctrl_enable         <= pwdata[0];
            ctrl_tx_irq_en      <= pwdata[1];
            ctrl_rx_irq_en      <= pwdata[2];
            ctrl_err_irq_en     <= pwdata[3];
            if (pwdata[4]) begin
              rx_fifo_clear        <= 1'b1;
              legacy_rx_valid_hold <= 1'b0;
              rx_timeout_counter   <= 16'h0000;
            end
            ctrl_tx_break       <= pwdata[5];
            ctrl_loopback_en    <= pwdata[6];
            ctrl_timeout_irq_en <= pwdata[7];
            ctrl_fifo_irq_en    <= pwdata[8];
          end
          A_STATUS: begin
            if (pwdata[3])  frame_err  <= 1'b0;
            if (pwdata[4])  overrun_err <= 1'b0;
            if (pwdata[8])  parity_err <= 1'b0;
            if (pwdata[9])  break_err <= 1'b0;
            if (pwdata[10]) rx_timeout <= 1'b0;
          end
          A_BAUD_DIV: begin
            baud_div_reg <= (pwdata[BAUD_DIV_WIDTH-1:0] == {BAUD_DIV_WIDTH{1'b0}}) ?
                            {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1} : pwdata[BAUD_DIV_WIDTH-1:0];
          end
          A_TXDATA: begin
            tx_data       <= pwdata[7:0];
            tx_fifo_wdata <= pwdata[7:0];
            tx_start      <= 1'b1;
            tx_fifo_push  <= 1'b1;
          end
          A_IRQ_STATUS: begin
            if (pwdata[0]) irq_tx_done    <= 1'b0;
            if (pwdata[2]) irq_error      <= 1'b0;
            if (pwdata[3]) irq_rx_timeout <= 1'b0;
          end
          A_FRAME_CFG: begin
            cfg_data_bits_sel <= pwdata[1:0];
            cfg_parity_en     <= pwdata[2];
            cfg_parity_odd    <= pwdata[3];
            cfg_stop2         <= pwdata[4];
          end
          A_FIFO_CTRL: begin
            if (pwdata[0]) begin
              tx_fifo_clear <= 1'b1;
            end
            if (pwdata[1]) begin
              rx_fifo_clear        <= 1'b1;
              legacy_rx_valid_hold <= 1'b0;
              rx_timeout_counter   <= 16'h0000;
            end
          end
          A_FIFO_THRESH: begin
            tx_threshold <= pwdata[7:0];
            rx_threshold <= pwdata[15:8];
          end
          A_RX_TIMEOUT: begin
            rx_timeout_cycles <= pwdata[15:0];
            rx_timeout_counter <= 16'h0000;
          end
          A_SCRATCH: begin
            scratch_reg <= pwdata;
          end
          default: begin
          end
        endcase
      end

      if (rx_pop_accept) begin
        rx_fifo_pop <= 1'b1;
        rx_timeout_counter <= 16'h0000;
      end
      if (legacy_rx_pop_accept) begin
        legacy_rx_valid_hold <= 1'b0;
        rx_timeout_counter <= 16'h0000;
      end
    end
  end
endmodule
