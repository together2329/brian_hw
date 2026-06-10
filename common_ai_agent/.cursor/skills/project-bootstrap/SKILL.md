---
name: project-bootstrap
description: Bootstrap ATLAS/Common AI Agent sessions. Use when starting work in this repo, resolving ATLAS paths, checking .env/.config setup, or orienting an agent to the project.
---

# Atlas Project Bootstrap

## Quick Start

1. Read `doc/wiki/index.md` Fast Context and LLM Reading Order.
2. Confirm task mode using `.cursor/rules/60-mode-routing.mdc`.
3. Check config sources in this order: shell env, `workflow/*/workspace.json`, `.config`, `.env`.
4. Use `.env.example` as the secrets template. Never copy `.env` content into notes, skills, or commits.

## Key Roots

- `ATLAS_SOURCE_ROOT`: this checkout.
- `ATLAS_WORKFLOW_ROOT`: `workflow/`.
- `ATLAS_PROJECT_ROOT`: parent directory containing IP folders.
- `ATLAS_IP_ROOT`: optional active IP override.

## First Commands

Use these only when the task needs runtime validation:

```bash
./scripts/run_tests.sh smoke
python3 src/atlas_ui.py --port 8765
python3 src/main.py -w default
```

Prefer reading existing docs and config before inventing new setup conventions.
