#!/usr/bin/env bash
# preflight.sh — Diagnose synthesis tool/PDK/IP inputs before running yosys.
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # IP names do not contain spaces; slash-command args are split here so
  # /syn-preflight <ip> works even when the command loader only sets env.
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"
DIR="$(cd "$(dirname "$0")" && pwd -P)"
PDK_ENV="$(cd "${DIR}/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

STATUS=0

_syn_check_file() {
  local label="$1" path="$2"
  if [ -r "${path}" ]; then
    echo "[SYN PREFLIGHT] ${label}: OK ${path}"
  else
    echo "[SYN PREFLIGHT] ${label}: MISSING ${path}" >&2
    STATUS=4
  fi
}

_syn_check_tool() {
  local tool="$1" required="$2" found
  found="$(command -v "${tool}" 2>/dev/null || true)"
  if [ -n "${found}" ]; then
    echo "[SYN PREFLIGHT] tool ${tool}: OK ${found}"
  elif [ "${required}" = "required" ]; then
    echo "[SYN TOOL MISSING] ${tool} not on PATH" >&2
    STATUS=3
  else
    echo "[SYN PREFLIGHT] tool ${tool}: not found (optional here)"
  fi
}

echo "[SYN PREFLIGHT] cwd=$(pwd -P)"
echo "[SYN PREFLIGHT] scripts=${DIR}"
echo "[SYN PREFLIGHT] PDK_ROOT=${PDK_ROOT:-}"
echo "[SYN PREFLIGHT] SKY130_PDK_ROOT=${SKY130_PDK_ROOT:-}"
echo "[SYN PREFLIGHT] PDK_LIB_PATH=${PDK_LIB_PATH:-}"

_syn_check_tool yosys required
_syn_check_tool sta optional
_syn_check_tool openroad optional

_syn_check_file "SKY130_LIB" "${SKY130_LIB:-}"
_syn_check_file "SKY130_TLEF" "${SKY130_TLEF:-}"
_syn_check_file "SKY130_LEF" "${SKY130_LEF:-}"
_syn_check_file "SKY130_TRACKS" "${SKY130_TRACKS:-}"

if [ -n "${IP}" ]; then
  if [ ! -d "${IP}" ]; then
    echo "[SYN PREFLIGHT] IP dir: MISSING ${IP}" >&2
    STATUS=2
  else
    echo "[SYN PREFLIGHT] IP dir: OK ${IP}"
    python3 - "${IP}" <<'PY' || STATUS=$?
import pathlib
import sys

ip = pathlib.Path(sys.argv[1])
ssot = ip / "yaml" / f"{ip.name}.ssot.yaml"
flist = ip / "list" / f"{ip.name}.f"
status = 0

def report(ok: bool, label: str, path: pathlib.Path) -> None:
    global status
    if ok:
        print(f"[SYN PREFLIGHT] {label}: OK {path}")
    else:
        print(f"[SYN PREFLIGHT] {label}: MISSING {path}", file=sys.stderr)
        status = 2

report(ssot.is_file(), "SSOT", ssot)
report(flist.is_file(), "filelist", flist)

if flist.is_file():
    missing = []
    entries = []
    for raw in flist.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("//", 1)[0].split("#", 1)[0].strip()
        if not line or line.startswith(("+", "-")):
            continue
        if not line.endswith((".v", ".sv", ".vh", ".svh")):
            continue
        p = pathlib.Path(line)
        candidates = [p] if p.is_absolute() else [ip / p, pathlib.Path.cwd() / p]
        hit = next((c for c in candidates if c.is_file()), None)
        if hit is None:
            missing.append(line)
        else:
            entries.append(hit)
    print(f"[SYN PREFLIGHT] filelist RTL entries: {len(entries)}")
    if missing:
        print("[SYN PREFLIGHT] missing RTL entries:", file=sys.stderr)
        for item in missing[:20]:
            print(f"  - {item}", file=sys.stderr)
        status = 2
    elif not entries:
        print("[SYN PREFLIGHT] filelist has no RTL entries", file=sys.stderr)
        status = 2

raise SystemExit(status)
PY
  fi
else
  echo "[SYN PREFLIGHT] IP dir: skipped (pass <ip> to check SSOT/filelist/RTL)"
fi

if [ "${STATUS}" -eq 0 ]; then
  echo "[SYN PREFLIGHT] OK"
else
  echo "[SYN PREFLIGHT] FAILED rc=${STATUS}" >&2
fi
exit "${STATUS}"
