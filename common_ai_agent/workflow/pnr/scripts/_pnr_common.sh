#!/usr/bin/env bash
# _pnr_common.sh — Sourced by every PnR stage script. Tool/PDK/handoff helpers.
set -uo pipefail

pnr_resolve_input_netlist () {
  local ip="$1"
  if [ -s "${ip}/dft/out/scan.v" ]; then echo "${ip}/dft/out/scan.v"; return 0; fi
  if [ -s "${ip}/syn/out/synth.v" ]; then echo "${ip}/syn/out/synth.v"; return 0; fi
  echo ""; return 1
}

pnr_check_tools () {
  if ! command -v openroad >/dev/null 2>&1; then
    echo "[PNR TOOL MISSING] openroad not on PATH" >&2; return 3
  fi
  local tlef="${SKY130_TLEF:-pdk/sky130/lef/sky130_fd_sc_hd.tlef}"
  local lef="${SKY130_LEF:-pdk/sky130/lef/sky130_fd_sc_hd_merged.lef}"
  local lib="${SKY130_LIB:-pdk/sky130/lib/sky130_fd_sc_hd__ss_n40C_1v40.lib}"
  local tracks="${SKY130_TRACKS:-pdk/sky130/make_tracks.tcl}"
  local rcx="${SKY130_RCX_RULES:-pdk/sky130/rcx_patterns.rules}"
  if [ ! -r "${tlef}" ] || [ ! -r "${lef}" ]; then
    echo "[PNR MISSING LEF] tlef=${tlef} lef=${lef}" >&2; return 4
  fi
  if [ ! -r "${lib}" ]; then
    echo "[PNR MISSING PDK] \$SKY130_LIB unreadable: ${lib}" >&2; return 4
  fi
  if [ ! -r "${tracks}" ]; then
    echo "[PNR MISSING TRACKS] \$SKY130_TRACKS unreadable: ${tracks}" >&2; return 4
  fi
  if [ ! -r "${rcx}" ]; then
    echo "[PNR MISSING RCX] \$SKY130_RCX_RULES unreadable: ${rcx}" >&2; return 4
  fi
  export SKY130_TLEF="${tlef}" SKY130_LEF="${lef}" SKY130_LIB="${lib}"
  export SKY130_TRACKS="${tracks}" SKY130_RCX_RULES="${rcx}"
  return 0
}

pnr_check_handoff () {
  local ip="$1"
  local netlist; netlist=$(pnr_resolve_input_netlist "${ip}")
  if [ -z "${netlist}" ]; then
    echo "[PNR HANDOFF MISSING] no scan.v or synth.v — run /syn (and optionally /dft) first" >&2
    return 5
  fi
  local sdc="${ip}/sta/out/${ip}.sdc"
  if [ ! -f "${sdc}" ]; then
    echo "[PNR SDC MISSING] ${sdc} — run /sta-sdc first" >&2; return 5
  fi
  echo "${netlist}"
  return 0
}

pnr_check_stale () {
  local label="$1" upstream="$2" output="$3"
  if [ ! -s "${upstream}" ]; then
    echo "[PNR STALE ${label}] upstream missing: ${upstream}" >&2; return 6
  fi
  if [ -f "${output}" ] && [ "${upstream}" -nt "${output}" ]; then
    echo "[PNR STALE ${label}] ${upstream} newer than ${output} — re-run prior stage" >&2; return 6
  fi
  return 0
}

pnr_top_from_ssot () {
  local ip="$1"
  local ssot="${ip}/yaml/${ip}.ssot.yaml"
  python3 - "${ssot}" "${ip}" <<'PY'
import sys, pathlib
ssot, ip = sys.argv[1:3]
try:
    import yaml; d = yaml.safe_load(pathlib.Path(ssot).read_text()) or {}
except Exception: d = {}
_t = d.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
print(_t or d.get("top") or ip)
PY
}
