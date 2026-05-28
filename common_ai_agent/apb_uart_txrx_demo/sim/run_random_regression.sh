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
      sim/random/random_regression_summary.tmp \
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

seed_args=()
for seed in ${SEEDS//,/ }; do
  seed_args+=("${seed}")
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
  python3 - "${seed}" "sim/random/random_seed_${seed}.json" "sim/random/random_seed_${seed}.csv" <<'PY'
import csv
import json
import sys
from pathlib import Path

seed = int(sys.argv[1])
json_path = Path(sys.argv[2])
csv_path = Path(sys.argv[3])
data = json.loads(json_path.read_text())
if data.get('seed') != seed:
    raise SystemExit(f"seed mismatch in {json_path}: got {data.get('seed')} expected {seed}")
rows = list(csv.DictReader(csv_path.open()))
fail_rows = [row for row in rows if row.get('result') != 'PASS']
missing_cov = sorted(k for k, v in data.get('coverage_flags', {}).items() if not v)
print(json.dumps({
    'seed': seed,
    'passed': bool(data.get('passed')),
    'txns': data.get('txns'),
    'scoreboard_pass': int(data.get('scoreboard_pass', 0)),
    'scoreboard_fail': int(data.get('scoreboard_fail', 0)),
    'csv_rows': len(rows),
    'csv_fail_rows': len(fail_rows),
    'coverage_missing': missing_cov,
}, separators=(',', ':')))
PY
done

python3 - "${SEEDS}" "${TXNS}" "${VCD}" "${seed_args[@]}" <<'PY'
import csv
import json
import sys
from pathlib import Path

seed_list = sys.argv[1]
requested_txns = int(sys.argv[2])
vcd_requested = bool(int(sys.argv[3]))
seeds = [int(arg) for arg in sys.argv[4:]]
if not seeds:
    raise SystemExit('no seeds provided')

seed_results = []
artifacts = []
effective_txns_by_seed = {}
coverage_missing_by_seed = {}
scoreboard_pass_total = 0
scoreboard_fail_total = 0
csv_fail_rows_total = 0

for seed in seeds:
    json_path = Path(f'sim/random/random_seed_{seed}.json')
    csv_path = Path(f'sim/random/random_seed_{seed}.csv')
    log_path = Path(f'sim/random/random_seed_{seed}.log')
    data = json.loads(json_path.read_text())
    if data.get('seed') != seed:
        raise SystemExit(f'seed mismatch in {json_path}: got {data.get("seed")} expected {seed}')
    rows = list(csv.DictReader(csv_path.open()))
    fail_rows = [row for row in rows if row.get('result') != 'PASS']
    missing_cov = sorted(k for k, v in data.get('coverage_flags', {}).items() if not v)

    scoreboard_pass_total += int(data.get('scoreboard_pass', 0))
    scoreboard_fail_total += int(data.get('scoreboard_fail', 0))
    csv_fail_rows_total += len(fail_rows)
    effective_txns_by_seed[str(seed)] = int(data.get('txns', 0))
    coverage_missing_by_seed[str(seed)] = missing_cov
    artifacts.append({
        'seed': seed,
        'json': str(json_path),
        'csv': str(csv_path),
        'log': str(log_path),
    })
    seed_results.append(data)

all_coverage_flags_hit = all(not missing for missing in coverage_missing_by_seed.values())
passed = (
    all(bool(data.get('passed')) for data in seed_results)
    and scoreboard_fail_total == 0
    and csv_fail_rows_total == 0
    and all_coverage_flags_hit
)
summary = {
    'passed': passed,
    'seed_list': seed_list,
    'seeds_requested': seeds,
    'txns': requested_txns,
    'requested_txns': requested_txns,
    'effective_txns_by_seed': effective_txns_by_seed,
    'vcd_requested': vcd_requested,
    'scoreboard_pass_total': scoreboard_pass_total,
    'scoreboard_fail_total': scoreboard_fail_total,
    'csv_fail_rows_total': csv_fail_rows_total,
    'all_coverage_flags_hit': all_coverage_flags_hit,
    'coverage_missing_by_seed': coverage_missing_by_seed,
    'artifacts': artifacts,
    'seeds': seed_results,
}
summary_path = Path('sim/random/random_regression_summary.json')
tmp_path = summary_path.with_suffix('.tmp')
tmp_path.write_text(json.dumps(summary, indent=2) + '\n')
tmp_path.replace(summary_path)
print(json.dumps(summary, separators=(',', ':')))
raise SystemExit(0 if passed else 10)
PY