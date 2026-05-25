#!/usr/bin/env bash
set -euo pipefail

# Reproducible constrained-random RTL simulation harness for real_llm_counter_demo.
# Verification-only: compiles DUT filelist plus sim/tb_real_llm_counter_demo_random.sv.
# Environment knobs:
#   SEEDS="1 2 3"                 space-separated seeds, default: 1 2 3 4 5
#   TXNS=512                       random accepted transactions per seed
#   MAX_GAP=3                      max idle cycles between transactions
#   RESET_PROB_PER_MILLE=10        per-transaction mid-test reset probability, 0..1000
#   DUMP_RANDOM_VCD=1              enable VCD dump for each seed

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${IP_DIR}"

mkdir -p sim/build sim/random

IVERILOG_BIN="${IVERILOG_BIN:-iverilog}"
VVP_BIN="${VVP_BIN:-vvp}"
SEEDS="${SEEDS:-1 2 3 4 5}"
TXNS="${TXNS:-512}"
MAX_GAP="${MAX_GAP:-3}"
RESET_PROB_PER_MILLE="${RESET_PROB_PER_MILLE:-10}"

COMPILE_CMD=("${IVERILOG_BIN}" -g2012 -Irtl -s tb_real_llm_counter_demo_random -o sim/build/tb_real_llm_counter_demo_random.vvp -f list/real_llm_counter_demo.f sim/tb_real_llm_counter_demo_random.sv)

summary_path="sim/random/random_regression_summary.json"
summary_tmp="${summary_path}.tmp"
: > "${summary_tmp}"

{
  echo "[run_random] ip_dir=${IP_DIR}"
  echo "[run_random] compile: ${COMPILE_CMD[*]}"
  "${COMPILE_CMD[@]}"
  echo "[run_random] seeds=${SEEDS} txns=${TXNS} max_gap=${MAX_GAP} reset_prob_per_mille=${RESET_PROB_PER_MILLE}"
} 2>&1 | tee sim/random/random_compile.log

printf '{\n' >> "${summary_tmp}"
printf '  "schema_version": 1,\n' >> "${summary_tmp}"
printf '  "ip": "real_llm_counter_demo",\n' >> "${summary_tmp}"
printf '  "type": "constrained_random_regression_summary",\n' >> "${summary_tmp}"
printf '  "compile_log": "sim/random/random_compile.log",\n' >> "${summary_tmp}"
printf '  "txns_per_seed": %s,\n' "${TXNS}" >> "${summary_tmp}"
printf '  "max_gap": %s,\n' "${MAX_GAP}" >> "${summary_tmp}"
printf '  "reset_prob_per_mille": %s,\n' "${RESET_PROB_PER_MILLE}" >> "${summary_tmp}"
printf '  "seeds": [\n' >> "${summary_tmp}"

seed_index=0
total_pass=0
total_fail=0
seed_count=0

for seed in ${SEEDS}; do
  seed_count=$((seed_count + 1))
  seed_log="sim/random/random_seed_${seed}.log"
  seed_json="sim/random/random_seed_${seed}_results.json"
  seed_csv="sim/random/random_seed_${seed}_scoreboard_events.csv"
  seed_vcd="sim/random/random_seed_${seed}.vcd"

  # Remove stale per-seed/current artifacts so disabled VCD or failed runs cannot
  # accidentally be reported from an older seed.
  rm -f "${seed_log}" "${seed_json}" "${seed_csv}" "${seed_vcd}" \
        sim/random/current_random_results.json \
        sim/random/current_scoreboard_events.csv \
        sim/random/current_random.vcd

  run_cmd=("${VVP_BIN}" sim/build/tb_real_llm_counter_demo_random.vvp +SEED="${seed}" +TXNS="${TXNS}" +MAX_GAP="${MAX_GAP}" +RESET_PROB_PER_MILLE="${RESET_PROB_PER_MILLE}")
  if [[ "${DUMP_RANDOM_VCD:-0}" == "1" ]]; then
    run_cmd+=(+DUMP_RANDOM_VCD)
  fi

  echo "[run_random] run seed=${seed}: ${run_cmd[*]}" | tee "${seed_log}"
  "${run_cmd[@]}" 2>&1 | tee -a "${seed_log}"

  cp sim/random/current_random_results.json "${seed_json}"
  cp sim/random/current_scoreboard_events.csv "${seed_csv}"
  if [[ -f sim/random/current_random.vcd ]]; then
    cp sim/random/current_random.vcd "${seed_vcd}"
  fi

  seed_pass=$(python3 - <<PY
import json
with open('${seed_json}') as f:
    d=json.load(f)
print(d['scoreboard_pass'])
PY
)
  seed_fail=$(python3 - <<PY
import json
with open('${seed_json}') as f:
    d=json.load(f)
print(d['scoreboard_fail'])
PY
)
  seed_passed=$(python3 - <<PY
import json
with open('${seed_json}') as f:
    d=json.load(f)
print('true' if d['passed'] else 'false')
PY
)
  seed_accepted=$(python3 - <<PY
import json
with open('${seed_json}') as f:
    d=json.load(f)
print(d['accepted_txns'])
PY
)

  total_pass=$((total_pass + seed_pass))
  total_fail=$((total_fail + seed_fail))

  if [[ ${seed_index} -gt 0 ]]; then
    printf ',\n' >> "${summary_tmp}"
  fi
  printf '    {"seed": %s, "passed": %s, "scoreboard_pass": %s, "scoreboard_fail": %s, "accepted_txns": %s, "log": "%s", "results": "%s", "scoreboard_csv": "%s"}' \
    "${seed}" "${seed_passed}" "${seed_pass}" "${seed_fail}" "${seed_accepted}" "${seed_log}" "${seed_json}" "${seed_csv}" >> "${summary_tmp}"
  seed_index=$((seed_index + 1))
done

printf '\n  ],\n' >> "${summary_tmp}"
printf '  "seed_count": %s,\n' "${seed_count}" >> "${summary_tmp}"
printf '  "total_scoreboard_pass": %s,\n' "${total_pass}" >> "${summary_tmp}"
printf '  "total_scoreboard_fail": %s,\n' "${total_fail}" >> "${summary_tmp}"
if [[ "${total_fail}" == "0" ]]; then
  printf '  "passed": true\n' >> "${summary_tmp}"
else
  printf '  "passed": false\n' >> "${summary_tmp}"
fi
printf '}\n' >> "${summary_tmp}"
mv "${summary_tmp}" "${summary_path}"

echo "[run_random] summary=${summary_path} total_scoreboard_pass=${total_pass} total_scoreboard_fail=${total_fail}"
[[ "${total_fail}" == "0" ]]
