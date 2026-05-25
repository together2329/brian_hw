#!/usr/bin/env bash
set -euo pipefail

# Reproducible RTL simulation harness for real_llm_counter_demo.
# Run from either repository root or the IP directory.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${IP_DIR}"

mkdir -p sim/build sim/waves

IVERILOG_BIN="${IVERILOG_BIN:-iverilog}"
VVP_BIN="${VVP_BIN:-vvp}"

# Keep all iverilog options before `-f`; this avoids older Icarus builds treating
# later options as preprocessor filenames when a command file is present.
COMPILE_CMD=("${IVERILOG_BIN}" -g2012 -Irtl -s tb_real_llm_counter_demo -o sim/build/tb_real_llm_counter_demo.vvp -f list/real_llm_counter_demo.f sim/tb_real_llm_counter_demo.sv)
RUN_CMD=("${VVP_BIN}" sim/build/tb_real_llm_counter_demo.vvp)

{
  echo "[run_sim] ip_dir=${IP_DIR}"
  echo "[run_sim] compile: ${COMPILE_CMD[*]}"
  "${COMPILE_CMD[@]}"
  echo "[run_sim] run: ${RUN_CMD[*]}"
  "${RUN_CMD[@]}"
} 2>&1 | tee sim/sim.log
