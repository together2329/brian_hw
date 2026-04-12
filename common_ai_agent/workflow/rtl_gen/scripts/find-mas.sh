#!/usr/bin/env bash
# find-mas.sh — locate *_mas.md files for rtl_gen
# Usage: find-mas.sh [directory]  (defaults to current directory)

DIR="${1:-.}"

echo "=== MAS Files in: $(realpath "$DIR") ==="
echo ""

MAS_FILES=$(find "$DIR" -maxdepth 3 -name "*_mas.md" 2>/dev/null | sort)

if [ -z "$MAS_FILES" ]; then
    echo "No *_mas.md files found."
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

    # Extract module overview from §1 if present
    OVERVIEW=$(grep -A1 "^## 1\. Overview" "$f" 2>/dev/null | tail -1 | head -c 80)

    echo "[$COUNT] $MODULE"
    echo "    File   : $f"
    echo "    Lines  : $SIZE | Modified: $CREATED"
    [ -n "$OVERVIEW" ] && echo "    Overview: $OVERVIEW..."
    echo ""
done <<< "$MAS_FILES"

echo "Total: $COUNT MAS document(s) found."
echo ""
if [ -n "$MODULE_NAME" ]; then
    echo "Active MODULE_NAME: $MODULE_NAME"
else
    echo "To set active module: export MODULE_NAME=<module_name>"
    echo "Then rtl_gen will automatically read \${MODULE_NAME}_mas.md"
fi
