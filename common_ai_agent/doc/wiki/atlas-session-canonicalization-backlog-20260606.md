# Atlas Session Canonicalization Backlog 2026-06-06

## Decision

New Atlas UI session state should use one canonical filesystem layout:

```text
$ATLAS_PROJECT_ROOT/<user>/<workspace_session>/.session/<ip>/<workflow>/
```

For the common local workspace this means paths like:

```text
/Users/brian/Desktop/Project/NEW_WORKSPACE/brian/brian_session/.session/timer_new_concept/default/
```

The older layouts are legacy compatibility only and should not be used by new
features:

```text
$ATLAS_PROJECT_ROOT/.session/<owner>/<ip>/<workflow>/
$ATLAS_PROJECT_ROOT/.session/<owner>/<workspace>/<ip>/<workflow>/
$ATLAS_PROJECT_ROOT/.session/<ip>/<workflow>/
$ATLAS_PROJECT_ROOT/.session/<workflow>/
```

## Why This Matters

The mixed layouts make UI behavior look random:

- chat transcript can hydrate from one path while todo state comes from another
- slash commands can appear to run but write no visible todo
- cost/session files can be nested under `.session/<user>/<workspace>/...`
  while todo files live under `<user>/<workspace>/.session/...`
- legacy fallback can hide the actual missing canonical write

For locked-truth and workflow evidence this is especially risky because the
user expects one active IP/session to own the requirement, todo, transcript,
and generated artifact trail.

## Current Minimal Fix

The immediate fix is not to remove every legacy branch. It is to make new Web UI
command behavior write only to the canonical user/workspace session path.

The first concrete case is `/locked-truth-finalize`:

```text
/locked-truth-finalize
  -> default command registry
  -> todo template locked-truth-finalize
  -> <user>/<workspace>/.session/<ip>/<workflow>/todo.json
```

It must not emit `INJECT_TODO_TEMPLATE:...` as chat text, and it must not write
to `$ATLAS_PROJECT_ROOT/.session/<owner>/<ip>/<workflow>/todo.json`.

## Later Cleanup Project

Legacy removal should be a separate migration with focused tests, not an
opportunistic edit during UI debugging.

Suggested order:

1. Add a canonical session path helper shared by Atlas UI, API jobs, local chat
   store, worker IPC, command execution, cost tracking, and TodoTracker binding.
2. Convert session tests to assert the new layout:

   ```text
   <root>/<user>/<workspace>/.session/<ip>/<workflow>/
   ```

3. Remove or quarantine old fallbacks in readers only after canonical writers
   are proven.
4. Replace broad "newest non-empty transcript" style discovery with explicit
   `(user, workspace_session, ip, workflow)` resolution.
5. Add a migration/report script that detects legacy session directories and
   prints actionable moves rather than silently reading from them.
6. Only after the report is clean, delete legacy write paths.

## Guardrail

Fallback is acceptable for one thing only: read-only recovery/reporting of old
runs. It should not be used for new writes, command side effects, todo state,
locked-truth files, or signoff evidence.

## Resolved — SSOT import wrote to the non-session IP root (2026-06-08)

A concrete instance of the "new writes must use canonical per-session layout"
rule being violated.

- **Symptom**: `/api/ssot/import/upload` + the `/import` command stored evidence
  under the non-session `_ip_root(ip)` (`PROJECT_ROOT/<ip>`), while the file
  tree, chat worker, and `/to-ssot` read the per-session
  `<root>/<owner>/<workspace_session>/<ip>`. Imports were therefore invisible in
  the UI ("import이 아예 안 되는 느낌"), and `wiki/`+`yaml/` were scaffolded in
  the wrong root.
- **Frontend was fine** — `ssot-qa-board.tsx` / `ssot-review.tsx` already send
  `session`; the upload endpoint just ignored it.
- **Fix** (branch `fix/ip-roster-phantom-leak`): thread `base_root` (= session
  workspace root) through the import chain. Entry points:
  `api_ssot_import_upload` (resolve `_ssot_context_for_session` →
  `_validated_context_workspace_root`) and `_handle_import_command`
  (`_session_script_root(ip, client_session)`). All helpers take
  `base_root=None` (legacy-compatible). The `/import` command runs in the
  multi-session main server, so explicit `client_session` threading — not a
  pinned `PROJECT_ROOT` — is the only correct approach.
- **Migration script** (satisfies backlog item 5):
  `scripts/migrate_misscoped_import.py` — backup-first, `.trash` quarantine of
  the drained legacy dir, and rewrites embedded `<ip>/{req,wiki,yaml}/` path
  prefixes so downstream resolution still finds the moved files. It preserves
  the session's own live wiki (`_graph.json`, `_generated/`, `user/`) and only
  brings over the import outputs.
- **Test**: `tests/test_atlas_multiuser_session_scope.py::test_ssot_import_upload_lands_in_session_workspace`.
  Note: `/api/session/activate` does `os.environ.update(context.export_env())`,
  which leaks `ATLAS_IP_ROOT`/`ATLAS_ROOT`/`ATLAS_ACTIVE_SESSION` past
  monkeypatch into later tests — a separate latent isolation bug to fix.

## Session-blind HTTP route audit (2026-06-09)

Process model clarified: `ATLAS_MULTI_USER_PROC=1` (default) gives **process-per-session**
workers (env frozen at spawn), so agent/command/worker state is already isolated.
The residual risk is only the **single shared main web process**: HTTP routes that
resolve per-IP filesystem paths from global state instead of the request's session.

Audit of `src/atlas_ui.py` routes that touch per-IP FS:

- **FIXED** `POST /api/ssot/validate` — ran the verifier with `--root PROJECT_ROOT`
  (took only `ip` + `_active_ssot_ip()`, no session). Now reads `session`, resolves
  `_ssot_context_for_session` → `_validated_context_workspace_root`, and runs
  `--root <owner>/<ws>`. Frontend (`ssot-qa-board.tsx`) now sends `session` too.
  Test: `...::test_ssot_validate_targets_session_workspace`.
- **OPEN — design question** `POST /api/soc/{layout,connect,instance/add,instance/delete}`
  and `POST /api/ipxact/import`: all read/write a single global
  `PROJECT_ROOT/soc.ssot.yaml` (and `PROJECT_ROOT/<name>`), no session. This is a
  cross-tenant write surface **iff** SoC is meant to be per-user; if SoC composition
  is one global artifact per deployment, it is correct by design. Decide before fixing.
- **OPEN** `GET /api/workspace/tree`: scans `PROJECT_ROOT.iterdir()` — shows the shared
  root, not the caller's session workspace. Fine if admin/debug; fix if user-facing.
- **PARTIAL (known / in-progress)** `/api/ip/create`, `/api/ip/list`: session-scoped in
  multi-user; single-user `PROJECT_ROOT` fallback only. The `fix/ip-roster-phantom-leak`
  branch already hardens `/api/ip/list`.
- **CORRECT** import/upload, ssot/doc-feedback, doc-source, export, req/export, ip git/*.
