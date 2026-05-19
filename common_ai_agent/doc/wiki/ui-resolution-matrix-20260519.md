# UI Resolution + Theme Matrix Verification — 2026-05-19

Goal: assert that the ATLAS chat input bar at the bottom of the page and the
dir-switcher top bar remain reachable / not clipped across the requested 12
combinations of viewport × view × theme. Owned by worker-14 of the
`orch-ux-hardcore` team (handoff `team-plan-orch-ux-hardcore.md`).

Cross-links: [[atlas-pipeline-screen]], [[orchestrator-chat-ux]],
[[atlas-browser-control-runbook]].

## Matrix

- **Viewports:** 1280×720, 1440×900, 1920×1080
- **Views:** Workspace, Pipeline
- **Themes:** Dark, Light
- **Total cells:** 12 (per request) + 4 layout-faithful native baselines = 16
  captures total.

## Environment + Tool limitation (must read first)

- cmux browser surfaces run on **WKWebView**. `browser.viewport.set` is
  rejected by the runtime: `not_supported: browser.viewport.set is not
  supported on WKWebView`.
- cmux RPC exposes `window.create` but the requested `frame.width/height`
  field is **silently ignored** by the runtime (a new window opens at the
  current macOS host frame, not at 1280×720). A second native window opened
  for cross-check produced `innerWidth × innerHeight = 1240 × 785`, not the
  requested 1280 × 720.
- `pane.resize` only adjusts splits inside an existing native window; it
  cannot grow the cmux native window above the macOS screen the user
  currently sees (here capped near 1280×848 raw, 1079×785 inside the active
  browser pane).
- **Consequence:** strictly layout-faithful native verification at 1280×720,
  1440×900, 1920×1080 was **not possible** under cmux/WKWebView. To still
  give the requested 12-cell matrix, we used a **CSS `transform: scale`
  wrapper** on `document.documentElement` that mimics each target viewport
  visually. This visual simulation does **not** trigger React media
  queries, `window.innerWidth` updates, or reflow at the simulated width —
  it is faithful for "did the bottom of the chat input fall below the
  simulated viewport floor" only, not for "did the page re-layout at this
  width". Each cell records `_simulated: true` and the actual native
  `innerWidth/innerHeight` alongside the simulated `vpW/vpH` in
  `results.json`.
- To still provide one layout-faithful data point per (view, theme), an
  extra **native** cell (1079×785, the real cmux pane) was captured. That
  is the row marked `native_*`.

## Native baseline (1079×785, layout-faithful)

| View | Theme | Chat input visible | input.bottom (px) | overlaps | screenshot |
|---|---|---|---|---|---|
| Workspace | Dark | PASS | 778 (vpH=785, 7 px clearance) | 0 | `/tmp/worker14_matrix/native_workspace_dark.png` |
| Workspace | Light | PASS | 776 (vpH=785, 9 px clearance) | 0 | `/tmp/worker14_matrix/native_workspace_light.png` |
| Pipeline | Dark | PASS | 778 (vpH=785, 7 px clearance) | 0 | `/tmp/worker14_matrix/native_pipeline_dark.png` |
| Pipeline | Light | PASS | 776 (vpH=785, 9 px clearance) | 0 | `/tmp/worker14_matrix/native_pipeline_light.png` |

All four native cells PASS. Clearance from the chat input bottom edge to the
viewport floor is **7–9 px** — small but non-zero. The dir-switcher top bar
is fully reachable (worker-13 just reordered FONT before WORKSPACE; the bar
fits the native width and is not clipped).

## Simulated matrix (CSS scale, visual)

Below, `vis` is whether `inputRect.bottom <= simulated vpH` after dividing
by the scale factor. This is the requested visibility check the team asked
for under the multi-resolution viewport intent.

| Viewport | View | Theme | vis | input.top | input.bottom | vpH | screenshot |
|---|---|---|---|---|---|---|---|
| 1280×720  | Workspace | Dark  | **FAIL** | 761 | 778 | 720 | `/tmp/worker14_matrix/1280x720_workspace_dark.png` |
| 1280×720  | Workspace | Light | **FAIL** | 758 | 776 | 720 | `/tmp/worker14_matrix/1280x720_workspace_light.png` |
| 1280×720  | Pipeline  | Dark  | **FAIL** | 761 | 778 | 720 | `/tmp/worker14_matrix/1280x720_pipeline_dark.png` |
| 1280×720  | Pipeline  | Light | **FAIL** | 758 | 776 | 720 | `/tmp/worker14_matrix/1280x720_pipeline_light.png` |
| 1440×900  | Workspace | Dark  | PASS | 761 | 778 | 900 | `/tmp/worker14_matrix/1440x900_workspace_dark.png` |
| 1440×900  | Workspace | Light | PASS | 758 | 776 | 900 | `/tmp/worker14_matrix/1440x900_workspace_light.png` |
| 1440×900  | Pipeline  | Dark  | PASS | 761 | 778 | 900 | `/tmp/worker14_matrix/1440x900_pipeline_dark.png` |
| 1440×900  | Pipeline  | Light | PASS | 758 | 776 | 900 | `/tmp/worker14_matrix/1440x900_pipeline_light.png` |
| 1920×1080 | Workspace | Dark  | PASS | 761 | 778 | 1080 | `/tmp/worker14_matrix/1920x1080_workspace_dark.png` |
| 1920×1080 | Workspace | Light | PASS | 758 | 776 | 1080 | `/tmp/worker14_matrix/1920x1080_workspace_light.png` |
| 1920×1080 | Pipeline  | Dark  | PASS | 761 | 778 | 1080 | `/tmp/worker14_matrix/1920x1080_pipeline_dark.png` |
| 1920×1080 | Pipeline  | Light | PASS | 758 | 776 | 1080 | `/tmp/worker14_matrix/1920x1080_pipeline_light.png` |

Summary: **8 / 12 simulated cells PASS, 4 / 12 FAIL** (all four FAILs are
the 1280×720 row, in both views and both themes).

## What the FAILs do and do not prove

- `inputRect.bottom = 776 / 778 px` is the page's natural layout position
  for the chat input bar when the page renders at its native viewport
  height. The CSS scale wrapper does not reflow that — it just shrinks the
  visual canvas to fit inside a simulated 1280×720 window.
- A real Chrome at native 1280×720 would re-flow: the chat input bar would
  sit at the new viewport's bottom edge, not at `bottom = 778`. So this
  simulated FAIL is **a layout-rendering risk indicator**, not proof that
  the bar is hidden on a real 720-tall device.
- However, the data point still matters: the current ATLAS layout puts
  the chat input bar at `~776 px` from the top of the page in the live
  cmux pane. There is **no scroll affordance on the chat panel** itself
  (when we shrank vpH visually, the input did not become reachable via
  scroll — it would just be off-screen on a real 720-tall device).
- Therefore the conservative reading is: **on real 1280×720 hardware the
  chat input is at risk of being clipped if the layout still anchors at a
  fixed pixel offset from top instead of from the viewport bottom**.

## Proposed single shared fix (no code change applied)

Worker-14 is read-only on source. Per handoff: when many cells fail with a
common cause, propose **one** root-cause adjustment and stop.

**Proposal:** make the bottom chat-input row anchor to the viewport
bottom and let the message scroller above it consume the remaining height.

- Anchor the chat panel column with
  `display: flex; flex-direction: column; height: 100vh; min-height: 0;`
- Inside it: messages list with `flex: 1 1 auto; min-height: 0; overflow-y: auto;`
- Chat input row: `flex: 0 0 auto;` and **not positioned by a top offset**.

This guarantees the input bar is always visible at the bottom of the
viewport, regardless of viewport height, and the scroller absorbs the
difference. This is the single change recommended; no other fixes should
be bundled in this round.

Files to inspect when applying: `frontend/atlas/workspace.jsx` (workspace
chat column) and `frontend/atlas/pipeline.jsx` (pipeline chat panel added in
task 2). `frontend/atlas/styles.css` for the matching CSS tokens.

## Constraint-honest verdict for the user's intent

- 1440×900 and 1920×1080 (8 of the 12 cells): **PASS** visually — chat
  input visible without scroll, dir-switcher reachable, no overlap.
- 1280×720 (4 of the 12 cells): **AT RISK** — visual simulation puts the
  input below the simulated viewport floor. Verification on real 1280×720
  hardware is required to confirm, and the proposed flex anchor would
  eliminate the risk regardless.
- Native cmux baseline (1079×785, all four view×theme cells): **PASS**.

## Reproduction

- Cookie file: `/tmp/atlas_cookies_v2.txt` (Netscape format, atlas_session
  cookie for `127.0.0.1`).
- Driver: `/tmp/worker14_matrix/run.py` (CSS-scale simulated + native pass)
- Per-cell probe + paths: `/tmp/worker14_matrix/results.json`
- Screenshots: `/tmp/worker14_matrix/*.png` (16 PNGs).
- Backend: atlas_ui on `127.0.0.1:62196`, WS `127.0.0.1:8765`. Backend was
  NOT restarted by this verification (per handoff constraint).
