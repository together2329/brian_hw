`timescale 1ns/1ps
// apb_uart_txrx_demo.sv — decomposed APB3 UART TX/RX demo top
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
  logic ctrl_enable, ctrl_tx_irq_en, ctrl_rx_irq_en, ctrl_err_irq_en, ctrl_tx_break;
  logic [BAUD_DIV_WIDTH-1:0] baud_div_reg, baud_eff;
  logic tx_start, tx_busy, tx_empty, tx_done_pulse;
  logic [7:0] tx_data;
  logic rx_valid, frame_err, overrun_err, irq_tx_done, irq_error, irq_pending;
  logic rx_valid_pulse, frame_err_pulse, overrun_err_pulse;
  logic [7:0] rx_data_hw;
  logic [7:0] rx_data_unused;

  baud_div_eff #(.BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) u_baud_div_eff (
    .baud_div_reg(baud_div_reg),
    .baud_eff(baud_eff)
  );

  apb_uart_irq u_irq (
    .ctrl_tx_irq_en(ctrl_tx_irq_en),
    .ctrl_rx_irq_en(ctrl_rx_irq_en),
    .ctrl_err_irq_en(ctrl_err_irq_en),
    .irq_tx_done(irq_tx_done),
    .rx_valid(rx_valid),
    .frame_err(frame_err),
    .overrun_err(overrun_err),
    .irq_error(irq_error),
    .irq_pending(irq_pending),
    .irq(irq)
  );

  uart_tx_8n1 #(.BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) u_tx (
    .pclk(pclk),
    .preset_n(preset_n),
    .enable(ctrl_enable),
    .tx_break(ctrl_tx_break),
    .tx_start(tx_start),
    .tx_data(tx_data),
    .baud_div(baud_eff),
    .uart_tx(uart_tx),
    .tx_busy(tx_busy),
    .tx_empty(tx_empty),
    .tx_done_pulse(tx_done_pulse)
  );

  uart_rx_8n1 #(.BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) u_rx (
    .pclk(pclk),
    .preset_n(preset_n),
    .enable(ctrl_enable),
    .uart_rx(uart_rx),
    .baud_div(baud_eff),
    .rx_full(rx_valid),
    .rx_valid_pulse(rx_valid_pulse),
    .rx_data(rx_data_hw),
    .frame_err_pulse(frame_err_pulse),
    .overrun_err_pulse(overrun_err_pulse)
  );

  apb_uart_regs #(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH),
    .BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)
  ) u_regs (
    .pclk(pclk),
    .preset_n(preset_n),
    .psel(psel),
    .penable(penable),
    .pwrite(pwrite),
    .paddr(paddr),
    .pwdata(pwdata),
    .prdata(prdata),
    .pready(pready),
    .pslverr(pslverr),
    .tx_busy(tx_busy),
    .tx_empty(tx_empty),
    .tx_done_hw_set(tx_done_pulse),
    .rx_valid_hw_set(rx_valid_pulse),
    .rx_data_hw(rx_data_hw),
    .frame_err_hw_set(frame_err_pulse),
    .overrun_err_hw_set(overrun_err_pulse),
    .irq_pending(irq_pending),
    .ctrl_enable(ctrl_enable),
    .ctrl_tx_irq_en(ctrl_tx_irq_en),
    .ctrl_rx_irq_en(ctrl_rx_irq_en),
    .ctrl_err_irq_en(ctrl_err_irq_en),
    .ctrl_tx_break(ctrl_tx_break),
    .baud_div_reg(baud_div_reg),
    .tx_start(tx_start),
    .tx_data(tx_data),
    .rx_valid(rx_valid),
    .rx_data(rx_data_unused),
    .frame_err(frame_err),
    .overrun_err(overrun_err),
    .irq_tx_done(irq_tx_done),
    .irq_error(irq_error)
  );
endmodule
