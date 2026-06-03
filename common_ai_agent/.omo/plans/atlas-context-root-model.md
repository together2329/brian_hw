# Atlas Context Root Model Plan

Created: 2026-06-03
Branch: `feat/atlas-context-root-model`

## Objective

Migrate ATLAS from the current implicit `PROJECT_ROOT + owner/ip/workflow`
layout to an explicit user/session/IP/workflow context model:

```text
ATLAS_ROOT/
  USER/
    SESSION/
      IP/
      .session/
        IP/
          WORKFLOW/
```

The worker should start inside the active IP directory, so ordinary tool calls
(`pwd`, `ls`, `make`, `rtl/foo.sv`) naturally operate on the active IP without
heuristic cwd injection.

## Target Contract

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
ATLAS_PROJECT_ROOT  = ATLAS_WORKSPACE_ROOT
ATLAS_ACTIVE_SESSION = ATLAS_CONTEXT_KEY
ACTIVE_WORKSPACE     = ATLAS_ACTIVE_WORKFLOW
ATLAS_SOURCE_ROOT    = runtime/import location only, never semantic cwd
```

## Key Decisions

- Keep `ATLAS_PROJECT_ROOT` as a compatibility alias first; do not delete it in
  the first implementation wave.
- Support both v1 session keys (`owner/ip/workflow`) and v2 keys
  (`user/session/ip/workflow`) through one parser.
- Add new launcher/UI concepts for `user` and `session`; do not silently change
  old `--session-id` semantics until tests cover both paths.
- Default `--root` to `~/ATLAS`, not cwd or `common_ai_agent`.
- Worker process cwd becomes `ATLAS_IP_ROOT` when IP is non-default and exists;
  otherwise it falls back to `ATLAS_WORKSPACE_ROOT`.
- Workflow wiki may be copied into the IP/session tree, but workflow execution
  scripts stay runtime/package details until a later package-entrypoint wave.
- No destructive migration of existing `.session` folders by default. Add read
  fallback first; provide an explicit migration command later if needed.

## Code Review Findings

- High: root/session construction is scattered. `src/atlas_ui.py` computes
  `PROJECT_ROOT` from cwd and many endpoints directly build
  `PROJECT_ROOT/.session/...`; this needs a central resolver before behavior
  changes.
- High: worker cwd does not match the target model. `core/session_process_manager.py`
  spawns `core.session_worker` with `cwd=str(self._project_root)`, while target
  behavior requires cwd to be the active IP root.
- High: frontend session parsing assumes v1 shape in several places. Helpers
  derive the active IP from the last two or fixed session segments; v2
  `user/session/ip/workflow` must not break file tree routing.
- Medium: todo/history/context are tied to `SESSION_DIR`, `TODO_FILE`, and
  `ATLAS_PROJECT_ROOT`. `/todo`, `/context`, todo display, and runtime todo
  events must be migrated with the path model.
- Medium: SCM and jobs use project-root/IP helpers. Git/Perforce roots and
  background job artifact manifests must resolve from `ATLAS_IP_ROOT`, not from
  source repo or shared root.
- Medium: `workflow-root` is still a script/runtime dependency in some paths.
  It can be removed from the user-facing context only after workflow commands
  stop requiring source-path scripts.

## Implementation Plan

### 1. Add Central Context Resolver

Files:
- `core/atlas_context.py`
- tests under `tests/`

Tasks:
- Extend the existing `SessionContext` into a v2-compatible `AtlasContext`.
- Add parser for:
  - v1: `owner/ip/workflow`
  - v2: `user/session/ip/workflow`
  - partial/default forms from URL/localStorage
- Add derived paths: `atlas_root`, `workspace_root`, `ip_root`, `session_dir`.
- Add env export/import helpers.
- Validate safe path segments once at the boundary.

Acceptance:
- `brian/s1/NEWIP_MCTP/default` derives `workspace_root=ROOT/brian/s1`,
  `ip_root=ROOT/brian/s1/NEWIP_MCTP`, and
  `session_dir=ROOT/brian/s1/.session/NEWIP_MCTP/default`.
- `brian/NEWIP_MCTP/default` still parses as v1 and maps through compatibility.
- Invalid path segments cannot escape root.

### 2. Launcher And Backend Bootstrap

Files:
- `scripts/run_atlas_desktop.sh`
- `src/atlas_runtime_run.py`
- `src/atlas_ui.py`

Tasks:
- Add `ATLAS_ROOT` default resolution:
  `--root` -> env -> persisted Desktop setting -> `~/ATLAS`.
- Add user/session inputs without breaking existing flags.
- Emit `ATLAS_ROOT`, `ATLAS_WORKSPACE_ROOT`, `ATLAS_IP_ROOT`,
  `ATLAS_SESSION_DIR`, and `ATLAS_CONTEXT_KEY`.
- Update `/healthz` to expose all resolved roots and the context key.
- Keep `project_root` in healthz as compatibility alias to workspace root.

Acceptance:
- Desktop dry-run with no `--root` reports `~/ATLAS`.
- Existing dry-run with `--root /tmp/root --ip IP --session-id brian` still
  generates a valid legacy context.
- Healthz clearly displays root/workspace/ip/session paths.

### 3. Worker Spawn And Tool Cwd

Files:
- `core/session_process_manager.py`
- `core/session_worker.py`
- `core/tools.py`
- `core/tools_verilog.py`

Tasks:
- Build worker env from the central context resolver.
- Spawn process workers from `ATLAS_IP_ROOT` when available.
- Set `PYTHONPATH`/runtime import path separately from cwd.
- Simplify `run_command` cwd semantics:
  - default cwd is current worker cwd
  - fallback cwd is `ATLAS_IP_ROOT`
  - legacy `<ip>/...` correction remains temporarily but is marked migration-only
- Make read/write/find path tools prefer `ATLAS_IP_ROOT` for relative IP paths.

Acceptance:
- Inside a v2 worker, `run_command("pwd")` returns `ATLAS_IP_ROOT`.
- `find_files(".")` lists IP files, not all workspace/user files.
- `read_file("yaml/IP.ssot.yaml")` resolves under active IP.
- Legacy `read_file("IP/yaml/IP.ssot.yaml")` still works during migration.

### 4. Session, Todo, Context, And Slash Commands

Files:
- `core/session_setup.py`
- `core/slash_commands.py`
- `src/config.py`
- `src/atlas_runtime_run.py`
- `lib/display.py`
- `lib/textual_ui.py`

Tasks:
- Replace direct `.session/<session>` construction with `ATLAS_SESSION_DIR`.
- Ensure `TODO_FILE`, `TODO_ERROR_FILE`, `HISTORY_FILE`, `COST_FILE`, and
  `SESSION_DIR` come from the resolved context.
- Update `/todo` to read/write the active context's todo file.
- Update `/context` root discovery to include workspace/IP/session roots and
  avoid treating `common_ai_agent` as user cwd.
- Update `/refresh-wiki` to use `ATLAS_IP_ROOT` plus runtime wiki tooling.

Acceptance:
- Two sessions under the same user can each have `NEWIP_MCTP/todo.json`
  independently.
- `/todo add`, `/todo`, and todo display do not leak across sessions.
- `/context` shows the active user/session/IP context and excludes source root
  unless explicitly needed for runtime diagnostics.
- `/refresh-wiki` defaults to the active IP and writes under that IP.

### 5. Frontend Session UI And Routing

Files:
- `frontend/atlas/app.tsx`
- `frontend/atlas/app-session-hook.tsx`
- `frontend/atlas/workspace-session-routing.tsx`
- `frontend/atlas/data.tsx`
- `frontend/atlas/data-loaders.tsx`
- `frontend/atlas/workspace-root-session-hook.tsx`
- `frontend/atlas/workspace-rootui-rail-tabs.tsx`

Tasks:
- Add session selector and `+ SESSION` UI.
- Display breadcrumb: `ROOT / USER / SESSION / IP / WORKFLOW`.
- Update route parser to understand v2 context.
- Update URL params to support `user`, `workspace_session`, `ip`, `workflow`,
  and full `session`.
- Keep legacy `session_id`, `ip`, `workflow` URL compatibility.
- Ensure file tree root follows `ATLAS_IP_ROOT` for the selected session.

Acceptance:
- Switching session changes the IP file tree root.
- Same user can open `s1/NEWIP_MCTP` and `s2/NEWIP_MCTP` independently.
- Existing `?session=brian/NEWIP_MCTP/default` links still load.
- `?session=brian/s1/NEWIP_MCTP/default` derives IP as `NEWIP_MCTP`.

### 6. File, SCM, Perforce, Jobs, And APIs

Files:
- `src/atlas_api_files.py`
- `src/atlas_api_sessions.py`
- `src/atlas_api_git.py`
- `src/atlas_api_jobs.py`
- `src/atlas_api_workspaces.py`
- `core/scm.py`
- `core/scm_perforce.py`

Tasks:
- Route file APIs through context-derived workspace/IP roots.
- Update `/api/session/*` history/state/list to use central session-dir resolver.
- Update Git/Perforce local root to active IP root by default.
- Keep explicit `scmRoot` override for Perforce workspaces.
- Update background jobs to record both workspace root and IP root.
- Ensure job artifacts and manifests write under the active IP root.

Acceptance:
- `/api/scm/status?ip=NEWIP_MCTP` returns `localRoot=.../brian/s1/NEWIP_MCTP`.
- Perforce pane can use `scmRoot` independently while local selected files are
  rooted in the active IP.
- Job dispatch for the same IP in two sessions writes to separate IP trees.
- `/api/session/history` can read both v1 and v2 session histories.

### 7. Legacy Fallback And Migration Safety

Tasks:
- Add v1 read fallback for existing `.session/<owner>/<ip>/<workflow>`.
- Add one-time UI warning when a v1 session is opened.
- Do not move old data automatically.
- Add optional migration command later:
  `atlas migrate-sessions --root ROOT --user USER --session SESSION`.

Acceptance:
- Existing sessions continue to display after the v2 parser lands.
- New sessions use v2 paths.
- No automatic deletion or relocation occurs.

### 8. Workflow-root De-scoping

Tasks:
- Remove `workflow-root` from user-facing Desktop docs/UI.
- Keep runtime/package path internal as `ATLAS_SOURCE_ROOT` or
  `ATLAS_RUNTIME_HOME`.
- Track remaining source-script dependencies explicitly.

Acceptance:
- Worker prompt/context does not present `common_ai_agent` as working cwd.
- Workflow wiki appears under the active IP/session.
- Any source-root usage is internal-only and visible in diagnostics, not in the
  workspace file tree.

## Test Strategy

### Unit Tests

- Context parser v1/v2/default/invalid segments.
- Derived path calculation for root/user/session/IP/workflow.
- Env export/import round trip.
- Frontend route parser:
  - `brian/NEWIP_MCTP/default`
  - `brian/s1/NEWIP_MCTP/default`
  - legacy URL params
  - v2 URL params

### Integration Tests

- `SessionProcessManager` spawns worker with cwd at IP root and env populated.
- `setup_session()` writes todo/history/cost under `workspace/.session/ip/workflow`.
- `run_command("pwd")` returns IP root.
- `read_file`, `write_file`, `find_files(".")`, and `grep_file` resolve from IP root.
- `/api/session/activate` sets v2 context and rejects cross-user session activation.
- `/api/session/history`, `/api/session/state`, `/api/session/list` support v2.
- `/todo` and `/context` operate on the active session only.
- `/api/scm/*` and `/api/git/*` return IP-local roots.
- Jobs dispatch writes artifacts under the active IP root.

### Frontend Tests

- Session dropdown renders, creates a session, and switches active context.
- File tree reloads when session changes even if IP id is the same.
- Header/breadcrumb displays root/user/session/IP/workflow.
- Existing tests for 3-part sessions remain green.

### Desktop Tests

- Dry run without `--root` uses `~/ATLAS`.
- Dry run with explicit root uses that root and does not hardcode local paths.
- URL contains canonical v2 session when user/session/IP/workflow are supplied.
- Existing `--session-id` behavior remains compatible.

### Product E2E

- Launch Desktop with default root.
- Create session `s1`, create/open IP `NEWIP_MCTP`, run `pwd`, inspect file tree.
- Create session `s2`, open same IP id, confirm independent empty/different tree.
- Add todo in `s1`, switch to `s2`, confirm todo isolation.
- Run SCM pane/status and a small job in both sessions; confirm roots differ.

## Review Checklist Before Implementation Is Considered Done

- No code path uses cwd as a semantic workspace root unless explicitly in a
  dev/debug fallback.
- `common_ai_agent` appears only as runtime/import/source root.
- Every path-bearing healthz/API response includes enough context to debug root,
  workspace, IP, and session separately.
- Multi-user authorization checks user and session scope.
- Existing v1 session histories remain readable.
- `ATLAS_PROJECT_ROOT` is only compatibility alias, not the new source of truth.
- Command plane, todo, context, SCM, jobs, and file APIs are covered by tests.
