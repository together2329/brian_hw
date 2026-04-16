# Cocotb DMA Testbench Makefile (Icarus Verilog)

SIM ?= icarus
TOPLEVEL_LANG := verilog

# Resolve paths relative to this Makefile (more robust than relying on $PWD)
# Strip trailing slash for stable/normalized path rendering in logs and artifacts.
THIS_DIR := $(patsubst %/,%,$(dir $(abspath $(lastword $(MAKEFILE_LIST)))))
RTL_DIR := $(abspath $(THIS_DIR)/../../rtl)
TB_DIR := $(abspath $(THIS_DIR)/../../tb)
TEST_DIR := $(abspath $(THIS_DIR)/tests)

# Improve PATH robustness for local venv/user installs
export PATH := $(THIS_DIR)/.venv/bin:$(HOME)/.local/bin:$(PATH)

# cocotb entry-point tool (resolved if available)
COCOTB_CONFIG ?= $(shell command -v cocotb-config 2>/dev/null)
COCOTB_MAKEFILES := $(shell if [ -n "$(COCOTB_CONFIG)" ]; then $(COCOTB_CONFIG) --makefiles 2>/dev/null; fi)

# DUT top module
TOPLEVEL := dma_cocotb_top

# Verilog sources
VERILOG_SOURCES := \
	$(RTL_DIR)/dma.sv \
	$(TB_DIR)/ram_model.sv \
	$(TB_DIR)/dma_cocotb_top.sv

# Python test module
MODULE := test_dma

# Cocotb test directory
export PYTHONPATH := $(TEST_DIR):$(PYTHONPATH)

# Extra compile options
COMPILE_ARGS += -g2012

# Wave dump (enable with: make WAVES=1)
ifeq ($(WAVES),1)
COMPILE_ARGS += -D DUMP_WAVES
EXTRA_ARGS += --trace --trace-structs
endif

# Deterministic regression presets
SMOKE_SEED ?= 101
SMOKE_NUM_RANDOM ?= 5

REGRESS_SEED ?= 12345
REGRESS_NUM_RANDOM ?= 20

STRESS_SEED ?= 424242
STRESS_NUM_RANDOM ?= 100

# Optional type-check control (non-blocking by default)
MYPY_BLOCKING ?= 0

# Lint strictness tiers (fast/full/ci)
LINT_FAST_RTL_WARN_AS_ERROR ?= 0
LINT_FULL_RTL_WARN_AS_ERROR ?= 0
LINT_CI_RTL_WARN_AS_ERROR ?= 1
LINT_FAST_MYPY_BLOCKING ?= 0
LINT_FULL_MYPY_BLOCKING ?= 0
LINT_CI_MYPY_BLOCKING ?= 1
LINT_CI_REQUIRE_RESULTS ?= 1

# Lint report outputs (CI artifacts)
LINT_REPORT ?= $(THIS_DIR)/lint_report.md
LINT_RTL_JSON ?= $(THIS_DIR)/lint_rtl_report.json
LINT_RTL_SARIF ?= $(THIS_DIR)/lint_rtl_report.sarif
COCOTB_RESULTS_XML ?= $(THIS_DIR)/results.xml
COCOTB_RESULTS_JSON ?= $(THIS_DIR)/cocotb_results_gate.json
REPO_ROOT := $(abspath $(THIS_DIR)/../..)
LINT_REPORT_REL := $(patsubst $(REPO_ROOT)/%,%,$(abspath $(LINT_REPORT)))
LINT_RTL_JSON_REL := $(patsubst $(REPO_ROOT)/%,%,$(abspath $(LINT_RTL_JSON)))
LINT_RTL_SARIF_REL := $(patsubst $(REPO_ROOT)/%,%,$(abspath $(LINT_RTL_SARIF)))
COCOTB_RESULTS_XML_REL := $(patsubst $(REPO_ROOT)/%,%,$(abspath $(COCOTB_RESULTS_XML)))
COCOTB_RESULTS_JSON_REL := $(patsubst $(REPO_ROOT)/%,%,$(abspath $(COCOTB_RESULTS_JSON)))
LINT_RTL_BASELINE ?=
LINT_RTL_INCLUDE ?= rtl/**/*.sv,tb/**/*.sv
LINT_RTL_EXCLUDE ?=
LINT_RTL_FAST_INCLUDE ?= rtl/dma.sv,tb/dma_cocotb_top.sv,tb/ram_model.sv
LINT_RTL_FAST_EXCLUDE ?=

# Convenience targets
.PHONY: help smoke regress stress lint lint-ci lint-fast lint-py lint-type lint-rtl lint-rtl-fast lint-rtl-report lint-report lint-cocotb-results check-cocotb matrix

help:
	@echo "Cocotb DMA targets:"
	@echo "  make smoke         - deterministic smoke subset (tests 1-3)"
	@echo "  make regress       - deterministic full-suite regression"
	@echo "  make stress        - deterministic stress/random-focused tests"
	@echo "  make matrix        - print seed/NUM_RANDOM/artifact matrix"
	@echo "  make lint          - full lint (lint-py + lint-type + lint-rtl)"
	@echo "  make lint-fast     - fast pre-commit lint (lint-py + lint-type + lightweight lint-rtl-fast)"
	@echo "  make lint-py       - python syntax/style lint"
	@echo "  make lint-type     - optional mypy type checks (non-blocking by default)"
	@echo "  make lint-rtl      - run RTL link/lint check via pyslang"
	@echo "  strictness defaults: fast/full=warns allowed, ci=warns as errors"
	@echo "  make lint-rtl-fast - lightweight RTL lint subset for pre-commit"
	@echo "  make lint-rtl-report - print unresolved-reference focused report"
	@echo "  make lint-cocotb-results - parse $(COCOTB_RESULTS_XML) and fail on failing tests"
	@echo "  make lint-ci       - aggregate lint for CI (py + type + rtl + cocotb results gate)"
	@echo "  make lint-report   - generate deterministic markdown lint artifact ($(LINT_REPORT_REL))"
	@echo "                     and structured RTL JSON artifact ($(LINT_RTL_JSON_REL)) (non-gating)"
	@echo "  vars: LINT_RTL_BASELINE=<path> to fail only on new diagnostics"
	@echo "        LINT_RTL_INCLUDE='rtl/**/*.sv,tb/**/*.sv' LINT_RTL_EXCLUDE='<glob,...>'"
	@echo "  make check-cocotb  - verify cocotb-config is available"
	@echo "  make sim           - cocotb simulator target from Makefile.sim"

check-cocotb:
	@if [ -z "$(COCOTB_CONFIG)" ] || [ -z "$(COCOTB_MAKEFILES)" ]; then \
		echo "ERROR: cocotb-config not found in PATH. Activate your venv or install cocotb: python3 -m pip install cocotb"; \
		exit 1; \
	fi

matrix:
	@echo "Deterministic regression matrix:"
	@echo "  smoke : seed=$(SMOKE_SEED)   num_random=$(SMOKE_NUM_RANDOM)   artifact_tag=smoke_seed$(SMOKE_SEED)_n$(SMOKE_NUM_RANDOM)"
	@echo "  regress: seed=$(REGRESS_SEED) num_random=$(REGRESS_NUM_RANDOM) artifact_tag=regress_seed$(REGRESS_SEED)_n$(REGRESS_NUM_RANDOM)"
	@echo "  stress: seed=$(STRESS_SEED)  num_random=$(STRESS_NUM_RANDOM)  artifact_tag=stress_seed$(STRESS_SEED)_n$(STRESS_NUM_RANDOM)"

smoke:
	$(MAKE) sim \
		TESTCASE=test_1_length_zero_noop,test_2_length_one_basic,test_3_back_to_back \
		DMA_SEED=$(SMOKE_SEED) DMA_NUM_RANDOM=$(SMOKE_NUM_RANDOM) \
		DMA_ARTIFACT_TAG=smoke_seed$(SMOKE_SEED)_n$(SMOKE_NUM_RANDOM)

regress:
	$(MAKE) sim \
		DMA_SEED=$(REGRESS_SEED) DMA_NUM_RANDOM=$(REGRESS_NUM_RANDOM) \
		DMA_ARTIFACT_TAG=regress_seed$(REGRESS_SEED)_n$(REGRESS_NUM_RANDOM)

stress:
	$(MAKE) sim \
		TESTCASE=test_9_random_transfers,test_16_stress_50_random_transfers \
		DMA_SEED=$(STRESS_SEED) DMA_NUM_RANDOM=$(STRESS_NUM_RANDOM) \
		DMA_ARTIFACT_TAG=stress_seed$(STRESS_SEED)_n$(STRESS_NUM_RANDOM)

lint:
	@$(MAKE) lint-py
	@$(MAKE) lint-type MYPY_BLOCKING=$(LINT_FULL_MYPY_BLOCKING)
	@$(MAKE) lint-rtl RTL_WARN_AS_ERROR=$(LINT_FULL_RTL_WARN_AS_ERROR)
	@echo "[lint] complete (tier=full, RTL_WARN_AS_ERROR=$(LINT_FULL_RTL_WARN_AS_ERROR), MYPY_BLOCKING=$(LINT_FULL_MYPY_BLOCKING))"

lint-fast:
	@$(MAKE) lint-py
	@$(MAKE) lint-type MYPY_BLOCKING=$(LINT_FAST_MYPY_BLOCKING)
	@$(MAKE) lint-rtl-fast RTL_WARN_AS_ERROR=$(LINT_FAST_RTL_WARN_AS_ERROR)
	@echo "[lint-fast] complete (tier=fast, RTL_WARN_AS_ERROR=$(LINT_FAST_RTL_WARN_AS_ERROR), MYPY_BLOCKING=$(LINT_FAST_MYPY_BLOCKING))"

lint-py:
	@set -e; \
	echo "[lint] py_compile"; \
	python3 -m py_compile $(TEST_DIR)/*.py; \
	if command -v ruff >/dev/null 2>&1; then \
		echo "[lint] ruff"; \
		ruff check $(TEST_DIR); \
	elif command -v flake8 >/dev/null 2>&1; then \
		echo "[lint] flake8"; \
		flake8 $(TEST_DIR); \
	else \
		echo "[lint] WARNING: neither ruff nor flake8 found; only py_compile executed"; \
	fi

lint-type:
	@set -e; \
	if command -v mypy >/dev/null 2>&1; then \
		echo "[lint-type] mypy (MYPY_BLOCKING=$(MYPY_BLOCKING))"; \
		if [ "$(MYPY_BLOCKING)" = "1" ]; then \
			mypy $(TEST_DIR); \
		else \
			mypy $(TEST_DIR) || echo "[lint-type] WARNING: mypy reported issues (non-blocking mode)"; \
		fi; \
	else \
		echo "[lint-type] INFO: mypy not found; skipping optional type check"; \
	fi

lint-rtl:
	@echo "[lint-rtl] pyslang link/compile check"
	@RTL_LINT_JSON=$(LINT_RTL_JSON) RTL_LINT_SARIF=$(LINT_RTL_SARIF) RTL_LINT_BASELINE=$(LINT_RTL_BASELINE) RTL_LINT_INCLUDE="$(LINT_RTL_INCLUDE)" RTL_LINT_EXCLUDE="$(LINT_RTL_EXCLUDE)" RTL_WARN_AS_ERROR=$(RTL_WARN_AS_ERROR) python3 $(THIS_DIR)/lint_rtl_pyslang.py

lint-rtl-fast:
	@echo "[lint-rtl-fast] lightweight pyslang lint subset"
	@RTL_LINT_JSON=$(LINT_RTL_JSON) RTL_LINT_SARIF=$(LINT_RTL_SARIF) RTL_LINT_BASELINE= RTL_LINT_INCLUDE="$(LINT_RTL_FAST_INCLUDE)" RTL_LINT_EXCLUDE="$(LINT_RTL_FAST_EXCLUDE)" RTL_WARN_AS_ERROR=$(RTL_WARN_AS_ERROR) python3 $(THIS_DIR)/lint_rtl_pyslang.py

lint-rtl-report:
	@echo "[lint-rtl-report] unresolved-reference focused summary"
	@$(MAKE) lint-rtl

lint-cocotb-results:
	@echo "[lint-cocotb-results] cocotb results quality gate"
	@if [ "$(LINT_CI_REQUIRE_RESULTS)" = "0" ] && [ ! -f "$(COCOTB_RESULTS_XML)" ]; then \
		echo "[lint-cocotb-results] SKIP: missing $(COCOTB_RESULTS_XML) and LINT_CI_REQUIRE_RESULTS=0"; \
	else \
		COCOTB_RESULTS_JSON=$(COCOTB_RESULTS_JSON) python3 $(THIS_DIR)/cocotb_results_gate.py $(COCOTB_RESULTS_XML); \
	fi

lint-ci:
	@$(MAKE) lint-py
	@$(MAKE) lint-type MYPY_BLOCKING=$(LINT_CI_MYPY_BLOCKING)
	@$(MAKE) lint-rtl RTL_WARN_AS_ERROR=$(LINT_CI_RTL_WARN_AS_ERROR)
	@$(MAKE) lint-cocotb-results LINT_CI_REQUIRE_RESULTS=$(LINT_CI_REQUIRE_RESULTS)
	@echo "[lint-ci] complete (tier=ci, RTL_WARN_AS_ERROR=$(LINT_CI_RTL_WARN_AS_ERROR), MYPY_BLOCKING=$(LINT_CI_MYPY_BLOCKING), REQUIRE_RESULTS=$(LINT_CI_REQUIRE_RESULTS))"

lint-report:
	@set -e; \
	status_py=FAIL; \
	status_type=FAIL; \
	status_rtl=FAIL; \
	status_results=FAIL; \
	status_ci=FAIL; \
	if $(MAKE) --no-print-directory lint-py >/dev/null 2>&1; then status_py=PASS; fi; \
	if $(MAKE) --no-print-directory lint-type >/dev/null 2>&1; then status_type=PASS; fi; \
	if $(MAKE) --no-print-directory lint-rtl >/dev/null 2>&1; then status_rtl=PASS; fi; \
	if $(MAKE) --no-print-directory lint-cocotb-results >/dev/null 2>&1; then status_results=PASS; fi; \
	if $(MAKE) --no-print-directory lint-ci >/dev/null 2>&1; then status_ci=PASS; fi; \
	echo "# Lint Report" > $(LINT_REPORT); \
	echo "" >> $(LINT_REPORT); \
	echo "Generated by: make lint-report" >> $(LINT_REPORT); \
	echo "Format: deterministic status summary (stable ordering, no volatile command logs)" >> $(LINT_REPORT); \
	echo "" >> $(LINT_REPORT); \
	echo "## Summary" >> $(LINT_REPORT); \
	echo "| Check | Status |" >> $(LINT_REPORT); \
	echo "|---|---|" >> $(LINT_REPORT); \
	echo "| lint-py | $$status_py |" >> $(LINT_REPORT); \
	echo "| lint-type | $$status_type |" >> $(LINT_REPORT); \
	echo "| lint-rtl | $$status_rtl |" >> $(LINT_REPORT); \
	echo "| lint-cocotb-results | $$status_results |" >> $(LINT_REPORT); \
	echo "| lint-ci | $$status_ci |" >> $(LINT_REPORT); \
	echo "" >> $(LINT_REPORT); \
	echo "## Artifacts" >> $(LINT_REPORT); \
	echo "- Markdown Report: $(LINT_REPORT_REL)" >> $(LINT_REPORT); \
	echo "- RTL JSON: $(LINT_RTL_JSON_REL)" >> $(LINT_REPORT); \
	echo "- RTL SARIF: $(LINT_RTL_SARIF_REL)" >> $(LINT_REPORT); \
	echo "- Cocotb Results XML: $(COCOTB_RESULTS_XML_REL)" >> $(LINT_REPORT); \
	echo "- Cocotb Gate JSON: $(COCOTB_RESULTS_JSON_REL)" >> $(LINT_REPORT); \
	echo "[lint-report] wrote $(LINT_REPORT_REL)"

# Include cocotb's make rules when available.
# This keeps non-sim targets (e.g., help/lint/check-cocotb) usable even if
# cocotb is not installed in the current PATH.
ifeq ($(strip $(COCOTB_MAKEFILES)),)
sim:
	@$(MAKE) check-cocotb
else
include $(COCOTB_MAKEFILES)/Makefile.sim
endif
