# Frontend modernization 2026-05-29 — TS migration · Vite cutover · Tauri desktop · gpt-5.5

One-stop overview of the 2026-05-29 modernization arc on `main`. The codebase now
runs the **TypeScript + Python + Rust** trio, applied per-layer (not a rewrite):
frontend → TypeScript/Vite, backend → Python (unchanged), desktop shell → Rust/Tauri.

Detailed runbooks: [[worker-model-gpt-switch]] · [[tauri-desktop-shell]]. Strategy
rationale: [[tech-direction-recommendation-20260529]].

## What changed (the arc)

| Phase | Change | Live by default? |
|---|---|---|
| **C** | 8 oversized migrated `.tsx` split to <1000 lines | n/a (inert mirrors) |
| **B** | `workspace.jsx` (13,286 lines) → 28 typed `workspace*.tsx` | no (inert until cutover) |
| **A1** | **Vite build cutover** — `main.tsx` entry bundles all `.tsx`; backend serves it behind `ATLAS_FRONTEND_MODE=vite` | was "no — default legacy `.jsx`"; **now YES by default (legacy retired 2026-05-30)** |
| **A2** | **Tauri v2 desktop shell** — native window loading the backend; runnable `ATLAS.app` | n/a (opt-in launch) |
| **D** | Worker/orchestrator LLM models switched glm → `gpt-5.5` in `.env` | **no — needs restart + OAuth** |

Net frontend state: **all `.tsx` type-check clean (`tsc --noEmit` 0) and pass
vitest (68/68); every file <1000 lines.** As of **2026-05-30** the legacy `.jsx`
frontend is **retired** (commits `59cdfb11`, `b6afdae0`) — the served `/` route is
**vite/`.tsx` only**, so the cutover described above is now the live default, not
an additive/inert layer.

## Current "live vs ready" state (important)

> **Update 2026-05-30:** the "behind a flag" framing below is historical. The
> legacy `.jsx` frontend has been **retired**; TSX+Vite is now the **only** live
> frontend and `ATLAS_FRONTEND_MODE=vite` is no longer needed to activate it
> (the `/` route in `src/atlas_ui.py` serves the built Vite `dist/` unconditionally,
> with a "run `npm run build`" page as the only fallback). See
> [[babel-retirement-cutover-20260529]].

- **Live now:** TSX+Vite frontend (built `dist/` bundle, no in-browser babel) is
  the default for `/`. gpt-5.5 still needs a restart + OAuth (model switch is the
  one piece that is not auto-active).
- **Ready, flip to activate:**
  - ~~TypeScript frontend → set `ATLAS_FRONTEND_MODE=vite`~~ — **no-op as of 2026-05-30**: TSX+Vite is the served default; the env flag no longer gates the `/` route.
  - gpt-5.5 → `.config` `USE_OPENCODE_OAUTH=true` + restart backend with `--model gpt-5.5`.
  - Desktop app → launch `ATLAS.app` / `scripts/run_atlas_desktop.sh`.

## How to run each

```bash
# Desktop window (backend must be serving on :3000):
open src-tauri/target/release/bundle/macos/ATLAS.app      # pre-built
scripts/run_atlas_desktop.sh                              # tauri dev (hot Rust reload)

# TSX+Vite is now the served default (2026-05-30). To also switch to gpt-5.5,
# restart the backend with the model flag (ATLAS_FRONTEND_MODE is no longer needed):
<your atlas server launch command> --model gpt-5.5

# Verify the gpt switch took:
scripts/atlas_model_smoke.sh        # PASS = orchestrator.model == gpt-5.5
```

## Architecture decisions

- **Single React instance.** `.tsx` use bundled `react`; `_react-global.ts` puts
  the *same* bundled React/ReactDOM on `window` before `app.tsx` self-mounts, so
  `window.ReactDOM.createRoot` doesn't pair a vendor react with bundled components
  (which would throw "invalid hook call"). This is why `workspace.jsx` had to be
  migrated (B) before the cutover — a babel-global-react workspace + bundled `.tsx`
  = two react copies.
- **Tauri Option A (webview → backend), not static bundling.** The served page
  needs server-side `window.ATLAS_BOOT_CONFIG` injection + same-origin `/vendor`,
  `/backend.js`, and the `/ws/agent` WebSocket, so a static `dist/` is a dead page.
  The shell loads `http://localhost:3000`; native capability via dialog/fs/opener
  plugins. See [[tauri-desktop-shell]].
- **Backend stays Python.** The bottleneck is LLM latency, not CPU — language
  rewrite ROI is zero. See [[tech-direction-recommendation-20260529]].

## Deferred (not in this arc)

- ~~Retire the legacy `.jsx` + flip the Vite frontend to default (after browser sign-off).~~ **DONE 2026-05-30** (commits `59cdfb11`, `b6afdae0`) — see [[babel-retirement-cutover-20260529]].
- Tauri distribution: PyInstaller-freeze the backend as a sidecar (Option B), code
  signing + notarization, `.dmg` packaging (`bundle_dmg.sh` needs a GUI session),
  real app icon + bundle identifier.

## Gotchas observed

- **Stale LSP vs `tsc`.** Editor diagnostics repeatedly showed
  `Property X does not exist on Window` after the migration; the authoritative
  `npx tsc --noEmit` was 0 errors every time. Trust the CLI; the LSP needs a reload.
- **Port.** The code default is `8765` (`src/atlas_runtime_run.py`) but the running
  instance is `:3000`; the Tauri config + scripts target `:3000` — keep them in sync
  with however the server is launched.

## Commits (main)

```
2c01a902  desktop: make ATLAS.app runnable (CLI, icons, app build, launcher)
73780b60  desktop: scaffold Tauri v2 shell (A2)
d3c73ad7  frontend+backend: Vite build cutover behind ATLAS_FRONTEND_MODE (A1)
b3d301cb  frontend: workspace.jsx -> 28 typed .tsx (B)
bda7e78a  ops: gpt-5.5 worker-model smoke + runbook (D)
a800c6a4  frontend: split 8 oversized .tsx <1000 lines (C)
```
