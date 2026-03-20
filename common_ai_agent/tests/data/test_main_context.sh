#!/bin/bash
# Test /context command in main.py

cd /Users/brian/Desktop/Project/brian_hw/common_ai_agent

# Create input file
cat > /tmp/brian_test_input.txt << 'EOF'
/context debug
exit
EOF

# Run common_ai_agent with input
python3 src/main.py < /tmp/brian_test_input.txt

# Clean up
rm /tmp/brian_test_input.txt
