# Todo Continuation Prompt Patterns

These are the message templates injected by the ReAct loop to keep the agent
on track with its todo list. The actual strings live in `hook_messages.json`.

## Template Keys

| Key | When injected |
|-----|--------------|
| `todo_continuation` | Task is pending or in_progress (normal) |
| `todo_rejected` | Task was rejected — fix required |
| `todo_review` | Task completed — review before approving |
| `todo_loop_continue` | Loop task restarted (exit_condition not met) |
| `todo_loop_max_reached` | Loop reached max_loop_iterations, auto-approved |

## Variables Available Per Template

**todo_continuation**: `{idx}`, `{total}`, `{content}`, `{first_action}`

**todo_rejected**: `{idx}`, `{total}`, `{rejection_reason}`

**todo_review**: `{idx}`, `{total}`, `{content}`

**todo_loop_continue**: `{idx}`, `{total}`, `{loop_count}`, `{max_loop}`,
`{content}`, `{exit_condition}`

**todo_loop_max_reached**: `{idx}`, `{total}`, `{loop_count}`

## Rules

- Always call `todo_update(index=N, status='in_progress')` before starting work
- Always call `todo_update(index=N, status='completed')` when done — BEFORE the next action
- For loop tasks: pass `tool_output=<simulation_output>` so the loop can check the exit condition
- Never skip a task or mark it approved without a review step
