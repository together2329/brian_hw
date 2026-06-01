---
name: atlas-headless-repro
description: Reproduce ATLAS pipeline or worker behavior from the command line. Use for CI failures, TDD reproduction, progress debugging, or comparing headless behavior to UI product flow.
---

# Atlas Headless Repro

Headless runs are for reproduction, contract tests, and workflow-script regression. They are not the final authority for user-visible product-flow claims when the UI/API/worker path is the product surface.

## Read First

- `doc/wiki/pipeline-progress-debugging.md`
- `doc/wiki/atlas-test-feature-coverage.md`
- `workflow/COMMON_ENGINE_FLOW.md`

## Commands

```bash
python3 src/headless_workflow.py --root <root> --ip <ip> --stages <stages>
python3 src/progress_debug.py
./scripts/run_tests.sh smoke
./scripts/run_tests.sh quick
```

Use fake or cached providers where possible. Use real/live providers only when explicitly needed and cost-approved.

When headless and UI disagree, debug the state boundary: root path, session, worker URL, workflow, run ID, and evidence freshness.
