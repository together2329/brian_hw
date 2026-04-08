# =============================================================================
# Cocotb Makefile for parameterized up/down counter
#
# Usage:
#   make                    # Run all tests with default WIDTH=8
#   make WIDTH=4            # Run with WIDTH=4
#   make WIDTH=16           # Run with WIDTH=16
#   make TEST=test_reset    # Run a single test module
#   make GUI=1              # Run with waveform dumping (FST)
# =============================================================================

# --- Simulator ---
SIM             ?= icarus

# --- Top-level RTL module ---
TOPLEVEL_LANG    = verilog
TOPLEVEL         = counter

# --- Test modules (cocotb 2.0+ uses COCOTB_TEST_MODULES) ---
ALL_TEST_MODULES := tests.test_reset,tests.test_up_count,tests.test_down_count,tests.test_enable,tests.test_load,tests.test_direction_switch,tests.test_stress,tests.test_param_width

# --- Width parameter (overridable) ---
WIDTH           ?= 8

# --- Verilog sources ---
VERILOG_SOURCES  = $(shell pwd)/../counter.v

# --- Extra compile-time defines for iverilog ---
COMPILE_ARGS    += -P counter.WIDTH=$(WIDTH)

# --- Test selection ---
# Run all tests by default; override with TEST=test_reset for a single module
ifneq ($(TEST),)
  COCOTB_TEST_MODULES := tests.$(TEST)
else
  COCOTB_TEST_MODULES := $(ALL_TEST_MODULES)
endif

# --- Python path: include tb_cocotb root for imports ---
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

# --- Waveform dumping ---
ifeq ($(GUI),1)
  EXTRA_ARGS += --waves
endif

# --- Cocotb import ---
include $(shell cocotb-config --makefile)/Makefile.sim

# --- Convenience targets ---
.PHONY: help clean_all widths

help: ## Show available targets
	@echo "Usage:"
	@echo "  make                  Run all tests (WIDTH=8)"
	@echo "  make WIDTH=4          Run all tests with WIDTH=4"
	@echo "  make WIDTH=16         Run all tests with WIDTH=16"
	@echo "  make TEST=test_reset  Run a single test module"
	@echo "  make GUI=1            Enable waveform dumping"
	@echo "  make widths           Run tests for WIDTH=4,8,16"
	@echo "  make clean_all        Remove all build artifacts"

widths: ## Run tests for all supported widths
	@echo "=== Running tests with WIDTH=4 ==="
	@$(MAKE) WIDTH=4
	@echo "=== Running tests with WIDTH=8 ==="
	@$(MAKE) WIDTH=8
	@echo "=== Running tests with WIDTH=16 ==="
	@$(MAKE) WIDTH=16
	@echo "=== All width configurations passed ==="

clean_all: ## Remove all build artifacts
	rm -rf results.xml sim_build __pycache__ tests/__pycache__
