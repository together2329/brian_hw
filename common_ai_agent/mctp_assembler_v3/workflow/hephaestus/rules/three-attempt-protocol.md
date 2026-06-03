# Three-Attempt Protocol

If your first approach to a problem fails, try a **materially different** approach. Not a small tweak to the same approach.

After three materially different approaches have failed, stop editing and escalate.

## What "materially different" means

**Materially different**:
- Switching algorithms (recursive ↔ iterative, push ↔ pull, sync ↔ async).
- Switching data structures (list ↔ map, single-pass ↔ two-pass).
- Switching the abstraction level (in-place patch vs new wrapper vs caller refactor).
- Switching the library or API (stdlib `re` ↔ `regex`, `requests` ↔ `httpx`).
- Switching the layer where the fix lands (caller ↔ producer ↔ middleware).

**Not materially different** (these all count as the *same* attempt):
- Renaming variables.
- Reordering statements without changing semantics.
- Adding/removing logging or comments.
- Tweaking error messages.
- Adjusting whitespace or formatting.
- Trying the same approach with a different config value.

If attempt 2 looks like attempt 1 with cosmetic changes, it is not attempt 2. It is still attempt 1.

## The protocol

### Attempt 1
Implement your best approach. Verify with `run_command` / `read_file` / test runner. If verify passes, you are done — exit the protocol.

### Attempt 1 fails — pivot to Attempt 2
Before writing attempt 2:
1. Capture **what failed** in a `Thought:` — exact error message, test name, exit code.
2. State **why** attempt 1 was the wrong approach in one sentence.
3. State **what is materially different** about attempt 2 in one sentence.
4. Revert attempt 1's edits if they leave the codebase in a worse state than before. Use `replace_in_file` to undo, or restore from `read_file` evidence captured during exploration.

Then implement attempt 2. Verify.

### Attempt 2 fails — pivot to Attempt 3
Same protocol. The bar for "materially different" is **higher** — if attempt 1 was algorithm A and attempt 2 was algorithm B, attempt 3 should not be algorithm C in the same family. Consider switching the layer entirely (e.g. fix in the caller instead of the function).

### Attempt 3 fails — escalate

Stop editing immediately. Do not start attempt 4.

1. **Revert** to the last known-good state. Use the read evidence from exploration to restore the original.
2. **Document** every attempt. For each: approach (one sentence), failure mode (one sentence + exit code/error), why the next attempt was materially different.
3. **`ask_user`** with the full failure record. Ask: *"three approaches failed (summarized below). Which path do you want to pursue?"*

Do **not**:
- Quietly leave the codebase in a broken state between attempts.
- Delete a failing test to get a green build — that hides the bug rather than fixing it.
- Stretch attempt 3 by trying small variants ("attempt 3a, 3b, 3c"). Three is three.
- Skip the revert step and hand the user a half-broken diff.

## Recording attempts in the todo tracker

Each attempt's verify failure resets the current task to `in_progress`. Use `tool_output` in the next `todo_update` call to record the attempt count:

```
todo_update(
  index=N,
  status="in_progress",
  tool_output="attempt 1/3 failed: TypeError in foo() — pivoting to caller-side fix"
)
```

When attempt 3 escalates, mark the task `rejected` with the full record:

```
todo_update(
  index=N,
  status="rejected",
  tool_output="3/3 attempts failed. (1) recursive — stack overflow on N>1000. (2) iterative with explicit stack — same OOM. (3) chunked streaming — chunk boundary corruption. Escalating."
)
```

## Why three

One attempt is the baseline.
Two attempts proves you considered an alternative.
Three attempts proves the problem is structural, not approach-dependent.

Beyond three, the marginal probability that attempt 4 succeeds without new information is low. The user has information you do not (intent, constraints, prior debugging context). Get it.
