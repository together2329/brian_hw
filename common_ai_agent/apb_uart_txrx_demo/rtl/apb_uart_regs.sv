`timescale 1ns/1ps
module apb_uart_regs #(
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

  input  logic                      tx_busy,
  input  logic                      tx_empty,
  input  logic                      tx_done_hw_set,
  input  logic                      rx_valid_hw_set,
  input  logic [7:0]                rx_data_hw,
  input  logic                      frame_err_hw_set,
  input  logic                      overrun_err_hw_set,
  input  logic                      irq_pending,

  output logic                      ctrl_enable,
  output logic                      ctrl_tx_irq_en,
  output logic                      ctrl_rx_irq_en,
  output logic                      ctrl_err_irq_en,
  output logic                      ctrl_tx_break,
  output logic [BAUD_DIV_WIDTH-1:0] baud_div_reg,
  output logic                      tx_start,
  output logic [7:0]                tx_data,
  output logic                      rx_valid,
  output logic [7:0]                rx_data,
  output logic                      frame_err,
  output logic                      overrun_err,
  output logic                      irq_tx_done,
  output logic                      irq_error
);
  localparam [7:0] A_CTRL       = 8'h00;
  localparam [7:0] A_STATUS     = 8'h04;
  localparam [7:0] A_BAUD_DIV   = 8'h08;
  localparam [7:0] A_TXDATA     = 8'h0c;
  localparam [7:0] A_RXDATA     = 8'h10;
  localparam [7:0] A_IRQ_STATUS = 8'h14;

  wire access     = psel && penable;
  wire write_xfer = access && pwrite;
  wire read_xfer  = access && !pwrite;
  wire [7:0] addr8 = paddr[7:0];

  function automatic logic valid_addr(input [7:0] a);
    valid_addr = (a == A_CTRL) || (a == A_STATUS) || (a == A_BAUD_DIV) ||
                 (a == A_TXDATA) || (a == A_RXDATA) || (a == A_IRQ_STATUS);
  endfunction

  wire unsupported = write_xfer && ((addr8 == A_RXDATA) || ((addr8 == A_TXDATA) && tx_busy));
  wire _unused_pwdata_upper = |pwdata[31:BAUD_DIV_WIDTH];

  assign pready = 1'b1;
  assign pslverr = access && (!valid_addr(addr8) || unsupported);

  always_comb begin
    case (addr8)
      A_CTRL:       prdata = {26'b0, ctrl_tx_break, 1'b0, ctrl_err_irq_en, ctrl_rx_irq_en, ctrl_tx_irq_en, ctrl_enable};
      A_STATUS:     prdata = {26'b0, irq_pending, overrun_err, frame_err, tx_busy, tx_empty, rx_valid};
      A_BAUD_DIV:   prdata = {{(32-BAUD_DIV_WIDTH){1'b0}}, baud_div_reg};
      A_TXDATA:     prdata = 32'h0000_0000;
      A_RXDATA:     prdata = {24'h0, rx_data};
      A_IRQ_STATUS: prdata = {29'h0, irq_error, rx_valid, irq_tx_done};
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
      tx_start        <= 1'b0;
      tx_data         <= 8'h00;
      rx_valid        <= 1'b0;
      rx_data         <= 8'h00;
      frame_err       <= 1'b0;
      overrun_err     <= 1'b0;
      irq_tx_done     <= 1'b0;
      irq_error       <= 1'b0;
    end else begin
      tx_start <= 1'b0;

      if (tx_done_hw_set) begin
        irq_tx_done <= 1'b1;
      end
      if (frame_err_hw_set) begin
        frame_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (overrun_err_hw_set) begin
        overrun_err <= 1'b1;
        irq_error <= 1'b1;
      end
      if (rx_valid_hw_set) begin
        rx_data <= rx_data_hw;
        rx_valid <= 1'b1;
      end

      if (write_xfer && !pslverr) begin
        case (addr8)
          A_CTRL: begin
            ctrl_enable     <= pwdata[0];
            ctrl_tx_irq_en  <= pwdata[1];
            ctrl_rx_irq_en  <= pwdata[2];
            ctrl_err_irq_en <= pwdata[3];
            if (pwdata[4]) rx_valid <= 1'b0;
            ctrl_tx_break   <= pwdata[5];
          end
          A_STATUS: begin
            if (pwdata[3]) frame_err   <= 1'b0;
            if (pwdata[4]) overrun_err <= 1'b0;
          end
          A_BAUD_DIV: begin
            baud_div_reg <= (pwdata[BAUD_DIV_WIDTH-1:0] == '0) ? {{(BAUD_DIV_WIDTH-1){1'b0}}, 1'b1} : pwdata[BAUD_DIV_WIDTH-1:0];
          end
          A_TXDATA: begin
            tx_data <= pwdata[7:0];
            tx_start <= ctrl_enable;
          end
          A_IRQ_STATUS: begin
            if (pwdata[0]) irq_tx_done <= 1'b0;
            if (pwdata[2]) irq_error   <= 1'b0;
          end
          default: ;
        endcase
      end

      if (read_xfer && !pslverr && addr8 == A_RXDATA) begin
        rx_valid <= 1'b0;
      end
    end
  end
endmodule
