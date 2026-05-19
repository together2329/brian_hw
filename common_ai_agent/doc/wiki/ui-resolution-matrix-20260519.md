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

## SSOT Design Preview pass (added post-font-bump 042ae7ac7)

After font bump `042ae7ac7` ("style(ui): bump font sizes + weight for
Windows readability") landed, an extra pass was run against the SSOT Design
Preview pane (`SsotReviewPane` in `frontend/atlas/workspace.jsx:9583`,
mounted when `mainTab='ssot'`). Surface was reloaded so the new
`styles.css?v=atlas-20260519-windows-fonts` was picked up. IP=pl330,
workflow=ssot-gen, file=`default/yaml/default.ssot.yaml`.

### What was checked

1. Pane renders content, not a blank / error state.
2. Readability after font bump (`--ui-control-font-size: 12.5px`,
   `--ui-text-weight: 500`).
3. Dark and Light themes both OK.
4. No content clipping at any viewport.

### Cells

| Viewport | Theme | Pane rendered | Error banner | Chat input visible | Screenshot |
|---|---|---|---|---|---|
| Native 1079×785 | Dark  | PASS | none | PASS | `/tmp/worker14_matrix/ssot_native_dark.png` |
| Native 1079×785 | Light | PASS | none | PASS | `/tmp/worker14_matrix/ssot_native_light.png` |
| 1280×720 sim    | Dark  | PASS | none | (sim FAIL — same root cause as base matrix; layout not reflowed) | `/tmp/worker14_matrix/ssot_1280x720_dark.png` |
| 1280×720 sim    | Light | PASS | none | (sim FAIL — same root cause as base matrix) | `/tmp/worker14_matrix/ssot_1280x720_light.png` |
| 1440×900 sim    | Dark  | PASS | none | PASS | `/tmp/worker14_matrix/ssot_1440x900_dark.png` |
| 1440×900 sim    | Light | PASS | none | PASS | `/tmp/worker14_matrix/ssot_1440x900_light.png` |
| 1920×1080 sim   | Dark  | PASS | none | PASS | `/tmp/worker14_matrix/ssot_1920x1080_dark.png` |
| 1920×1080 sim   | Light | PASS | none | PASS | `/tmp/worker14_matrix/ssot_1920x1080_light.png` |

Each cell rendered the SSOT pane with all expected blocks present:
top header (`SSOT DESIGN PREVIEW`, file picker, tag count), left card list
(`Brief`, `Architecture`, `Review Gaps`, `Raw YAML`), Top Module block,
Review Coverage tag grid, plus the Architecture / Features / Interfaces /
Registers · Dataflow sections.

### Font bump (042ae7ac7) — what is and is not in effect

CSS variables verified live via `getComputedStyle` on `<html>`:

| Variable | Value at runtime |
|---|---|
| `--ui-control-font-size` | `12.5px` (post-bump default/large) |
| `--ui-text-weight` | `500` (post-bump) |
| `--ui-control-weight` | `600` |

Body computed font-size = `16px` (browser default; pane text uses the
explicit CSS variables, not body inheritance — confirmed by visual
inspection of SSOT card text in the captured PNGs).

**Caveat — separate from this matrix's PASS/FAIL but worth flagging:**
the top-row `tab-chip` elements (`chat`/`ssot`/`Q&A`/`split view`/`full
view`/`git`) are rendered with an **inline `style="font-size:11px"`**, not
the `--ui-control-font-size` token. So the font bump did NOT reach the tab
chips themselves; they remain at 11 px regardless of profile. If
Windows-readability is the goal, the tab-chip inline `font-size` should be
removed so it picks up `--ui-control-font-size` like other controls.
Location: search `frontend/atlas/workspace.jsx` for `tab-chip` and replace
hard-coded `fontSize: '11px'` with `var(--ui-control-font-size)` or omit it.

### Verdict

- 8 / 8 SSOT cells: **pane renders correctly, no error banner, no
  content clipping, dark and light both OK**.
- Chat-input visibility under SSOT view follows the same pattern as the
  base 12-cell matrix: PASS at 1440×900 / 1920×1080 / native, simulated
  FAIL at 1280×720 from the same layout-anchor root cause. Same single
  shared fix proposed above applies.
- Font bump 042ae7ac7 is **live for CSS-variable-driven controls** but
  **silently bypassed** by hard-coded inline `font-size: 11px` on
  `tab-chip`.

## Reproduction

- Cookie file: `/tmp/atlas_cookies_v2.txt` (Netscape format, atlas_session
  cookie for `127.0.0.1`).
- Driver: `/tmp/worker14_matrix/run.py` (base matrix: CSS-scale simulated
  + native pass) and `/tmp/worker14_matrix/run_ssot.py` (SSOT pane pass).
- Per-cell probe + paths: `/tmp/worker14_matrix/results.json` (base),
  `/tmp/worker14_matrix/results_ssot.json` (SSOT pane).
- Screenshots: `/tmp/worker14_matrix/*.png` (16 base + 8 SSOT = 24 PNGs).
- Backend: atlas_ui on `127.0.0.1:62196`, WS `127.0.0.1:8765`. Backend was
  NOT restarted by this verification (per handoff constraint).
