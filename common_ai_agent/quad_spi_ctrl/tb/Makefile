export PATH := /Users/brian/Library/Python/3.9/bin:$(PATH)

# Makefile for quad_spi_ctrl cocotb simulation
# TOPLEVEL_LANG = verilog
TOPLEVEL = quad_spi_ctrl_top

VERILOG_SOURCES = $(PWD)/../rtl/quad_spi_ctrl_top.sv \
                  $(PWD)/../rtl/quad_spi_ctrl_apb.sv \
                  $(PWD)/../rtl/quad_spi_ctrl_fifo.sv \
                  $(PWD)/../rtl/quad_spi_ctrl_sclk_gen.sv \
                  $(PWD)/../rtl/quad_spi_ctrl_fsm.sv \
                  $(PWD)/../rtl/quad_spi_ctrl_irq.sv

COMPILE_ARGS = -g2012

MODULE = cocotb.test_quad_spi_ctrl

export PYTHONPATH := $(PWD):$(PYTHONPATH)

CUSTOM_SIM_MAKEFILE = /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share/makefiles/Makefile.sim
include $(CUSTOM_SIM_MAKEFILE)
