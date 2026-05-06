COCOTB_ROOT = /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb
COCOTB_SHARE = $(COCOTB_ROOT)/share

SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOPLEVEL = gpio_pad

MODULE ?= tests.tb

VERILOG_SOURCES = $(PWD)/../rtl/gpio_pad_pkg.sv
VERILOG_SOURCES += $(PWD)/../rtl/gpio_pad_regs.sv
VERILOG_SOURCES += $(PWD)/../rtl/gpio_pad_core.sv
VERILOG_SOURCES += $(PWD)/../rtl/gpio_pad_wrapper.sv
VERILOG_SOURCES += $(PWD)/sim_dump.v

export COCOTB_SHARE_DIR = $(COCOTB_SHARE)
export LIB_DIR = $(COCOTB_SHARE)/lib
export COCOTB_PYTHONPATH = $(PWD)

include $(COCOTB_SHARE)/makefiles/Makefile.deprecations
include $(COCOTB_SHARE)/makefiles/simulators/Makefile.icarus
