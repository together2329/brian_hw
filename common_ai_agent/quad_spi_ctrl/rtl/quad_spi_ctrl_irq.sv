// quad_spi_ctrl_irq.sv — Interrupt generation
// SSOT refs: interrupts.output, interrupts.sources, features.Interrupt
module quad_spi_ctrl_irq (
  input  wire        PCLK,
  input  wire        PRESETn,

  // Interrupt source inputs (level)
  input  wire        tx_empty_src,
  input  wire        rx_avail_src,
  input  wire        done_event,
  input  wire        error_event,

  // Interrupt enable inputs
  input  wire        ie_tx_empty,
  input  wire        ie_rx_avail,
  input  wire        ie_done,
  input  wire        ie_error,

  // Sticky clear inputs (W1C)
  input  wire        w1c_done,
  input  wire        w1c_error,
  input  wire        sw_reset,

  // Interrupt output
  output wire        irq_o,

  // Source status outputs (for STATUS register readback)
  output wire        status_done,
  output wire        status_error_flag
);

  reg done_pending, error_pending;

  // Sticky DONE bit
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn)
      done_pending <= 1'b0;
    else if (sw_reset || w1c_done)
      done_pending <= 1'b0;
    else if (done_event)
      done_pending <= 1'b1;
  end

  // Sticky ERROR bit
  always @(posedge PCLK or negedge PRESETn) begin
    if (!PRESETn)
      error_pending <= 1'b0;
    else if (sw_reset || w1c_error)
      error_pending <= 1'b0;
    else if (error_event)
      error_pending <= 1'b1;
  end

  assign status_done       = done_pending;
  assign status_error_flag = error_pending;

  // Combined interrupt: OR of (source_active AND ie_bit)
  assign irq_o = (tx_empty_src  && ie_tx_empty)  |
                 (rx_avail_src  && ie_rx_avail)  |
                 (done_pending  && ie_done)      |
                 (error_pending && ie_error);

endmodule
