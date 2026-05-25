---
title: workspace.jsx Decomposition Plan
type: process
tags: [atlas-ui, frontend, refactor, workspace, maintainability, plan]
updated: 2026-05-25
related: [atlas-test-hardening-2026-05-23, atlas-ui-playwright-screenshot-recipe-2026-05-23]
---

# workspace.jsx Decomposition Plan

Status: proposed and parked. Do not implement until P0 is complete.

This page captures the agreed incremental split plan for
`frontend/atlas/workspace.jsx` after the 2026-05-25 review. The goal is to make
the ATLAS workspace source maintainable without changing runtime behavior.

## Current Constraint

`workspace.jsx` is about 18K lines and currently mixes product concerns:
workspace shell, chat feed, workflow routing, SSOT digest visualization, file
viewers, status/cost panels, and worker observability.

The browser loading model is still in-browser Babel scripts. New JSX files must
therefore load before `workspace.jsx` from `frontend/atlas/index.html` and
publish explicit globals such as:

```js
window.AtlasWorkspacePrimitives = { CopyBtn, Splitter };
```

`workspace.jsx` then consumes those globals. This keeps the first split
mechanical and avoids a bundler migration in the same change.

## Non-Goals

- No big-bang rewrite.
- No behavior changes.
- No UI redesign.
- No bundler migration.
- No split while active frontend routing/session work is still dirty.
- No moving components that close over `Workspace` local state until their props
  boundary is explicit.

## P0 Gate

P0 must finish before any split begins.

Required state:

- Parallel frontend work, especially `lib/session_routing.js/.mjs` extraction,
  has landed or been deliberately parked.
- `workspace.jsx`, `index.html`, and related frontend tests are no longer a
  moving target.
- Baseline verification passes:
  - frontend esbuild syntax/bundle check
  - frontend vitest suite
  - targeted pytest contracts for session routing and pipeline theme flow
  - browser smoke of the workspace screen

Reason: without P0, failures cannot be attributed cleanly to either the
decomposition or the concurrent routing extraction.

## Naming Rule

Use explicit product namespaces, not short aliases:

```text
window.AtlasWorkspacePrimitives
window.AtlasWorkspaceSession
window.AtlasWorkspaceSsotDigest
window.AtlasWorkspaceViewers
window.AtlasWorkspaceSsotQa
window.AtlasWorkspaceFeed
window.AtlasWorkspacePanels
window.AtlasWorkspaceAgentStatus
```

Rejected: `window.WsX`. It is too opaque for debugging and future handoffs.

## Phase Plan

### P1a: ws-primitives.jsx

Move the safest reusable primitives first:

- `CopyBtn`
- `Splitter`
- `AtlasStatusBadge`
- `ToolOutputPre`
- `DiffOutputPre`
- required helpers such as Prism language sanitation/highlighting and
  `_toolOutputLanguage`

This phase proves the global loading pattern end to end with the smallest
behavior surface.

### P1b: ws-session-switcher.jsx

Move `SessionSwitcher` only after session routing extraction settles.

`SessionSwitcher` depends on `normalizeUiSession`. If the routing helper has
already moved to `lib/session_routing.js/.mjs`, consume that shared API instead
of reintroducing a duplicate helper in the component file.

### P2: ws-ssot-digest.jsx

Move the SSOT digest visualization cluster:

- digest cards and key/value/list helpers
- register bitmap
- gate panels
- FSM visualization helpers
- module tree and block diagram
- source section digest views

This has the largest line-count payoff and is mostly props/data driven.

### P3: ws-viewers.jsx

Move file and report viewers:

- preview/foldable file panes
- lint report cards
- coverage report cards
- file viewer modal

This is moderately risky because these components share viewer helpers and
open-file behavior, but the UI boundary is clear.

### P4: ws-ssot-qa-cards.jsx

Move QA and approval cards before feed extraction:

- `SsotApprovalCard`
- `AskUserQuestionBlock`
- `SsotQaBoard`
- `AskUserCall`
- `AskUserPrompt`
- `QaHistoryPanel`

Reason: `FeedEntry` references these components, so extracting feed first would
force either temporary globals or cyclic ownership.

### P5: ws-feed.jsx

Move chat feed rendering:

- `ObsCard`
- `HandoffCard`
- `ToolCard`
- `LiveAgentPreview`
- `FeedEntry`
- related feed formatting helpers

This should happen after P4 so `FeedEntry` can depend on stable exported QA
card globals.

### P6: ws-panels.jsx

Move larger workspace side panels:

- `SsotReviewPane`
- `SsotPanel`
- `ProgressPanel`
- `TodoPanel`
- `TodoGraph`
- `GitPanel`
- `OrchestratorChatPanel`

This phase is stateful and should be reviewed for prop lifting before editing.

### Separate Phase: ws-agent-status-panel.jsx

Do not include `AgentStatusPanel` in P1.

It owns more than display:

- `/healthz` polling
- live worker polling
- model/effort updates
- cost display
- worker context and active job summary

Treat it as its own extraction after the small component pattern is proven.

### P7: Workspace Hooks

Optional and later only:

- `useChatFeed`
- `usePipelineState`
- `useOrchestratorChat`
- `useWorkspaceSessionRoute`

This is the highest-risk stage because it changes ownership of state and side
effects. Do it only when the component split has stabilized.

## Verification Per Phase

Each phase must verify:

- New JSX file parses.
- `index.html` loads the new JSX file before `workspace.jsx`.
- `workspace.jsx` consumes globals without changing rendered JSX behavior.
- Existing frontend vitest tests pass.
- Relevant pytest source-contract tests pass.
- Browser smoke confirms the workspace screen loads and the moved UI still
  renders.

If any check fails, fix within the same phase before starting the next one.

## Stop Condition

Stop the decomposition when `workspace.jsx` is reduced to the workspace shell
and glue code, even if P7 has not happened. The product goal is lower collision
risk and clearer ownership, not maximum abstraction.

## Related Notes

This detailed plan refines the broader product-structure guidance in
`.omx/wiki/atlas-frontend-product-structure.md`. The older high-level rule
still applies: split by product responsibility, not by technology category.
