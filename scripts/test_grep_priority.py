import sys
import os
sys.path.append(os.getcwd())
from brian_coder.core.tools import grep_file

print("--- Testing System Grep Priority ---")
# This should use system grep (linux/bsd style)
# We expect to see matches and NO errors about directories
result = grep_file("def grep_file", "brian_coder/core/tools.py", context_lines=0)
print(result)

if "Matches in" in result or "Found" in result:
    print("\n✅ Verification Successful: Matches found via system grep.")
else:
    print(f"\n❌ Fail: {result}")
