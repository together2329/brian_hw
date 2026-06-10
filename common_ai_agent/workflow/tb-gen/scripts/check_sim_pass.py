#!/usr/bin/env python3
"""check_sim_pass.py (tb-gen) — thin delegator to the canonical sim validator.

Single source of truth lives at workflow/sim/scripts/check_sim_pass.py.  This
file re-executes it via sys.executable with ``--variant tb-gen`` so the tb-gen
verdict text is preserved and no validation logic can drift between the two
copies.  CLI, exit code, and environment handling (IP_NAME / TOOL_OUTPUT) are
all owned by the canonical script.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    canonical = repo_root / "workflow" / "sim" / "scripts" / "check_sim_pass.py"
    proc = subprocess.run([sys.executable, str(canonical), "--variant", "tb-gen"])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
