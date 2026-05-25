#!/usr/bin/env bash
set -euo pipefail

# Run from the IP root: apb_uart_txrx_demo/
if [[ ! -f rtl/apb_uart_txrx_demo.sv || ! -f sim/tb_apb_uart_txrx_demo.sv ]]; then
  echo "ERROR: run from apb_uart_txrx_demo/ IP root" >&2
  exit 2
fi

mkdir -p sim/waves
rm -f sim/tb_apb_uart_txrx_demo.vvp \
      sim/sim.log \
      sim/sim_results.json \
      sim/scoreboard_events.csv \
      sim/coverage_results.json \
      sim/waveform_manifest.json \
      sim/waves/apb_uart_txrx_demo.vcd

iverilog -g2012 -Wall -o sim/tb_apb_uart_txrx_demo.vvp \
  rtl/apb_uart_txrx_demo.sv \
  sim/tb_apb_uart_txrx_demo.sv

set +e
vvp sim/tb_apb_uart_txrx_demo.vvp | tee sim/sim.log
sim_status=${PIPESTATUS[0]}
set -e
if [[ ${sim_status} -ne 0 ]]; then
  echo "ERROR: vvp failed with status ${sim_status}" >&2
  exit ${sim_status}
fi

if [[ ! -f sim/sim_results.json ]]; then
  echo "ERROR: missing sim/sim_results.json" >&2
  exit 3
fi
if [[ ! -f sim/scoreboard_events.csv ]]; then
  echo "ERROR: missing sim/scoreboard_events.csv" >&2
  exit 4
fi
if [[ ! -s sim/waves/apb_uart_txrx_demo.vcd ]]; then
  echo "ERROR: missing or empty VCD" >&2
  exit 5
fi

python3 - <<'PY'
import json, sys
from pathlib import Path
p = Path('sim/sim_results.json')
data = json.loads(p.read_text())
if not data.get('passed', False) or data.get('scoreboard_fail') != 0:
    print(f"ERROR: scoreboard failure in {p}: {data}", file=sys.stderr)
    sys.exit(6)
print(f"Directed simulation passed: {data}")
PY
