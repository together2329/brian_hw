# Requirements Wiki Deep Test Notepad

## Bootstrap

- User request: save requirements to the wiki and run deep tests per requirement.
- Session: `.omo/ulw-loop/requirements-wiki-deep-test-20260601`.
- Codex goal tool: `create_goal` failed because the previous completed coverage goal still exists in this thread. Work continues through the OMO session state and this conflict is recorded here.
- Relevant skills:
  - `omo:ulw-loop`: required by user and used for goal/state/evidence.
  - `omo:programming`: required for TypeScript/Python edits and strict TDD.
  - `omo:frontend-ui-ux`: relevant only if Sim Debug UI changes are needed; current intent is verification/minimal fixes.
  - `omo:debugging`: relevant if runtime/browser/manual QA exposes failures.
  - `browser`: relevant for browser-facing Sim Debug QA if the in-app browser is available; otherwise use Playwright/Chrome.

## Initial Findings

- Existing dirty worktree includes relevant pre-existing/untracked work:
  - `doc/wiki/sim-debug-requirements-2026-06-01.md`
  - `frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx`
  - updates to `doc/wiki/index.md` and `doc/wiki/log.md`
- No `AGENTS.md` applies inside this repo; discovered `AGENTS.md` files are under `../external_refs/open-design/`.
- The worktree has many unrelated user changes. Do not revert unrelated files.
- `explore_req_wiki_deep` located the core surfaces:
  - requirement/wiki save: `src/headless_workflow.py`, `src/atlas_ui.py`, `workflow/wiki/build_graph.py`
  - deep requirement tests: `frontend/atlas/__tests__/sim-debug-requirements-deep.test.tsx`, `src/atlas_api_sim_debug.py`
  - simulation quality gate: `workflow/sim_debug/scripts/check_simulation_quality.py`, `tests/test_simulation_quality_gate.py`
- Plan agent timed out twice without producing `plans/requirements-wiki-deep-test.md`; root wrote the fallback executable plan at that path.

## Plan

- C001 wiki persistence: add/verify a failing-first project wiki graph test, then prove `sim-debug-requirements-2026-06-01` is indexed.
- C002 requirement deep tests: run and fix focused SDR deep Vitest coverage.
- C003 simulation quality: run/fix requirement-class quality gate and prove malformed/missing evidence is rejected.
- C004 regression: rerun adjacent wiki/sim-debug checks and capture cleanup receipts.
