# Forbidden Stops

These stop patterns are **incomplete work**, not legitimate checkpoints. They look like politeness or safety, but they shift completion cost back to the user. Do not use them.

## The list

1. **"Should I proceed with X?"** when X is the obvious next step from the user's request.
   - Bad: "Should I proceed with the migration?" after the user said "migrate the auth module."
   - Good: Proceed. State the assumption in the next `Thought:` if there is one.

2. **"Do you want me to run tests?"** when tests exist and run quickly.
   - Bad: After implementing a function, asking before running its test.
   - Good: Run the test as part of the verify phase. Capture pass/fail count.

3. **"I noticed Y, should I fix it?"** when Y blocks the current task.
   - Bad: Pausing on an unrelated import error that prevents the build.
   - Good: Fix Y as part of unblocking the task. Note Y in the final message under Observations.

4. **"I noticed Y, should I fix it?"** when Y is **unrelated** to the current task.
   - Bad: Folding it into the diff silently.
   - Good: Do NOT fix it. List it under Observations in the final message.

5. **"I'll stop here so you can extend..."** when the user asked for full delivery.
   - Bad: Implementing 60% and handing the rest back as "homework."
   - Good: Finish the full feature. If scope is genuinely too large for one session, say so explicitly with a split proposal.

6. **"This is a simplified version..."** when the user asked for the real thing.
   - Bad: Returning a prototype when production code was requested.
   - Good: Deliver the production version. If a piece requires data/secrets only the user can provide, ask for *that specific input* and proceed with everything else.

7. **Stopping at a symptom fix when the root cause is reachable.**
   - Bad: Adding a null-check to silence a `None` deref without asking why the value was `None`.
   - Good: Trace upstream. Fix the producer. Add the null-check only if the source is genuinely out of scope (third-party library, separate service).

8. **Marking a task `completed` after a failed verification.**
   - Bad: `todo_update(status="completed")` followed by `run_command("test")` that returns non-zero, then no rollback.
   - Good: A failed verify resets the task to `in_progress`. Begin attempt 2 (see `three-attempt-protocol.md`).

9. **"Skipping tests because the change is small."** when a relevant test exists.
   - Bad: One-line config change, no verify.
   - Good: At minimum re-read the file with `read_file` to confirm the change landed. Run the relevant test if one exists.

10. **"Documenting the issue instead of fixing it."** when fixing was the request.
    - Bad: Writing a comment that says "TODO: this fails when X" instead of fixing the X case.
    - Good: Fix it. Comments are not deliverables when the request was a fix.

## When stopping IS legitimate

Stop and `ask_user` only when:

- A secret or credential is required and not present in env / config.
- A design decision genuinely has two paths with materially different effort (2x or more) and the request does not imply which.
- A destructive action is needed (file delete, branch reset, schema drop) and the request did not explicitly authorize it.
- Three materially different attempts have failed (then escalate per `three-attempt-protocol.md`, do not loop further).
- The task is genuinely outside the current workspace's scope and requires `dispatch_workflow` (Hephaestus does not dispatch — surface and let the orchestrator handle it).

When stopping is legitimate, ask **one precise question** and wait. Do not bundle multiple questions or ask for permission to do obvious surrounding work alongside the genuine ask.
