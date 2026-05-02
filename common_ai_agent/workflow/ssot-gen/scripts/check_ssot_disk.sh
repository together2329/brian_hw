#!/usr/bin/env bash
# check_ssot_disk.sh — Disk-truth validator for ssot-gen tasks.
#
# Verifies the SSOT YAML actually exists on disk with all required
# top-level sections. Replaces "trust the LLM's reason text" approval
# with concrete file inspection.
#
# Inputs (env):
#   IP_NAME — IP slug (auto-detected from cwd if missing)
#   MIN_YAML — minimum bytes for <ip>.ssot.yaml (default 4000)
#   MIN_SECTIONS — minimum top-level section count (default 18)
#
# Exit 0 = real SSOT YAML exists, has section keys, parses as YAML.
# Exit 1 = file missing / too small / sections missing / not valid YAML.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
[ -z "$IP" ] || [ ! -d "$IP" ] && { echo "[check_ssot_disk] FAIL: IP dir not found"; exit 1; }

# Locate the SSOT YAML (two naming conventions exist in the codebase).
YAML=""
for cand in "$IP/yaml/$IP.ssot.yaml" "$IP/yaml/${IP}_ssot.yaml" "$IP/yaml/$IP.ssot.yml"; do
    [ -f "$cand" ] && { YAML="$cand"; break; }
done
[ -z "$YAML" ] && { echo "[check_ssot_disk] FAIL: no SSOT YAML at $IP/yaml/${IP}.ssot.yaml or _ssot.yaml"; exit 1; }

MIN_YAML="${MIN_YAML:-4000}"
MIN_SECTIONS="${MIN_SECTIONS:-18}"

SZ=$(wc -c < "$YAML" | tr -d ' ')
[ "$SZ" -lt "$MIN_YAML" ] && { echo "[check_ssot_disk] FAIL: $YAML = ${SZ}B (need ≥${MIN_YAML})"; exit 1; }

# Required canonical 20-section keys (spelling matches ssot-template.yaml).
REQUIRED='top_module|sub_modules|parameters|io_list|features|dataflow|clock_reset_domains|cdc_requirements|rdc_requirements|registers|memory|interrupts|fsm|coding_rules|reuse_modules|custom|dir_structure|filelist|test_requirements|traceability|generation_flow'
HITS=$(grep -cE "^($REQUIRED):" "$YAML" || echo 0)
if [ "$HITS" -lt "$MIN_SECTIONS" ]; then
    echo "[check_ssot_disk] FAIL: $YAML only has $HITS top-level section keys (need ≥$MIN_SECTIONS)"
    exit 1
fi

# YAML parseability via python.
if command -v python3 >/dev/null 2>&1; then
    python3 -c "import yaml,sys; yaml.safe_load(open('$YAML'))" 2>/tmp/_ssot_yaml.err \
        || { echo "[check_ssot_disk] FAIL: $YAML does not parse as YAML"; cat /tmp/_ssot_yaml.err | head -5 | sed 's/^/  /'; exit 1; }
fi

# No live <TBD> markers in non-comment lines (template placeholders).
TBD_COUNT=$(grep -vE '^\s*#' "$YAML" | grep -cE '<TBD>|<placeholder>|TODO: confirm' | head -1 | tr -d '[:space:]')
TBD_COUNT="${TBD_COUNT:-0}"
if [ "$TBD_COUNT" -gt 5 ]; then
    echo "[check_ssot_disk] FAIL: $YAML has $TBD_COUNT live TBD markers (limit 5 — resolve via /grill-me)"
    exit 1
fi

echo "[check_ssot_disk] PASS: $YAML = ${SZ}B, ${HITS} sections, ${TBD_COUNT} TBDs"
exit 0
