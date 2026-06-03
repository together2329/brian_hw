# cocotb sim for mctp_assembler_v3_axi_wr_ingress (FL-oracle scoreboard)
TOPLEVEL_LANG ?= verilog
SIM ?= icarus

THIS_DIR := $(shell pwd)
VERILOG_SOURCES := $(THIS_DIR)/../../rtl/mctp_assembler_v3_axi_wr_ingress.sv
TOPLEVEL := mctp_assembler_v3_axi_wr_ingress
MODULE := test_axi_wr_ingress

COMPILE_ARGS += -g2012
WAVES ?= 1

export PYTHONPATH := $(THIS_DIR)/../../model:$(THIS_DIR):$(PYTHONPATH)

include $(shell cocotb-config --makefiles)/Makefile.sim
