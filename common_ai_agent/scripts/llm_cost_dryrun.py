#!/usr/bin/env python3
"""
scripts/llm_cost_dryrun.py — Estimate LLM call cost before running live tests.

Usage:
    python3 scripts/llm_cost_dryrun.py --mode live
    python3 scripts/llm_cost_dryrun.py --mode full
    python3 scripts/llm_cost_dryrun.py --mode quick

No network calls are made. Pure static analysis + pricing table lookup.
"""

import argparse
import os
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Resolve repo root so this script works from any cwd
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Import pricing table from lib/model_pricing.py (no network needed)
# ---------------------------------------------------------------------------
sys.path.insert(0, str(REPO_ROOT))
from lib.model_pricing import _lookup_pricing  # noqa: E402

# ---------------------------------------------------------------------------
# Worker model defaults (mirrors src/atlas_api_jobs.py _WORKER_MODEL_DEFAULTS)
# ---------------------------------------------------------------------------
_WORKER_MODEL_DEFAULTS = {
    "orchestrator":  "gpt-5.5",
    "ssot-gen":      "gpt-5.5",
    "fl-model-gen":  "gpt-5.5",
    "rtl-gen":       "gpt-5.3-codex",
    "tb-gen":        "deepseek",
    "sim_debug":     "kimi",
    "lint":          "deepseek",
    "sim":           "gpt-5.3-codex",
    "coverage":      "gpt-5.3-codex",
    "goal-audit":    "gpt-5.5",
    "syn":           "gpt-5.3-codex",
    "sta":           "gpt-5.3-codex",
    "pnr":           "gpt-5.3-codex",
    "sta-post":      "gpt-5.3-codex",
}

# Default fallback model when test file doesn't mention a specific model
_DEFAULT_MODEL = "gpt-5.5"

# Conservative per-test token estimates (over-estimate to avoid surprise bills)
_DEFAULT_INPUT_TOKENS  = 4_000
_DEFAULT_OUTPUT_TOKENS = 2_000

# ---------------------------------------------------------------------------
# Test suites per mode
# All paths relative to tests/
# ---------------------------------------------------------------------------
_LIVE_ONLY_FILES = [
    "tests/test_worker_chaining.py",
    "tests/test_worker_tool_execution.py",
    "tests/test_agent_server.py",
    "tests/test_real_glm51_headless_flow.py",
    "tests/test_llm_api.py",
]

# full mode adds agent_server and llm_api on top of quick exclusions
# (run_tests.sh full ignores worker_chaining, worker_tool_execution, real_glm51)
_FULL_EXTRA_FILES = [
    "tests/test_agent_server.py",
    "tests/test_llm_api.py",
]

_MODE_FILES = {
    "live":  _LIVE_ONLY_FILES,
    "full":  _FULL_EXTRA_FILES,
    "quick": [],  # quick mode excludes all live-LLM files
}


def _count_tests(filepath: Path) -> int:
    """Count test functions in a file (grep for 'def test_')."""
    if not filepath.exists():
        return 0
    text = filepath.read_text(errors="replace")
    return len(re.findall(r"^\s*def test_", text, re.MULTILINE))


def _detect_model(filepath: Path) -> str:
    """Detect explicit model= override in test file; fall back to default."""
    if not filepath.exists():
        return _DEFAULT_MODEL
    text = filepath.read_text(errors="replace")
    # Look for model="<name>" or model='<name>'
    matches = re.findall(r'model\s*=\s*["\']([^"\']+)["\']', text)
    for m in matches:
        if _lookup_pricing(m) is not None:
            return m
    return _DEFAULT_MODEL


def _estimate_cost(model: str, n_tests: int) -> float:
    """Return estimated USD cost for n_tests with given model."""
    pricing = _lookup_pricing(model)
    if pricing is None:
        # Unknown model — use gpt-5.5 as conservative upper bound
        pricing = _lookup_pricing(_DEFAULT_MODEL)
    if pricing is None:
        return 0.0
    input_cost  = (pricing.input  / 1_000_000) * _DEFAULT_INPUT_TOKENS  * n_tests
    output_cost = (pricing.output / 1_000_000) * _DEFAULT_OUTPUT_TOKENS * n_tests
    return input_cost + output_cost


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Estimate LLM cost for a run_tests.sh mode (no network calls)."
    )
    parser.add_argument(
        "--mode",
        choices=["live", "full", "quick"],
        default="live",
        help="Test mode to estimate (default: live)",
    )
    args = parser.parse_args()

    files = _MODE_FILES[args.mode]
    if not files:
        print(f"[dryrun] mode={args.mode}: no live-LLM test files — estimated cost $0.00")
        return 0

    # Table header
    col_file   = 46
    col_cases  = 10
    col_model  = 18
    col_cost   = 14
    header = (
        f"{'File':<{col_file}}  {'Cases':>{col_cases}}  "
        f"{'Model':<{col_model}}  {'Est. Cost':>{col_cost}}"
    )
    sep = "-" * len(header)
    print(f"\n[dryrun] mode={args.mode} — LLM cost estimate (conservative; no network calls)\n")
    print(header)
    print(sep)

    total_cases = 0
    total_cost  = 0.0

    for rel_path in files:
        filepath = REPO_ROOT / rel_path
        n_tests  = _count_tests(filepath)
        model    = _detect_model(filepath)
        cost     = _estimate_cost(model, n_tests)
        total_cases += n_tests
        total_cost  += cost
        label = Path(rel_path).name
        print(
            f"{label:<{col_file}}  {n_tests:>{col_cases}}  "
            f"{model:<{col_model}}  ${cost:>{col_cost-1}.4f}"
        )

    print(sep)
    print(
        f"{'TOTAL':<{col_file}}  {total_cases:>{col_cases}}  "
        f"{'':>{col_model}}  ${total_cost:>{col_cost-1}.4f}"
    )
    print()
    print(
        f"  Assumptions: {_DEFAULT_INPUT_TOKENS:,} input tokens + "
        f"{_DEFAULT_OUTPUT_TOKENS:,} output tokens per test case (no cache credit)."
    )
    print(f"  Actual cost may be lower (cache hits, shorter outputs).\n")

    # Machine-readable summary line for run_tests.sh to parse
    print(f"DRYRUN_TOTAL_USD={total_cost:.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
