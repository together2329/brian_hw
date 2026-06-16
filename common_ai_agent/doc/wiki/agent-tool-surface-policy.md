---
title: Agent tool surface policy
type: design
tags: [agent, tools, todo, external-db, plan-mode]
created: 2026-06-16
related: [oag-mode-integration, todo-loop-verification-hardening-20260608, andes-rtl-db-wiki-20260527]
---

# Agent Tool Surface Policy

The default ATLAS agent should expose the smallest tool set that is useful for
the current mode. Broad tools increase accidental calls, latency, and side
effects. Keep optional retrieval and planning tools gated unless the user or mode
explicitly asks for them.

## Current policy

- External reference DB lookup is opt-in. Do not expose the dedicated
  `external_db_query` tool in the default tool surface.
- TODO creation tools (`todo_add`, `todo_write`) are planning tools. Expose them
  only in `plan` / `plan_q` modes; execution may still use `todo_update` for
  progress transitions on an existing plan.

