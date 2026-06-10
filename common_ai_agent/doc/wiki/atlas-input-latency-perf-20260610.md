---
title: "ATLAS chat input latency — analysis + round-2 optimization + live perf HUD"
tags: ["atlas", "frontend", "performance", "input-latency", "workspace"]
date: 2026-06-10
status: active
---

# ATLAS chat input latency — analysis + round-2 optimization + live perf HUD

## Symptom

Typing in the workspace chat input visibly stutters, especially with large
sessions / while orchestrator jobs run. (Reported as "worktree 나눠서 input
prompt가 느린 느낌" — the worktree split itself is unrelated; it correlates via
stale bundles and machine CPU contention.)

## Architecture recap (post-50214677 "Reduce Atlas chat input re-rendering")

- Input value is owned by the workspace ROOT data hook
  (`workspace-root-data-hook.tsx` `useState` `input`) — a root re-render per
  change by construction.
- `WorkspacePromptComposer` (`workspace-root-render.tsx`) is `memo` + local
  draft state; keystrokes only re-render the composer. Parent sync is
  debounced (`PARENT_INPUT_SYNC_DELAY_MS`).
- `WorkspaceFeedList` is `memo` with a custom comparator; feed slice capped.

## Round-2 findings (2026-06-10)

1. **Stale bundle trap** (see [[vite-env-stale-build]] memory): server up 23h,
   dist rebuilt the same morning — an unreloaded tab keeps the old bundle.
   Always hard-reload before judging input perf.
2. **Parent sync fired at 60ms for ALL drafts** — during prose typing the root
   re-rendered at nearly every word boundary.
3. **Four pollers re-rendered the root even when nothing changed** (new object
   identity every tick): worker status (3s), orch workers (3s), health
   telemetry (30s + context sync), worker progress (1.5s while a job runs).

## Changes

- `workspace-root-render.tsx`
  - Adaptive parent sync delay: slash/`@` drafts keep 60ms (popups are
    root-rendered and must feel instant); plain prose syncs at 240ms
    (`parentInputSyncDelayFor`).
  - `ATLAS_INPUT_PERF` store + `WorkspaceInputPerfHud` (opt-in live meter,
    rendered at the right edge of the prompt row).
- `workspace-root.tsx` — root render counter bump for the HUD.
- `workspace-root-data-hook.tsx` — `samePolledState` (JSON-equality) bail-outs
  in all four pollers: updater returns the previous reference when the payload
  is unchanged, so React skips the root render entirely.

## Live perf HUD — how to watch input latency in real time

```js
localStorage.ATLAS_PERF = '1'   // or open the app with ?perf=1
// hard reload (Cmd+Shift+R)
```

The prompt row then shows, updated every 500ms:

```
⌨ 12ms (max 48) · root 0.5/s · sync 3
```

- `⌨ Nms` — last keystroke→paint latency (double-rAF after the draft change);
  `max` since load. This is literally "what the eye sees".
- `root N/s` — Workspace root renders per second. Idle should be ~0 now
  (pollers bail out); >2/s while typing prose means a regression.
- `sync N` — cumulative debounced parent input syncs.

Disable: `localStorage.removeItem('ATLAS_PERF')` + reload.

## Expected profile after this change

- Keystroke→paint: composer-local render only (small, ~a few ms on idle CPU).
- Root renders: ~0/s idle, brief bursts at typing pauses (240ms) and on real
  feed/poll changes only.

## Related

- [[atlas-modular-refactor-status-20260530]] — module split that made the
  composer/feed memo boundaries possible.
- Machine-level contention (multiple Claude TUI sessions, Xprotect, remote
  desktop encoding) still adds jitter on top — measured 2026-06-10.
