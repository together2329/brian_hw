# =============================================================================
# DMA-330 Cocotb Test Makefile
# =============================================================================
# Usage:
#   make test_irq            — Run IRQ controller tests
#   make test_mfifo          — Run MFIFO tests
#   make test_decoder        — Run instruction decoder tests
#   make test_periph         — Run peripheral interface tests
#   make test_regfile        — Run register file tests
#   make test_axi            — Run AXI master tests
#   make test_channel        — Run channel thread tests
#   make test_manager        — Run manager thread tests
#   make test_apb            — Run APB slave tests
#   make test_cache          — Run instruction cache tests
#   make test_top            — Run top-level integration tests
#   make test_all            — Run all tests
#
# Waveform generation (for visual debugging with GTKWave, surfer, etc.):
#   make waves               — Quick waveform: runs channel test with VCD dump
#   make waves_top           — Top-level integration test with VCD dump
#   make waves_<testname>    — Any module test with VCD dump
#                              (irq, mfifo, decoder, periph, regfile, axi,
#                               channel, manager, apb, cache, top)
#   WAVES_FMT=fst            — Use FST format instead of VCD (smaller files)
#
#   Output: test_<name>_waves_work/dump.vcd  (or dump.fst)
#   Open:   gtkwave test_channel_waves_work/dump.vcd
#
# Lint:
#   make lint                — Verilator lint (summary)
#   make lint_verbose        — Verilator lint (full report)
# =============================================================================

# Common settings
SIM             ?= icarus
COCOTB_REDUCED_LOG_FMT ?= 1
WAVES           ?= 0
WAVES_FMT       ?= vcd
PROJ_ROOT       := $(CURDIR)/..
RTL_DIR         := $(PROJ_ROOT)/rtl
COMPILE_ARGS    := -g2012 -Wall
TEST_DIR        := $(CURDIR)

# Common RTL sources (shared by all tests)
PKG_SRC         := $(RTL_DIR)/dma330_pkg.sv

# Per-module source dependencies
MODULE_SRC_irq      := $(PKG_SRC) $(RTL_DIR)/dma330_irq_controller.sv
MODULE_SRC_mfifo    := $(PKG_SRC) $(RTL_DIR)/dma330_mfifo.sv
MODULE_SRC_decoder  := $(PKG_SRC) $(RTL_DIR)/dma330_instr_decoder.sv
MODULE_SRC_periph   := $(PKG_SRC) $(RTL_DIR)/dma330_periph_intf.sv
MODULE_SRC_regfile  := $(PKG_SRC) $(RTL_DIR)/dma330_regfile.sv
MODULE_SRC_axi      := $(PKG_SRC) $(RTL_DIR)/dma330_axi_master.sv
MODULE_SRC_channel  := $(PKG_SRC) $(RTL_DIR)/dma330_channel_thread.sv
MODULE_SRC_manager  := $(PKG_SRC) $(RTL_DIR)/dma330_manager_thread.sv
MODULE_SRC_apb      := $(PKG_SRC) $(RTL_DIR)/dma330_apb_slave.sv
MODULE_SRC_cache    := $(PKG_SRC) $(RTL_DIR)/dma330_instr_cache.sv
MODULE_SRC_top      := $(PKG_SRC) $(RTL_DIR)/dma330_axi_master.sv \
                        $(RTL_DIR)/dma330_apb_slave.sv \
                        $(RTL_DIR)/dma330_regfile.sv \
                        $(RTL_DIR)/dma330_instr_decoder.sv \
                        $(RTL_DIR)/dma330_instr_cache.sv \
                        $(RTL_DIR)/dma330_mfifo.sv \
                        $(RTL_DIR)/dma330_manager_thread.sv \
                        $(RTL_DIR)/dma330_channel_thread.sv \
                        $(RTL_DIR)/dma330_periph_intf.sv \
                        $(RTL_DIR)/dma330_irq_controller.sv \
                        $(RTL_DIR)/dma330_top.sv

# =============================================================================
# Helper macro for running a test
# Pattern: $(call run_test,name,toplevel,module,python_file,sources)
# =============================================================================

# =============================================================================
# Individual test targets
# =============================================================================

.PHONY: test_irq test_mfifo test_decoder test_periph test_regfile \
        test_axi test_channel test_manager test_apb test_cache test_top \
        test_all clean_all lint lint_verbose \
        waves waves_irq waves_mfifo waves_decoder waves_periph waves_regfile \
        waves_axi waves_channel waves_manager waves_apb waves_cache waves_top

# --- IRQ Controller ---
test_irq:
	@mkdir -p test_irq_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_irq_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_irq_controller \
		MODULE=test_irq \
		VERILOG_SOURCES="$(MODULE_SRC_irq)" \
		TESTFILE=test_irq.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- MFIFO ---
test_mfifo:
	@mkdir -p test_mfifo_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_mfifo_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_mfifo \
		MODULE=test_mfifo \
		VERILOG_SOURCES="$(MODULE_SRC_mfifo)" \
		TESTFILE=test_mfifo.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Instruction Decoder ---
test_decoder:
	@mkdir -p test_decoder_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_decoder_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_instr_decoder \
		MODULE=test_decoder \
		VERILOG_SOURCES="$(MODULE_SRC_decoder)" \
		TESTFILE=test_decoder.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Peripheral Interface ---
test_periph:
	@mkdir -p test_periph_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_periph_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_periph_intf \
		MODULE=test_periph \
		VERILOG_SOURCES="$(MODULE_SRC_periph)" \
		TESTFILE=test_periph.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Register File ---
test_regfile:
	@mkdir -p test_regfile_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_regfile_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_regfile \
		MODULE=test_regfile \
		VERILOG_SOURCES="$(MODULE_SRC_regfile)" \
		TESTFILE=test_regfile.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- AXI Master ---
test_axi:
	@mkdir -p test_axi_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_axi_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_axi_master \
		MODULE=test_axi \
		VERILOG_SOURCES="$(MODULE_SRC_axi)" \
		TESTFILE=test_axi.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Channel Thread ---
test_channel:
	@mkdir -p test_channel_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_channel_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_channel_thread \
		MODULE=test_channel \
		VERILOG_SOURCES="$(MODULE_SRC_channel)" \
		TESTFILE=test_channel.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Manager Thread ---
test_manager:
	@mkdir -p test_manager_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_manager_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_manager_thread \
		MODULE=test_manager \
		VERILOG_SOURCES="$(MODULE_SRC_manager)" \
		TESTFILE=test_manager.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- APB Slave ---
test_apb:
	@mkdir -p test_apb_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_apb_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_apb_slave \
		MODULE=test_apb \
		VERILOG_SOURCES="$(MODULE_SRC_apb)" \
		TESTFILE=test_apb.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Instruction Cache ---
test_cache:
	@mkdir -p test_cache_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_cache_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_instr_cache \
		MODULE=test_cache \
		VERILOG_SOURCES="$(MODULE_SRC_cache)" \
		TESTFILE=test_cache.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Top-Level Integration ---
test_top:
	@mkdir -p test_top_work
	PATH="$(TEST_DIR):$${PATH}" $(MAKE) -C test_top_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=dma330_top \
		MODULE=test_top \
		VERILOG_SOURCES="$(MODULE_SRC_top)" \
		TESTFILE=test_top.py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) sim

# --- Run all tests ---
test_all: test_irq test_mfifo test_decoder test_periph test_regfile \
          test_axi test_channel test_manager test_apb test_cache test_top

# =============================================================================
# Waveform Generation Targets (VCD / FST)
# =============================================================================
# Usage:
#   make waves               — Quick waveform: runs channel test with VCD dump
#   make waves_<testname>    — Run specific test with waveform capture
#   WAVES_FMT=fst            — Use FST format (smaller, needs libfst)
#
# Output: test_<name>_waves_work/dump.vcd  (or dump.fst)
# View:   gtkwave test_<name>_waves_work/dump.vcd
# =============================================================================

# Determine waveform file extension
ifeq ($(WAVES_FMT),fst)
  WAVES_EXT := fst
else
  WAVES_EXT := vcd
endif

define WAVES_RULE
waves_$(1):
	@echo "🌊 Running $(1) with waveform capture ($(WAVES_FMT))..."
	@mkdir -p test_$(1)_waves_work
	PATH="$(TEST_DIR):$$$${PATH}" $(MAKE) -C test_$(1)_waves_work -f $(CURDIR)/Makefile.test \
		TOPLEVEL=$(2) \
		MODULE=test_$(1) \
		VERILOG_SOURCES="$(3)" \
		TESTFILE=test_$(1).py \
		TEST_DIR=$(TEST_DIR) \
		SIM=$(SIM) \
		WAVES=1 \
		WAVES_FMT=$(WAVES_FMT) sim
	@if [ -f test_$(1)_waves_work/dump.$(WAVES_EXT) ]; then \
		echo "✅ Waveform saved: test_$(1)_waves_work/dump.$(WAVES_EXT)"; \
		echo "   Open with: gtkwave test_$(1)_waves_work/dump.$(WAVES_EXT)"; \
	else \
		echo "⚠️  No $(WAVES_EXT) file found — check simulator output"; \
	fi
endef

# Generate waves_* targets for every test module
$(eval $(call WAVES_RULE,irq,dma330_irq_controller,$(MODULE_SRC_irq)))
$(eval $(call WAVES_RULE,mfifo,dma330_mfifo,$(MODULE_SRC_mfifo)))
$(eval $(call WAVES_RULE,decoder,dma330_instr_decoder,$(MODULE_SRC_decoder)))
$(eval $(call WAVES_RULE,periph,dma330_periph_intf,$(MODULE_SRC_periph)))
$(eval $(call WAVES_RULE,regfile,dma330_regfile,$(MODULE_SRC_regfile)))
$(eval $(call WAVES_RULE,axi,dma330_axi_master,$(MODULE_SRC_axi)))
$(eval $(call WAVES_RULE,channel,dma330_channel_thread,$(MODULE_SRC_channel)))
$(eval $(call WAVES_RULE,manager,dma330_manager_thread,$(MODULE_SRC_manager)))
$(eval $(call WAVES_RULE,apb,dma330_apb_slave,$(MODULE_SRC_apb)))
$(eval $(call WAVES_RULE,cache,dma330_instr_cache,$(MODULE_SRC_cache)))
$(eval $(call WAVES_RULE,top,dma330_top,$(MODULE_SRC_top)))

# Convenience target: `make waves` runs channel test with waveform capture.
# Override with: make waves TEST=decoder
TEST            ?= channel
waves: waves_$(TEST)
	@true

# =============================================================================
# Verilator Lint
# =============================================================================
VERILATOR      ?= verilator
RTL_SRCS       := $(sort $(wildcard $(RTL_DIR)/dma330_*.sv))
# Filter out _check files, _vNN files, and .bak
RTL_PRODUCTION := $(RTL_DIR)/dma330_pkg.sv \
                  $(RTL_DIR)/dma330_irq_controller.sv \
                  $(RTL_DIR)/dma330_mfifo.sv \
                  $(RTL_DIR)/dma330_instr_decoder.sv \
                  $(RTL_DIR)/dma330_periph_intf.sv \
                  $(RTL_DIR)/dma330_regfile.sv \
                  $(RTL_DIR)/dma330_axi_master.sv \
                  $(RTL_DIR)/dma330_apb_slave.sv \
                  $(RTL_DIR)/dma330_instr_cache.sv \
                  $(RTL_DIR)/dma330_manager_thread.sv \
                  $(RTL_DIR)/dma330_channel_thread.sv \
                  $(RTL_DIR)/dma330_top.sv
LINT_WAIVER    := $(CURDIR)/verilator_waiver.vlt
LINT_TOP       := dma330_top

.PHONY: lint lint_verbose lint_summary

# Default lint: summary only
lint:
	@if ! command -v $(VERILATOR) >/dev/null 2>&1; then \
		echo "❌ verilator not found. Install with: brew install verilator"; \
		exit 1; \
	fi
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  DMA-330 Verilator Lint — Summary                          ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@$(VERILATOR) --lint-only -sv --top-module $(LINT_TOP) \
		$(LINT_WAIVER) $(RTL_PRODUCTION) 2>&1 | tee lint_work.log \
		| grep -E '%Warning|%Error' | sed 's/%//' | sort | uniq -c | sort -rn || true
	@echo ""
	@echo "── Files checked ──"
	@for f in $(RTL_PRODUCTION); do echo "  $$f"; done
	@echo ""
	@if grep -q '%Error' lint_work.log 2>/dev/null; then \
		echo "❌ Lint ERRORS found — run 'make lint_verbose' for details"; \
	else \
		warnings=$$(grep -c '%Warning' lint_work.log 2>/dev/null || echo 0); \
		echo "✅ Lint passed with $$warnings warnings — run 'make lint_verbose' for details"; \
	fi

# Verbose: show all messages
lint_verbose:
	@if ! command -v $(VERILATOR) >/dev/null 2>&1; then \
		echo "❌ verilator not found. Install with: brew install verilator"; \
		exit 1; \
	fi
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  DMA-330 Verilator Lint — Full Report                       ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@$(VERILATOR) --lint-only -sv --top-module $(LINT_TOP) \
		$(LINT_WAIVER) $(RTL_PRODUCTION) 2>&1; true

# --- Clean all work directories ---
clean_all:
	rm -rf test_*_work lint_work.log
