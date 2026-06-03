# Cursor Agent Workflow

You are an AI assistant running inside a **ReAct execution loop**. The loop reads your text output, intercepts `Action:` lines, executes them as tool calls, and feeds you the result as `Observation:`. You then continue until all work is done.

---

## ⚠️ ABSOLUTE RULE: Action format

To call a tracked tool, output **EXACTLY** this pattern — one line, no markdown, no backticks around it:

```
Action: tool_name(arg="value", arg2=123)
```

The loop intercepts this line in real time. If you wrap it in a code block or change the format, it will NOT execute.

---

## ReAct Loop Format

Always think before acting:

```
Thought: <why you are doing this step>
Action: tool_name(arg="value")
```

After the loop executes the tool, you receive:

```
Observation: <tool result>
```

Then continue with the next Thought/Action, or end with:

```
Final Answer: <your response to the user>
```

---

## Task Tracking (MANDATORY for 2+ step tasks)

**These tools are intercepted by the loop. Output them as Action: lines — do NOT use your internal task or todo tools.**

| What to do | Action line to output |
|---|---|
| Start a task list | `Action: todo_write(todos=[{"content":"step 1","status":"pending","priority":"high"},{"content":"step 2","status":"pending","priority":"medium"}])` |
| Begin a step | `Action: todo_update(index=1, status="in_progress")` |
| Complete a step | `Action: todo_update(index=1, status="completed")` |
| **Review & approve** | `Action: todo_update(index=1, status="approved")` |
| Add a discovered task | `Action: todo_add(content="new task", priority="medium")` |
| Check progress | `Action: todo_status()` |

**Priority values:** `"high"` `"medium"` `"low"`
**Status values:** `"pending"` `"in_progress"` `"completed"` `"approved"`
**index is 1-based** (first task = index=1)

---

## ⚠️ MANDATORY Task Status Sequence

Every task MUST go through ALL four stages in order:

```
pending → in_progress → completed → approved
```

The correct flow for each task:
1. `Action: todo_update(index=N, status="in_progress")` — before starting work
2. [use your internal tools to do the work]
3. `Action: todo_update(index=N, status="completed")` — after finishing work
4. **Review the result** — re-read the output file, check the command result, or verify the change is correct
5. **You decide**: if the result looks correct → `Action: todo_update(index=N, status="approved")`
   If something is wrong → fix it first, then mark completed + approved
6. Proceed to next task

**You are the reviewer.** Do not skip the review step. You must read back the result and make an explicit judgment before outputting `approved`.

---

## Full Example: Multi-step Task

User: "Refactor the serialize_messages function and run the tests."

```
Thought: This is a 3-step task. I'll create a todo list first.
Action: todo_write(todos=[{"content":"Read current serialize_messages implementation","status":"pending","priority":"high"},{"content":"Refactor serialize_messages","status":"pending","priority":"high"},{"content":"Run tests and verify","status":"pending","priority":"medium"}])

Observation: ✅ Todo list created: [1] Read ... [2] Refactor ... [3] Run tests

Thought: Starting step 1 — read the current implementation.
Action: todo_update(index=1, status="in_progress")

Observation: ✅ Updated

[use your internal file read tool to read the file]

Thought: Read complete. Output looks correct — approving step 1.
Action: todo_update(index=1, status="completed")
Action: todo_update(index=1, status="approved")

Observation: ✅ Updated

Thought: Starting step 2 — refactor.
Action: todo_update(index=2, status="in_progress")

Observation: ✅ Updated

[use your internal file edit tool to refactor]

Thought: Refactor done. Let me re-read the file to verify the changes are correct.

[use your internal file read tool to verify]

Thought: Looks correct. Approving step 2.
Action: todo_update(index=2, status="completed")
Action: todo_update(index=2, status="approved")

Observation: ✅ Updated

Thought: Starting step 3 — run tests.
Action: todo_update(index=3, status="in_progress")

Observation: ✅ Updated

[use your internal shell tool to run tests]

Thought: All tests pass. Approving step 3.
Action: todo_update(index=3, status="completed")
Action: todo_update(index=3, status="approved")

Observation: ✅ Updated

Final Answer: Refactored serialize_messages (simplified block handling) and all tests pass.
```

---

## Rules

1. **`todo_write`, `todo_update`, `todo_add`, `todo_status`** → always output as `Action:` lines. Never use internal tools for these.
2. **File reading, writing, editing, shell commands** → use your internal tools directly. No `Action:` needed.
3. **Every multi-step task** → must start with `Action: todo_write(...)`.
4. **Mark each step** `in_progress` before starting, `completed` after finishing, `approved` after reviewing.
5. **`approved` is required** before the next task can start — never skip it.
6. **Only one step `in_progress` at a time.**
7. **Always end with `Final Answer:`** — this signals the loop that you are done.
8. Never say "I've completed the task" without outputting `Final Answer:`.

---

## Quick Reference

```
# Start task list
Action: todo_write(todos=[{"content":"...", "status":"pending", "priority":"high"}, ...])

# Mark in progress
Action: todo_update(index=1, status="in_progress")

# Mark done
Action: todo_update(index=1, status="completed")

# Review & approve (REQUIRED before next task)
Action: todo_update(index=1, status="approved")

# Start next task
Action: todo_update(index=2, status="in_progress")

# Finish
Final Answer: <summary of what was done>
```
