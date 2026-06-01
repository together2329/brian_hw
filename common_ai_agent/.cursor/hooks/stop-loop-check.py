#!/usr/bin/env python3
"""One-pass completion loop reminder based on changed project files."""

import json
import subprocess
import sys


def changed_files():
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    if result.returncode not in (0, 1):
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main():
    try:
        json.load(sys.stdin)
    except Exception:
        pass

    files = changed_files()
    if not files:
        print("{}")
        return

    relevant = [path for path in files if path.startswith("common_ai_agent/")]
    if not relevant:
        print("{}")
        return

    needs_test = any(
        path.endswith((".py", ".js", ".jsx", ".html", ".sv", ".v", ".sh", ".yaml", ".yml"))
        for path in relevant
    )
    generated = any(
        marker in path
        for path in relevant
        for marker in ("/sim/", "/verify/", "/cov/", "/syn/out/", "/sta/out/", "/pnr/out/")
    )

    if generated:
        message = (
            "Before finalizing, confirm any generated evidence changes were regenerated through the owning workflow "
            "and not hand-edited. Cite the command or validator output."
        )
    elif needs_test:
        message = (
            "Before finalizing, make sure the response mentions the relevant fresh check, such as "
            "`./scripts/run_tests.sh smoke`, `./scripts/run_tests.sh frontend`, or the owning workflow validator."
        )
    else:
        print("{}")
        return

    print(json.dumps({"followup_message": message}))


if __name__ == "__main__":
    main()
