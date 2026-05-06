#!/usr/bin/env bash
# auto_sta_post.sh — End-to-end sign-off STA driver.
# Args: <ip>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: auto_sta_post.sh <ip>" >&2; exit 2; fi
if [ ! -d "${IP}" ]; then echo "[STA-POST] no such IP dir: ${IP}" >&2; exit 2; fi

DIR="$(dirname "$0")"
ROUTED_V="${IP}/pnr/out/routed.v"
ROUTED_SPEF="${IP}/pnr/out/routed.spef"
ROUTED_DEF="${IP}/pnr/out/routed.def"
CTS_V="${IP}/pnr/out/cts.v"
SDC="${IP}/sta/out/${IP}.sdc"
OUT="${IP}/sta-post/out"
mkdir -p "${OUT}"

# Handoff gates
if [ ! -s "${ROUTED_V}" ]; then
  echo "[STA-POST HANDOFF MISSING] ${ROUTED_V} — run /pnr-route first" >&2; exit 5
fi
if [ ! -s "${ROUTED_SPEF}" ]; then
  echo "[STA-POST SPEF MISSING] ${ROUTED_SPEF} — re-run /pnr-route to extract parasitics" >&2; exit 5
fi
if [ ! -f "${SDC}" ]; then
  echo "[STA-POST SDC MISSING] ${SDC} — run /sta-sdc first" >&2; exit 5
fi
if [ -f "${CTS_V}" ] && [ "${CTS_V}" -nt "${ROUTED_V}" ]; then
  echo "[STA-POST STALE NETLIST] ${CTS_V} newer than ${ROUTED_V}" >&2; exit 6
fi
if [ -f "${ROUTED_DEF}" ] && [ "${ROUTED_DEF}" -nt "${ROUTED_SPEF}" ]; then
  echo "[STA-POST STALE SPEF] ${ROUTED_DEF} newer than ${ROUTED_SPEF}" >&2; exit 6
fi

if ! command -v sta >/dev/null 2>&1; then
  echo "[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
LIB="${SKY130_LIB:-pdk/sky130/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib}"
if [ ! -r "${LIB}" ]; then
  echo "[STA-POST MISSING PDK] \$SKY130_LIB unreadable: ${LIB}" >&2; exit 4
fi
export SKY130_LIB="${LIB}"

bash "${DIR}/write_sta_post_tcl.sh" "${IP}" || exit $?
bash "${DIR}/run_sta_post.sh"       "${IP}" || exit $?
bash "${DIR}/parse_wns.sh"          "${IP}" || exit $?
bash "${DIR}/write_report.sh"       "${IP}" || exit $?

if [ -f "${OUT}/wns.json" ]; then
  python3 - "${OUT}/wns.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
res = "PASS" if d['summary'].get('all_setup_met') and d['summary'].get('all_hold_met') else \
      ("HOLD FAIL" if not d['summary'].get('all_hold_met') else "SETUP FAIL")
clocks = ", ".join(f"{c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']} hold_wns={c['hold_wns_ns']}"
                   for c in d.get('clocks', []))
print(f"[STA-POST RESULT] {res} (sign-off, parasitic-aware) — {clocks}")
PY
fi
