# Cocotb Makefile for dma_real simulation v2
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
RTL_DIR = /Users/brian/Desktop/Project/brian_hw/common_ai_agent/dma_real/rtl
TB_DIR  = /Users/brian/Desktop/Project/brian_hw/common_ai_agent/dma_real/tb/cocotb
VERILOG_SOURCES = $(RTL_DIR)/dma_real_cdc_sync.sv \
                  $(RTL_DIR)/dma_real_cg_cell.sv \
                  $(RTL_DIR)/dma_real_async_fifo.sv \
                  $(RTL_DIR)/dma_real_irq.sv \
                  $(RTL_DIR)/dma_real_arbiter.sv \
                  $(RTL_DIR)/dma_real_ahb_master.sv \
                  $(RTL_DIR)/dma_real_channel.sv \
                  $(RTL_DIR)/dma_real_apb_cfg.sv \
                  $(RTL_DIR)/dma_real_engine.sv \
                  $(RTL_DIR)/dma_real_top.sv \
                  $(TB_DIR)/dma_real_tb.sv
TOPLEVEL = dma_real_tb
MODULE = test_dma_real
COMPILE_ARGS = -g2012

COCOTB_MAKEFILES_DIR = /Users/brian/Library/Python/3.9/lib/python/site-packages/cocotb/share/makefiles
include $(COCOTB_MAKEFILES_DIR)/Makefile.sim
