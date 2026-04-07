# ============================================================================
# TDISP cocotb Makefile
# Supports: Icarus Verilog (default), Verilator (fallback)
# ============================================================================

# --- Simulator selection ---
SIM ?= icarus

# --- Top-level module and testbench ---
TOPLEVEL_LANG = verilog
TOPLEVEL      = tdisp_top
MODULE        ?= test_full_lifecycle

# --- Source file paths ---
HDL_DIR   := $(shell pwd)/hdl
RTL_DIR   := $(shell pwd)/..

# RTL source files (order matters for iverilog)
RTL_SRCS = \
	$(RTL_DIR)/tdisp_pkg.sv \
	$(RTL_DIR)/tdisp_fsm.sv \
	$(RTL_DIR)/tdisp_lock_handler.sv \
	$(RTL_DIR)/tdisp_msg_codec.sv \
	$(RTL_DIR)/tdisp_reg_tracker.sv \
	$(RTL_DIR)/tdisp_req_handler.sv \
	$(RTL_DIR)/tdisp_tlp_filter.sv \
	$(RTL_DIR)/tdisp_top.sv

# Cocotb wrapper (thin SV shim for DUT instantiation + waveform probes)
WRAPPER_SRC = $(HDL_DIR)/tb_tdisp_cocotb.sv

# All verilog sources combined
VERILOG_SOURCES = $(RTL_SRCS) $(WRAPPER_SRC)

# --- Common cocotb settings ---
GPI_EXTRA :=

# --- Python path (so cocotb can find tdisp_tb package) ---
export PYTHONPATH := $(shell pwd):$(PYTHONPATH)

# --- Icarus Verilog specific ---
# iverilog handles SystemVerilog with -g2012 flag
# Extra compile flags for SV packed struct support
ifeq ($(SIM),icarus)
    COMPILE_ARGS += -g2012
    # Icarus may need extended timescale for clock generation
    COMPILE_ARGS += -timescale 1ns/1ps
    # Disable some warnings that fire on SV structs
    COMPILE_ARGS += -Wno-timescale
    EXTRA_ARGS += -DTV_NUM_TDI=2
endif

# --- Verilator specific ---
ifeq ($(SIM),verilator)
    # Verilator needs --binary for cocotb, not standalone
    COMPILE_ARGS += --binary --trace
    # Allow SV packed structs
    COMPILE_ARGS += --language 1800-2017
    # Verilator lint waivers
    COMPILE_ARGS += -Wno-WIDTHEXPAND -Wno-UNUSEDSIGNAL -Wno-UNOPTFLAT
    COMPILE_ARGS += -Wno-CASEINCOMPLETE -Wno-CMPCONST -Wno-INITIALDLY
    COMPILE_ARGS += -Wno-TIMESCALEMOD -Wno-EOFNEWLINE
    # Extra MFCU (make faster)
    COMPILE_ARGS += --threads 1
    EXTRA_ARGS += -DTV_NUM_TDI=2
endif

# --- Waveform output ---
ifeq ($(WAVES),1)
    ifeq ($(SIM),icarus)
        # Icarus: VCD dump controlled by wrapper $dumpfile/$dumpvars
        COMPILE_ARGS += -DTVCD_DUMP=1
    endif
    ifeq ($(SIM),verilator)
        # Verilator: --trace already added above
    endif
endif

# --- Test timeout (cocotb) ---
export COCOTB_TIMEOUT ?= 60

# ============================================================================
# Include cocotb's standard Makefile.sim u2014 this MUST be at top level
# (include is a Make directive, not a shell command)
# ============================================================================
include $(shell cocotb-config --makefiles)/Makefile.sim

# ============================================================================
# Additional Targets
# ============================================================================

# Run all tests sequentially
.PHONY: test_all
test_all:
	@echo "=== Running all TDISP cocotb tests ==="
	@for mod in test_full_lifecycle test_error_scenarios test_tlp_filter test_multi_tdi test_protocol test_random_stress; do \
		echo "--- Running $$mod ---"; \
		$(MAKE) run MODULE=$$mod || exit 1; \
	done
	@echo "=== All tests passed ==="

# Clean build artifacts
.PHONY: clean
clean:
	rm -rf sim_build/ results.xml __pycache__/ .cocotb/
	find . -name "*.pyc" -delete
	find . -name "*.vcd" -delete
	find . -name "*.fst" -delete

# Help
.PHONY: help
help:
	@echo "TDISP cocotb Testbench"
	@echo ""
	@echo "Usage:"
	@echo "  make run              - Run default test (test_full_lifecycle)"
	@echo "  make run MODULE=X     - Run specific test module"
	@echo "  make test_all         - Run all tests"
	@echo "  make SIM=verilator    - Use Verilator instead of Icarus"
	@echo "  make WAVES=1          - Enable waveform dumping"
	@echo "  make clean            - Remove build artifacts"
	@echo ""
	@echo "Available test modules:"
	@echo "  test_full_lifecycle   - Full TDI lifecycle (CONFIG_UNLOCKED u2192 RUN)"
	@echo "  test_error_scenarios  - Error injection and recovery"
	@echo "  test_tlp_filter       - Egress/ingress TLP filtering"
	@echo "  test_multi_tdi        - Multi-TDI independence"
	@echo "  test_protocol         - Protocol compliance tests"
	@echo "  test_random_stress    - Random stress with backpressure"
