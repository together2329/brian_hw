# Cocotb Makefile for example_counter
SIM ?= icarus
TOPLEVEL_LANG = verilog

VERILOG_SOURCES = $(PWD)/../rtl/example_counter.sv
TOPLEVEL = example_counter
MODULE = test_example_counter

# Cocotb root
COCOTB_HDL_TIMEUNIT = 1ns
COCOTB_HDL_TIMEPRECISION = 1ps

include /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share/makefiles/Makefile.sim
