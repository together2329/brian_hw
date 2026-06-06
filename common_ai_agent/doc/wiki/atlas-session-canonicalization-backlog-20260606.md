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
