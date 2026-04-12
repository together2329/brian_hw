#!/usr/bin/env bash
# find-mas.sh — locate *_mas.md files for rtl_gen / tb_gen
# Searches both flat layout and IP directory structure:
#   <ip>/mas/<ip>_mas.md   (new structure)
#   <ip>_mas.md            (legacy flat layout)
#
# Usage: find-mas.sh [directory]  (defaults to current directory)

DIR="${1:-.}"

echo "=== MAS Files in: $(realpath "$DIR") ==="
echo ""

# Search new IP structure (<ip>/mas/*_mas.md) first, then flat fallback
MAS_FILES=$(find "$DIR" -maxdepth 4 -name "*_mas.md" 2>/dev/null | sort)

if [ -z "$MAS_FILES" ]; then
    echo "No *_mas.md files found."
    echo ""
    echo "Expected IP structure:"
    echo "  <ip_name>/"
    echo "  ├── mas/<ip_name>_mas.md   ← MAS document"
    echo "  ├── rtl/<ip_name>.sv"
    echo "  ├── list/<ip_name>.f"
    echo "  ├── tb/tb_<ip_name>.sv"
    echo "  ├── sim/sim_report.txt"
    echo "  └── lint/lint_report.txt"
    echo ""
    echo "Tip: Run 'python3 src/main.py -w mas_gen' to generate a MAS document first."
    exit 0
fi

COUNT=0
while IFS= read -r f; do
    COUNT=$((COUNT + 1))
    MODULE=$(basename "$f" "_mas.md")
    CREATED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null || stat -c "%y" "$f" 2>/dev/null | cut -d'.' -f1)
    SIZE=$(wc -l < "$f" | tr -d ' ')

    # Detect layout type
    PARENT_DIR=$(basename "$(dirname "$f")")
    if [ "$PARENT_DIR" = "mas" ]; then
        IP_DIR=$(dirname "$(dirname "$f")")
        IP_NAME=$(basename "$IP_DIR")
        LAYOUT="structured"
        RTL_PATH="$IP_DIR/rtl/${IP_NAME}.sv"
        TB_PATH="$IP_DIR/tb/tb_${IP_NAME}.sv"
        LIST_PATH="$IP_DIR/list/${IP_NAME}.f"
        SIM_PATH="$IP_DIR/sim/"
        LINT_PATH="$IP_DIR/lint/"
    else
        LAYOUT="flat"
        RTL_PATH="$(dirname "$f")/${MODULE}.sv"
        TB_PATH="$(dirname "$f")/tb_${MODULE}.sv"
        LIST_PATH=""
        SIM_PATH=""
        LINT_PATH=""
    fi

    # Extract module overview from §1 if present
    OVERVIEW=$(grep -A1 "^## 1\. Overview" "$f" 2>/dev/null | tail -1 | head -c 80)

    echo "[$COUNT] $MODULE  ($LAYOUT)"
    echo "    MAS    : $f"
    echo "    Lines  : $SIZE | Modified: $CREATED"
    if [ "$LAYOUT" = "structured" ]; then
        RTL_STATUS=$([ -f "$RTL_PATH" ] && echo "✓" || echo "✗ missing")
        TB_STATUS=$([ -f "$TB_PATH" ] && echo "✓" || echo "✗ missing")
        LIST_STATUS=$([ -f "$LIST_PATH" ] && echo "✓" || echo "✗ missing")
        echo "    RTL    : $RTL_PATH  [$RTL_STATUS]"
        echo "    TB     : $TB_PATH  [$TB_STATUS]"
        echo "    Filelist: $LIST_PATH  [$LIST_STATUS]"
        echo "    Sim    : $SIM_PATH"
        echo "    Lint   : $LINT_PATH"
    else
        echo "    Layout : flat (consider migrating to <ip>/mas/<ip>_mas.md structure)"
    fi
    [ -n "$OVERVIEW" ] && echo "    Overview: $OVERVIEW..."
    echo ""
done <<< "$MAS_FILES"

echo "Total: $COUNT MAS document(s) found."
echo ""
if [ -n "$MODULE_NAME" ]; then
    echo "Active MODULE_NAME: $MODULE_NAME"
    echo "  → MAS: ${MODULE_NAME}/mas/${MODULE_NAME}_mas.md"
    echo "  → RTL: ${MODULE_NAME}/rtl/${MODULE_NAME}.sv"
    echo "  → TB:  ${MODULE_NAME}/tb/tb_${MODULE_NAME}.sv"
else
    echo "To set active module: export MODULE_NAME=<ip_name>"
    echo "  rtl_gen will read: \${MODULE_NAME}/mas/\${MODULE_NAME}_mas.md"
    echo "  rtl_gen will write: \${MODULE_NAME}/rtl/\${MODULE_NAME}.sv"
fi
