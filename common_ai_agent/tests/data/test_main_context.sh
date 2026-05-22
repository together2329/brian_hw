#!/bin/bash
# Test /context command in main.py

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$SCRIPT_DIR"

# Create input file
INPUT_FILE="$(mktemp /tmp/common_ai_agent_context.XXXXXX)"
cat > "$INPUT_FILE" << 'EOF'
/context debug
exit
EOF

# Run common_ai_agent with input
python3 src/main.py < "$INPUT_FILE"

# Clean up
rm "$INPUT_FILE"
