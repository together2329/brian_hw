`timescale 1ns/1ps
// apb_uart_irq.sv — combinational enabled-source IRQ combiner for the
// enhanced APB UART.  Sticky/level source state is maintained in the register
// block; this helper only applies the interrupt enables and OR-reduces sources.
module apb_uart_irq (
  input  logic ctrl_tx_irq_en,
  input  logic ctrl_rx_irq_en,
  input  logic ctrl_err_irq_en,
  input  logic ctrl_timeout_irq_en,
  input  logic ctrl_fifo_irq_en,

  input  logic irq_tx_done,
  input  logic rx_valid,
  input  logic frame_err,
  input  logic parity_err,
  input  logic overrun_err,
  input  logic break_err,
  input  logic irq_error,
  input  logic irq_rx_timeout,
  input  logic irq_tx_threshold,
  input  logic irq_rx_threshold,

  output logic irq_pending,
  output logic irq
);
  logic tx_pending;
  logic rx_pending;
  logic err_pending;
  logic timeout_pending;
  logic fifo_pending;

  assign tx_pending      = ctrl_tx_irq_en      && irq_tx_done;
  assign rx_pending      = ctrl_rx_irq_en      && rx_valid;
  assign err_pending     = ctrl_err_irq_en     &&
                           (frame_err || parity_err || overrun_err ||
                            break_err || irq_error);
  assign timeout_pending = ctrl_timeout_irq_en && irq_rx_timeout;
  assign fifo_pending    = ctrl_fifo_irq_en    &&
                           (irq_tx_threshold || irq_rx_threshold);

  assign irq_pending = tx_pending || rx_pending || err_pending ||
                       timeout_pending || fifo_pending;
  assign irq = irq_pending;
endmodule
