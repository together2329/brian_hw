#!/usr/bin/env bash
# =============================================================================
# run_synth.sh — yosys generic synthesis + area/cell statistics
# =============================================================================
# Usage:
#   run_synth.sh <ip> [--root .] [--liberty <path>]
#
# Generates:
#   <ip>/syn/<ip>.netlist.v   — gate-level netlist
#   <ip>/syn/<ip>.synth.json  — yosys JSON dump
#   <ip>/syn/synth_report.txt — yosys stat output (cell count, area)
#   <ip>/syn/synth.log        — full yosys log
#
# Without --liberty: generic synthesis (yosys built-in cells, no real
# area). Report shows cell counts but area is "generic gate equivalent".
#
# With --liberty <path>: technology-mapped synthesis. Report includes
# real area numbers. Requires sky130 / asap7 / etc. liberty file.
# =============================================================================
set -uo pipefail

IP=""
ROOT="."
LIBERTY=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --root=*) ROOT="${1#*=}"; shift ;;
        --liberty) LIBERTY="$2"; shift 2 ;;
        --liberty=*) LIBERTY="${1#*=}"; shift ;;
        -*) echo "[run_synth] unknown flag: $1" >&2; exit 2 ;;
        *) IP="$1"; shift ;;
    esac
done

[[ -z "$IP" ]] && { echo "usage: run_synth.sh <ip> [--root .] [--liberty file.lib]" >&2; exit 2; }
ROOT="$(cd "$ROOT" && pwd)"
IP_DIR="$ROOT/$IP"
[[ ! -d "$IP_DIR" ]] && { echo "missing IP dir: $IP_DIR" >&2; exit 2; }

SYN_DIR="$IP_DIR/syn"
mkdir -p "$SYN_DIR"

NETLIST="$SYN_DIR/${IP}.netlist.v"
JSON="$SYN_DIR/${IP}.synth.json"
LOG="$SYN_DIR/synth.log"
REPORT="$SYN_DIR/synth_report.txt"

# Collect RTL sources in dep order from filelist if present, else glob.
SOURCES=()
if [[ -f "$IP_DIR/list/${IP}.f" ]]; then
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        # Filelist entries are relative to IP_DIR.
        SOURCES+=("$IP_DIR/$line")
    done < "$IP_DIR/list/${IP}.f"
else
    while IFS= read -r f; do SOURCES+=("$f"); done < <(ls "$IP_DIR"/rtl/*.sv "$IP_DIR"/rtl/*.v 2>/dev/null)
fi

if [[ ${#SOURCES[@]} -eq 0 ]]; then
    echo "[run_synth] no RTL sources found" >&2
    exit 1
fi

# Top module: from SSOT.top_module.name if present, else <ip>_wrapper, else <ip>.
TOP="$(python3 - <<PY 2>/dev/null
import yaml; d=yaml.safe_load(open('$IP_DIR/yaml/$IP.ssot.yaml'))
tm = d.get('top_module') or {}
name = tm.get('name') or '$IP'
# spi_wrapper convention: try wrapper first if it exists in sub_modules
for sm in d.get('sub_modules') or []:
    if isinstance(sm, dict) and sm.get('wiring_only'):
        nm = (sm.get('file') or '').split('/')[-1].replace('.sv', '').replace('.v', '')
        if nm: print(nm); raise SystemExit
print(name)
PY
)"
[[ -z "$TOP" ]] && TOP="${IP}_wrapper"

INC="-I$IP_DIR/rtl"

# Yosys script: generic synth + stat. Optional ABC techmap with liberty.
YOSYS_SCRIPT=$(cat <<EOF
# Auto-generated yosys script from workflow/syn/scripts/run_synth.sh
read_verilog -sv $INC $(printf '"%s" ' "${SOURCES[@]}")
hierarchy -check -top $TOP
proc
flatten
opt -fast
fsm
opt
memory
opt -fast
EOF
)

if [[ -n "$LIBERTY" && -f "$LIBERTY" ]]; then
    YOSYS_SCRIPT+=$'\n'"techmap"
    YOSYS_SCRIPT+=$'\n'"dfflibmap -liberty \"$LIBERTY\""    # map DFFs to liberty cells
    YOSYS_SCRIPT+=$'\n'"abc -liberty \"$LIBERTY\""
    YOSYS_SCRIPT+=$'\n'"clean"
    YOSYS_SCRIPT+=$'\n'"stat -liberty \"$LIBERTY\""
else
    YOSYS_SCRIPT+=$'\n'"techmap; opt"
    YOSYS_SCRIPT+=$'\n'"stat"
fi

# -noattr -noexpr: simpler netlist for downstream STA/PnR tools
YOSYS_SCRIPT+=$'\n'"write_verilog -noattr -noexpr \"$NETLIST\""
YOSYS_SCRIPT+=$'\n'"write_json \"$JSON\""

echo "[run_synth] top=$TOP, sources=${#SOURCES[@]}, liberty=${LIBERTY:-<generic>}"
echo "[run_synth] running yosys..."

if yosys -p "$YOSYS_SCRIPT" 2>&1 | tee "$LOG" | tail -100 > "$REPORT"; then
    echo ""
    echo "[run_synth] === SYNTH STATS ==="
    grep -A 200 "Printing statistics" "$LOG" | head -80
    echo ""
    echo "[run_synth] OK"
    echo "[run_synth]   netlist: $NETLIST"
    echo "[run_synth]   json:    $JSON"
    echo "[run_synth]   log:     $LOG"
    exit 0
else
    echo "[run_synth] yosys failed — see $LOG" >&2
    exit 1
fi
