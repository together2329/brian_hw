# RULES — Normal Execution Mode

1. Read before editing — never modify a file you haven't read first
2. One task in_progress at a time — never start a new task before the current one is approved
3. Mark completed before moving on — call `todo_update(status='completed')` as the FIRST action when done, not the last
4. Review before approving — after completing, perform a critical self-review; only approve with concrete evidence
5. Reject clearly — if work is wrong, reject with an exact description of the problem
6. No skipping — tasks must be processed in order; never jump ahead
7. No fabrication — never claim a tool ran or a file was written without actually calling the tool
8. **Simple task → just do it.** A single read, one-line edit, quick lookup, trivial command — execute immediately, no todo_add needed.
9. **Multi-step task → use `todo_add` to track.** When the user asks for something that needs ≥3 distinct steps, branches between files, or carries state across iterations, append items with `todo_add(content="...", priority=...)` so progress is visible. Never call `todo_write` in Normal Mode — it's blocked and would wipe the existing list. Use `todo_add` to append, `todo_update` to change status, `todo_remove` to delete.
10. **`todo_write` is plan-only.** If the work is large enough to need a fresh plan, switch to Plan Mode (`/plan`); otherwise build incrementally with `todo_add`.
