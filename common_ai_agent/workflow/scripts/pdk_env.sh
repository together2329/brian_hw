#!/usr/bin/env bash
# Resolve bundled PDK paths relative to common_ai_agent/, independent of cwd.

_pdk_env_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd -P)"

if [ -z "${PDK_ROOT:-}" ]; then
  PDK_ROOT="${_pdk_env_root}/pdk"
elif [ "${PDK_ROOT#/}" = "${PDK_ROOT}" ]; then
  PDK_ROOT="${_pdk_env_root}/${PDK_ROOT}"
fi

if [ -z "${SKY130_PDK_ROOT:-}" ]; then
  SKY130_PDK_ROOT="${PDK_ROOT}/sky130"
elif [ "${SKY130_PDK_ROOT#/}" = "${SKY130_PDK_ROOT}" ]; then
  SKY130_PDK_ROOT="${_pdk_env_root}/${SKY130_PDK_ROOT}"
fi

if [ -z "${PDK_LIB_PATH:-}" ]; then
  PDK_LIB_PATH="${SKY130_PDK_ROOT}/lib"
elif [ "${PDK_LIB_PATH#/}" = "${PDK_LIB_PATH}" ]; then
  PDK_LIB_PATH="${_pdk_env_root}/${PDK_LIB_PATH}"
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
  SKY130_LIB="${_pdk_env_root}/${SKY130_LIB}"
fi

if [ -z "${SKY130_TLEF:-}" ]; then
  SKY130_TLEF="${SKY130_PDK_ROOT}/lef/sky130_fd_sc_hd.tlef"
elif [ "${SKY130_TLEF#/}" = "${SKY130_TLEF}" ]; then
  SKY130_TLEF="${_pdk_env_root}/${SKY130_TLEF}"
fi

if [ -z "${SKY130_LEF:-}" ]; then
  SKY130_LEF="${SKY130_PDK_ROOT}/lef/sky130_fd_sc_hd_merged.lef"
elif [ "${SKY130_LEF#/}" = "${SKY130_LEF}" ]; then
  SKY130_LEF="${_pdk_env_root}/${SKY130_LEF}"
fi

if [ -z "${SKY130_TRACKS:-}" ]; then
  SKY130_TRACKS="${SKY130_PDK_ROOT}/make_tracks.tcl"
elif [ "${SKY130_TRACKS#/}" = "${SKY130_TRACKS}" ]; then
  SKY130_TRACKS="${_pdk_env_root}/${SKY130_TRACKS}"
fi

if [ -z "${SKY130_RCX_RULES:-}" ]; then
  SKY130_RCX_RULES="${SKY130_PDK_ROOT}/rcx_patterns.rules"
elif [ "${SKY130_RCX_RULES#/}" = "${SKY130_RCX_RULES}" ]; then
  SKY130_RCX_RULES="${_pdk_env_root}/${SKY130_RCX_RULES}"
fi

export PDK_ROOT SKY130_PDK_ROOT PDK_LIB_PATH
export SKY130_LIB SKY130_TLEF SKY130_LEF SKY130_TRACKS SKY130_RCX_RULES

unset _pdk_env_root _pdk_env_lib
