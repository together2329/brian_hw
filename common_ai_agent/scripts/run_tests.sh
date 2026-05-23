#!/usr/bin/env bash
# run_tests.sh — single entry point for the ATLAS test quality check.
#
# Usage:
#   ./scripts/run_tests.sh             # default: quick (no live LLM, ~3 min)
#   ./scripts/run_tests.sh quick       # same as above
#   ./scripts/run_tests.sh full        # everything except live LLM (~5 min)
#   ./scripts/run_tests.sh live        # full + live LLM workers (~10 min, needs .env)
#   ./scripts/run_tests.sh smoke       # 5 fastest critical paths (~30s)
#   ./scripts/run_tests.sh load        # real subprocess load tests (slow — minutes)
#   ./scripts/run_tests.sh mutation    # mutmut mutation testing (minutes to hours; needs pip3 install mutmut)
#   ./scripts/run_tests.sh -- <args>   # pass args directly to pytest
#
# What it does:
# - Loads .env (LLM API keys etc.)
# - Excludes CLI-only test scripts (moved to scripts/cli_tests/)
# - Excludes dead-import dirs (filed for deletion — see wiki §5.1)
# - Returns the same exit code as pytest
#
# Quality report:
#   doc/wiki/atlas-test-feature-coverage.md describes which test gates which feature.

set -uo pipefail
cd "$(dirname "$0")/.."

# ── env ──────────────────────────────────────────────────────────────
if [[ -f .env ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

MODE="${1:-quick}"
shift || true

# Pass-through after `--`
PYTEST_EXTRA=()
if [[ "$MODE" == "--" ]]; then
  PYTEST_EXTRA=("$@")
  MODE="quick"
fi

# Common args. `collect_ignore_glob` in tests/conftest.py handles the
# dead-import paths so the operator never has to list 7 --ignore flags.
BASE_ARGS=(tests/ -q --tb=short --no-header)

case "$MODE" in
  smoke)
    echo "[run_tests] mode=smoke (critical paths only)"
    python3 -m pytest \
      tests/test_atlas_db_orchestrator.py \
      tests/test_orchestrator_workers_route.py \
      tests/test_orchestrator_dispatch_seed.py \
      tests/test_orchestrator_chat_ip_extraction.py \
      tests/test_chat_full_multiuser_system.py \
      tests/test_production_parity.py::test_atlas_ui_imports_cleanly_as_main_module \
      tests/test_workflow_tool_inventory.py \
      -q --tb=short ${PYTEST_EXTRA[@]+"${PYTEST_EXTRA[@]}"}
    ;;

  quick)
    echo "[run_tests] mode=quick (no live LLM)"
    python3 -m pytest \
      "${BASE_ARGS[@]}" \
      --ignore=tests/test_agent_server.py \
      --ignore=tests/test_worker_chaining.py \
      --ignore=tests/test_worker_tool_execution.py \
      --ignore=tests/test_real_glm51_headless_flow.py \
      --ignore=tests/test_llm_api.py \
      --ignore=tests/test_llm_benchmark.py \
      ${PYTEST_EXTRA[@]+"${PYTEST_EXTRA[@]}"}
    ;;

  full)
    echo "[run_tests] mode=full (excludes only live-LLM-bound suites)"
    python3 -m pytest \
      "${BASE_ARGS[@]}" \
      --ignore=tests/test_worker_chaining.py \
      --ignore=tests/test_worker_tool_execution.py \
      --ignore=tests/test_real_glm51_headless_flow.py \
      ${PYTEST_EXTRA[@]+"${PYTEST_EXTRA[@]}"}
    ;;

  live)
    echo "[run_tests] mode=live (real LLM calls — costs money)"
    if [[ -z "${LLM_API_KEY:-}${ANTHROPIC_API_KEY:-}${PROFILE_glm_API_KEY:-}" ]]; then
      echo "[run_tests] ERROR: no LLM API key in env. Configure .env first." >&2
      exit 2
    fi

    # ── Cost estimate + confirmation gate ─────────────────────────────────
    # Skip when --yes flag is present (non-interactive / CI usage).
    _YES=0
    for _arg in "$@"; do
      [[ "$_arg" == "--yes" || "$_arg" == "-y" ]] && _YES=1
    done

    _DRYRUN_OUT=$(python3 "$(dirname "$0")/llm_cost_dryrun.py" --mode live 2>&1)
    echo "$_DRYRUN_OUT" | grep -v "^DRYRUN_TOTAL_USD="
    _TOTAL_USD=$(echo "$_DRYRUN_OUT" | grep "^DRYRUN_TOTAL_USD=" | cut -d= -f2)

    if [[ "$_YES" -eq 0 ]]; then
      printf "\nContinue with ~\$%s estimated cost? [y/N] " "${_TOTAL_USD:-?}"
      read -r _CONFIRM </dev/tty
      if [[ "$_CONFIRM" != "y" && "$_CONFIRM" != "Y" ]]; then
        echo "[run_tests] Aborted by user." >&2
        exit 1
      fi
    fi
    # ── End cost gate ──────────────────────────────────────────────────────

    export ATLAS_RUN_REAL_LLM_TDD=1
    python3 -m pytest "${BASE_ARGS[@]}" ${PYTEST_EXTRA[@]+"${PYTEST_EXTRA[@]}"}
    ;;

  load)
    echo "[run_tests] mode=load (real subprocess load tests, slow — minutes)"
    ATLAS_LOAD_TEST=1 python3 -m pytest \
      tests/test_lazy_worker_real_cold_start.py \
      tests/test_lazy_worker_memory_leak.py \
      -v --tb=short ${PYTEST_EXTRA[@]+"${PYTEST_EXTRA[@]}"}
    ;;

  mutation)
    echo "[run_tests] mode=mutation (mutmut, slow — minutes to hours)"
    MUTMUT_BIN=/Users/brian/Library/Python/3.9/bin/mutmut
    if command -v mutmut &>/dev/null; then
      MUTMUT_BIN=mutmut
    elif [[ ! -x "$MUTMUT_BIN" ]]; then
      echo "[run_tests] ERROR: mutmut not found. Run: pip3 install mutmut" >&2
      exit 2
    fi
    "$MUTMUT_BIN" run
    "$MUTMUT_BIN" results
    ;;

  frontend)
    echo "[run_tests] mode=frontend (vitest JSX component tests)"
    cd frontend/atlas && npx vitest run
    ;;

  help|-h|--help)
    sed -n '2,20p' "$0"
    exit 0
    ;;

  *)
    echo "[run_tests] unknown mode: $MODE (try 'quick', 'full', 'live', 'smoke', 'load', 'mutation', 'frontend', or 'help')" >&2
    exit 2
    ;;
esac
