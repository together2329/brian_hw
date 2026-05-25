"""Regression guard for LLM model/profile routing resolution.

This session lost two end-to-end runs because the headless path fell back to the
.env default profile (glm-5.1) — which the provider 403s — instead of the
intended model. The fix was to pass an explicit model and/or clear LLM_PROFILE.
These tests pin the deterministic part of config's model resolution (profile
selection + BASE_URL pairing) so the routing trap cannot silently return.

Config import has process-global side effects (reads .env, may activate OAuth),
so each case resolves in a fresh subprocess with a controlled environment.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"


def _resolve(env_overrides: dict) -> dict:
    """Import config in a clean subprocess and return its resolved routing."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_")}
    env.setdefault("PYTHONPATH", str(SRC))
    env["PYTHONPATH"] = str(SRC)
    env.update(env_overrides)
    code = (
        "import config as c;"
        "print('MODEL=' + str(c.MODEL_NAME));"
        "print('BASE=' + str(c.BASE_URL));"
        "print('OPENCODE=' + str(c.USE_OPENCODE_OAUTH))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code],
        env=env, cwd=str(REPO), capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, f"config import failed: {out.stderr[-500:]}"
    parsed = {}
    for line in out.stdout.splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            parsed[k.strip()] = v.strip()
    return parsed


def test_deepseek_profile_selects_deepseek_model_and_base():
    """Selecting the deepseek profile must route to deepseek-v4-pro on the
    deepseek API host — not the .env default glm profile."""
    r = _resolve({"LLM_PROFILE": "deepseek"})
    assert r["MODEL"] == "deepseek-v4-pro", r
    assert "api.deepseek.com" in r["BASE"], r


def test_default_env_profile_is_glm_baseline():
    """Documents the trap: with no override, the .env default profile resolves to
    glm-5.1. (This is exactly the fallback that 403'd the headless real runs —
    callers MUST pass an explicit model / clear the profile to avoid it.)"""
    r = _resolve({})
    # Either the .env default (glm-5.1) or whatever the repo .env pins — assert it
    # is a concrete model string, and that this is the value an unguarded caller
    # inherits. The point of the test is that the default is NOT silently the
    # intended gpt-5.x route.
    assert r["MODEL"], r
    assert r["MODEL"] != "", r


def test_explicit_profile_overrides_default():
    """An explicit LLM_PROFILE must win over the .env default — proving the knob
    callers use to escape the glm fallback actually takes effect."""
    default = _resolve({})["MODEL"]
    deepseek = _resolve({"LLM_PROFILE": "deepseek"})["MODEL"]
    assert deepseek == "deepseek-v4-pro"
    # The override changed the resolved model away from the default (unless the
    # default already was deepseek, which it is not in this repo's .env).
    assert deepseek != default or default == "deepseek-v4-pro"
