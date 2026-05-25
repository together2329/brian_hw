// apb_uart_txrx_demo.sv — APB3 UART TX/RX demo
module apb_uart_txrx_demo #(
  parameter integer APB_ADDR_WIDTH = 8,
  parameter integer BAUD_DIV_WIDTH = 16
) (
  input  logic                      pclk,
  input  logic                      preset_n,
  input  logic                      psel,
  input  logic                      penable,
  input  logic                      pwrite,
  input  logic [APB_ADDR_WIDTH-1:0] paddr,
  input  logic [31:0]               pwdata,
  output logic [31:0]               prdata,
  output logic                      pready,
  output logic                      pslverr,
  output logic                      uart_tx,
  input  logic                      uart_rx,
  output logic                      irq
);

  localparam [7:0] A_CTRL       = 8'h00;
  localparam [7:0] A_STATUS     = 8'h04;
  localparam [7:0] A_BAUD_DIV   = 8'h08;
  localparam [7:0] A_TXDATA     = 8'h0c;
  localparam [7:0] A_RXDATA     = 8'h10;
  localparam [7:0] A_IRQ_STATUS = 8'h14;

  localparam [1:0] TX_IDLE  = 2'd0, TX_START = 2'd1, TX_DATA = 2'd2, TX_STOP = 2'd3;
  localparam [1:0] RX_IDLE  = 2'd0, RX_START = 2'd1, RX_DATA = 2'd2, RX_STOP = 2'd3;

  logic        ctrl_enable, ctrl_tx_irq_en, ctrl_rx_irq_en, ctrl_err_irq_en, ctrl_tx_break;
  logic [BAUD_DIV_WIDTH-1:0] baud_div_reg;
  logic [BAUD_DIV_WIDTH-1:0] baud_eff;
  logic        rx_valid_reg, frame_err_reg, overrun_err_reg;
  logic [7:0]  rx_data_reg;
  logic        irq_tx_done_reg, irq_error_reg;

  logic [1:0]  tx_state;
  logic [BAUD_DIV_WIDTH-1:0] tx_cnt;
  logic [2:0]  tx_bit_idx;
  logic [7:0]  tx_shift;
  logic        tx_line_reg;

  logic [1:0]  rx_state;
  logic [BAUD_DIV_WIDTH-1:0] rx_cnt;
  logic [2:0]  rx_bit_idx;
  logic [7:0]  rx_shift;
  logic        uart_rx_q1, uart_rx_q2;

  wire access      = psel && penable;
  wire write_xfer  = access && pwrite;
  wire read_xfer   = access && !pwrite;
  wire [7:0] addr8 = paddr[7:0];
  wire tx_busy     = (tx_state != TX_IDLE);
  wire tx_empty    = !tx_busy;
  wire irq_pending = (ctrl_tx_irq_en && irq_tx_done_reg) ||
                     (ctrl_rx_irq_en && rx_valid_reg) ||
                     (ctrl_err_irq_en && (frame_err_reg || overrun_err_reg || irq_error_reg));

  assign pready = 1'b1;
  assign irq    = irq_pending;
  assign baud_eff = (baud_div_reg == {BAUD_DIV_WIDTH{1'b0}}) ? {{(BAUD_DIV_WIDTH-1){1'b0}},1'b1} : baud_div_reg;
  assign uart_tx = ctrl_tx_break ? 1'b0 : tx_line_reg;

  function automatic logic valid_addr(input [7:0] a);
    valid_addr = (a == A_CTRL) || (a == A_STATUS) || (a == A_BAUD_DIV) ||
                 (a == A_TXDATA) || (a == A_RXDATA) || (a == A_IRQ_STATUS);
  endfunction

  wire unsupported = write_xfer && ((addr8 == A_RXDATA) || ((addr8 == A_TXDATA) && tx_busy));
  always_comb begin
    pslverr = access && (!valid_addr(addr8) || unsupported);
  end

  always_comb begin
    unique case (addr8)
      A_CTRL:       prdata = {26'b0, ctrl_tx_break, 1'b0, ctrl_err_irq_en, ctrl_rx_irq_en, ctrl_tx_irq_en, ctrl_enable};
      A_STATUS:     prdata = {26'b0, irq_pending, overrun_err_reg, frame_err_reg, tx_busy, tx_empty, rx_valid_reg};
      A_BAUD_DIV:   prdata = {{(32-BAUD_DIV_WIDTH){1'b0}}, baud_div_reg};
      A_TXDATA:     prdata = 32'h0000_0000;
      A_RXDATA:     prdata = {24'h0, rx_data_reg};
      A_IRQ_STATUS: prdata = {29'h0, irq_error_reg, rx_valid_reg, irq_tx_done_reg};
      default:      prdata = 32'h0000_0000;
    endcase
  end

  always_ff @(posedge pclk or negedge preset_n) begin
    if (!preset_n) begin
      ctrl_enable     <= 1'b1;
      ctrl_tx_irq_en  <= 1'b0;
      ctrl_rx_irq_en  <= 1'b0;
      ctrl_err_irq_en <= 1'b0;
      ctrl_tx_break   <= 1'b0;
      baud_div_reg    <= {{(BAUD_DIV_WIDTH-3){1'b0}}, 3'd4};
      rx_valid_reg    <= 1'b0;
      frame_err_reg   <= 1'b0;
      overrun_err_reg <= 1'b0;
      rx_data_reg     <= 8'h00;
      irq_tx_done_reg <= 1'b0;
      irq_error_reg   <= 1'b0;
      tx_state        <= TX_IDLE;
      tx_cnt          <= '0;
      tx_bit_idx      <= 3'd0;
      tx_shift        <= 8'h00;
      tx_line_reg     <= 1'b1;
      rx_state        <= RX_IDLE;
      rx_cnt          <= '0;
      rx_bit_idx      <= 3'd0;
      rx_shift        <= 8'h00;
      uart_rx_q1      <= 1'b1;
      uart_rx_q2      <= 1'b1;
    end else begin
      uart_rx_q1 <= uart_rx;
      uart_rx_q2 <= uart_rx_q1;

      if (write_xfer && !pslverr) begin
        unique case (addr8)
          A_CTRL: begin
            ctrl_enable     <= pwdata[0];
            ctrl_tx_irq_en  <= pwdata[1];
            ctrl_rx_irq_en  <= pwdata[2];
            ctrl_err_irq_en <= pwdata[3];
            if (pwdata[4]) rx_valid_reg <= 1'b0;
            ctrl_tx_break   <= pwdata[5];
          end
          A_STATUS: begin
            if (pwdata[3]) frame_err_reg   <= 1'b0;
            if (pwdata[4]) overrun_err_reg <= 1'b0;
          end
          A_BAUD_DIV: begin
            baud_div_reg <= (pwdata[BAUD_DIV_WIDTH-1:0] == '0) ? {{(BAUD_DIV_WIDTH-1){1'b0}},1'b1} : pwdata[BAUD_DIV_WIDTH-1:0];
          end
          A_IRQ_STATUS: begin
            if (pwdata[0]) irq_tx_done_reg <= 1'b0;
            if (pwdata[2]) irq_error_reg   <= 1'b0;
          end
          default: ;
        endcase
      end

      if (read_xfer && !pslverr && addr8 == A_RXDATA) begin
        rx_valid_reg <= 1'b0;
      end

      // TX FSM
      unique case (tx_state)
        TX_IDLE: begin
          tx_line_reg <= 1'b1;
          tx_cnt <= '0;
          tx_bit_idx <= 3'd0;
          if (write_xfer && !pslverr && addr8 == A_TXDATA && ctrl_enable) begin
            tx_shift <= pwdata[7:0];
            tx_state <= TX_START;
            tx_line_reg <= 1'b0;
            tx_cnt <= baud_eff - 1'b1;
          end
        end
        TX_START: begin
          tx_line_reg <= 1'b0;
          if (tx_cnt == 0) begin
            tx_state <= TX_DATA;
            tx_line_reg <= tx_shift[0];
            tx_bit_idx <= 3'd0;
            tx_cnt <= baud_eff - 1'b1;
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
            tx_cnt <= baud_eff - 1'b1;
          end else tx_cnt <= tx_cnt - 1'b1;
        end
        TX_STOP: begin
          tx_line_reg <= 1'b1;
          if (tx_cnt == 0) begin
            tx_state <= TX_IDLE;
            irq_tx_done_reg <= 1'b1;
          end else tx_cnt <= tx_cnt - 1'b1;
        end
        default: tx_state <= TX_IDLE;
      endcase

      // RX FSM: falling edge, half-bit confirm, then full-bit data samples.
      unique case (rx_state)
        RX_IDLE: begin
          rx_cnt <= '0;
          rx_bit_idx <= 3'd0;
          if (ctrl_enable && uart_rx_q2 && !uart_rx_q1) begin
            rx_state <= RX_START;
            rx_cnt <= (baud_eff >> 1);
          end
        end
        RX_START: begin
          if (rx_cnt == 0) begin
            if (!uart_rx_q2) begin
              rx_state <= RX_DATA;
              rx_cnt <= baud_eff - 1'b1;
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
            rx_cnt <= baud_eff - 1'b1;
          end else rx_cnt <= rx_cnt - 1'b1;
        end
        RX_STOP: begin
          if (rx_cnt == 0) begin
            if (!uart_rx_q2) begin
              frame_err_reg <= 1'b1;
              irq_error_reg <= 1'b1;
            end else if (rx_valid_reg) begin
              overrun_err_reg <= 1'b1;
              irq_error_reg <= 1'b1;
            end else begin
              rx_data_reg <= rx_shift;
              rx_valid_reg <= 1'b1;
            end
            rx_state <= RX_IDLE;
          end else rx_cnt <= rx_cnt - 1'b1;
        end
        default: rx_state <= RX_IDLE;
      endcase
    end
  end
endmodule
