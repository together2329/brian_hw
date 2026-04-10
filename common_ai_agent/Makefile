# =============================================================================
# Makefile for Counter Module
# Targets: build, sim, wave, clean
# Requirements: Icarus Verilog (iverilog, vvp)
# Optional: GTKWave for waveform viewing
# =============================================================================

# --- Configuration -----------------------------------------------------------
TOP_MODULE   = counter
TB_MODULE    = counter_tb
WIDTH        ?= 8

# --- Paths -------------------------------------------------------------------
RTL_DIR      = rtl
TB_DIR       = tb
BUILD_DIR    = build
WAVE_DIR     = waves

# --- Source Files ------------------------------------------------------------
RTL_SRCS     = $(RTL_DIR)/counter.v
TB_SRCS      = $(TB_DIR)/counter_tb.sv

# --- Output Files ------------------------------------------------------------
COMPILED     = $(BUILD_DIR)/$(TB_MODULE)
VCD_FILE     = $(BUILD_DIR)/$(TB_MODULE).vcd

# --- Tools -------------------------------------------------------------------
IVERILOG     = iverilog
VVP          = vvp
GTKWAVE      = gtkwave

# --- Flags -------------------------------------------------------------------
IVERILOG_FLAGS = -g2012 -Wall -DTB_WIDTH=$(WIDTH)

# =============================================================================
# Targets
# =============================================================================

.PHONY: all build sim wave clean help

# --- Default target ----------------------------------------------------------
all: build

# --- Build (compile only, no simulation) -------------------------------------
build: $(BUILD_DIR)
	$(IVERILOG) $(IVERILOG_FLAGS) -o $(COMPILED) $(RTL_SRCS) $(TB_SRCS)
	@echo ""
	@echo "✅ Build complete: $(COMPILED)"

# --- Simulate (build + run) --------------------------------------------------
sim: build
	@echo ""
	@echo "▶ Running simulation..."
	@cd $(BUILD_DIR) && $(VVP) $(TB_MODULE)
	@echo ""
	@echo "✅ Simulation complete"

# --- Wave (build + sim + open GTKWave) ---------------------------------------
wave: sim
	@if command -v $(GTKWAVE) >/dev/null 2>&1; then \
		echo "▶ Opening GTKWave..."; \
		$(GTKWAVE) $(VCD_FILE) &; \
	else \
		echo "⚠️  GTKWave not found. VCD file at: $(VCD_FILE)"; \
	fi

# --- Clean build artifacts ---------------------------------------------------
clean:
	@echo "🧹 Cleaning build directory..."
	@rm -rf $(BUILD_DIR)
	@echo "✅ Clean complete"

# --- Help --------------------------------------------------------------------
help:
	@echo ""
	@echo "Counter Module — Makefile Help"
	@echo "==============================="
	@echo ""
	@echo "  make          Build the simulation binary"
	@echo "  make build    Build the simulation binary"
	@echo "  make sim      Build and run simulation"
	@echo "  make wave     Build, simulate, and open GTKWave"
	@echo "  make clean    Remove build artifacts"
	@echo "  make help     Show this help message"
	@echo ""
	@echo "Options:"
	@echo "  WIDTH=N       Set counter width (default: 8)"
	@echo ""
	@echo "Examples:"
	@echo "  make sim              # Run with WIDTH=8"
	@echo "  make sim WIDTH=16     # Run with WIDTH=16"
	@echo "  make wave WIDTH=4     # Simulate and view waveforms"
	@echo ""

# --- Create build directory --------------------------------------------------
$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)
