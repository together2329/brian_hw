# Makefile for quad_spi_ctrl cocotb simulation
export PATH := /Users/brian/Library/Python/3.9/bin:$(PATH)

# Work around broken cocotb-config shebang
COCOTB_MAKEFILES_DIR = /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share/makefiles
export COCOTB_MAKEFILES_DIR

# Force PYTHON_BIN to the Python that has cocotb
PYTHON_BIN = /Library/Developer/CommandLineTools/usr/bin/python3

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

include $(COCOTB_MAKEFILES_DIR)/Makefile.sim
