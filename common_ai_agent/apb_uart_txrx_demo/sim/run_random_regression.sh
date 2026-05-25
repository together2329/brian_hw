#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f rtl/apb_uart_txrx_demo.sv || ! -f sim/tb_apb_uart_txrx_demo_random.sv ]]; then
  echo "ERROR: run from apb_uart_txrx_demo/ IP root" >&2
  exit 2
fi

SEEDS=${SEEDS:-${1:-1}}
TXNS=${TXNS:-${2:-20}}
VCD=${VCD:-0}

mkdir -p sim/random/waves
rm -f sim/random/random_regression_summary.json \
      sim/random/random_results.json \
      sim/random/random_scoreboard_events.csv \
      sim/random/random.log \
      sim/random/random_seed_*.json \
      sim/random/random_seed_*.csv \
      sim/random/random_seed_*.log \
      sim/random/waves/random*.vcd \
      sim/tb_apb_uart_txrx_demo_random.vvp

iverilog -g2012 -Wall -o sim/tb_apb_uart_txrx_demo_random.vvp \
  -c list/apb_uart_txrx_demo.f \
  sim/tb_apb_uart_txrx_demo_random.sv

summary_tmp=sim/random/random_regression_summary.tmp
printf '{"seeds":[' > "${summary_tmp}"
first=1
fail_total=0
for seed in ${SEEDS//,/ }; do
  echo "Running random seed=${seed} txns=${TXNS}"
  set +e
  vvp sim/tb_apb_uart_txrx_demo_random.vvp +SEED=${seed} +TXNS=${TXNS} +VCD=${VCD} | tee sim/random/random_seed_${seed}.log
  status=${PIPESTATUS[0]}
  set -e
  if [[ ${status} -ne 0 ]]; then
    echo "ERROR: random sim failed seed=${seed} status=${status}" >&2
    exit ${status}
  fi
  cp sim/random/random_results.json sim/random/random_seed_${seed}.json
  cp sim/random/random_scoreboard_events.csv sim/random/random_seed_${seed}.csv
  python3 - "${seed}" <<'PY'
import json, sys
from pathlib import Path
seed=int(sys.argv[1])
data=json.loads(Path('sim/random/random_results.json').read_text())
assert data['seed']==seed, (data, seed)
print(json.dumps(data, separators=(',',':')))
if not data.get('passed') or data.get('scoreboard_fail') != 0:
    sys.exit(10)
PY
  if [[ ${first} -eq 0 ]]; then printf ',' >> "${summary_tmp}"; fi
  first=0
  cat sim/random/random_seed_${seed}.json >> "${summary_tmp}"
done
printf '],"txns":%s,"seed_list":"%s","passed":true,"scoreboard_fail_total":%s}\n' "${TXNS}" "${SEEDS}" "${fail_total}" >> "${summary_tmp}"
mv "${summary_tmp}" sim/random/random_regression_summary.json
python3 -m json.tool sim/random/random_regression_summary.json >/tmp/random_regression_summary_pretty.json
cat sim/random/random_regression_summary.json
