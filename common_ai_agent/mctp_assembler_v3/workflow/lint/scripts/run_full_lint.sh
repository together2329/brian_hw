#!/usr/bin/env bash
# =============================================================================
# run_full_lint.sh — Verilator -Wall lint with project-specific waiver file
# =============================================================================
# Usage:
#   run_full_lint.sh <ip> [--root .]
#
# Pipeline:
#   1. Locate <ip>/rtl/<ip>_lint.vlt waiver file (created on first run if absent)
#   2. Run verilator --lint-only -Wall on full filelist
#   3. Exit non-zero if any warning slips through (Stable gate G_LINT_CLEAN)
#
# Waiver philosophy:
#   - Real bugs (WIDTHEXPAND, UNSIGNED, dangling drivers) are NOT waived.
#   - Architectural choices (shared header includes, AXI partial-bus use,
#     intentionally unconnected outputs) ARE waived with rationale comment.
# =============================================================================
set -uo pipefail

IP=""
ROOT="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        -*) echo "[run_full_lint] unknown flag: $1" >&2; exit 2 ;;
        *) IP="$1"; shift ;;
    esac
done
[[ -z "$IP" ]] && { echo "usage: run_full_lint.sh <ip> [--root .]" >&2; exit 2; }
ROOT="$(cd "$ROOT" && pwd)"
IP_DIR="$ROOT/$IP"

WAIVER="$IP_DIR/rtl/${IP}_lint.vlt"
[[ -f "$WAIVER" ]] || { echo "[run_full_lint] missing waiver: $WAIVER" >&2; echo "  See spi/rtl/spi_lint.vlt for template." >&2; exit 1; }

# Filelist or glob
SOURCES=()
if [[ -f "$IP_DIR/list/${IP}.f" ]]; then
    while IFS= read -r line; do
        [[ -z "$line" || "$line" =~ ^# ]] && continue
        SOURCES+=("$IP_DIR/$line")
    done < "$IP_DIR/list/${IP}.f"
else
    while IFS= read -r f; do SOURCES+=("$f"); done < <(ls "$IP_DIR"/rtl/*.sv "$IP_DIR"/rtl/*.v 2>/dev/null)
fi

# Top module from SSOT
TOP="$(python3 - <<PY 2>/dev/null
import yaml; d=yaml.safe_load(open('$IP_DIR/yaml/$IP.ssot.yaml'))
for sm in d.get('sub_modules') or []:
    if isinstance(sm, dict) and sm.get('wiring_only'):
        nm = (sm.get('file') or '').split('/')[-1].replace('.sv','').replace('.v','')
        if nm: print(nm); raise SystemExit
print((d.get('top_module') or {}).get('name') or '$IP')
PY
)"
[[ -z "$TOP" ]] && TOP="${IP}_wrapper"

LINT_DIR="$IP_DIR/lint"
mkdir -p "$LINT_DIR"
LOG="$LINT_DIR/verilator_lint.log"

echo "[run_full_lint] top: $TOP"
echo "[run_full_lint] waiver: $WAIVER"
echo "[run_full_lint] sources: ${#SOURCES[@]}"

if verilator --lint-only -Wall -I"$IP_DIR/rtl" --top-module "$TOP" \
        "$WAIVER" "${SOURCES[@]}" 2>&1 | tee "$LOG"; then
    echo ""
    echo "[run_full_lint] G_LINT_CLEAN: PASS"
    exit 0
else
    NWARN="$(grep -cE '^%(Warning|Error)' "$LOG" || true)"
    echo ""
    echo "[run_full_lint] G_LINT_CLEAN: FAIL — $NWARN warning(s)/error(s)"
    echo "[run_full_lint] log: $LOG"
    exit 1
fi
