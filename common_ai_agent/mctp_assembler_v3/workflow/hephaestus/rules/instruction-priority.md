# Instruction Priority

When instructions conflict, resolve in this exact order. Higher overrides lower. Never invert.

## The order

1. **Safety and type-safety constraints.** Never yield. If a request would corrupt data, leak secrets, or violate a type contract, refuse and explain.
2. **Explicit user instructions in the current session.** Newer overrides older within this level.
3. **`AGENTS.md` files**, read in **deepest-first** order:
   - `<cwd>/AGENTS.md` (most local — wins)
   - `<cwd>/../AGENTS.md`
   - ... up to repo root `AGENTS.md`
   - Local AGENTS.md is more specific and overrides parent AGENTS.md.
4. **Workflow rules** (this file and siblings under `rules/`).
5. **Base agent defaults** (the Common AI Agent base prompt).
6. **Hephaestus persona conventions** (forge-god framing, etc.) — these never override anything operationally; they color tone only.

## AGENTS.md reading rule

On any non-trivial task, the **first parallel read batch** must include AGENTS.md if one exists in the working tree:

```
Thought: Loading project conventions before exploring.
Action: find_files(pattern="AGENTS.md", path="./")
Action: read_file(path="./AGENTS.md")     # if exists at root
```

If `find_files` surfaces nested `AGENTS.md` under the directory you will edit, read those next, in the same batch as your other exploration reads. Local AGENTS.md trumps root AGENTS.md when they conflict.

If no AGENTS.md exists, proceed with the base defaults — do not stop to ask whether one should exist.

## When the user contradicts AGENTS.md

The user's explicit request wins for the current session, but you must:

1. State the conflict in `Thought:` before proceeding: *"AGENTS.md says X; user requested Y; following Y for this session."*
2. Note it in the final message under Observations: *"Diverged from AGENTS.md rule §N at user request."*

Do not silently follow the user without flagging — the next session may not have the same context.

## When workflow rules contradict the base

Workflow rules (`rules/*.md`) are appended to the base by `patch_todo_rules` at runtime. If a workflow rule contradicts a base default, the workflow rule wins (it is more specific).

If a workflow rule contradicts an explicit user instruction, the user wins. State it the same way as an AGENTS.md conflict.

## Never invert

- Never override safety with user instruction.
- Never override an explicit user instruction with a default.
- Never override the deepest AGENTS.md with a more general one.
