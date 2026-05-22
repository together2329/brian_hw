# Makefile for quad_spi_ctrl cocotb simulation
export PATH := /tmp:$(PATH)

# Use wrapper cocotb-config
COCOTB_MAKEFILES_DIR := $(shell cocotb-config --makefiles 2>/dev/null || echo /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share/makefiles)
export COCOTB_MAKEFILES_DIR

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

include $(shell cocotb-config --makefiles)/Makefile.sim
