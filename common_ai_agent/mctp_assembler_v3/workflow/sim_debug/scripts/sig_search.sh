#!/usr/bin/env bash
QUERY="${HOOK_CMD_ARGS:-$1}"
[ -z "${QUERY}" ] && { echo "Usage: /sig <name>"; exit 1; }
echo "=== Search: '${QUERY}' across VCDs ==="
HITS=0
while IFS= read -r vcd; do
    matches=$(grep -i "\$var.*${QUERY}" "${vcd}" 2>/dev/null | head -10)
    if [ -n "${matches}" ]; then
        echo ""
        echo "  ${vcd}:"
        echo "${matches}" | sed 's/^/    /'
        HITS=$((HITS+1))
    fi
done < <(find . -maxdepth 4 -name "*.vcd" 2>/dev/null)
[ $HITS -eq 0 ] && echo "(no matches in any VCD)"
