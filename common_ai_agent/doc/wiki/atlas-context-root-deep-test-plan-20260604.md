# Atlas Context Root Deep Test Plan

Date: 2026-06-04
Branch under test: `feat/atlas-context-root-model`
Primary design note: [[atlas-context-root-model-20260603]]

## Objective

Verify the user/session/IP/workflow context-root implementation end to end before
it is considered mergeable. The tester must prove that ATLAS no longer treats
`common_ai_agent` cwd or a root-level IP directory as the user's active
workspace, and that Web and Desktop both use:

```text
ATLAS_ROOT/
  USER/
    SESSION/
      IP/
      .session/
        IP/
          WORKFLOW/
```

Canonical expectations:

- `ATLAS_ROOT` defaults to `~/ATLAS` when Desktop is launched without `--root`.
- `ATLAS_WORKSPACE_ROOT = ATLAS_ROOT / USER / SESSION`.
- `ATLAS_IP_ROOT = ATLAS_WORKSPACE_ROOT / IP`.
- `ATLAS_SESSION_DIR = ATLAS_WORKSPACE_ROOT / ".session" / IP / WORKFLOW`.
- New writes must not create root-level `ATLAS_ROOT/IP` artifacts.
- New writes must not create `ATLAS_WORKSPACE_ROOT/.session/USER/SESSION/IP/WORKFLOW`.
  That longer path is legacy-read-only at most, not the v2 write target.
- Worker shell cwd for user tasks is `ATLAS_IP_ROOT`, while source imports use
  `ATLAS_SOURCE_ROOT` / workflow package paths internally.

## Pass Gate

All of these must pass before merge to `main`:

1. Backend regression tests pass.
2. Frontend unit/build tests pass.
3. Tauri/Desktop launcher tests pass.
4. Live HTTP API E2E passes on a fresh root.
5. Browser Web UI E2E passes using the Browser or Chrome UI automation path.
6. Desktop visual E2E passes using Computer Use.
7. DB rows, on-disk files, side panels, context/todo/chat, and worker/job logs
   all agree on the same `USER/SESSION/IP/WORKFLOW`.
8. No evidence is collected from a stale server, stale browser tab, or stale
   environment.

If Browser or Computer Use is unavailable, record the run as `blocked`, not
`passed`. Playwright can provide supplemental evidence, but it does not replace
the required Browser/Computer Use check.

## Preparation

Use a fresh root and explicit ports. Do not reuse `~/ATLAS` for destructive
checks.

```bash
git switch feat/atlas-context-root-model
git status --short

export ATLAS_E2E_ROOT="$(mktemp -d /tmp/atlas-context-root-deep.XXXXXX)"
export ATLAS_E2E_DB="$ATLAS_E2E_ROOT/atlas.db"
export ATLAS_E2E_PORT=49191
export ATLAS_E2E_ADMIN_PORT=49192

unset ATLAS_CONTEXT_KEY ATLAS_ACTIVE_SESSION ATLAS_WORKSPACE_ROOT
unset ATLAS_PROJECT_ROOT ATLAS_IP_ROOT ATLAS_SESSION_DIR ACTIVE_WORKSPACE
unset PROJECT_ROOT ATLAS_DESKTOP_ROOT ATLAS_DESKTOP_BACKEND_URL
```

Preflight fails if `git status --short` shows staged unrelated files. Unstaged
unrelated files may exist, but the tester must not revert them.

## Mode Matrix

Run the plan against these three topologies. Passing only one topology is not
enough.

| ID | Purpose | Required env and launch shape |
|---|---|---|
| A | Single-user Web/local-admin baseline | `ATLAS_MULTI_USER=0`, `ATLAS_ADMIN_LOGIN_REQUIRED=0`, explicit `--root $ATLAS_E2E_ROOT`, no auth cookies required |
| B | Multi-user auth isolation | `ATLAS_MULTI_USER=1`, fresh `ATLAS_DB_PATH`, two authenticated users `alice` and `bob`, same IP name in same workspace-session name |
| C | Desktop launcher and reconnect | `scripts/run_atlas_desktop.sh --prod`, explicit root and no-root `~/ATLAS` case, plus backend closed/restarted state |

For each topology, record:

- `ATLAS_ROOT`
- `PROJECT_ROOT`
- `ATLAS_CONTEXT_KEY`
- `ATLAS_ACTIVE_SESSION`
- `ATLAS_WORKSPACE_ROOT`
- `ATLAS_IP_ROOT`
- `ATLAS_SESSION_DIR`
- active `USER / SESSION / IP / WORKFLOW`

Topology B requires login cookies for each user. Use the existing auth test
helpers or UI login flow, but never reuse one user's cookie for another user's
request. Expected cross-user behavior is 403/404 for foreign session/IP/job
reads, not silent fallback to the caller's old state.

## Wave 1: Static Review

Review these files for direct path construction and stale-env behavior:

- `core/atlas_context.py`
- `core/atlas_context_paths.py`
- `src/atlas_ui.py`
- `src/atlas_api_sessions.py`
- `src/atlas_api_jobs.py`
- `core/agent_server.py`
- `scripts/run_atlas_desktop.sh`
- `frontend/atlas/app-session-hook.tsx`
- `frontend/atlas/workspace-root-session-hook.tsx`
- `frontend/atlas/workspace-root-data-hook.tsx`
- `frontend/atlas/main.tsx`
- `frontend/atlas/app.tsx`

Required checks:

- No user artifact path is derived from the repo cwd.
- `--workflow-root` is internal source/workflow code location only.
- `/api/session/activate`, `/healthz`, `/api/ip/list`, `/api/ip/create`,
  `/api/session/state`, `/api/session/history`, `/api/todos`,
  `/api/job/dispatch`, `/api/job/{id}/log`, Git, Perforce, and command routing
  all accept or derive workspace session scope.
- Single-user Desktop mode honors explicit `ATLAS_ROOT` even if
  `ATLAS_CONTEXT_KEY` is stale.
- Multi-user Web mode does not accept a stale exported `ATLAS_ROOT` that points
  outside the active server root.
- Job records use `project_root=ATLAS_ROOT/USER/SESSION` and
  `session_dir=.session/IP/WORKFLOW`.
- Job log fallback reads `job.session_dir` first, then legacy session paths.
- Vite actually loads the files under review. Confirm the live entry from
  `frontend/atlas/main.tsx` and avoid testing an inert mirror.
- `core/atlas_context.py` and `core/atlas_context_paths.py` agree for v2
  `USER/SESSION/IP/WORKFLOW` parsing, env export, workspace root, IP root, and
  session dir.

Static review fails if any new write path uses `.session/USER/SESSION/IP/WF`
under the workspace root, or if `PROJECT_ROOT` is used as a semantic user root
instead of a compatibility alias.

## Wave 2: Regression Tests

Run these from repo root:

```bash
python3 -m py_compile \
  src/atlas_ui.py \
  src/atlas_api_jobs.py \
  src/atlas_api_sessions.py \
  core/agent_server.py \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_api_pipeline_state.py \
  tests/test_pipeline_orchestrator_worker_integration.py

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_multiuser_session_scope.py \
  tests/test_atlas_api_pipeline_state.py \
  -q

PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py \
  tests/test_multiuser_job_isolation.py \
  tests/test_run_atlas_desktop_script.py \
  tests/test_session_worker_e2e.py \
  -q
```

Focused regressions that must exist and pass:

- Fresh user gets a default workspace session.
- Same user can create `s1` and `s2`.
- Same IP name in `s1` and `s2` creates separate trees.
- A new session does not list IPs from the previous session.
- `/api/session/activate` creates `ATLAS_ROOT/user/session/.session/ip/workflow`.
- `/api/ip/list?session_id=user/session` filters to that session.
- `/api/todos`, `/api/session/history`, `/api/session/state` are isolated by
  user and session.
- Single-user Desktop dispatch with stale `ATLAS_CONTEXT_KEY` still uses
  explicit `ATLAS_ROOT/user/session`.
- V2 job log reads `job.session_dir=.session/ip/workflow/conversation.json`.
- A request from another user/session cannot read, cancel, or list the job.
- Worker payloads carry `project_root=ATLAS_ROOT/user/session`.
- Worker cwd or command cwd is the active IP root, not the source repo.
- Multi-user auth creates `alice/default/SHARED_IP` and
  `bob/default/SHARED_IP`; neither user sees or reads the other user's IP,
  todo, history, cost, jobs, or worker status.
- Concurrent activation of `brian/s1/CONCURRENT_IP/default` and
  `brian/s2/CONCURRENT_IP/default` does not race environment variables into the
  other workspace root.
- Stale localStorage/session URL values are sanitized when the selected session
  does not contain the old IP.
- Backend closed and session-worker missing states do not render as green
  `agent ready`.

Frontend:

```bash
cd frontend/atlas
npm test -- --run \
  __tests__/app-session-switch-behavior.test.tsx \
  __tests__/submitmsg-dispatch.test.tsx \
  __tests__/workspace-render-smoke.test.tsx \
  __tests__/pipeline-render-smoke.test.tsx \
  __tests__/worker-orchestra-identity.test.tsx \
  __tests__/perforce-sync.test.tsx \
  __tests__/perforce-sync-navigation.test.tsx \
  --no-file-parallelism
npm run build
cd ../..
```

Tauri:

```bash
cd src-tauri
cargo test
cd ..
```

Desktop launcher dry run:

```bash
HOME="$(mktemp -d /tmp/atlas-home.XXXXXX)" \
ATLAS_DESKTOP_DRY_RUN=1 \
bash scripts/run_atlas_desktop.sh --prod --ip DRY_IP --workflow default
```

Expected dry-run evidence:

- It creates/uses `$HOME/ATLAS`.
- The backend command includes `--root $HOME/ATLAS`.
- The URL contains `session=<user>%2Fdefault%2FDRY_IP%2Fdefault`,
  `workspace_session=default`, and `ip=DRY_IP`.

## Wave 3: Live HTTP API E2E

Start a fresh local server:

```bash
ATLAS_AGENT_AUTOSTART=0 \
ATLAS_MULTI_USER=0 \
ATLAS_MULTI_USER_PROC=0 \
ATLAS_ADMIN_LOGIN_REQUIRED=0 \
ATLAS_DB_PATH="$ATLAS_E2E_DB" \
python3 src/atlas_ui.py \
  --host 127.0.0.1 \
  --port "$ATLAS_E2E_PORT" \
  --admin "$ATLAS_E2E_ADMIN_PORT" \
  --root "$ATLAS_E2E_ROOT" \
  --workflow-root "$PWD" \
  --session brian \
  --workspace-session default \
  --ip default \
  --workflow default \
  --exec s
```

Set `BASE=http://127.0.0.1:$ATLAS_E2E_PORT`.

Run this sequence and save every response:

1. `GET /healthz`
   - Expect `atlas_root=$ATLAS_E2E_ROOT`.
   - Expect current context `brian/default/default/default`.

2. Activate session `s1`:
   ```bash
   curl -sS -X POST "$BASE/api/session/activate" \
     -H 'Content-Type: application/json' \
     -d '{"owner":"brian","user_name":"brian","workspace_session":"s1","ip":"default","workflow":"default"}'
   ```
   Expected directories:
   - `$ATLAS_E2E_ROOT/brian/s1`
   - `$ATLAS_E2E_ROOT/brian/s1/.session/default/default`

3. Create IP `NEWIP_MCTP` in `s1` through `/api/ip/create`.
   - Expect `$ATLAS_E2E_ROOT/brian/s1/NEWIP_MCTP`.
   - Expect no `$ATLAS_E2E_ROOT/NEWIP_MCTP`.
   - `GET /api/ip/list?session_id=brian/s1` returns `NEWIP_MCTP`.

4. Activate session `s2` with `ip=default`.
   - `GET /api/ip/list?session_id=brian/s2` must not list `NEWIP_MCTP`.
   - File tree for `s2/default` must show "select IP" or empty IP state, not
     `s1` files.

5. Create the same IP name `NEWIP_MCTP` in `s2`.
   - Expect `$ATLAS_E2E_ROOT/brian/s2/NEWIP_MCTP`.
   - Verify `s1` and `s2` IP directories differ by inode/path and content.

6. Add todo in `s1/NEWIP_MCTP/default`; add different todo in
   `s2/NEWIP_MCTP/default`.
   - `GET /api/todos?session=brian/s1/NEWIP_MCTP/default` returns only s1 todo.
   - `GET /api/todos?session=brian/s2/NEWIP_MCTP/default` returns only s2 todo.

7. Switch workflow to `rtl-gen` in `s2`.
   - Expect `$ATLAS_E2E_ROOT/brian/s2/.session/NEWIP_MCTP/rtl-gen`.
   - `default` workflow history/todo remains separate.

8. Dispatch a mocked or local job if the test harness provides a worker.
   - Job response `session=brian/s2/NEWIP_MCTP/<workflow>`.
   - Job response `session_dir=.session/NEWIP_MCTP/<workflow>`.
   - Worker payload `project_root=$ATLAS_E2E_ROOT/brian/s2`.
   - Any command cwd/pwd evidence is `$ATLAS_E2E_ROOT/brian/s2/NEWIP_MCTP`.

9. Query DB:
   ```bash
   sqlite3 "$ATLAS_E2E_DB" '.tables'
   sqlite3 "$ATLAS_E2E_DB" \
     "select session_id, user_id, ip, workflow from runtime_sessions order by session_id;"
   sqlite3 "$ATLAS_E2E_DB" \
     "select name, workspace_id from ip_blocks order by name, workspace_id;"
   ```
   Expected rows include `brian/s1/...` and `brian/s2/...` without collapsing
   both sessions into one IP or one cost bucket.

10. Repeat with two authenticated users in topology B:
    - `alice/default/SHARED_IP/default`
    - `bob/default/SHARED_IP/default`
    - Both users create one todo and one chat/history entry.
    - Alice cannot read Bob's `/api/session/history`, `/api/todos`,
      `/api/ip/list`, `/api/jobs`, job log, or worker status by adding Bob's
      session id to query params.

11. Concurrent request guard:
    - In two shells, repeatedly activate `brian/s1/CONCURRENT_IP/default` and
      `brian/s2/CONCURRENT_IP/default` while calling `/api/ip/list`,
      `/api/session/state`, and `/api/todos`.
    - Expected: every response path remains under the requested workspace
      session. No response may flip to the other session after a neighboring
      request mutates process env.

HTTP E2E fails if a previous IP appears in a new session before it is created,
if cost/context from a previous session appears in the new session, or if any
artifact is written under source repo cwd.

## Wave 4: Web UI E2E

Use Browser or Chrome automation against the same server. Open:

```text
http://127.0.0.1:$ATLAS_E2E_PORT/?session=brian%2Fs1%2FNEWIP_MCTP%2Fdefault&session_id=brian&workspace_session=s1&ip=NEWIP_MCTP&workflow=default
```

Required visual assertions:

- Top bar order includes `USER`, `SESSION`, `+ SESSION`, `IP_ID`, `+ IP`,
  `WORKFLOW`.
- `USER=brian`, `SESSION=s1`, `IP_ID=NEWIP_MCTP`, `WORKFLOW=default`.
- Left file tree breadcrumb is `dir > NEWIP_MCTP`.
- File tree entries come from `$ATLAS_E2E_ROOT/brian/s1/NEWIP_MCTP`.
- Right side panel cost line includes the active user/IP, not `default` after
  a fresh IP creation.
- Footer must not show green `agent ready` if backend/session worker status is
  actually failed or closed.

Before the first assertion, clear browser state for this origin:

- cookies,
- localStorage,
- sessionStorage.

Then deliberately seed stale state once:

```javascript
localStorage.setItem("atlas.active.ip", "OLD_IP_FROM_LOCAL_STORAGE")
localStorage.setItem("atlas.active.session", "brian/s0/OLD_IP_FROM_LOCAL_STORAGE/default")
```

Reload with `session=brian/s2-ui/default/default`. Expected: the UI rejects the
stale old IP and renders select-IP/default state until a valid IP is created in
`s2-ui`.

Interactive sequence:

1. Click `+ SESSION`, create `s2-ui`.
   - The session dropdown changes to `s2-ui`.
   - The IP dropdown must not show `NEWIP_MCTP` from `s1`.
   - The file tree must show "select IP" or empty current session state.

2. Click `+ IP`, create `UI_DUP_IP`.
   - File tree shows `UI_DUP_IP`.
   - URL query updates to `session=brian/s2-ui/UI_DUP_IP/default`.
   - No `file tree error -- not found`.

3. Switch workflow `default -> rtl-gen -> sim_debug -> default`.
   - Chat transcript changes per workflow.
   - `No <workflow> worker transcript yet` is acceptable for a fresh workflow.
   - Old workflow chat must not remain visible as the active transcript.

4. In chat, run `/session`.
   - Response reports `brian/s2-ui/UI_DUP_IP/default`.

5. Run `/todo add ui session todo`, then `/todo`.
   - Todo appears in right TODO panel and chat response.
   - Switch to `s1`; the todo must disappear.
   - Switch back to `s2-ui`; the todo returns.

6. Run `/context` or a context-status command supported by the UI.
   - The response references the active session/IP.
   - It must not mention `common_ai_agent` as the active workspace root.

7. Ask `What is your active IP?`.
   - The answer must identify `UI_DUP_IP` without asking the user to provide an
     IP.
   - If the agent uses a tool, tool search scope must be active IP/session, not
     full repo `find_files("*.ssot.yaml", ".")` across every IP.

Record Browser screenshots after each session/IP switch and save network
responses for `/healthz`, `/api/session/list`, `/api/ip/list`,
`/api/session/state`, `/api/todos`, and `/api/session/worker/status`.

Network-level assertions:

- `/healthz.context_key` matches the top bar.
- `/api/session/list` contains only the caller's sessions.
- `/api/ip/list?session_id=<active user/session>` contains only that session's
  IPs.
- `/api/session/state?session=<active canonical>` uses the same session as the
  URL and top bar.
- `/api/session/worker/status?session_id=<active canonical>` must not report
  another user's active worker as this session's worker.

## Wave 5: Desktop E2E

Build first if the previous build is stale:

```bash
cd frontend/atlas && npm run build && cd ../..
cd src-tauri && cargo test && cd ..
```

Launch Desktop with explicit root:

```bash
bash scripts/run_atlas_desktop.sh \
  --prod \
  --root "$ATLAS_E2E_ROOT" \
  --session-id brian \
  --workspace-session desk-s1 \
  --ip DESK_IP \
  --workflow default \
  --port 3047 \
  --host localhost
```

Use Computer Use to inspect the ATLAS window. Required visual assertions:

- Window title is ATLAS.
- Top bar shows `USER brian`, `SESSION desk-s1`, `IP_ID DESK_IP`,
  `WORKFLOW default`.
- Left panel `dir > DESK_IP`; no `file tree error -- not found`.
- Right panel shows active user/IP/session context and does not show stale
  `default` after `DESK_IP` is selected.
- Footer state matches backend/session-worker state. If backend is closed, it
  says backend closed/input held, not green ready.

Desktop interactions:

1. Click `+ SESSION`, create `desk-s2`.
   - `DESK_IP` must not remain selected unless it also exists in `desk-s2`.
   - Old IPs from `desk-s1` must not appear in the `desk-s2` IP dropdown.

2. Create `DESK_IP` in `desk-s2`.
   - It creates `$ATLAS_E2E_ROOT/brian/desk-s2/DESK_IP`.
   - It does not modify `$ATLAS_E2E_ROOT/brian/desk-s1/DESK_IP`.

3. Switch workflows and verify transcript isolation as in Web.

4. Type a short prompt.
   - While sending, footer should show responding/backend connecting according
     to actual state.
   - It must not get stuck forever in `Backend connecting`.
   - If backend closes, input is held and auto-sends only when backend returns.

5. Close the Desktop window.
   - The launcher exits.
   - The port is no longer listening unless the run intentionally reused an
     external backend.

Backend unavailable state:

```bash
bash scripts/run_atlas_desktop.sh \
  --prod \
  --backend-url http://127.0.0.1:59999/?ip=BACKEND_DOWN \
  --session-id brian \
  --workspace-session closed \
  --ip BACKEND_DOWN \
  --workflow default \
  --no-start-backend
```

Expected Computer Use evidence:

- The UI says backend closed, backend unavailable, or input held.
- It must not say green `End of loop · agent ready`.
- Typing a prompt may hold input, but must not claim a worker response was sent.

Launch without `--root`:

```bash
HOME="$(mktemp -d /tmp/atlas-home.XXXXXX)" \
bash scripts/run_atlas_desktop.sh \
  --prod \
  --session-id brian \
  --workspace-session default \
  --ip HOME_ROOT_IP \
  --workflow default \
  --port 3048 \
  --host localhost
```

Expected:

- The backend root is `$HOME/ATLAS`.
- No artifact is created under `common_ai_agent`.
- UI shows `HOME_ROOT_IP` from `$HOME/ATLAS/brian/default/HOME_ROOT_IP`.

## Wave 6: Worker, Tool, Command, LSP, And SCM Checks

Run these in both Web and Desktop sessions:

- `pwd` through the agent/tool command path.
  - Expected: `ATLAS_ROOT/user/session/ip`.
- `ls` through the agent/tool command path.
  - Expected: IP-local files such as `yaml/`, `rtl/`, `wiki/`, not repo files.
- `Review SSOT`.
  - Expected: active IP SSOT is reviewed directly.
  - Failure: agent asks "which IP?" while UI has an active IP, or scans all
    repo IPs.
- `/todo add`, `/todo`, `/context`, `/session`, workflow dispatch, and job log.
  - Expected: all use the same active context.
- LSP/definition/reference command if available.
  - Expected: source file paths resolve inside active IP root or source root
    only when inspecting application code. IP artifact LSP must not default to
    `common_ai_agent`.
- Git tab.
  - Expected: local root is active IP root.
- Perforce tab/provider.
  - Launch with `--scm-provider perforce`.
  - Expected: Perforce UI is visible or reports a clear not-configured state.
    It must not disappear because session/IP root changed.

Validate each worker lane separately:

1. Interactive session worker.
   - Activate `user/session/ip/default`.
   - Send a prompt that runs `pwd`.
   - Expected cwd: `ATLAS_ROOT/user/session/ip`.
   - Expected conversation file:
     `ATLAS_ROOT/user/session/.session/ip/default/conversation.json`.

2. IPC/orchestrator job worker.
   - Dispatch `rtl-gen` or `ssot-gen`.
   - Expected job `project_root=ATLAS_ROOT/user/session`.
   - Expected job `session=user/session/ip/workflow`.
   - Expected job `session_dir=.session/ip/workflow`.
   - `/api/job/{id}/log` reads the same session dir.

3. Lazy HTTP worker if enabled.
   - Warm/dispatch two users with the same IP/workflow.
   - Expected distinct worker URLs or routing keys by user/session/IP/workflow.
   - No URL-scoped shared worker may write into another user's workspace.

## Wave 7: Negative Tests

Run these as explicit failure guards:

- Set stale `ATLAS_CONTEXT_KEY=brian/old/OLD_IP/default` before starting a
  single-user Desktop backend with explicit `--root`.
  - Dispatch must still use the explicit Desktop root.
- Start Web multi-user with a stale exported `ATLAS_ROOT` from another temp
  root.
  - Requests must use the server root, not the stale exported root.
- Try `session_id=brian/s1/OTHER_IP/default` while authenticated/active as a
  different user/session.
  - Expect 403 or sanitized fallback, never cross-session reads.
- Use path-like session/IP values such as `../x`, `a/b`, blank, and unicode
  separators.
  - Expect validation rejection or safe normalization.
- Open a stale URL with `ip=OLD_IP` that does not exist in the selected session.
  - UI must reset to select-IP/default state, not show `file tree error`.
- Kill backend after page load.
  - Footer/chat input must report backend closed/input held; it must not show
    green ready.
- Symlink/path escape:
  - Create a symlink inside one workspace pointing outside `ATLAS_ROOT`.
  - File APIs, Git, Perforce, job log, and workspace tree must not follow it
    into another session, another user, or the source repo.
- DB spoof:
  - Insert or mock a legacy ownerless job/session row.
  - Scoped `/api/jobs`, `/api/session/state`, and `/api/pipeline/state` must not
    attribute it to the active user unless it is explicitly legacy-readable for
    the same default workspace.

## Evidence Package

The tester must create:

```text
.omo/ulw-loop/evidence/atlas-context-root-deep-test-20260604.txt
.omo/ulw-loop/evidence/atlas-context-root-deep-test-web-20260604.md
.omo/ulw-loop/evidence/atlas-context-root-deep-test-desktop-20260604.md
.omo/ulw-loop/evidence/browser/<run-id>/*.png
.omo/ulw-loop/evidence/desktop/<run-id>/*.png
```

Each evidence file must include:

- exact git commit/branch,
- exact root/db/port,
- exact start command,
- screenshots or response JSON,
- DB query output,
- pass/fail table for every wave,
- blocker list with reproduction steps.

## Final Review And Merge Rule

After all waves pass:

```bash
python3 workflow/wiki/build_graph.py --check
python3 workflow/wiki/build_graph.py --root "$ATLAS_E2E_ROOT/brian/s1" --ip NEWIP_MCTP --check
git status --short
```

Then perform a code review against:

- root/session path consistency,
- worker cwd and command cwd,
- stale env handling,
- DB session/IP ownership,
- job/session_dir log fallback,
- frontend session/IP dropdown filtering,
- backend closed/ready footer status,
- Perforce/Git visibility,
- LSP/tool path roots,
- evidence completeness.

Only if Web and Desktop E2E both pass with Browser/Computer Use evidence should
the branch be merged into `main`. If any required UI automation is blocked,
commit the branch/evidence if useful, but do not merge to `main`.
