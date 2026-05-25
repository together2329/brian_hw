`timescale 1ns/1ps
module apb_uart_irq (
  input  logic ctrl_tx_irq_en,
  input  logic ctrl_rx_irq_en,
  input  logic ctrl_err_irq_en,
  input  logic irq_tx_done,
  input  logic rx_valid,
  input  logic frame_err,
  input  logic overrun_err,
  input  logic irq_error,
  output logic irq_pending,
  output logic irq
);
  assign irq_pending = (ctrl_tx_irq_en && irq_tx_done) ||
                       (ctrl_rx_irq_en && rx_valid) ||
                       (ctrl_err_irq_en && (frame_err || overrun_err || irq_error));
  assign irq = irq_pending;
endmodule
