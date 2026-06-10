#!/usr/bin/env python3
"""check_lint_pass.py — Validator for lint stage.

Python port of check_lint_pass.sh for native-Windows portability. Returns 0 if
lint passed (0 errors), 1 otherwise. Used as validator in converge loop criteria
checks.

Reads the tool output from the TOOL_OUTPUT environment variable (matching the
shell original) and greps it for the lint verdict.
"""

from __future__ import annotations

import os
import re
import sys


def main() -> int:
    output = os.environ.get("TOOL_OUTPUT", "")

    # `grep -qi "0 error"` — case-insensitive substring match.
    if re.search(r"0 error", output, re.IGNORECASE):
        print("Lint PASS: 0 errors")
        return 0

    # `grep -oiP '\d+(?= error)' | head -1` — first count preceding " error".
    err_match = re.search(r"\d+(?= error)", output, re.IGNORECASE)
    warn_match = re.search(r"\d+(?= warning)", output, re.IGNORECASE)
    errors = err_match.group(0) if err_match else "?"
    warnings = warn_match.group(0) if warn_match else "?"
    print(f"Lint FAIL: {errors} errors, {warnings} warnings")
    return 1


if __name__ == "__main__":
    sys.exit(main())
