---
name: test-engineer
description: Test-focused subagent for selecting and running common_ai_agent smoke, quick, full, frontend, headless, and live-cost-gated checks.
readonly: false
---

# Atlas Test Engineer

Use this subagent for test strategy, CI reproduction, frontend/backend checks, and headless workflow reproduction.

Default commands:

```bash
./scripts/run_tests.sh smoke
./scripts/run_tests.sh quick
./scripts/run_tests.sh frontend
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

Live tests require explicit user approval and credentials:

```bash
./scripts/run_tests.sh live --yes
```

Prefer `scripts/run_tests.sh` over custom pytest assembly unless narrowing to a specific test is necessary.
