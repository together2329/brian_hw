`timescale 1ns/1ps
// apb_uart_txrx_demo.sv — APB3 UART top with configurable framed TX/RX,
// shallow TX/RX FIFOs, internal loopback, timeout/status plumbing, and IRQ.
module apb_uart_txrx_demo #(
  parameter integer APB_ADDR_WIDTH   = 8,
  parameter integer BAUD_DIV_WIDTH   = 16,
  parameter integer FIFO_DEPTH       = 4,
  parameter integer FIFO_PTR_WIDTH   = (FIFO_DEPTH <= 1) ? 1 : $clog2(FIFO_DEPTH),
  parameter integer FIFO_LEVEL_WIDTH = (FIFO_DEPTH <= 1) ? 1 : $clog2(FIFO_DEPTH + 1)
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
  logic ctrl_enable;
  logic ctrl_tx_irq_en;
  logic ctrl_rx_irq_en;
  logic ctrl_err_irq_en;
  logic ctrl_tx_break;
  logic ctrl_loopback_en;
  logic ctrl_timeout_irq_en;
  logic ctrl_fifo_irq_en;
  logic [BAUD_DIV_WIDTH-1:0] baud_div_reg;
  logic [BAUD_DIV_WIDTH-1:0] baud_eff;
  logic [1:0] cfg_data_bits_sel;
  logic cfg_parity_en;
  logic cfg_parity_odd;
  logic cfg_stop2;

  logic tx_busy;
  logic tx_idle;
  logic tx_empty_status;
  logic tx_done_pulse;
  logic tx_start_unused;
  logic [7:0] tx_data_unused;
  logic tx_fifo_push;
  logic [7:0] tx_fifo_wdata;
  logic tx_fifo_clear;
  logic tx_fifo_pop;
  logic [7:0] tx_fifo_rdata;
  logic tx_fifo_full;
  logic tx_fifo_empty;
  logic [FIFO_LEVEL_WIDTH-1:0] tx_fifo_level;

  logic rx_fifo_push;
  logic [7:0] rx_fifo_wdata;
  logic rx_fifo_pop;
  logic [7:0] rx_fifo_rdata;
  logic rx_fifo_full;
  logic rx_fifo_empty;
  logic [FIFO_LEVEL_WIDTH-1:0] rx_fifo_level;
  logic rx_fifo_clear;
  logic rx_fifo_overflow_pulse;
  logic rx_activity_pulse;

  logic frame_err_pulse;
  logic parity_err_pulse;
  logic break_err_pulse;
  logic overrun_err_pulse;
  logic frame_err;
  logic parity_err;
  logic overrun_err;
  logic break_err;
  logic rx_timeout;
  logic rx_valid;

  logic irq_tx_done;
  logic irq_error;
  logic irq_rx_timeout;
  logic irq_tx_threshold;
  logic irq_rx_threshold;
  logic irq_pending_base;
  logic irq_base_level;
  logic irq_pending;
  logic [7:0] tx_threshold;
  logic [7:0] rx_threshold;
  logic [15:0] rx_timeout_cycles;
  logic [31:0] scratch_reg_unused;
  logic [7:0] rx_data_unused;
  logic tx_fifo_overflow_pulse;
  logic tx_fifo_underflow_pulse;
  logic rx_fifo_underflow_pulse;
  logic _unused_top_outputs;
  logic uart_tx_int;
  logic uart_rx_selected;

  assign uart_tx = uart_tx_int;
  assign uart_rx_selected = ctrl_loopback_en ? uart_tx_int : uart_rx;
  assign tx_empty_status = tx_fifo_empty && tx_idle;
  assign irq_pending = irq_pending_base ||
                       (ctrl_timeout_irq_en && irq_rx_timeout) ||
                       (ctrl_fifo_irq_en && (irq_tx_threshold || irq_rx_threshold));
  assign irq = irq_pending;
  assign _unused_top_outputs = parity_err ^ break_err ^ rx_timeout ^
                               tx_start_unused ^ (|tx_data_unused) ^
                               (|tx_threshold) ^ (|rx_threshold) ^
                               (|rx_timeout_cycles) ^ (|scratch_reg_unused) ^
                               (|rx_data_unused) ^ tx_fifo_overflow_pulse ^
                               tx_fifo_underflow_pulse ^ rx_fifo_underflow_pulse ^
                               irq_base_level;

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
    .irq_pending(irq_pending_base),
    .irq(irq_base_level)
  );

  uart_fifo_sync #(
    .DATA_WIDTH(8),
    .DEPTH(FIFO_DEPTH),
    .PTR_WIDTH(FIFO_PTR_WIDTH),
    .LEVEL_WIDTH(FIFO_LEVEL_WIDTH)
  ) u_tx_fifo (
    .clk(pclk),
    .reset_n(preset_n),
    .clear(tx_fifo_clear),
    .push(tx_fifo_push),
    .push_data(tx_fifo_wdata),
    .pop(tx_fifo_pop),
    .pop_data(tx_fifo_rdata),
    .fifo_full(tx_fifo_full),
    .fifo_empty(tx_fifo_empty),
    .level(tx_fifo_level),
    .overflow_pulse(tx_fifo_overflow_pulse),
    .underflow_pulse(tx_fifo_underflow_pulse)
  );

  uart_tx_framed #(.BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) u_tx (
    .pclk(pclk),
    .preset_n(preset_n),
    .enable(ctrl_enable),
    .tx_break(ctrl_tx_break),
    .cfg_data_bits_sel(cfg_data_bits_sel),
    .cfg_parity_en(cfg_parity_en),
    .cfg_parity_odd(cfg_parity_odd),
    .cfg_stop2(cfg_stop2),
    .baud_div(baud_eff),
    .fifo_data(tx_fifo_rdata),
    .fifo_empty(tx_fifo_empty),
    .fifo_pop(tx_fifo_pop),
    .uart_tx(uart_tx_int),
    .tx_busy(tx_busy),
    .tx_idle(tx_idle),
    .tx_done_pulse(tx_done_pulse)
  );

  uart_rx_framed #(.BAUD_DIV_WIDTH(BAUD_DIV_WIDTH)) u_rx (
    .pclk(pclk),
    .preset_n(preset_n),
    .enable(ctrl_enable),
    .uart_rx(uart_rx_selected),
    .cfg_data_bits_sel(cfg_data_bits_sel),
    .cfg_parity_en(cfg_parity_en),
    .cfg_parity_odd(cfg_parity_odd),
    .cfg_stop2(cfg_stop2),
    .baud_div(baud_eff),
    .rx_fifo_full(rx_fifo_full),
    .rx_fifo_push(rx_fifo_push),
    .rx_fifo_data(rx_fifo_wdata),
    .rx_activity_pulse(rx_activity_pulse),
    .frame_err_pulse(frame_err_pulse),
    .parity_err_pulse(parity_err_pulse),
    .break_err_pulse(break_err_pulse),
    .overrun_err_pulse(overrun_err_pulse)
  );

  uart_fifo_sync #(
    .DATA_WIDTH(8),
    .DEPTH(FIFO_DEPTH),
    .PTR_WIDTH(FIFO_PTR_WIDTH),
    .LEVEL_WIDTH(FIFO_LEVEL_WIDTH)
  ) u_rx_fifo (
    .clk(pclk),
    .reset_n(preset_n),
    .clear(rx_fifo_clear),
    .push(rx_fifo_push),
    .push_data(rx_fifo_wdata),
    .pop(rx_fifo_pop),
    .pop_data(rx_fifo_rdata),
    .fifo_full(rx_fifo_full),
    .fifo_empty(rx_fifo_empty),
    .level(rx_fifo_level),
    .overflow_pulse(rx_fifo_overflow_pulse),
    .underflow_pulse(rx_fifo_underflow_pulse)
  );

  apb_uart_regs #(
    .APB_ADDR_WIDTH(APB_ADDR_WIDTH),
    .BAUD_DIV_WIDTH(BAUD_DIV_WIDTH),
    .FIFO_LEVEL_WIDTH(FIFO_LEVEL_WIDTH)
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
    .tx_empty(tx_empty_status),
    .tx_fifo_empty(tx_fifo_empty),
    .tx_fifo_full(tx_fifo_full),
    .tx_fifo_level(tx_fifo_level),
    .tx_done_hw_set(tx_done_pulse),
    .rx_fifo_empty(rx_fifo_empty),
    .rx_fifo_full(rx_fifo_full),
    .rx_fifo_level(rx_fifo_level),
    .rx_fifo_data(rx_fifo_rdata),
    .rx_activity_pulse(rx_activity_pulse),
    .frame_err_hw_set(frame_err_pulse),
    .parity_err_hw_set(parity_err_pulse),
    .break_err_hw_set(break_err_pulse),
    .overrun_err_hw_set(overrun_err_pulse || rx_fifo_overflow_pulse),
    .irq_pending(irq_pending),
    .ctrl_enable(ctrl_enable),
    .ctrl_tx_irq_en(ctrl_tx_irq_en),
    .ctrl_rx_irq_en(ctrl_rx_irq_en),
    .ctrl_err_irq_en(ctrl_err_irq_en),
    .ctrl_tx_break(ctrl_tx_break),
    .ctrl_loopback_en(ctrl_loopback_en),
    .ctrl_timeout_irq_en(ctrl_timeout_irq_en),
    .ctrl_fifo_irq_en(ctrl_fifo_irq_en),
    .baud_div_reg(baud_div_reg),
    .cfg_data_bits_sel(cfg_data_bits_sel),
    .cfg_parity_en(cfg_parity_en),
    .cfg_parity_odd(cfg_parity_odd),
    .cfg_stop2(cfg_stop2),
    .tx_start(tx_start_unused),
    .tx_data(tx_data_unused),
    .tx_fifo_push(tx_fifo_push),
    .tx_fifo_wdata(tx_fifo_wdata),
    .tx_fifo_clear(tx_fifo_clear),
    .rx_fifo_pop(rx_fifo_pop),
    .rx_fifo_clear(rx_fifo_clear),
    .tx_threshold(tx_threshold),
    .rx_threshold(rx_threshold),
    .rx_timeout_cycles(rx_timeout_cycles),
    .scratch_reg(scratch_reg_unused),
    .rx_valid(rx_valid),
    .rx_data(rx_data_unused),
    .frame_err(frame_err),
    .parity_err(parity_err),
    .overrun_err(overrun_err),
    .break_err(break_err),
    .rx_timeout(rx_timeout),
    .irq_tx_done(irq_tx_done),
    .irq_error(irq_error),
    .irq_rx_timeout(irq_rx_timeout),
    .irq_tx_threshold(irq_tx_threshold),
    .irq_rx_threshold(irq_rx_threshold)
  );
endmodule
