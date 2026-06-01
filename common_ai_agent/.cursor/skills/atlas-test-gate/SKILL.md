---
name: atlas-test-gate
description: Select and run common_ai_agent test gates. Use before claiming completion, after backend/frontend changes, or when the user asks to verify or run tests.
---

# Atlas Test Gate

## Default Gate

Use the repository wrapper instead of hand-assembling pytest commands:

```bash
./scripts/run_tests.sh smoke
./scripts/run_tests.sh quick
./scripts/run_tests.sh full
./scripts/run_tests.sh frontend
```

Choose `smoke` for fast critical-path checks, `quick` for the normal no-live-LLM suite, `full` for broader non-live coverage, and `frontend` for `frontend/atlas/`.

## Live LLM Tests

Live tests cost money and require `.env` credentials:

```bash
./scripts/run_tests.sh live --yes
```

Run or reference `scripts/llm_cost_dryrun.py` first when estimating live-test cost.

## Direct Pytest

If running pytest directly on macOS, prefer:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

Do not remove `tests/conftest.py` collection guards without checking the wiki.
