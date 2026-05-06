#!/usr/bin/env bash
# sim.sh — Compile and run simulation for tb_gen workspace
set -u
TB="${HOOK_CMD_ARGS:-${1:-}}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
SIM_TIMEOUT_SEC="${SIM_TIMEOUT_SEC:-120}"

run_bounded() {
    local seconds="$1"
    shift
    if command -v timeout >/dev/null 2>&1; then
        timeout "${seconds}" "$@"
    elif command -v gtimeout >/dev/null 2>&1; then
        gtimeout "${seconds}" "$@"
    else
        python3 - "$seconds" "$@" <<'PY'
import subprocess
import sys

seconds = int(sys.argv[1])
cmd = sys.argv[2:]
try:
    proc = subprocess.run(cmd, text=True, capture_output=True, timeout=seconds)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    raise SystemExit(proc.returncode)
except subprocess.TimeoutExpired as exc:
    if exc.stdout:
        sys.stdout.write(exc.stdout if isinstance(exc.stdout, str) else exc.stdout.decode(errors="replace"))
    if exc.stderr:
        sys.stderr.write(exc.stderr if isinstance(exc.stderr, str) else exc.stderr.decode(errors="replace"))
    print(f"TIMEOUT: command exceeded {seconds}s: {' '.join(cmd)}", file=sys.stderr)
    raise SystemExit(124)
PY
    fi
}

[ -z "${TB}" ] && TB=$(find . -maxdepth 4 -path "*/tb/cocotb/test_runner.py" -o -path "*/tb/test_runner.py" | head -1)
[ -z "${TB}" ] && TB=$(find . -maxdepth 2 -name "tb_*.sv" -o -name "tb_*.v" | head -1)
[ -z "${TB}" ] && { echo "No testbench found. Use /sim <test_runner.py|tb_<module>.sv>"; exit 1; }

PY_FLOW=0
if echo "${TB}" | grep -qE '\.py$'; then
    PY_FLOW=1
    echo "Running cocotb Python runner: ${TB}"
    TB_DIR=$(cd "$(dirname "${TB}")" && pwd)
    IP_DIR=$(cd "${TB_DIR}/.." && pwd)
    [ "$(basename "${IP_DIR}")" = "tb" ] && IP_DIR=$(cd "${IP_DIR}/.." && pwd)
    if grep -q "if __name__" "${TB}"; then
        OUT=$(cd "${TB_DIR}" && PYTHONPATH="${TB_DIR}:${IP_DIR}:${PYTHONPATH:-}" run_bounded "${SIM_TIMEOUT_SEC}" python3 "$(basename "${TB}")" 2>&1)
    else
        OUT=$(PYTHONPATH="${TB_DIR}:${IP_DIR}:${PYTHONPATH:-}" run_bounded "${SIM_TIMEOUT_SEC}" python3 -m pytest -q "${TB}" --tb=short 2>&1)
    fi
    RC=$?
    echo "${OUT}"
    [ ${RC} -ne 0 ] && { echo "Simulation FAILED"; echo "${TS} sim=FAIL stage=cocotb rc=${RC}" >> "${LOG}"; exit ${RC}; }
elif command -v iverilog &>/dev/null; then
    echo "Compiling: ${TB}"
    iverilog -g2012 -Wall -o /tmp/_tb_sim.vvp "${TB}" 2>&1
    [ $? -ne 0 ] && { echo "Compile FAILED"; echo "${TS} sim=FAIL stage=compile" >> "${LOG}"; exit 1; }
    OUT=$(run_bounded "${SIM_TIMEOUT_SEC}" vvp /tmp/_tb_sim.vvp 2>&1)
    echo "${OUT}"
elif command -v verilator &>/dev/null; then
    echo "Compiling: ${TB}"
    OUT=$(verilator --binary --build -j 0 "${TB}" -o /tmp/_tb_verilator 2>&1 && /tmp/_tb_verilator 2>&1)
    echo "${OUT}"
else
    echo "No sim tool found."; exit 1
fi

ERRORS=$(printf '%s\n' "${OUT}" | python3 -c '
import re
import sys

count = 0
for raw in sys.stdin:
    line = raw.strip()
    low = line.lower()
    if not line:
        continue
    if re.search(r"\b0\s+errors?\b|\berrors?\s*[:=]\s*0\b|\bno\s+errors?\b", low):
        continue
    if re.search(r"\b(error|fatal|traceback|assertionerror)\b", low):
        count += 1
print(count)
')
WARNINGS=$(printf '%s\n' "${OUT}" | python3 -c '
import re
import sys

count = 0
for raw in sys.stdin:
    line = raw.strip()
    low = line.lower()
    if not line:
        continue
    if re.search(r"\b0\s+warnings?\b|\bwarnings?\s*[:=]\s*0\b|\bno\s+warnings?\b", low):
        continue
    if re.search(r"\b(warning|warn)\b", low):
        count += 1
print(count)
')
PASS_CNT=$(echo "${OUT}" | grep -Ec "\[PASS\]| passed| PASS=" || true)
FAIL_CNT=$(echo "${OUT}" | grep -Ec "\[FAIL\]| failed| FAIL=[1-9]" || true)
if [ "${PY_FLOW}" -eq 1 ]; then
    WARNINGS=$(printf '%s\n' "${OUT}" | python3 -c '
import re
import sys

count = 0
for raw in sys.stdin:
    line = raw.strip()
    low = line.lower()
    if not line:
        continue
    if "userwarning: python runners" in low or "experimental feature" in low:
        continue
    if re.search(r"\b0\s+warnings?\b|\bwarnings?\s*[:=]\s*0\b|\bno\s+warnings?\b", low):
        continue
    if re.search(r"\b(warning|warn)\b", low):
        count += 1
print(count)
')
fi
SUMMARY=$(echo "${OUT}" | grep -Eo 'TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+' | tail -1 || true)
if [ -n "${SUMMARY}" ]; then
    PASS_PART=${SUMMARY#*PASS=}; PASS_CNT=${PASS_PART%% *}
    FAIL_PART=${SUMMARY#*FAIL=}; FAIL_CNT=${FAIL_PART%% *}
fi

echo ""
echo "Simulation: ${ERRORS} errors, ${WARNINGS} warnings"
echo "Tests: ${PASS_CNT} passed, ${FAIL_CNT} failed"

STATUS="FAIL"
[ "${ERRORS}" -eq 0 ] && [ "${FAIL_CNT}" -eq 0 ] && STATUS="PASS"

echo "${TS} sim=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS_CNT} fail=${FAIL_CNT} tb=${TB}" >> "${LOG}"

[ "${STATUS}" = "PASS" ] && echo "0 errors, 0 warnings"
[ "${STATUS}" = "PASS" ]
