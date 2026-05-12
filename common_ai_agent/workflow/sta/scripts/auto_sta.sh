#!/usr/bin/env bash
# auto_sta.sh — End-to-end STA driver. Single entry point for /sta.
# Args: <ip_name>
# Pipeline: handoff gate → SDC → tcl → OpenSTA → parse WNS/TNS → report
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA] usage: auto_sta.sh <ip_name>" >&2; exit 2; fi
if [ ! -d "${IP}" ]; then echo "[STA] no such IP dir: ${IP}" >&2; exit 2; fi

DIR="$(dirname "$0")"
NETLIST="${IP}/syn/out/synth.v"
OUT="${IP}/sta/out"
mkdir -p "${OUT}"

# Handoff gate
if [ ! -s "${NETLIST}" ]; then
  echo "[STA HANDOFF MISSING] ${NETLIST} — run /syn first" >&2; exit 5
fi
if compgen -G "${IP}/rtl/*.sv" >/dev/null || compgen -G "${IP}/rtl/*.v" >/dev/null; then
  NEWEST_RTL=$(ls -t ${IP}/rtl/*.sv ${IP}/rtl/*.v 2>/dev/null | head -1)
  if [ -n "${NEWEST_RTL}" ] && [ "${NEWEST_RTL}" -nt "${NETLIST}" ]; then
    echo "[STA STALE NETLIST] ${NEWEST_RTL} newer than ${NETLIST} — re-run /syn" >&2; exit 6
  fi
fi

# Tool / PDK preflight
if ! command -v sta >/dev/null 2>&1; then
  echo "[STA TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
LIB="${SKY130_LIB:-}"
if [ ! -r "${LIB}" ]; then
  echo "[STA MISSING PDK] \$SKY130_LIB unreadable: ${LIB}" >&2; exit 4
fi
export SKY130_LIB="${LIB}"
echo "[STA] liberty=${SKY130_LIB}"

bash "${DIR}/write_sdc.sh"      "${IP}" || exit $?
bash "${DIR}/write_sta_tcl.sh"  "${IP}" || exit $?
bash "${DIR}/run_opensta.sh"    "${IP}" || exit $?
bash "${DIR}/parse_wns.sh"      "${IP}" || exit $?
bash "${DIR}/write_report.sh"   "${IP}" || exit $?

WNS_JSON="${OUT}/wns.json"
if [ -f "${WNS_JSON}" ]; then
  python3 - "${WNS_JSON}" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
res = "PASS" if d['summary'].get('all_setup_met') and d['summary'].get('all_hold_met') else \
      ("HOLD FAIL" if not d['summary'].get('all_hold_met') else "SETUP FAIL")
clocks = ", ".join(f"{c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']:.3f} hold_wns={c['hold_wns_ns']:.3f}" for c in d.get('clocks', []))
print(f"[STA RESULT] {res} — {clocks}")
PY
fi
