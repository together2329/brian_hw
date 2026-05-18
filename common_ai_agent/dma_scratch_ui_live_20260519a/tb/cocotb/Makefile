# Cocotb Makefile for dma_scratch_ui_live_20260519a
# Simulator: Icarus Verilog (default)

TOPLEVEL_LANG = verilog
TOPLEVEL = dma_scratch_ui_live_20260519a

VERILOG_SOURCES = $(shell cat ../list/dma_scratch_ui_live_20260519a.f | sed 's|^|../|')

# Icarus-specific
SIM ?= icarus
COMPILE_ARGS = -g2012

# Module under test
MODULE ?= test_dma_scratch_ui_live_20260519a

# Test case selection
COCOTB_TESTCASE ?= test_reset_only

# Waveform
PLUSARGS += -fst
WAVES ?= 1
ifeq ($(WAVES),1)
    EXTRA_ARGS += -DCOCOTB_DUMP_WAVES
endif

include $(shell python3 -m cocotb.config --makefiles)/Makefile.sim
