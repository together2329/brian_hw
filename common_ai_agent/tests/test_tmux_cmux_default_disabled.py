"""tmux/cmux tools must be OPT-IN (default disabled).

They are POSIX-only surfaces (tmux does not exist on native Windows) and
control side-channels; a default agent toolset must not expose them. cmux was
already gated by CMUX_ENABLE; tmux had the ENABLE_TMUX_TOOLS flag in config but
the registration block in core/tools.py ignored it and registered
unconditionally.

Registration happens at import time of core.tools, so assert via a fresh
subprocess with a controlled environment (no reload tricks).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_PROBE = (
    "import json, sys;"
    "from core import tools;"
    "names = sorted(k for k in tools.AVAILABLE_TOOLS if k.startswith(('tmux_', 'cmux_')));"
    "print(json.dumps(names))"
)


def _registered_tools(extra_env: dict) -> list:
    env = {**os.environ, "PYTHONPATH": f"{REPO}:{REPO / 'src'}"}
    for key in ("TMUX_ENABLE", "CMUX_ENABLE"):
        env.pop(key, None)
    env.update(extra_env)
    proc = subprocess.run(
        [sys.executable, "-c", _PROBE],
        capture_output=True, text=True, cwd=str(REPO), env=env, timeout=120,
    )
    assert proc.returncode == 0, proc.stderr[-500:]
    return json.loads(proc.stdout.strip().splitlines()[-1])


def test_tmux_and_cmux_tools_disabled_by_default():
    names = _registered_tools({})
    assert names == [], f"tmux/cmux must be opt-in, but default registers: {names}"


def test_tmux_tools_register_when_enabled():
    names = _registered_tools({"TMUX_ENABLE": "true"})
    assert any(n.startswith("tmux_") for n in names), names
    assert not any(n.startswith("cmux_") for n in names), names
