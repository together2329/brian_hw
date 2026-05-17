# cocotb Makefile for pl330realverify
# Uses Icarus Verilog as the simulator

TOPLEVEL_LANG ?= verilog
TOPLEVEL = pl330realverify
MODULE = test_pl330realverify

SIM ?= icarus

# RTL sources
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_param.vh
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_regs.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_channel_fsm.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_axi_rd.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_axi_wr.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_datapath.sv
VERILOG_SOURCES += $(PWD)/../../rtl/pl330realverify_event_irq.sv

# Icarus flags
COMPILE_ARGS += -g2012

# Coverage and waveform
PLUSARGS += -fst
export COCOTB_RESOLVE_X = ZEROS

include $(shell cocotb-config --makefiles)/Makefile.sim
