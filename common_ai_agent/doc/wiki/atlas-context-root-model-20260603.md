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
no live worker for the active owner slot, the footer should show `Agent worker
failed · session worker failed`, not a green ready state. A live
`agent_state running` event still takes precedence so stale worker-status polling
does not hide `Agent responding`.

Verification recorded for this follow-up:

- `npm test -- __tests__/workspace-render-smoke.test.tsx` -> 28 passed.
- `npx tsc --noEmit` -> pass.
- `npm run build` -> pass.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest -q tests/test_atlas_multiuser_session_scope.py tests/test_production_parity.py::test_atlas_ui_direct_script_bootstraps_from_external_cwd` -> 44 passed.
- Web E2E on `127.0.0.1:3030`: idle failed footer appears, synthetic
  `agent_state running` shows `Agent responding`, and the old connected seed
  is absent.
- Desktop E2E with `open -na /Applications/ATLAS.app --args --backend-url ...`:
  login succeeds and the footer shows the same session-worker failure as the
  right rail.
