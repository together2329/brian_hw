# Atlas Context Root Model

Date: 2026-06-03
Branch: `feat/atlas-context-root-model`

## Decision

ATLAS should stop treating `common_ai_agent` cwd or an implicit
`PROJECT_ROOT/<ip>` layout as the worker's working context. The safer model is
an explicit user/session/IP/workflow context:

```text
ATLAS_ROOT/
  USER/
    SESSION/
      IP/
      .session/
        IP/
          WORKFLOW/
```

Target env contract:

```text
ATLAS_ROOT            = visible storage root, default ~/ATLAS
ATLAS_USER_NAME       = authenticated user or launcher --user
ATLAS_SESSION_ID      = user-visible workspace/session id
ATLAS_WORKSPACE_ROOT  = ATLAS_ROOT / ATLAS_USER_NAME / ATLAS_SESSION_ID
ATLAS_ACTIVE_IP       = selected IP id
ATLAS_ACTIVE_WORKFLOW = selected workflow id
ATLAS_IP_ROOT         = ATLAS_WORKSPACE_ROOT / ATLAS_ACTIVE_IP
ATLAS_SESSION_DIR     = ATLAS_WORKSPACE_ROOT / ".session" / ATLAS_ACTIVE_IP / ATLAS_ACTIVE_WORKFLOW
ATLAS_CONTEXT_KEY     = ATLAS_USER_NAME / ATLAS_SESSION_ID / ATLAS_ACTIVE_IP / ATLAS_ACTIVE_WORKFLOW
```

Compatibility during migration:

```text
ATLAS_PROJECT_ROOT   = ATLAS_WORKSPACE_ROOT
ATLAS_ACTIVE_SESSION = ATLAS_CONTEXT_KEY
ACTIVE_WORKSPACE     = ATLAS_ACTIVE_WORKFLOW
ATLAS_SOURCE_ROOT    = runtime/import location only
```

Worker processes should start with:

```text
cwd = ATLAS_IP_ROOT
```

That makes `pwd`, `ls`, `make`, `rtl/foo.sv`, and `yaml/foo.ssot.yaml`
naturally operate on the active IP without tool-level cwd injection.

## Why

The current model has three sources of confusion:

- `PROJECT_ROOT` can become the backend cwd, which may be `common_ai_agent`.
- Session identity currently looks like `owner/ip/workflow`, so it cannot
  distinguish same-user, same-IP, different test sessions.
- Tool calls are compensated by path heuristics, instead of starting the worker
  from the active IP root.

The v2 model isolates:

- different users,
- multiple sessions for the same user,
- same IP name in different sessions,
- todo/history/context state,
- worker shell cwd and IP artifacts.

## Code Review Findings

- High: root/session construction is scattered. `src/atlas_ui.py` computes
  `PROJECT_ROOT` from cwd and many endpoints directly construct
  `PROJECT_ROOT/.session/...`.
- High: worker cwd does not match the desired model. `core/session_process_manager.py`
  currently spawns workers from project root.
- High: frontend session parsing assumes the v1 3-part shape in routing helpers.
  `user/session/ip/workflow` needs a new parser before UI changes.
- Medium: `/todo`, `/context`, todo display, and runtime todo events all depend
  on `SESSION_DIR`, `TODO_FILE`, and `ATLAS_PROJECT_ROOT`.
- Medium: Git/Perforce and jobs route through project-root/IP helpers and need
  explicit `ATLAS_IP_ROOT` behavior.
- Medium: `workflow-root` can be removed from user-facing context, but runtime
  scripts still need an internal package/source path until workflow tools become
  package entrypoints.

## Implementation Plan

1. Add a central context resolver in `core/atlas_context.py`.
   - Parse v1 `owner/ip/workflow` and v2 `user/session/ip/workflow`.
   - Derive root/workspace/IP/session paths.
   - Export/import env.
   - Validate path segments once.

2. Update launcher/backend bootstrap.
   - Default root to `~/ATLAS`.
   - Add user/session inputs without breaking existing `--session-id`.
   - Expose `atlas_root`, `workspace_root`, `ip_root`, `session_dir`, and
     `context_key` from `/healthz`.

3. Update worker spawn and tool cwd.
   - Worker cwd becomes `ATLAS_IP_ROOT`.
   - `ATLAS_SOURCE_ROOT` remains runtime/import-only.
   - Simplify `run_command` cwd rules; keep legacy correction temporarily.

4. Migrate session, todo, context, and slash commands.
   - `setup_session()` uses `ATLAS_SESSION_DIR`.
   - `/todo`, `/context`, `/refresh-wiki` resolve through the central context.
   - Todo/history/cost files are isolated by user/session/IP/workflow.

5. Add session UI.
   - Top bar exposes `USER`, `SESSION`, `IP`, `WORKFLOW`.
   - `+ SESSION` creates a new workspace session.
   - File tree reloads when session changes, even if IP name is the same.

6. Update file APIs, SCM, Perforce, and jobs.
   - File APIs resolve from active workspace/IP roots.
   - SCM local root defaults to active IP root.
   - Perforce keeps explicit `scmRoot`.
   - Jobs record and use both workspace root and IP root.

7. Add legacy fallback.
   - Existing `.session/<owner>/<ip>/<workflow>` remains readable.
   - New sessions write v2 paths.
   - No destructive auto-migration.

8. De-scope `workflow-root` from user-facing UX.
   - Keep runtime/package path internal.
   - Do not present `common_ai_agent` as worker cwd.

## Test Method

Unit tests:

- v1 and v2 context parsing.
- derived paths and env round trips.
- frontend route parsing for legacy and v2 sessions.
- invalid path segment rejection.

Integration tests:

- worker spawn cwd is `ATLAS_IP_ROOT`.
- `run_command("pwd")` returns active IP root.
- `find_files(".")` lists active IP files only.
- `setup_session()` writes under `workspace/.session/ip/workflow`.
- `/api/session/activate`, history, state, and list work for v2.
- `/todo`, `/context`, `/refresh-wiki` stay session-local.
- Git/Perforce status and jobs use IP-local roots.

Frontend tests:

- session selector renders and switches.
- same IP id in two sessions shows different file trees.
- breadcrumb displays root/user/session/IP/workflow.
- existing 3-part session links still load.

Desktop/product E2E:

- Launch with no `--root`; verify default `~/ATLAS`.
- Create `s1/NEWIP_MCTP`, run shell `pwd`, inspect file tree.
- Create `s2/NEWIP_MCTP`; confirm independent files and todo.
- Run SCM pane/status and a small job in both sessions; confirm roots differ.

## Review Checklist

- No semantic workspace path is derived from `common_ai_agent` cwd.
- `ATLAS_PROJECT_ROOT` is compatibility alias only.
- Worker cwd, shell cwd, file tool root, file tree root, SCM local root, and job
  artifact root agree for the active IP.
- `/todo`, `/context`, slash commands, and runtime todo display use the active
  `ATLAS_SESSION_DIR`.
- Multi-user auth checks both user and session scope.
- v1 session histories remain readable.
- `/healthz` exposes enough path context to debug root mistakes quickly.

## 2026-06-03 UI Status Follow-Up

The top-level backend connection and the interactive session worker are separate
health concepts:

- Backend open means the page can talk to the ATLAS HTTP/WebSocket server.
- Session worker ready means the current user/session/IP/workflow has a live
  interactive agent lane.
- Workflow workers are separate orchestrator/job workers.

The workspace footer must not collapse those states into `End of loop · agent
ready`. The intended priority is:

1. backend missing/closed/error/auth required,
2. active command, ask_user, worker run, or live `agent_state running`,
3. interactive session worker failed/starting/capacity-wait,
4. backend connecting,
5. terminal worker progress,
6. idle ready.

This matches the right-side Agent panel: if `/api/session/worker/status` returns
`worker: null` for the active owner slot, the footer should show `Agent worker
failed · session worker failed`, not a green ready state. The endpoint's
`active_count` is global, so it must not make the current session look ready
when another user's worker is alive. A live `agent_state running` event still
takes precedence so stale worker-status polling does not hide `Agent
responding`.

Verification recorded for this follow-up:

- `npm test -- __tests__/workspace-render-smoke.test.tsx` -> 29 passed.
- Added a regression where `/api/session/worker/status` returns
  `active_count: 1` and `worker: null`; the footer still shows session-worker
  failure because the current owner slot has no live worker.
- `npx tsc --noEmit` -> pass.
- `npm run build` -> pass.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/test_atlas_multiuser_session_scope.py tests/test_production_parity.py::test_atlas_ui_direct_script_bootstraps_from_external_cwd` -> 44 passed.
- Web E2E on `127.0.0.1:3030`: idle failed footer appears, synthetic
  `agent_state running` shows `Agent responding`, and the old connected seed
  is absent.
- Desktop launcher E2E with
  `scripts/run_atlas_desktop.sh --prod --root /tmp/atlas-desktop-launcher-qa --ip QA_IP --workspace-session qa --session-id qa_user --workflow default --port 3046`:
  this earlier footer follow-up opened the absolute `ATLAS.app` path via
  `open -W -na ... --args --backend-url`, and the backend was cleaned up after
  the app process exited. The final C003 closure below supersedes the local
  Desktop backend host evidence with the corrected `localhost` default.
- Computer Use E2E on the ATLAS Desktop window: footer and right rail both show
  `Agent worker failed · session worker failed`, confirming the UI no longer
  reports a false green ready state.

## 2026-06-03 Session/IP Roster Follow-Up

The session selector is part of the context key, not a cosmetic label. The
intended active key is:

```text
user/workspace_session/ip_id/workflow
```

Creating a new workspace session must start at `default/default`; it must not
carry the previous session's `ip_id` or workflow. Otherwise the UI immediately
re-activates the old IP under the new session, making it look as if previous
session state or workers leaked.

The IP roster endpoint must also be scoped by `user/workspace_session`. A
request for `alice/s1/...` may return IPs from `alice/s1`, but not from
`alice/s2`. Owner-only requests such as `session_id=alice` remain a broad
compatibility view for older callers; top-bar, side-panel, Git/Perforce/SOC UI
surfaces should prefer the workspace-session-scoped form.

Regression evidence:

- `tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_per_user`
  creates `alice/s1/ip_alpha` and `alice/s2/ip_beta`; `/api/ip/list?session_id=alice/s1/default/default`
  returns only `ip_alpha`, and `/api/ip/list?session_id=alice/s2` returns only
  `ip_beta`.
- Web E2E on a temporary server at `127.0.0.1:3058`: loading
  `alice/s1/ip_alpha/default` requested `/api/ip/list?session_id=alice/s1` and
  set `window.IP_OPTIONS` to `["default", "ip_alpha"]`.
- Web E2E create-session flow: pressing `+ Session`, creating `s3`, and waiting
  for activation produced `ACTIVE_SESSION=alice/s3/default/default`,
  `ATLAS_WORKSPACE_SESSION_ID=s3`, `ACTIVE_IP=default`, and
  `IP_OPTIONS=["default"]`; no `ip_alpha`/`ip_beta` text remained on the page.
- Computer Use on the existing ATLAS Desktop window confirmed it was attached to
  a separate existing `127.0.0.1:3030` instance and now reports failed worker
  state honestly instead of green ready.

## 2026-06-03 Session Worker Status Scope Follow-Up

Interactive session workers may remain hot for old sessions so users can switch
back quickly, but the active UI must never read status from a previous
workspace session. The status request is now exact-scoped by the canonical
context key:

```text
/api/session/worker/status?session_id=user/session/ip/workflow
```

The backend validates the requested session owner against the authenticated
user before returning worker status. That prevents `alice/s1/...` from seeing
`bob/...`, and it prevents `alice/s1/...` from accidentally displaying the
latest `alice/s2/...` worker.

Regression evidence:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_session_worker_e2e.py -q`
  -> 3 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_owner_slot_switch.py tests/test_session_worker_e2e.py -q`
  -> 19 passed.
- `npm run test -- --run __tests__/workspace-render-smoke.test.tsx __tests__/agent-worker-status.test.tsx`
  -> 37 passed.
- `npm run build` -> pass.
- Web E2E on temporary server `127.0.0.1:37971`: after activating
  `alice/s1/ip_a/default` and `alice/s2/ip_a/default`, the frontend polled
  `/api/session/worker/status?session_id=.../s1/...` before the switch and
  `/api/session/worker/status?session_id=.../s2/...` after the switch. Direct
  status calls returned the matching worker session for both `s1` and `s2`;
  a cross-owner request returned 403. Screenshot:
  `.omo/ulw-loop/evidence/browser/atlas-session-status-e2e.png`.
- Computer Use was attempted against both installed ATLAS app paths, but the
  tool returned `cgWindowNotFound` / `remoteConnection` for this desktop window
  during this follow-up. The browser E2E above covered the Web UI status
  request path that the Desktop shell also loads from the backend URL.

## 2026-06-03 Session Switch IP Leak Fix

Two separate issues caused a new workspace session to look like it inherited
the previous session's IP:

- Frontend session switching preserved the current `activeIp` and workflow,
  so choosing a new session could immediately activate
  `user/new_session/old_ip/old_workflow`.
- In Desktop/single-user mode, `/api/ip/list?session_id=user/session` still
  scanned the root-level IP directory, so legacy or previous root IPs could
  appear in the new session's IP dropdown.

The fix is intentionally conservative:

- `selectSessionId()` now activates `user/session/default/default`.
- `/api/ip/list` scopes v2 session requests to
  `ATLAS_ROOT/user/workspace_session` even when `ATLAS_MULTI_USER=0`.
- Scoped desktop IP listing rejects symlinked `user/session` paths instead of
  following them into another session, another user, or outside `ATLAS_ROOT`.
- Workspace prompt dispatch now treats the active 4-part route as authoritative,
  so a prompt after switching to `user/new_session/default/default` does not
  fall back to the previous session's IP.
- Exact worker-status scoping remains: old session workers may stay hot for
  fast switching, but the UI asks status for the exact active
  `user/session/ip/workflow` and must not display/send input to another
  session's worker.

Latest regression evidence:

- `tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_in_desktop_mode`
  proves `legacy_ip` at root is not returned for `alice/s1` or `alice/s2`
  scoped IP list requests.
- `tests/test_atlas_multiuser_session_scope.py::test_ip_list_rejects_workspace_session_symlinks_in_desktop_mode`
  proves symlinked workspace-session roots are rejected with HTTP 400 and empty
  `items`.
- `frontend/atlas/__tests__/app-session-switch-behavior.test.tsx` mounts the
  real App, starts at `alice/s1/ip_alpha/rtl-gen`, switches the session select
  to `s2`, and verifies `alice/s2/default/default` plus IP options
  `["default", "ip_beta"]`.
- `frontend/atlas/__tests__/submitmsg-dispatch.test.tsx` verifies prompt input
  after a session switch is sent to `alice/s2/default/default`, not to stale
  `alice/s2/ip_alpha/default`.
- `frontend/atlas/__tests__/ip-roster-source.test.mjs` proves session select
  resets to `default/default`.
- Browser dropdown E2E switched from `alice/s1/ip_alpha/default` to `s2` using
  the real `select[aria-label="Workspace session"]`; the final state was
  `alice/s2/default/default`, and the IP options were only
  `["default", "ip_beta"]`.
- Test/build rerun:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_run_atlas_desktop_script.py tests/test_atlas_session_trace.py tests/test_session_worker_e2e.py ... -q`
  -> 22 passed;
  `npm run test -- --run __tests__/workspace-render-smoke.test.tsx __tests__/agent-worker-status.test.tsx __tests__/ip-roster-source.test.mjs __tests__/app-session-switch-behavior.test.tsx __tests__/submitmsg-dispatch.test.tsx`
  -> 55 passed;
  `npm run test -- --run --no-file-parallelism __tests__/workspace-render-smoke.test.tsx __tests__/agent-worker-status.test.tsx __tests__/ip-roster-source.test.mjs __tests__/app-session-switch-behavior.test.tsx __tests__/submitmsg-dispatch.test.tsx`
  -> 55 passed;
  `npm run test -- --run __tests__/app-session-switch-behavior.test.tsx __tests__/submitmsg-dispatch.test.tsx`
  -> 10 passed;
  `npx tsc --noEmit` -> pass;
  `npm run build` -> pass.
- Evidence file:
  `.omo/ulw-loop/evidence/atlas-context-root-session-ip-regression-20260603.md`.

## 2026-06-04 Worker CWD and Desktop C003 Follow-Up

Worker behavior on session switch:

- A workspace-session switch changes the current active context key to the new
  `user/session/ip/workflow`.
- The UI intentionally resets a new workspace session to
  `user/new_session/default/default`; it does not carry the old IP/workflow.
- An old session worker may remain hot in its own namespace so switching back
  is fast, but the current UI must not send input to it or read its status,
  costs, context, todo, or file tree data.
- Exact status polling remains
  `/api/session/worker/status?session_id=user/session/ip/workflow`.

Worker spawn is now covered by a runtime regression:

```text
tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root
```

That test verifies spawning `alice/s1/spi_core/rtl-gen` calls
`subprocess.Popen` with:

```text
cwd = ATLAS_ROOT/alice/s1/spi_core
ATLAS_WORKSPACE_ROOT = ATLAS_ROOT/alice/s1
ATLAS_PROJECT_ROOT = ATLAS_ROOT/alice/s1
ATLAS_IP_ROOT = ATLAS_ROOT/alice/s1/spi_core
ATLAS_SESSION_DIR = ATLAS_ROOT/alice/s1/.session/spi_core/rtl-gen
ATLAS_CONTEXT_KEY = alice/s1/spi_core/rtl-gen
ATLAS_ACTIVE_SESSION = alice/s1/spi_core/rtl-gen
```

The intended model is therefore: `common_ai_agent` is runtime/source root only;
worker commands run from the active IP root.

Latest verification:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root -q`
  -> 1 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_run_atlas_desktop_script.py tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root tests/test_session_worker_e2e.py::test_worker_status_uses_requested_v2_workspace_session -q`
  -> 6 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_run_atlas_desktop_script.py tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root tests/test_session_worker_e2e.py::test_worker_status_uses_requested_v2_workspace_session tests/test_atlas_session_trace.py -q`
  -> 18 passed.
- `cd frontend/atlas && npm run test -- --run __tests__/app-session-switch-behavior.test.tsx __tests__/submitmsg-dispatch.test.tsx --no-file-parallelism`
  -> 10 passed.
- `cd frontend/atlas && npx tsc --noEmit` -> pass.
- `cd frontend/atlas && npm run build` -> pass.

Desktop launcher dry-run verified:

- no `--root` uses `~/ATLAS`;
- explicit `--root` is propagated to the backend;
- backend URLs carry `workspace_session=s2` and canonical
  `session=alice/s2/NEWIP_MCTP/rtl-gen`;
- `--scm-provider perforce` propagates through
  `ATLAS_SCM_PROVIDER=perforce`.

At this point C003 still had an OS-level Desktop UI inspection gap. Computer
Use and macOS screen capture could not see an ATLAS window in that earlier
run:

```text
/Applications/ATLAS.app -> cgWindowNotFound
repo ATLAS.app -> remoteConnection, then cgWindowNotFound
bundle id com.atlas.desktop -> ambiguous because installed and repo app share it
screencapture -> wallpaper/background only, no positive ATLAS UI capture
```

That blocker was later closed in the final C003 Desktop closure section below.
Full C003 evidence, including the earlier failed attempts and the final pass,
is in `.omo/ulw-loop/evidence/atlas-context-root-desktop-e2e.md`.

### 2026-06-04 KST Worker Parent Guard Follow-Up

The session-switch symptom had one more backend lifecycle risk: worker
processes started with `start_new_session=True` could survive as PPID=1 if the
backend or an E2E server exited without graceful shutdown. That leaves stale
workers able to consume old queues or make a session look hot after the UI has
switched to another `user/session/ip/workflow`.

Follow-up fix:

- `SessionProcessManager.build_worker_env()` stamps
  `ATLAS_SESSION_WORKER_PARENT_PID`.
- `core.session_worker.run_worker()` exits before agent load if the stamped
  parent pid is already gone.
- running workers monitor the parent pid and request shutdown when the parent
  disappears.

Verification:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root tests/test_process_based_sessions.py::test_session_worker_exits_before_agent_load_when_parent_dead -q`
  -> 2 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions.py::test_session_process_manager_spawns_worker_from_project_root tests/test_process_based_sessions.py::test_session_worker_exits_before_agent_load_when_parent_dead tests/test_process_based_sessions.py::test_stop_all tests/test_process_based_sessions.py::test_spawn_prunes_orphan_same_session_worker tests/test_process_based_sessions_runtime.py::test_runtime_mode_spawn_cmd_and_env_route_to_runtime_db tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root tests/test_session_worker_e2e.py::test_worker_status_uses_requested_v2_workspace_session -q`
  -> 7 passed.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_run_atlas_desktop_script.py tests/test_process_based_sessions.py::test_session_worker_exits_before_agent_load_when_parent_dead tests/test_process_based_sessions_runtime.py::test_v2_workspace_session_worker_starts_in_active_ip_root tests/test_session_worker_e2e.py::test_worker_status_uses_requested_v2_workspace_session tests/test_atlas_session_trace.py -q`
  -> 19 passed.

Cleanup evidence:

- `.omo/ulw-loop/evidence/desktop/c003-temp-orphan-worker-scrub.txt`
  recorded 150 temp/pytest orphan workers terminated with SIGTERM,
  `sigkill_count=0`, `remaining_temp_orphans=0`.
- User-runtime workers under `~/.common_ai_agent` were left untouched.

## 2026-06-04 Per-User Orchestrator Worker Follow-Up

Orchestrator workflow workers are scoped by the full context key:

```text
user / workspace_session / ip / workflow
```

In multi-user mode, the worker snapshot and dispatch contract expose:

```text
worker_owner      = authenticated user name
workspace_session = selected workspace session
worker_session    = user/workspace_session/ip/workflow
worker_partition  = hashed db-user + worker_session partition
```

This is intentionally different from single-user mode. In single-user mode the
worker identity fields stay blank so the UI does not invent a fake user label.
In multi-user mode they must be present; otherwise two users can appear to share
one `ip/workflow` worker even when the backend is routing them separately.

Warm-pool and direct lazy-worker startup must use the same key. A worker that is
pre-started as `user/ip/workflow` is not equivalent to a dispatched worker
running as `user/workspace_session/ip/workflow`; it can write conversation/todo
state into the wrong session namespace.

The worker process must also start from the matching workspace root. For
`alice/alt/pl330/rtl-gen`, the process root is `ATLAS_ROOT/alice/alt`, not the
global repo root and not `ATLAS_ROOT/alice/default`. A warm worker whose session
is per-user but whose `project_root` is shared is still wrong because its
conversation, todo, and generated artifacts can land in the wrong workspace.

Route input rules for this key:

```text
ip:
  must be a valid IP identifier before warm scheduling starts

workspace_session:
  must be one path-safe segment
  path-like values such as ../bob, /bob, and alt/child fall back to default

legacy global-root jobs:
  visible only from the same user's default workspace
  not visible from another workspace session
```

Live HTTP E2E result:

```text
Atlas server:
  src/atlas_ui.py --port 50226

environment:
  ATLAS_MULTI_USER=1
  ATLAS_MULTI_USER_PROC=1
  ATLAS_WORKFLOW_WORKER_PER_USER=1
  ATLAS_WORKFLOW_WORKER_PER_SESSION=1
  ATLAS_WORKER_TRANSPORT=http
  ATLAS_LAZY_WORKERS=0

alice:
  owner   = alice
  session = alice/alt/pl330/rtl-gen
  url     = http://127.0.0.1:6511

bob:
  owner   = bob
  session = bob/alt/pl330/rtl-gen
  url     = http://127.0.0.1:5840

assertions:
  alice and bob worker URLs differ
  /api/job/dispatch sends alice to alice's URL
  /api/job/dispatch sends bob to bob's URL
  fake workers receive /run with the matching worker_session
  active worker snapshots do not show the other user's session
```

The test used external fake workers, so lazy worker startup was disabled. A
separate earlier attempt with lazy startup enabled failed because the lazy
launcher tried to start a real worker on the same port as the fake worker. That
was a test-harness conflict, not proof that the per-user routing contract is
wrong.

Follow-up live HTTP E2E also checked session artifacts:

```text
Atlas server:
  src/atlas_ui.py --port 51764

alice:
  worker URL = http://127.0.0.1:6585
  /run session = alice/alt/pl330/rtl-gen
  conversation = ATLAS_ROOT/alice/alt/.session/alice/alt/pl330/rtl-gen/conversation.json
  todo         = ATLAS_ROOT/alice/alt/.session/alice/alt/pl330/rtl-gen/todo.json

bob:
  worker URL = http://127.0.0.1:6271
  /run session = bob/alt/pl330/rtl-gen
  conversation = ATLAS_ROOT/bob/alt/.session/bob/alt/pl330/rtl-gen/conversation.json
  todo         = ATLAS_ROOT/bob/alt/.session/bob/alt/pl330/rtl-gen/todo.json

assertions:
  fake workers received the exact user/workspace/ip/workflow session
  dispatch created conversation.json and todo.json under each user's workspace root
  /api/jobs?workspace_session=alt did not leak the other user's run id
  active worker snapshots did not show the other user's session
  no Atlas/fake-worker process remained after cleanup
```

This still does not claim a real GPT-5.5 RTL generation run. It proves the
server/worker/session/artifact routing contract that a real worker run depends
on.

Current-code live HTTP E2E rerun:

```text
Atlas server:
  src/atlas_ui.py --port 56985

environment:
  ATLAS_MULTI_USER=1
  ATLAS_MULTI_USER_PROC=1
  ATLAS_WORKFLOW_WORKER_PER_USER=1
  ATLAS_WORKFLOW_WORKER_PER_SESSION=1
  ATLAS_WORKER_TRANSPORT=http
  ATLAS_LAZY_WORKERS=0
  ATLAS_WORKER_WARM_POOL=0
  ATLAS_MODEL=gpt-5.5
  ATLAS_WORKER_MODEL_RTL_GEN=gpt-5.5

alice:
  worker URL = http://127.0.0.1:6597
  session    = alice/alt/pl330/rtl-gen
  root       = ATLAS_ROOT/alice/alt
  artifacts  = ATLAS_ROOT/alice/alt/.session/alice/alt/pl330/rtl-gen

bob:
  worker URL = http://127.0.0.1:6128
  session    = bob/alt/pl330/rtl-gen
  root       = ATLAS_ROOT/bob/alt
  artifacts  = ATLAS_ROOT/bob/alt/.session/bob/alt/pl330/rtl-gen

assertions:
  worker URLs differ
  /api/orchestrator/workers runtime is restricted for non-admin callers
  /api/job/dispatch sends each user to the matching fake worker URL
  fake workers receive project_root = ATLAS_ROOT/user/workspace_session
  fake workers write conversation.json and todo.json below that root
  Alice's /api/jobs?workspace_session=alt response does not contain Bob's run
```

The rerun used fake workers for the worker `/health` and `/run` endpoints. It
exercises the real Atlas HTTP server, auth/session cookies, worker snapshot,
dispatch route, worker payload, and artifact path contract.

Real agent-server per-user worker E2E:

```text
test:
  tests/test_per_user_real_worker_e2e.py::test_job_dispatch_reaches_distinct_real_agent_server_workers_per_user

setup:
  real Atlas TestClient with Alice and Bob auth cookies
  real core.agent_server FastAPI worker app on Alice's computed per-user port
  real core.agent_server FastAPI worker app on Bob's computed per-user port
  worker ReAct body patched only to avoid live LLM calls

assertions:
  Alice and Bob compute different rtl-gen worker URLs
  Alice dispatch reaches Alice's real worker URL
  Bob dispatch reaches Bob's real worker URL
  worker /run payload carries session = user/alt/pl330/rtl-gen
  worker /run payload carries project_root = ATLAS_ROOT/user/alt
  both worker payloads carry model = gpt-5.5

result:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_per_user_real_worker_e2e.py -q
  -> 1 passed
```

This closes the "user 별로 떠야 한다" routing check at the real worker HTTP
surface. It still does not claim live GPT-5.5 RTL generation; it proves the
worker process selected for a real run is user/workspace scoped before the LLM
body starts.

Real `_run_react_task` session override check:

```text
test:
  tests/test_agent_server_session_override.py::test_run_react_task_writes_history_and_todo_under_request_project_root

setup:
  source root = /tmp/source
  worker request project_root = /tmp/alice/alt
  worker request session = alice/alt/pl330/rtl-gen
  ReAct loop patched only to avoid live LLM execution

assertions:
  SESSION_DIR = /tmp/alice/alt/.session/alice/alt/pl330/rtl-gen
  HISTORY_FILE = /tmp/alice/alt/.session/alice/alt/pl330/rtl-gen/conversation.json
  TODO_FILE = /tmp/alice/alt/.session/alice/alt/pl330/rtl-gen/todo.json
  files are not written under /tmp/source/.session/...

result:
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_agent_server_session_override.py -q
  -> 1 passed
```

This caught and fixed a real gap: `_run_react_task` previously based session
override files on the source root's `_project_root`. It now uses the request
`project_root`, so conversation and todo state follow the selected
`user/workspace_session/ip/workflow` worker.

Explicit worker session spoofing is also rejected. In multi-user mode, an
explicit `session` body field for `/api/job/dispatch` or
`/api/jobs/dispatch_many` must match the authenticated
`user/workspace_session/ip/workflow` session that the backend would generate.
For example, Alice dispatching with `session=bob/alt/pl330/rtl-gen` now returns
403 before a job is created, and `dispatch_many` reports a per-item
`session owner/workspace mismatch` error.

Worker `/run` also now checks the worker process boundary. If the worker was
started with `ATLAS_WORKSPACE_ROOT` or `ATLAS_PROJECT_ROOT`, a request
`project_root` must resolve under that boundary before the worker starts the
ReAct task. A request outside the worker workspace returns 403 and does not run.

Locked truth writes are guarded at the same HTTP worker surface. A sync `/run`
request that reaches a real worker and then mutates an approved
`req/*_requirements.md` file is reported as an error, and the locked requirement
file is restored under the request `project_root`.

Targeted verification after the per-user worker changes:

```text
python3 -m py_compile core/agent_server.py src/atlas_api_jobs.py \
  tests/test_agent_server_session_override.py \
  tests/test_per_user_real_worker_e2e.py
  -> pass

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_orchestrator_worker_identity_snapshot.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_pipeline_orchestrator_worker_integration.py::test_jobs_clear_only_removes_completed_jobs_visible_to_workspace \
  tests/test_pipeline_orchestrator_worker_integration.py::test_same_user_other_workspace_job_log_and_cancel_are_forbidden \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_progress_debug_scopes_same_user_jobs_by_workspace_session \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_http_worker_partition_includes_workspace_session \
  tests/test_pipeline_orchestrator_worker_integration.py::test_rootless_legacy_job_is_not_visible_cancelled_or_deduped_from_scoped_workspace -q
  -> 30 passed

cd frontend/atlas && npm test -- --run \
  __tests__/worker-orchestra-identity.test.tsx \
  __tests__/worker-snapshot-workspace-scope.test.tsx \
  __tests__/pipeline-render-smoke.test.tsx \
  __tests__/soc-architect-render-smoke.test.tsx
  -> 18 passed

cd frontend/atlas && npm exec tsc -- --noEmit
  -> pass

cd frontend/atlas && npm run build
  -> pass

ATLAS_RUNTIME_DB_MODE=session ATLAS_MULTI_USER=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_runtime_session_mode_e2e_f3.py -q
  -> 1 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py::test_v2_session_history_state_and_todos_use_workspace_session_root \
  tests/test_todo_session_binding.py \
  tests/test_atlas_session_trace.py -q
  -> 16 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_worker_warm_pool.py \
  tests/test_orchestrator_workers_route.py::test_workers_warm_route_uses_workspace_session_for_worker_jobs \
  tests/test_orchestrator_workers_route.py::test_workers_warm_route_rejects_path_like_workspace_session_by_falling_back_to_default \
  tests/test_orchestrator_workers_route.py::test_workers_warm_route_rejects_invalid_ip_before_scheduling \
  tests/test_orchestrator_workers_route.py::test_same_user_different_sessions_use_separate_worker_processes -q
  -> 12 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_orchestrator_worker_identity_snapshot.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_worker_warm_pool.py \
  tests/test_pipeline_orchestrator_worker_integration.py::test_jobs_clear_only_removes_completed_jobs_visible_to_workspace \
  tests/test_pipeline_orchestrator_worker_integration.py::test_same_user_other_workspace_job_log_and_cancel_are_forbidden \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_progress_debug_scopes_same_user_jobs_by_workspace_session \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_http_worker_partition_includes_workspace_session \
  tests/test_pipeline_orchestrator_worker_integration.py::test_rootless_legacy_job_is_not_visible_cancelled_or_deduped_from_scoped_workspace -q
  -> 46 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_agent_server_session_override.py \
  tests/test_per_user_real_worker_e2e.py \
  tests/test_worker_warm_pool.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_orchestrator_worker_identity_snapshot.py \
  tests/test_worker_ipc_dispatch.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_rejects_explicit_session_for_another_user \
  tests/test_pipeline_orchestrator_worker_integration.py::test_dispatch_many_rejects_explicit_session_for_another_workspace -q
  -> 62 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_agent_server_locked_truth_guard.py \
  tests/test_agent_server_session_override.py \
  tests/test_per_user_real_worker_e2e.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_orchestrator_worker_identity_snapshot.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_worker_ipc_dispatch.py \
  tests/test_worker_warm_pool.py -q
  -> 98 passed, 5 skipped
```

## Final C003 Desktop Closure

2026-06-04 KST follow-up closed the remaining C003 blocker and corrected the
Desktop evidence after a review found stale Terminal/window captures.

- Computer Use inspected the repo release app by full path:
  `src-tauri/target/release/bundle/macos/ATLAS.app`.
- The old `127.0.0.1` Desktop path showed a Tauri WebView bootstrap failure
  (`bootstrap failed: Importing a module script failed`). The launcher now
  defaults local Desktop backends to `localhost`; explicit `--host 127.0.0.1`
  remains supported and tested.
- Final launcher run used no `--host` argument, explicit root
  `/tmp/atlas-c003-final-default-host`, port `3047`, `--ip DESK_QA_IP`,
  `--workspace-session s1`, `--workflow rtl-gen`, and
  `--scm-provider perforce`.
- The Desktop UI showed canonical namespace
  `.session/2076604/s1/DESK_QA_IP/rtl-gen`, `USER=2076604`,
  `SESSION=s1`, `IP_ID=DESK_QA_IP`, `WORKFLOW=rtl-gen`, side panel
  `dir > DESK_QA_IP`, `PERFORCE/GIT/TODO` tabs, workflow switch
  confirmation, and session worker hot/alive.
- Closing the Desktop window made `open -W` return and port `3047` had no
  remaining listener.
- Worker parent monitor follow-up now covers dead parent, non-parent reparent,
  startup interrupt, monitor start failure, and live parent-change shutdown.

Evidence:

```text
.omo/ulw-loop/evidence/atlas-context-root-desktop-e2e.md
.omo/ulw-loop/evidence/desktop/c003-final-desktop-default-localhost-rtl-gen.png

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_run_atlas_desktop_script.py \
  tests/test_process_based_sessions.py \
  tests/test_process_based_sessions_runtime.py -q -ra
-> 37 passed in 6.92s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_agent_server_locked_truth_guard.py \
  tests/test_agent_server_session_override.py \
  tests/test_per_user_real_worker_e2e.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_orchestrator_worker_identity_snapshot.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_worker_ipc_dispatch.py \
  tests/test_worker_warm_pool.py -q -ra
-> 100 passed, 5 skipped in 22.86s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_todo_session_binding.py \
  tests/test_atlas_session_trace.py -q -ra
-> 61 passed in 12.07s

cd frontend/atlas && npm test -- --run \
  __tests__/app-session-switch-behavior.test.tsx \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/workspace-render-smoke.test.tsx \
  __tests__/ip-roster-source.test.mjs \
  --no-file-parallelism
-> 48 passed

cd frontend/atlas && npm test -- --run \
  __tests__/worker-orchestra-identity.test.tsx \
  __tests__/worker-snapshot-workspace-scope.test.tsx \
  __tests__/pipeline-render-smoke.test.tsx \
  __tests__/soc-architect-render-smoke.test.tsx \
  --no-file-parallelism
-> 18 passed

cd frontend/atlas && npx tsc --noEmit
-> pass

cd frontend/atlas && npm run build
-> pass, vite built in 1.49s

python3 workflow/wiki/build_graph.py --check
-> doc/wiki/_graph.json regenerated with broken_refs=0
```

## 2026-06-04 Final Isolation Refresh

The final review found a few late isolation gaps after the Desktop closure.
Those were fixed before commit:

- Pipeline state no longer merges ownerless legacy DB `workflow_runs` into an
  authenticated user's scoped workspace view. A legacy root-level run for the
  same IP/workflow must not make `user/session/ip/workflow` look failed.
- Active job dedupe now considers the request workspace root and user identity,
  so a scoped user's dispatch is not blocked by another user's ownerless legacy
  active job.
- Handoff list/save/take routes resolve the IP directory from the authenticated
  request's workspace/session root, not the process-global project root.
- `dispatch_workflow` tool calls recover user/session context from the
  orchestrator run id when the body omits it, and reject explicit session/db
  user spoofing with `session owner/workspace mismatch`.

Latest verification:

```text
python3 -m py_compile src/atlas_api_jobs.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_atlas_api_pipeline_state.py
-> pass

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_does_not_dedupe_against_other_user_legacy_job \
  tests/test_pipeline_orchestrator_worker_integration.py::test_handoff_routes_use_authenticated_workspace_session_root \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_state_hides_ownerless_legacy_db_runs_from_scoped_user \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_dispatch_workflow_tool_rejects_spoofed_session_owner -q -ra
-> 4 passed in 6.01s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_agent_server_locked_truth_guard.py tests/test_agent_server_session_override.py \
  tests/test_per_user_real_worker_e2e.py tests/test_orchestrator_workers_route.py \
  tests/test_orchestrator_worker_identity_snapshot.py tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py tests/test_worker_ipc_dispatch.py tests/test_worker_warm_pool.py \
  tests/test_atlas_api_pipeline_state.py -q -ra
-> 143 passed, 5 skipped in 28.04s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_run_atlas_desktop_script.py tests/test_process_based_sessions.py \
  tests/test_process_based_sessions_runtime.py -q -ra
-> 37 passed in 10.75s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py tests/test_todo_session_binding.py \
  tests/test_atlas_session_trace.py -q -ra
-> 61 passed in 28.04s

cd frontend/atlas && npm test -- --run \
  __tests__/app-session-switch-behavior.test.tsx \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/workspace-render-smoke.test.tsx \
  __tests__/ip-roster-source.test.mjs \
  --no-file-parallelism
-> 48 passed

cd frontend/atlas && npm test -- --run \
  __tests__/worker-orchestra-identity.test.tsx \
  __tests__/worker-snapshot-workspace-scope.test.tsx \
  __tests__/pipeline-render-smoke.test.tsx \
  __tests__/soc-architect-render-smoke.test.tsx \
  --no-file-parallelism
-> 18 passed

cd frontend/atlas && npx tsc --noEmit
-> pass

cd frontend/atlas && npm run build
-> pass, vite built in 5.22s

python3 workflow/wiki/build_graph.py --check
-> wrote doc/wiki/_graph.json: nodes=135 edges=608 types=6 tags=109 broken_refs=0
```

## 2026-06-04 Final3 Blocker Closure

A follow-up implementation review found three remaining session/root edge
cases. All were fixed before staging:

- Username-scoped dispatch no longer dedupes against ownerless legacy active
  jobs. Ownerless jobs are still visible only to legacy ownerless callers.
- Architect single-workflow dispatch no longer sends a synthetic
  `session=<ip>/<workflow>`. The backend derives the canonical
  `user/session/ip/workflow` session from `workspace_session`.
- Orchestrator-authored handoffs now store the canonical session owner segment
  in `handoff.scope.user_id`. This keeps `/api/pipeline/state`,
  `/api/handoff/list`, and `/api/handoff/take` aligned with the authenticated
  request scope instead of mixing DB UUID and username ownership.

Regression verification:

```text
python3 -m py_compile src/atlas_api_jobs.py src/orchestrator/react_bridge.py \
  tests/test_pipeline_orchestrator_worker_integration.py
-> pass

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_active_job_conflicts_excludes_ownerless_legacy_jobs_for_username_scope \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_bridge_handoff_uses_session_owner_for_request_scope \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_does_not_dedupe_against_other_user_legacy_job \
  tests/test_pipeline_orchestrator_worker_integration.py::test_handoff_routes_use_authenticated_workspace_session_root -q -ra
-> 4 passed in 2.99s

cd frontend/atlas && npm test -- --run \
  __tests__/soc-architect-render-smoke.test.tsx --no-file-parallelism
-> 7 passed in 7.85s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_does_not_dedupe_against_other_user_legacy_job \
  tests/test_pipeline_orchestrator_worker_integration.py::test_handoff_routes_use_authenticated_workspace_session_root \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_state_hides_ownerless_legacy_db_runs_from_scoped_user \
  tests/test_pipeline_orchestrator_worker_integration.py::test_orchestrator_dispatch_workflow_tool_rejects_spoofed_session_owner \
  tests/test_atlas_api_pipeline_state.py -q -ra
-> 38 passed in 32.02s

cd frontend/atlas && npm run build
-> pass, vite built in 12.56s

python3 workflow/wiki/build_graph.py --check
-> wrote doc/wiki/_graph.json: nodes=135 edges=608 types=6 tags=109 broken_refs=0
```

## 2026-06-04 Final5 Desktop Healthz Closure

Web/Desktop single-user mode exposed one more product-facing bug: `+ IP`
correctly created `ATLAS_ROOT/user/session/ip`, but `/healthz` treated the
local `local-admin` identity as an owner guard and rejected explicit
`session_id=user/session/ip/workflow` query hints. The UI then polled health as
`local-admin/default/default/default`, so the top bar/file tree could fall back
to `default` and show `file tree error -- not found`.

Fix:

- `/healthz` keeps strict owner filtering in multi-user mode.
- In Desktop/single-user mode, an explicit query `session_id` is accepted as
  the active context even when the fallback request user is `local-admin`.
- IP creation in single-user Desktop continues to use the owner/session hint
  from the create payload, so `+ IP` writes under
  `ATLAS_ROOT/user/session/ip` instead of the backend source/root directory.

New regression:

```text
tests/test_atlas_multiuser_session_scope.py::
  test_healthz_honors_query_session_root_in_single_user_desktop_mode
```

This first failed with:

```text
expected brian/s2/desktop_ip/default
actual   local-admin/default/default/default
```

Verification:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py::test_healthz_honors_query_session_root_in_single_user_desktop_mode \
  tests/test_atlas_multiuser_session_scope.py::test_ip_create_endpoint_uses_session_root_in_single_user_desktop_mode -q
-> 2 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_multiuser_session_scope.py -q
-> 48 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py tests/test_multiuser_job_isolation.py -q
-> 54 passed, 5 skipped

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_api_pipeline_state.py -q
-> 34 passed

cd frontend/atlas && npm test -- --run __tests__/submitmsg-dispatch.test.tsx --no-file-parallelism
-> 10 passed

cd frontend/atlas && npm run build
-> pass
```

Final command refresh after documenting the fix:

```text
python3 -m py_compile src/atlas_ui.py src/atlas_api_jobs.py \
  src/orchestrator/react_bridge.py tests/test_atlas_multiuser_session_scope.py \
  tests/test_pipeline_orchestrator_worker_integration.py
-> pass

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py tests/test_atlas_api_pipeline_state.py -q
-> 82 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py tests/test_run_atlas_desktop_script.py -q
-> 60 passed, 5 skipped

cd frontend/atlas && npm test -- --run __tests__/submitmsg-dispatch.test.tsx --no-file-parallelism
-> 10 passed

cd frontend/atlas && npm run build
-> pass

python3 workflow/wiki/build_graph.py --check
-> nodes=135 edges=608 broken_refs=0
```

Web E2E on `127.0.0.1:43123`:

- Registered/logged in `brian` through the real auth API.
- Used the visible `+ IP` modal to create `final5_web_ip`.
- Verified `/healthz?session_id=brian/s1/final5_web_ip/default` returned
  `active_session=brian/s1/final5_web_ip/default`,
  `project_root=ATLAS_ROOT/brian/s1`, and
  `ip_root=ATLAS_ROOT/brian/s1/final5_web_ip`.
- Verified `/api/files?path=final5_web_ip&session_id=...` returned the IP file
  tree.
- Switched workflow through the left rail to `rtl-gen`; health returned
  `brian/s1/final5_web_ip/rtl-gen`.
- Sent `/context` and `/todo`; both were handled in the active
  `brian/s1/final5_web_ip/rtl-gen` route.
- Clean authenticated final page had no network errors and no visible
  `file tree error`.

Evidence screenshots:

- `.omo/ulw-loop/evidence/browser/final5-web-session-root-e2e-fixed.png`
- `.omo/ulw-loop/evidence/browser/final5-web-workflow-context-todo-e2e.png`
- `.omo/ulw-loop/evidence/browser/final5-web-clean-authenticated-e2e.png`

Desktop/Computer Use note:

- `scripts/run_atlas_desktop.sh` dry-run builds the expected backend URL:
  `session=brian/s1/final5_web_ip/default`, `workspace_session=s1`, and
  `scm=perforce`.
- `tests/test_run_atlas_desktop_script.py` passed (`6 passed`).
- A new `/Applications/ATLAS.app` process launched with the 43123 backend URL,
  but macOS System Events reported `count of windows = 0`, and Computer Use
  returned `cgWindowNotFound` for `/Applications/ATLAS.app`, the repo release
  app path, and app name `ATLAS`.
- Therefore final Desktop visual inspection was blocked by the current
  app-window/automation state, not by the backend/session-root path. The
  launcher/backend URL and WebView target route are recorded in
  `.omo/ulw-loop/evidence/atlas-context-root-desktop-e2e.md`.

## 2026-06-04 Final6 Root/Session Refresh

One more order-dependent backend bug was fixed after the final5 recheck.
`/api/session/activate` mutates process-level `ATLAS_ROOT`; if a later request
arrived with a current `ATLAS_CONTEXT_KEY` but a stale exported `ATLAS_ROOT`,
job and pipeline-state helpers could resolve the wrong root. The fix in
`src/atlas_api_jobs.py` makes `_atlas_root_for_jobs()` prefer the current
request/runtime `project_root()` when the active context and exported root
disagree, while still honoring explicit Desktop `ATLAS_ROOT` launches when no
request-context conflict exists.

Regression proof:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py::test_session_activate_policy_and_mode_sweep_keeps_namespace_todos_isolated \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_state_isolates_handoffs_by_authenticated_user -q -s
-> 2 passed in 1.58s

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_job_dispatch_uses_session_root_in_single_user_desktop_mode -q
-> 1 passed in 1.10s
```

Final6 Web E2E used the live server at `127.0.0.1:49191` with root
`/private/tmp/atlas-context-root-e2e/root.bGeEdY`. The in-app Browser connector
was unavailable, so Playwright was used against the real Web UI. In
single-user/no-login mode the effective owner is `local-admin`, so the correct
fixtures are under `ATLAS_ROOT/local-admin/<session>`. The Web UI then passed:

- `local-admin/s1/CTX_E2E/default` loaded with session `s1` and IP `CTX_E2E`;
- creating session `s3` reset to `local-admin/s3/default/default`;
- `CTX_E2E` did not leak into the new `s3` IP dropdown;
- creating `CTX_NEWUI` wrote only
  `ATLAS_ROOT/local-admin/s3/CTX_NEWUI`, with no legacy root-level IP;
- workflow switch selected `local-admin/s3/CTX_NEWUI/ssot-gen`;
- `/todo` and `/context` stayed scoped to that active route.

Evidence:

```text
.omo/ulw-loop/evidence/atlas-context-root-http-e2e.txt
.omo/ulw-loop/evidence/atlas-context-root-browser-e2e.md
.omo/ulw-loop/evidence/browser/final6-web-result.json
.omo/ulw-loop/evidence/browser/final6-web-command-result.json
```

Final command verification after documentation refresh:

```text
python3 -m py_compile src/atlas_ui.py src/atlas_api_jobs.py core/agent_server.py \
  tests/test_atlas_multiuser_session_scope.py tests/test_atlas_api_pipeline_state.py \
  tests/test_pipeline_orchestrator_worker_integration.py
-> pass

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py tests/test_atlas_api_pipeline_state.py -q
-> 85 passed

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py tests/test_run_atlas_desktop_script.py -q
-> 61 passed, 5 skipped

cd frontend/atlas && npm test -- --run \
  __tests__/submitmsg-dispatch.test.tsx __tests__/workspace-render-smoke.test.tsx \
  __tests__/pipeline-render-smoke.test.tsx __tests__/soc-architect-render-smoke.test.tsx \
  __tests__/worker-orchestra-identity.test.tsx --no-file-parallelism
-> 5 files passed, 58 tests passed

cd frontend/atlas && npm run build
-> pass

cd src-tauri && cargo test
-> 3 passed

python3 workflow/wiki/build_graph.py --check
-> broken_refs=0
```

Final6 Desktop visual recheck remains blocked in the current automation
environment. `/Applications/ATLAS.app` and the repo release app both launched
processes, but macOS reported zero windows and Computer Use returned
`cgWindowNotFound` or bundle ambiguity. Backend/launcher evidence and
`src-tauri` unit tests still pass, but this latest Desktop visual attach does
not satisfy a fresh "Web + Desktop" E2E gate. The branch should not be merged to
`main` on the basis of the final6 refresh unless the Desktop window attach is
rerun successfully or the earlier corrected C003 Desktop proof is explicitly
accepted as the release gate.

## 2026-06-04 Session IP Dropdown Isolation Patch

Chrome/Computer Use found one additional frontend isolation bug after the
root/session model was already in place. When the user switched workspace
session, `activateNamespace()` updated the active namespace to
`<user>/<new-session>/default/default`, but the IP dropdown kept the previous
session's `ipOptions` until the scoped `/api/ip/list` response returned. A slow
or out-of-order roster request could also let an older scope update the current
dropdown after a newer switch.

Patch:

- `frontend/atlas/app.tsx`: on owner/workspace-session scope changes, reset
  `ipOptions` and `window.IP_OPTIONS` to `["default"]` immediately.
- `frontend/atlas/app-session-hook.tsx`: add a refresh epoch guard around
  `/api/session/list` and `/api/ip/list`, so stale responses from an earlier
  scope cannot write the current roster.
- `frontend/atlas/app-auth-hook.tsx`: when `/api/users/me` rebinds the browser
  from a stale owner to the authenticated owner, clear `ipOptions` and
  `window.IP_OPTIONS` to `["default"]` before the new owner's scoped roster
  resolves.
- `frontend/atlas/app-session-hook.tsx`: also validate the owner/workspace
  roster scope at response-application time and invalidate in-flight roster
  refreshes whenever backend context events move the UI to a different
  workspace session.
- `frontend/atlas/__tests__/app-session-switch-behavior.test.tsx`: regression
  test keeps the new session's IP dropdown at `["default"]` while the scoped
  roster request is intentionally held, then accepts `ip_beta` only after the
  `alice/s2` response resolves. Follow-up regressions cover stale owner
  rebinding (`alice -> bob`) and a late old `alice/s1` roster response after
  backend context switches to `alice/s2`.

Verification:

```text
cd frontend/atlas && npm test -- --run __tests__/app-session-switch-behavior.test.tsx
-> 4 passed

cd frontend/atlas && npm test -- --run \
  __tests__/ip-roster-source.test.mjs __tests__/app-session-switch-behavior.test.tsx
-> 9 passed

pytest -q \
  tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_in_desktop_mode \
  tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_per_user
-> 2 passed

cd frontend/atlas && npm run build
-> pass
```

Additional focused verification on 2026-06-04 KST:

```text
pytest -q \
  tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_in_desktop_mode \
  tests/test_atlas_multiuser_session_scope.py::test_ip_list_scopes_v2_workspace_session_per_user
-> 2 passed
```

Computer Use on the live Chrome page verified:

- before switch: `USER brian`, `SESSION hi`, `IP_ID jjj`,
  `.session/brian/hi/jjj/default`;
- switch to `SESSION default`: URL/topbar/sidebar/live divider all changed to
  `.session/brian/default/default/default`, and `IP_ID` reset to `default`;
- switch back to `SESSION hi`: `IP_ID` first reset to `default`, then scoped
  `hi` IP options appeared.
- after the follow-up patch, the live `brian/hi` IP dropdown showed only
  `default`, `jjj`, `real_ip`, and `uart`.

Important data note: `SESSION hi` currently shows `jjj`, `real_ip`, and `uart`
because those directories exist under `ATLAS_ROOT/brian/hi/`. That is same
user+same session data, not a cross-user/session code leak. The old `default`
session also contains many legacy IPs because historical namespaces are mapped
to `workspace_session=default`; cleaning that data is a separate migration or
operator cleanup policy, not this frontend race fix.
