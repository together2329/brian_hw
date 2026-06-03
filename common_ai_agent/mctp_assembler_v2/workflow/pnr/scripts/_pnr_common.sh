#!/usr/bin/env bash
# _pnr_common.sh — Sourced by every PnR stage script. Tool/PDK/handoff helpers.
set -uo pipefail

PDK_ENV="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

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
  local tlef="${SKY130_TLEF:-}"
  local lef="${SKY130_LEF:-}"
  local lib="${SKY130_LIB:-}"
  local tracks="${SKY130_TRACKS:-}"
  local rcx="${SKY130_RCX_RULES:-}"
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

pnr_layer_direction () {
  local layer="$1"
  awk -v want="${layer}" '
    toupper($1) == "LAYER" && $2 == want { in_layer = 1; next }
    in_layer && toupper($1) == "DIRECTION" {
      gsub(/;/, "", $2)
      print tolower($2)
      exit
    }
    in_layer && toupper($1) == "END" { in_layer = 0 }
  ' "${SKY130_TLEF:-}"
}

pnr_check_io_layers () {
  local hor="$1" ver="$2"
  local hor_dir ver_dir
  hor_dir="$(pnr_layer_direction "${hor}")"
  ver_dir="$(pnr_layer_direction "${ver}")"
  if [ "${hor_dir}" != "horizontal" ]; then
    echo "[PNR IO LAYER ERROR] horizontal layer ${hor} has direction ${hor_dir:-unknown}; use a horizontal routing layer such as met3" >&2
    return 8
  fi
  if [ "${ver_dir}" != "vertical" ]; then
    echo "[PNR IO LAYER ERROR] vertical layer ${ver} has direction ${ver_dir:-unknown}; use a vertical routing layer such as met2" >&2
    return 8
  fi
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
    echo "[PNR REBUILD ${label}] ${upstream} newer than ${output} — regenerating ${output}" >&2
    rm -f "${output}"
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
    import yaml; d = yaml.safe_load(pathlib.Path(ssot).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
_t = d.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
print(_t or d.get("top") or ip)
PY
}
