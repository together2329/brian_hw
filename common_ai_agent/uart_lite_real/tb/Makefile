# Makefile for uart_lite_real cocotb testbench

SIM ?= icarus
TOPLEVEL_LANG = verilog

VERILOG_SOURCES = \
	$(RTLDIR)/uart_lite_real_param.vh \
	$(RTLDIR)/uart_lite_real_baud_gen.sv \
	$(RTLDIR)/uart_lite_real_tx_fifo.sv \
	$(RTLDIR)/uart_lite_real_rx_fifo.sv \
	$(RTLDIR)/uart_lite_real_tx.sv \
	$(RTLDIR)/uart_lite_real_rx.sv \
	$(RTLDIR)/uart_lite_real_regs.sv \
	$(RTLDIR)/uart_lite_real_core.sv \
	$(RTLDIR)/uart_lite_real.sv

RTLDIR = ../rtl
TOPLEVEL = uart_lite_real
MODULE = test_uart_lite_real

COMPILE_ARGS = -g2012 -I$(RTLDIR)

include $(shell cocotb-config --makefiles)/Makefile.sim
