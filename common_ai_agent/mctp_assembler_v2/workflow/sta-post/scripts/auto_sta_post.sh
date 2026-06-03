#!/usr/bin/env bash
# auto_sta_post.sh — End-to-end sign-off STA driver.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: auto_sta_post.sh <ip>" >&2; exit 2; fi
if [ ! -d "${IP}" ]; then echo "[STA-POST] no such IP dir: ${IP}" >&2; exit 2; fi

DIR="$(dirname "$0")"
OUT="${IP}/sta-post/out"
mkdir -p "${OUT}"

bash "${DIR}/preflight.sh"          "${IP}" || exit $?
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
