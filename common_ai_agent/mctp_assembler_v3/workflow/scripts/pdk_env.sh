#!/usr/bin/env bash
# Resolve bundled PDK paths relative to common_ai_agent/, independent of cwd.

_pdk_env_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

_pdk_env_abs() {
  case "${1:-}" in
    "") return 1 ;;
    /*) printf '%s\n' "$1" ;;
    *) printf '%s\n' "${_pdk_env_root}/$1" ;;
  esac
}

_pdk_env_load_dotenv() {
  local _pdk_env_file="${1:-}"
  [ -f "${_pdk_env_file}" ] || return 0
  local _pdk_env_line _pdk_env_key _pdk_env_val
  while IFS= read -r _pdk_env_line || [ -n "${_pdk_env_line}" ]; do
    _pdk_env_line="${_pdk_env_line#"${_pdk_env_line%%[![:space:]]*}"}"
    case "${_pdk_env_line}" in
      ""|\#*) continue ;;
      export\ *) _pdk_env_line="${_pdk_env_line#export }" ;;
    esac
    _pdk_env_key="${_pdk_env_line%%=*}"
    _pdk_env_val="${_pdk_env_line#*=}"
    _pdk_env_key="$(printf '%s' "${_pdk_env_key}" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//')"
    case "${_pdk_env_key}" in
      PDK_ROOT|SKY130_PDK_ROOT|PDK_LIB_PATH|SKY130_LIB|SKY130_TLEF|SKY130_LEF|SKY130_TRACKS|SKY130_RCX_RULES) ;;
      *) continue ;;
    esac
    [ -z "${!_pdk_env_key:-}" ] || continue
    _pdk_env_val="$(printf '%s' "${_pdk_env_val}" | sed 's/[[:space:]]#.*$//; s/^[[:space:]]*//; s/[[:space:]]*$//')"
    _pdk_env_val="${_pdk_env_val%\"}"; _pdk_env_val="${_pdk_env_val#\"}"
    _pdk_env_val="${_pdk_env_val%\'}"; _pdk_env_val="${_pdk_env_val#\'}"
    printf -v "${_pdk_env_key}" '%s' "${_pdk_env_val}"
  done < "${_pdk_env_file}"
}

_pdk_env_load_dotenv "${_pdk_env_root}/.env"

if [ -z "${PDK_ROOT:-}" ]; then
  PDK_ROOT="${_pdk_env_root}/pdk"
elif [ "${PDK_ROOT#/}" = "${PDK_ROOT}" ]; then
  PDK_ROOT="$(_pdk_env_abs "${PDK_ROOT}")"
fi

if [ -z "${SKY130_PDK_ROOT:-}" ]; then
  SKY130_PDK_ROOT="${PDK_ROOT}/sky130"
elif [ "${SKY130_PDK_ROOT#/}" = "${SKY130_PDK_ROOT}" ]; then
  SKY130_PDK_ROOT="$(_pdk_env_abs "${SKY130_PDK_ROOT}")"
fi

if [ -z "${PDK_LIB_PATH:-}" ]; then
  PDK_LIB_PATH="${SKY130_PDK_ROOT}/lib"
elif [ "${PDK_LIB_PATH#/}" = "${PDK_LIB_PATH}" ]; then
  PDK_LIB_PATH="$(_pdk_env_abs "${PDK_LIB_PATH}")"
fi

if [ -z "${SKY130_LIB:-}" ]; then
  for _pdk_env_lib in \
    "${PDK_LIB_PATH}/sky130_fd_sc_hd__ss_100C_1v40.lib" \
    "${PDK_LIB_PATH}/sky130_fd_sc_hd__ss_n40C_1v40.lib" \
    "${PDK_LIB_PATH}"/*.lib
  do
    if [ -r "${_pdk_env_lib}" ]; then
      SKY130_LIB="${_pdk_env_lib}"
      break
    fi
  done
elif [ "${SKY130_LIB#/}" = "${SKY130_LIB}" ]; then
  SKY130_LIB="$(_pdk_env_abs "${SKY130_LIB}")"
fi

if [ -z "${SKY130_TLEF:-}" ]; then
  SKY130_TLEF="${SKY130_PDK_ROOT}/lef/sky130_fd_sc_hd.tlef"
elif [ "${SKY130_TLEF#/}" = "${SKY130_TLEF}" ]; then
  SKY130_TLEF="$(_pdk_env_abs "${SKY130_TLEF}")"
fi

if [ -z "${SKY130_LEF:-}" ]; then
  SKY130_LEF="${SKY130_PDK_ROOT}/lef/sky130_fd_sc_hd_merged.lef"
elif [ "${SKY130_LEF#/}" = "${SKY130_LEF}" ]; then
  SKY130_LEF="$(_pdk_env_abs "${SKY130_LEF}")"
fi

if [ -z "${SKY130_TRACKS:-}" ]; then
  SKY130_TRACKS="${SKY130_PDK_ROOT}/make_tracks.tcl"
elif [ "${SKY130_TRACKS#/}" = "${SKY130_TRACKS}" ]; then
  SKY130_TRACKS="$(_pdk_env_abs "${SKY130_TRACKS}")"
fi

if [ -z "${SKY130_RCX_RULES:-}" ]; then
  SKY130_RCX_RULES="${SKY130_PDK_ROOT}/rcx_patterns.rules"
elif [ "${SKY130_RCX_RULES#/}" = "${SKY130_RCX_RULES}" ]; then
  SKY130_RCX_RULES="$(_pdk_env_abs "${SKY130_RCX_RULES}")"
fi

export PDK_ROOT SKY130_PDK_ROOT PDK_LIB_PATH
export SKY130_LIB SKY130_TLEF SKY130_LEF SKY130_TRACKS SKY130_RCX_RULES

unset _pdk_env_root _pdk_env_lib
unset -f _pdk_env_abs _pdk_env_load_dotenv
