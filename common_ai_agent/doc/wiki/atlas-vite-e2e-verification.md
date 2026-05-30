# ATLAS vite frontend — automated E2E verification

One command that proves the vite/.tsx frontend **actually works in a real browser**
(not just `tsc`/`build` passing — that gap shipped a white screen + "no response"
before). Lives in `scripts/`, runs in isolation on a **test port (3019)** so it
never touches a running app on `:3000`.

## Run
```bash
scripts/atlas_vite_e2e_verify.sh
# options:
ATLAS_E2E_PORT=3025 PYTHON=python3 SKIP_VITEST=1 scripts/atlas_vite_e2e_verify.sh
```
Exit 0 = ✅ VERIFIED. Screenshots land in `/tmp/atlas_e2e_shots/` (01_initial,
02_workspace, 03_chat). Server log: `/tmp/atlas_e2e_server_<port>.log`.

## What it checks (5 steps)
1. `tsc --noEmit` → 0 errors
2. `vitest run` → unit/render smoke green (`SKIP_VITEST=1` to skip)
3. `vite build` → dist refreshed (the step whose absence = white-screen 503 shell)
4. starts `ATLAS_FRONTEND_MODE=vite python src/atlas_ui.py --port 3019`, waits for `/healthz`
5. **real headless Chromium** (`scripts/atlas_vite_e2e.mjs`, Playwright):
   - render: `#root` non-empty, no `#atlas-error-banner`, **no `/assets`·`/backend.js`·`/vendor` 404s**
   - auth (POST `/api/auth/login` admin/1151, or `/tmp/atlas_cookie`, or the login form)
   - workspace renders: chat input + left rail present
   - sends **"hi"** and asserts the `/ws/agent` handshake: `agent_received{msg_id}` +
     `agent_accepted{ok:true}` (proves delivery — the old silent-loss "no response" is gone)

## Prereqs
- `npm install` in `frontend/atlas` (the script also auto-installs Playwright +
  chromium on first run if missing).
- A working LLM/worker backend config for the chat step (delivery handshake is
  asserted; full LLM token is best-effort).

## Notes
- Desktop (Tauri) loads the **same** `http://localhost:3000` as the web
  (`src-tauri/tauri.conf.json` frontendDist/devUrl), so a green web E2E ⇒ desktop
  renders too — but WKWebView caches hard: after a dist rebuild, fully **quit
  (Cmd+Q) + relaunch** the desktop app. See [[project_ts_vite_tauri_cutover]].
- Lesson this codifies: **build-pass ≠ renders.** Run this before flipping the
  served default to vite. Related: [[project_merge_broke_prompt_delivery]].
