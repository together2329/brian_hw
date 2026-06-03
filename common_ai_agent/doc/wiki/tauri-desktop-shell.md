# ATLAS desktop shell (Tauri v2) — MVP runbook

A native desktop window for ATLAS, for distribution + native file access (OS
file dialogs, arbitrary local paths) beyond what a sandboxed browser tab allows.

## Architecture: Option A (webview → running backend)

The Tauri shell is a **native window that loads the running ATLAS backend**
(`http://localhost:3000`). It is **not** a static-asset host, by necessity:

- The served HTML gets `window.ATLAS_BOOT_CONFIG` **injected server-side** at
  request time (`src/atlas_ui.py` `_vite_index_html()` / `_html_with_atlas_boot_config`).
- The page depends on same-origin backend routes: `/vendor/*`, `/backend.js`,
  `/vcd-parser.js`, `/assets/*`, and the `ws://<host>/ws/agent` WebSocket
  (`backend.js` builds the URL from `location.host`).

A statically-bundled `dist/` would therefore be a dead page. So the MVP shell
points its webview at the live backend and adds native capability via Tauri
plugins (dialog, fs, opener). This compiles and runs today with **zero changes
to the Python backend**.

> **Port:** `frontendDist`/`devUrl` in `src-tauri/tauri.conf.json` is
> `http://localhost:3000` — matching the running ATLAS instance. The code's
> argparse default is `8765` (`src/atlas_runtime_run.py`), so if you launch the
> server on a different port, update both URLs to match.

## Files (`src-tauri/`)

| File | Purpose |
|---|---|
| `Cargo.toml` | Rust crate: `tauri` v2 + `tauri-plugin-{dialog,fs,opener}` v2 |
| `build.rs` | `tauri_build::build()` |
| `src/main.rs` | minimal shell: registers the 3 plugins, runs the app |
| `tauri.conf.json` | window (1600×1000), `frontendDist`/`devUrl` → localhost:3000, bundle (app+dmg) |
| `capabilities/default.json` | v2 permissions: `core/dialog/fs/opener :default` |
| `icons/icon.png` | 512×512 placeholder (replace with the real ATLAS icon before distribution) |

`/target` and `/gen` are gitignored (build artifacts / CLI-generated schemas).

## Run / verify

Already done in-repo: `@tauri-apps/{cli,api}` are in `frontend/atlas/package.json`
devDeps, the icon set is generated, and a release `ATLAS.app` has been built and
verified. On a fresh checkout:

```bash
# 0. install node deps (pulls the Tauri CLI binary into node_modules/.bin)
(cd common_ai_agent/frontend/atlas && npm install)

# 1. (optional) prove the Rust shell compiles — first build pulls ~400 crates (~2 min)
(cd common_ai_agent/src-tauri && cargo check)

# 2. RUN the desktop window. Pass the IP parent explicitly with --root; the
#    launcher starts a local backend for that root unless a matching backend
#    is already serving.
common_ai_agent/scripts/run_atlas_desktop.sh --root /path/to/ip-parent --ip <ip-name>
common_ai_agent/scripts/run_atlas_desktop.sh --prod --root /path/to/ip-parent --ip <ip-name>

# Existing backend mode is still supported:
common_ai_agent/scripts/run_atlas_desktop.sh --backend-url 'http://127.0.0.1:3000/?ip=<ip-name>'

# 3. build the runnable .app yourself (app-only target, ~2 min release compile):
(cd common_ai_agent && frontend/atlas/node_modules/.bin/tauri build)
#    -> src-tauri/target/release/bundle/macos/ATLAS.app   (double-clickable)
```

The launcher never hardcodes a project root. Root selection belongs to the
backend and flows through `src/atlas_ui.py --root <ip-parent>`. To expose the
Perforce SCM tab, pass the provider explicitly:

```bash
common_ai_agent/scripts/run_atlas_desktop.sh \
  --root /path/to/ip-parent \
  --ip <ip-name> \
  --scm-provider perforce
```

## Backend URL and white-window troubleshooting

The Desktop shell loads one backend URL. If no URL is supplied, the Tauri binary
defaults to `http://localhost:3000/`. That is correct only when the ATLAS server
is listening on localhost.

If the server was started with a LAN-only bind, for example:

```bash
python3 src/atlas_ui.py --host 192.168.45.139 --port 3000 ...
```

then `localhost:3000` is closed and a default Desktop launch can show a white
window. Either start the server on localhost/0.0.0.0, or pass the exact backend
URL:

```bash
open -na /Applications/ATLAS.app --args \
  --backend-url 'http://192.168.45.139:3000/?session_id=admin&ip=NEW_IP_v5&workflow=default'
```

The product launcher should be preferred for normal use because it keeps root,
backend URL, session, IP, workflow, and SCM flags together:

```bash
common_ai_agent/scripts/run_atlas_desktop.sh \
  --prod \
  --backend-url 'http://127.0.0.1:3000/?session_id=admin&ip=NEW_IP_v5&workflow=default'
```

For the installed macOS app, launch through `open -na ... --args --backend-url`
rather than executing `Contents/MacOS/atlas-desktop` directly. Direct binary
execution can create a window without driving the WebView through the normal
LaunchServices app path.

`scripts/run_atlas_desktop.sh --prod` uses the same LaunchServices path and
blocks with `open -W -na` so its backend cleanup trap still runs when the app
exits. The `.app` path must be absolute for `open` to treat it as a bundle path
rather than an application name.

Status interpretation:

- `Backend disconnected` means the page/backend transport is missing, closed, or
  unauthorized.
- `Agent worker failed · session worker failed` means the backend is reachable
  but the active interactive session worker is not live.
- `Agent responding` means a live `agent_state running` event is active and takes
  priority over stale worker-status polling.

2026-06-03 launcher verification:

- `scripts/run_atlas_desktop.sh --prod --root /tmp/atlas-desktop-launcher-qa --ip QA_IP --workspace-session qa --session-id qa_user --workflow default --port 3046`
  started a backend at `127.0.0.1:3046` with project root
  `/private/tmp/atlas-desktop-launcher-qa`.
- The launched process was
  `atlas-desktop --backend-url http://127.0.0.1:3046/?ip=QA_IP&workflow=default&session_id=qa_user&workspace_session=qa&session=qa_user%2Fqa%2FQA_IP%2Fdefault`.
- After that app process exited, `127.0.0.1:3046/healthz` was closed, proving
  the launcher backend cleanup trap ran.

> `bundle.targets` is `["app"]` (not `dmg`): the `.app` is the runnable artifact.
> `tauri build`'s `.dmg` step (`bundle_dmg.sh`) needs a GUI Finder/AppleScript
> session and fails headless — DMG/installer packaging is part of the deferred
> distribution pass (with signing + notarization).

## Deferred to a later architecture pass (kept out of the MVP on purpose)

| Item | Why deferred |
|---|---|
| **PyInstaller backend freeze + Tauri sidecar (Option B)** | True single-bundle distribution needs the FastAPI app (which spawns EDA subprocesses + touches a DB) frozen to a binary and registered as a Tauri `externalBin`, spawned on app start. Until then the user runs the Python server out-of-band. Auto-spawning uvicorn from the shell now would be a fragile env-specific shim (hardcoded python path, port races). |
| **Static `frontendDist` + `index.vite.html`→`index.html`** | Only relevant under Option B. Also requires reworking the server-side `ATLAS_BOOT_CONFIG` injection into a runtime `/api/boot-config` fetch so a static page can hydrate. |
| **Code signing + notarization** | macOS Gatekeeper requirement for public distribution; needs an Apple Developer cert. Confirm the real bundle `identifier` (currently placeholder `com.atlas.desktop`) before any signed build. |
| **CSP hardening** | `security.csp` is `null` for the MVP — the backend already ships its own asset policy + DOMPurify. A second restrictive CSP would block `/vendor` + the WebSocket; revisit with Option B. |
| **Mobile targets** | `lib.rs`/`gen` split is a mobile concern; desktop-only MVP omits it. |

## Decisions that need you before distribution

1. **Bundle identifier** — `com.atlas.desktop` is a placeholder, baked into the
   macOS bundle and painful to change later. Set the real reverse-DNS ID.
2. **Real app icon** — replace the generated solid-navy placeholder
   (`cargo tauri icon <512.png>` regenerates all sizes).
3. **Port** — confirm the backend port the shell should target (MVP assumes 3000).
