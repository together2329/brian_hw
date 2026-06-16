---
type: reference
tags: [frontend, vite, stale-build, cache]
updated: 2026-06-16
related: [atlas-vite-e2e-verification, sim-debug-module-signals-2026-05-30]
---

# Project Vite Env Stale Build

Stub node for stale Vite/Tauri build symptoms where code changes are correct but the visible desktop/web surface still serves an old bundle. Verify the active bundle and relaunch path before debugging the wrong layer.

## Entry-document cache policy (no-store)  — 2026-06-16

**Symptom class:** "works in a fresh / incognito browser but is blank (or stuck
on old behaviour) in my normal browser." A returning browser renders nothing
even though the server, the WS path, and the agent all work; a brand-new
browser context against the *same* server works every time.

**Root cause:** `atlas_ui.create_app()` serves a VITE-ONLY frontend. The built
dist (`frontend/atlas/dist/`) references **content-hashed** asset filenames
(`app-BMBL11Ur.js`, …). The assets are served `no-store` (`_NoCacheStatic`), but
the **entry documents** `index.vite.html` / `lobby.vite.html` were returned by
`index()` / `lobby()` with **no `Cache-Control` header at all**. Browsers then
heuristically cache the entry HTML. After a rebuild changes the asset hashes, a
returning browser keeps booting its cached OLD entry → requests asset hashes
that no longer exist → 404 → blank shell. A fresh browser has no cached entry,
fetches the current one, and works — which is exactly the fresh-vs-returning
asymmetry.

**Fix:** serve the entry documents `Cache-Control: no-store, max-age=0`
(`src/atlas_ui.py` `index()` + `lobby()`). The entry revalidates every load;
assets stay `no-store`; returning browsers always boot the current frontend.
Note: a browser that *already* holds a heuristically-fresh stale entry may still
serve it once more without revalidating, so an already-poisoned cache needs one
hard reload to escape; thereafter `no-store` keeps it current.

**Evidence:** `tests/test_atlas_entry_cache_headers.py` (builds a fake dist,
drives `/` and `/lobby` via TestClient, asserts `no-store`). Live check:
`curl -sD - http://127.0.0.1:8810/ -o /dev/null | grep -i cache-control`.

**Ontology:** `REQ_PLAT_FRONTEND_ENTRY_NO_STORE_001` (unit `ui.tui`).

