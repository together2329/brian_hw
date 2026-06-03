# Large single-file decomposition plan 2026-05-30 — Python backend split + legacy `.jsx` retirement

Prioritized, behavior-preserving plan to break up the biggest single files in
`common_ai_agent`. Companion pages: [[atlas-refactoring-exceptions]] (sub-1000-line
policy + the ≥1000-line registry + extraction-pattern catalogue), [[atlas-modular-refactor-status-20260528]]
(what's already been extracted from `src/atlas_ui.py` + the `scripts/atlas_jsx_integration_test.js`
verification rig), [[babel-retirement-cutover-20260529]] (the legacy-jsx/Babel
retirement track this plan's frontend workstream feeds into), and the overall
[[common-ai-agent-map]].

All line/mechanism claims below were verified by parallel `Explore` passes with
`file:line` citations on 2026-05-30. This page is a **plan**, not a status record —
it does not assert any of the work is done.

## Why

Several core files carry too many responsibilities, making review and change
risky. `src/atlas_ui.py` (10,440 lines) is dominated by a single `create_app()`
function of ≈9,250 lines; `core/tools.py` (8,302 lines) mixes 142 tool functions.
These are the live server's heart, so the work is scoped as **separate, small,
independently-shippable refactors** — never mixed with bug work — each preserving
behavior 100%.

## Measurement (first-party only; vendor/tests/gen-scripts excluded)

| File | Lines | Shape | Verdict |
|---|---|---|---|
| `src/atlas_ui.py` | 10,440 | `create_app()` single fn ≈9,250 lines; ~50 routes + WS handler nested | 🔴 continue extraction |
| `core/tools.py` | 8,302 | 142 top-level fns, 1 class; grab-bag | 🔴 cleanest split |
| `src/atlas_api_jobs.py` | 7,634 | already-extracted module (phase 6) | 🟢 leave |
| `src/llm_client.py` | 5,427 | 4 classes; `chat_completion_stream()` ≈1,100 lines | 🟡 extract helpers |
| `core/atlas_db.py` | 5,109 | single `AtlasDB` class, 148 methods (god-DAO) | 🟡 repository mixins |
| `src/headless_workflow.py` | 4,318 | 8 classes | 🟢 cohesive |
| `lib/textual_ui.py` | 4,237 | 23 classes, terminal TUI (still wired) | 🟢 cohesive |
| `core/slash_commands.py` | 3,914 | 1 registry class, 106 methods | 🟡 later |
| `src/main.py` | 3,286 | `chat_loop()` ≈1,500 lines | 🟡 extract helpers |
| `src/config.py` | 3,004 | env/profile/model/oauth/prompt mixed | 🟡 later |
| `src/atlas_api_soc.py` | 2,744 | already-extracted module | 🟢 leave |
| `core/react_loop.py` | 2,700 | `ReactLoopDeps` + agent loop | 🟢 intrinsic |

Legacy frontend (being discarded — see Workstream W): `frontend/atlas/workspace.jsx`
(13,366) + 34 sibling `.jsx` = 35 files, ≈44,041 lines. Every `.jsx` has a `.tsx`
twin; vite/`.tsx` is the default (`ATLAS_FRONTEND_MODE=vite`).

## Priority

| # | Target | Risk | Payoff |
|---|---|---|---|
| **P1** | `core/tools.py` split | low | high |
| **P3** | `src/llm_client.py` helper extraction | low | med (quick win) |
| **P2** | `src/atlas_ui.py` more `register_*_routes` | med | high |
| **W** | legacy `.jsx` retirement (−44k) | **gated** | very high |
| P4 | `src/main.py` `chat_loop()` | med | med |
| P5 | `core/atlas_db.py` mixins | med-high | med |

Recommended order: **P1 → P3 → P2(easy) → W-gate → W-delete → P2(medium/ssot) → P4 → P2(WS) → P5.**
Each step = one PR/commit, verified before the next.

---

## P1 — `core/tools.py` split (first)

Preserve the registration surface; move function families out.

- **Keep:** `AVAILABLE_TOOLS` dict (`tools.py:8107-8177`), `filtered_available_tools()`
  (`:8180-8197`; consumers `core/agent_server.py:1102`, `core/agent_runner.py:537`,
  `src/main.py:799,1346`), and the optional conditional-import block (`:8199-8302`).
- **New `core/tools_shared.py` (~250 lines):** module state + callbacks so families
  can import from one place — `_TODO_RUNTIME`(:62), `_git_lock`(:835),
  `_commit_llm_failures`(:836), `_MCP_MANAGER`(:8280); the 5 callbacks + setters
  (`:5889-6062`, e.g. `set_ask_user_callback` — injected by the server at boot, so
  position matters); shared helpers `_get_todo_tracker()`(:3227), `_get_jobs_dir()`(:5389),
  `_resolve_asset_path()`(:422), `scoped_todo_runtime()`(:74).
- **New family submodules:** `tools_file_ops` (read/write/replace + 10 fuzzy replacers,
  list_dir, grep_file, read_lines, find_files, read_doc), `tools_git`, `tools_rag`,
  `tools_todo`, `tools_agents`, `tools_jobs`, `tools_projects`, `tools_workflow`,
  `tools_ssot`, `tools_soc`, `tools_ask_user`.
- **`tools.py` becomes an aggregator:** imports family fns, builds `AVAILABLE_TOOLS`,
  keeps `filtered_available_tools()` + conditional imports. External import surface unchanged.
- **Verified tangles:** callbacks decouple families (no cross-family direct calls);
  `todo_*` share `_get_todo_tracker()` → must live in `tools_shared`.

**Verify:** `AVAILABLE_TOOLS` key set/count identical pre/post (diff), `import core.tools`
smoke, tool-related pytest green.

## P2 — `src/atlas_ui.py` route extraction (incremental)

Established pattern: 13 `atlas_api_*.py` already expose `register_*_routes(app, *, ...)`.
**Injection contract** (refs `atlas_api_jobs.py:4630`, `atlas_api_soc.py:40`; call sites
`atlas_ui.py:9195,4184`): pass live values as **callables** (`project_root=lambda: PROJECT_ROOT`
— `PROJECT_ROOT` is rebound by `--root` at `:10410`), shared mutable as **lock instances**,
immutables as-is; **kwarg names match the original create_app locals exactly** → route
bodies need zero textual edits.

Difficulty-ordered (one block → one new `atlas_api_*.py`):

| Order | Block | Routes (span) | Difficulty | create_app-local deps |
|---|---|---|---|---|
| 1 | settings | `/api/settings/*` (1827-1940) | easy | config mutation only |
| 2 | control-plane | stop/shutdown (1798-1825) | easy | `bridge` |
| 3 | version/health | (1649-2100) | easy | cost-cache (own lock) |
| 4 | admin | `/api/admin/*` (9403-9700+) | easy | `with AtlasDB()`, `_admin_required` |
| 5 | catalog/workspace-tree | (8464-8550) | easy | PROJECT_ROOT, SKIP_DIRS |
| 6 | conversation | `/api/conversation` (9113-9170) | easy | file I/O |
| 7 | todos | `/api/todos/*` (3657-3931) | med | `main.todo_tracker` → callback inject |
| 8 | git+IP | ip commit/log/graph/revert (3200-3440) | med | `_safe`, `_run_command` |
| 9 | IP create | `/api/ip/create` (3036-3180) | med | AtlasDB, bridge warmup, ssot helpers |
| 10 | soc layout | layout/connect/instance/ipxact (8593-8979) | med | PROJECT_ROOT, `_safe`, YAML lock |
| 11 | ssot import/export | (8025-8361) | **hard** | 17+ helper closures → extract helpers first |
| 12 | **WS handler + broadcaster** | `ws_agent`(9840), `_broadcast_outbox`(1312) | **hardest / defer** | see below |

**WS handler (12) — last + separate:** `broadcaster_task` is a `create_app()` nonlocal
(`:1213,1369`); `_queue_prompt_for_session`(:1218) closes over `bridge`(:1167). Moving to a
new `atlas_api_ws.py` needs the broadcaster reworked into a module-level factory.
⚠️ **Latent bug found, fix separately from extraction:** multi-client reconnect can make
`_ensure_broadcaster()`(:1368) spawn duplicate tasks → duplicate WS events.

**Verify (per block):** boot app + diff registered route-path set pre/post (must be equal),
smoke the endpoints. Beware live stale-build trap (rebuild + cache-buster + hard reload).

## P3 — `src/llm_client.py` `chat_completion_stream()` (quick win)

≈1,100 lines (`:3475-4587`), already ~60-70% delegated (`_execute_streaming_request`,
`_execute_streaming_request_responses`, `_build_responses_request_body`,
`_chat_completion_nonstream`). Extract the 3 inline regions:
- `_apply_rate_limit(...)` ← (3640-3650)
- `_prepare_messages_for_api(messages, config)` ← (3652-3781) cache/flatten/sanitize/strip pipeline
- `_build_api_request_config(model, config)` ← (3786-3811) url/headers/key/model resolve

Body ≈1,100 → ≈400 lines, control-flow only. Coupling risk ~0.
**Verify:** LLM streaming pytest + one live call smoke (stream text + usage unchanged).

## W — legacy `.jsx` retirement (⚠️ gated; feeds [[babel-retirement-cutover-20260529]])

Confirmed: `.tsx`↔`.jsx` trees are **runtime-independent** (0 `.jsx` imports in any `.tsx`;
boot config flows Python→HTML `<script>` at `atlas_ui.py:1499-1543`, not `.jsx`→window).
All 35 `.jsx` have `.tsx` twins.

**🚨 The one gate — no build guarantee:** `dist/` is git-ignored; CI runs `vitest` only,
**never `vite build`**, and nothing builds at startup. Legacy currently IS the fallback when
`_vite_index_html()` returns None. Deleting legacy without first guaranteeing a vite build at
runtime → blank app on fresh checkout / stale dist. So: **establish a real build step
(CI/startup/packaged dist) before any deletion** — this is a build-pipeline decision, not a shim.

Sequence: (1) build guarantee → (2) remove legacy fallback in `index()`(:1587-1611) +
`lobby()`(:1639-1641), replace with explicit error if dist missing → (3) delete dead Python
(`_inline_html_cached`:1442, `_html_with_atlas_boot_config`:1483, `_inject_scm_ui_override`:1433
+ `_scm_ui_override_*`:1385-1431, `_INLINE_INDEX_RE`:1380, `ATLAS_FRONTEND_MODE` branch) →
(4) delete 35 `.jsx` + legacy html (`index.html`, `lobby.html`, `preview.html`, test artifacts)
+ `vendor/babel.min.js` + legacy `__tests__/*.test.jsx`. Admin (`admin.html`/`atlas_admin.py`
inline path) handled separately if admin isn't yet on vite.
Note: this supersedes the parked [[workspace-jsx-decomposition-plan]] (no longer split — discard).
**Verify:** `npm --prefix frontend/atlas run build` + `npx vitest run`; `/` and `/lobby` render
from built dist with `ATLAS_FRONTEND_MODE` unset.

## P4 — `src/main.py` `chat_loop()` (later)

≈1,515 lines (`:1449-2964`). Pure-setup blocks extract cleanly:
`_init_chat_loop_state()`(1449-1610), `_setup_multiline_input()`(1642-1787),
`_get_user_input()`(1795-1890), `_handle_shell_command()`(1947-1977). The slash-result
dispatch table (2058-2749) is tangled with shared loop state → make it a strategy dict of
per-handler fns that **return state deltas** (`messages, agent_mode, context_tracker = handler(state)`).
**Verify:** loop smoke (input / slash / session-switch / model-switch) + pytest.

## P5 — `core/atlas_db.py` repository mixins (last)

Single `AtlasDB`, 148 methods, shared connection. Split into domain mixins
(`_UserRepoMixin`, `_SessionRepoMixin`, `_MessageRepoMixin`, `_WorkspaceRepoMixin`,
`_PermissionRepoMixin`) keeping `_execute/_connect/_fetchone` in the base. Invasive, lowest ROI.
(`AtlasDB()` init-overhead guard already applied.) **Verify:** DB pytest full pass + 1-time
schema-init guard regression-free.

## Operating rules

- Behavior-preserving; author and review in separate passes (`code-reviewer`/`verifier`).
- One commit per step; live server (atlas_ui / frontend) never mixed with bug work.
- Keep this page + code + tests + real-use notes in sync (per [[wiki-curation-policy]]).
- Reusable verification scripts go under `scripts/` (`.omc` is git-ignored).
- Run `python3 workflow/wiki/build_graph.py --check` after wiki edits.
