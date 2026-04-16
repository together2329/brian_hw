# Open Decision: CI Strictness Defaults and Backward Compatibility

## Status

- **State:** Open
- **Owner:** TBD (maintainer decision required)
- **Last updated:** 2026-04-16

## Context

Current lint-tier defaults in `sim/cocotb/Makefile` are:

- `LINT_FAST_MYPY_BLOCKING=0`
- `LINT_FAST_RTL_WARN_AS_ERROR=0`
- `LINT_FULL_MYPY_BLOCKING=0`
- `LINT_FULL_RTL_WARN_AS_ERROR=0`
- `LINT_CI_MYPY_BLOCKING=1`
- `LINT_CI_RTL_WARN_AS_ERROR=1`
- `LINT_CI_REQUIRE_RESULTS=1`

This means CI is intentionally strict by default, while fast/full local tiers are warning-tolerant by default.

## Open Decision

Do we keep CI strict defaults as-is, or relax defaults for backward compatibility with existing pipelines that historically tolerated warnings or missing cocotb results artifacts?

## Decision Options

### Option A — Keep strict CI defaults (current behavior)

- Keep `LINT_CI_MYPY_BLOCKING=1`
- Keep `LINT_CI_RTL_WARN_AS_ERROR=1`
- Keep `LINT_CI_REQUIRE_RESULTS=1`

**Pros**
- Stronger signal quality for merges.
- Prevents warning debt and missing-test-artifact regressions.
- Matches documented fast/full/ci strictness model.

**Cons**
- Can break legacy CI jobs that depended on non-blocking type checks or optional results.xml.
- May require rollout coordination.

### Option B — Compatibility-first defaults with opt-in strictness

- Set one or more of:
  - `LINT_CI_MYPY_BLOCKING=0`
  - `LINT_CI_RTL_WARN_AS_ERROR=0`
  - `LINT_CI_REQUIRE_RESULTS=0`
- Require strict mode explicitly in CI config/environment.

**Pros**
- Lower migration friction for existing branches and downstream users.
- Fewer immediate CI disruptions.

**Cons**
- Weakens default gate quality.
- Increases risk of silently accepting degraded lint/test quality.

## Backward-Compatibility Expectations (regardless of option)

1. **Override stability:** all `LINT_CI_*` controls remain externally overrideable via environment or make CLI.
2. **Documentation parity:** `make help` and `sim/cocotb/lint_modes_guide.md` must always reflect actual defaults.
3. **Behavior transparency:** CI jobs should print effective strictness values in logs (`lint-ci` completion line already reports this).
4. **Transition guidance:** if defaults change, publish a short migration note with before/after examples.

## Recommended Resolution Path

1. Decide target policy (A or B).
2. If changing defaults, implement in `sim/cocotb/Makefile` only (single source of truth).
3. Update:
   - `sim/cocotb/lint_modes_guide.md`
   - `make -C sim/cocotb help` text (if needed)
   - `sim/cocotb/lint_validation_test_plan.md` expectations
4. Announce migration window and override examples for CI maintainers.
