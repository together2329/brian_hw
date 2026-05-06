# Evidence Required Before Declaring Done

A task is complete when there is **on-disk or runtime evidence** that the change is correct, not when you believe the change is correct.

## The evidence ladder

Apply the strongest evidence the situation supports. Stop at the highest level you can reach.

### Level 1 — Read-back (minimum, always required)

After every `write_file` / `replace_in_file`, re-read the changed region with `read_file` or `read_lines` to confirm the diff landed as intended.

Why: `write_file` and `replace_in_file` can fail silently in edge cases (path typo, locked file, partial write). The read-back is the only proof the disk state matches your intent.

### Level 2 — Static check

If the language has a static checker (type checker, linter, formatter), run it on the changed file with `run_command`. Capture exit code.

Examples:
- Python: `mypy <file>` / `ruff check <file>`
- TypeScript: `tsc --noEmit` / `eslint <file>`
- Verilog: `verilator --lint-only <file>`
- Generic: project's own `make lint` / `npm run lint`

### Level 3 — Build

If the project has a build step, run it. Exit code 0 is required.

`run_command("make")` / `run_command("npm run build")` / etc.

### Level 4 — Test

Run the test that covers the changed code path. Start narrow (the specific test for the function you changed), widen to the file-level suite if confidence is needed.

Capture the pass/fail count and any new failures. **Pre-existing failures are NOT yours to fix** — note them in the final message under Observations, but do not let them block declaring your task done.

### Level 5 — Manual run

When the change is user-visible or runnable (CLI flag added, endpoint added, output format changed), actually run the program and observe the output.

`run_command("./tool --new-flag")` and capture the result.

Why: types and tests catch logic errors against asserted invariants. They miss surprises in the *unasserted* surface — UX, output format, exit codes, log shape.

## What does NOT count as evidence

- Your prose. "The change should work" / "This will fix it" is not evidence.
- A successful `write_file` Action with no read-back.
- A `[MAS RESULT] DONE` from a sub-workflow with no `run_command` or `read_file` confirming the artifacts.
- Exit code 0 from an unrelated command (e.g. `ls` succeeds — that does not mean your build passed).
- A green status that came from skipping the failing test.

## Required evidence before `todo_update(status="completed")`

For every task in the todo list, before transitioning to `completed`, the conversation must contain:

- At least one Level 1 read-back of every file you wrote or edited.
- At least one Level 2-5 verification appropriate to the task type:
  - Code change → Level 2 minimum, Level 4 strongly preferred.
  - Build/config change → Level 3 minimum.
  - User-visible feature → Level 5 required.
  - Documentation-only change → Level 1 sufficient.

If the conversation does not contain that evidence, do not mark `completed`. Run the verification first.

## Recording evidence in `tool_output`

Use `tool_output` to capture the verdict, not your interpretation:

Good:
```
todo_update(
  index=N,
  status="completed",
  tool_output="ruff: 0 errors. pytest tests/test_foo.py: 12 passed in 0.34s. Manual run with --new-flag emitted expected JSON shape."
)
```

Bad:
```
todo_update(
  index=N,
  status="completed",
  tool_output="implemented and verified"
)
```

The first is auditable. The second is hallucination-prone — the next compression pass cannot tell whether evidence exists.

## CLAIMED vs VERIFIED in the final message

In the final message's Verification section, distinguish:

- **VERIFIED**: backed by tool output captured in this session. Cite the command and the verdict line.
- **CLAIMED** (use sparingly, only when verification is impossible): explain why verification could not be done (test infra unavailable, manual smoke test requires a deployed env, etc.) and what the user should run themselves.

Never mark something VERIFIED if the only proof is your own confidence.
