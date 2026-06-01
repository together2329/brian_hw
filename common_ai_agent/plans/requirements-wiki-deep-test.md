# Requirements Wiki Deep Test Plan

## Goal

Persist the Sim Debug requirement ledger in `doc/wiki` and prove the requirements with requirement-id-level deep tests and real-surface QA.

## Success Criteria

1. Wiki persistence: `doc/wiki/sim-debug-requirements-2026-06-01.md` is reachable from `doc/wiki/index.md`, `doc/wiki/log.md`, and `doc/wiki/_graph.json`.
   - Test: `tests/test_wiki_build_graph.py::test_project_graph_indexes_sim_debug_requirements_ledger`
   - Manual QA: tmux runs `python3 workflow/wiki/build_graph.py --wiki doc/wiki --check`, captures output proving the page exists in `_graph.json`.

2. Requirement deep tests: each Sim Debug requirement group has a named SDR coverage test in `frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx`.
   - Test: `frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx`
   - Manual QA: tmux runs the focused Vitest file and captures the pass summary.

3. Requirement simulation quality: requirement classes reject missing/malformed evidence and accept contract-driven scenarios.
   - Test: `tests/test_simulation_quality_gate.py`
   - Manual QA: tmux runs `workflow/sim_debug/scripts/check_simulation_quality.py` against a temporary IP with required classes and captures pass/fail output plus generated report paths.

4. Adjacent regression: wiki query/build and existing Sim Debug suites still work.
   - Tests: `tests/test_wiki_build_graph.py`, `tests/test_simulation_quality_gate.py`, focused Sim Debug Vitest.
   - Manual QA: tmux captures a combined regression command and cleanup receipt.

## Waves

Wave 1: Inspect existing relevant files and add missing RED tests only.

Wave 2: Minimal implementation/doc graph updates to make RED tests pass. Do not rewrite unrelated dirty files.

Wave 3: Manual QA through tmux scenarios, then targeted full verification (`pytest` + `vitest` + `tsc`/build if TS changed).

Wave 4: Final review and OMO checkpoint.

## Critical Path

Wiki graph test -> graph/doc update -> focused wiki QA -> frontend deep test -> simulation quality gate -> regression suite.

