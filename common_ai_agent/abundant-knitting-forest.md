# Plan: Session & Workflow Storage Restructure + Task Delegation

## Context

Two goals:
1. **Storage restructure** — separate primary/sub-agent conversation history, isolate todo state per workflow, add global `template/todo/`.
2. **Task delegation** — each todo task (or an entire workflow) can be delegated to a specific execution backend: cursor-agent, codex, gemini-cli, or direct API call. The primary LLM orchestrates; the delegated backend executes.

---

## Part A — Target Directory Structure

```
template/
  todo/
    bugfix.json        ← global todo templates (was: workflow/*/todo_templates/)
    feature.json
    refactor.json

.session/
  <session_name>/          e.g. "default", "rtl-gen"
    primary/
      conversation.json        ← was: conversation_history.json
      full_conversation.json   ← was: full_conversation_history.json
      <workflow_name>/         e.g. "default", "rtl-gen", "mas-gen"
        todo.json              ← was: current_todos.json
    sub/
      agent1/                  ← numbered by execution order per session
        conversation.json
        full_conversation.json
        <workflow_name>/
          todo.json
      agent2/
        ...
```

---

## Part B — Task Delegation Design

### B1. Todo item delegation field

Each todo item gets an optional `delegate` field:

```json
{
  "content": "Implement serialize_messages refactor",
  "status": "pending",
  "priority": "high",
  "delegate": "cursor-agent"
}
```

**Supported delegate values:**
| Value | Backend |
|---|---|
| `""` / omitted | Primary LLM (default, current behavior) |
| `"cursor-agent"` | cursor-agent CLI (`src/cursor_agent_backend.py`) |
| `"codex"` | OpenAI Codex CLI |
| `"gemini"` | Google Gemini CLI |
| `"api"` | Direct LLM API call (explicit, same as default) |

### B2. Workflow-level delegation

`workflow/<name>/workspace.json` gets a `default_delegate` field:

```json
{
  "name": "rtl-gen",
  "default_delegate": "cursor-agent",
  ...
}
```

When set, all tasks in that workflow delegate to the specified backend unless the task overrides it.

### B3. Delegation execution flow

```
Primary LLM marks task in_progress
  → checks todo.delegate (or workflow default_delegate)
  → if delegate set:
      spawn DelegateRunner(backend, task_content, context)
      wait for result
      inject result as Observation
      primary LLM reviews → marks approved
  → if no delegate:
      primary LLM executes directly (current behavior)
```

### B4. New file: `core/delegate_runner.py`

```python
class DelegateRunner:
    """Routes a todo task to the appropriate execution backend."""

    BACKENDS = {
        "cursor-agent": CursorAgentDelegate,
        "codex":        CodexDelegate,
        "gemini":       GeminiDelegate,
        "api":          APIDelegate,
    }

    def run(self, backend: str, task: str, context: str) -> str:
        """Execute task via backend, return result string."""
        cls = self.BACKENDS.get(backend)
        if not cls:
            raise ValueError(f"Unknown backend: {backend}")
        return cls().run(task, context)
```

Each delegate class:
- `CursorAgentDelegate` — wraps `cursor_agent_call()` from `src/cursor_agent_backend.py`
- `CodexDelegate` — subprocess call to `codex` CLI (similar pattern)
- `GeminiDelegate` — subprocess call to `gemini` CLI
- `APIDelegate` — calls `call_llm_raw()` directly

### B5. Integration point: `core/tools.py` `todo_update()`

When a task transitions to `in_progress`, check delegate:

```python
def todo_update(index, status, ...):
    ...
    if status == "in_progress":
        item = todo_tracker.todos[idx]
        delegate = item.delegate or _get_workflow_delegate()
        if delegate:
            result = DelegateRunner().run(delegate, item.content, _build_context())
            # Store result so primary LLM can review
            item.delegate_result = result
            return f"✅ Task {index} delegated to [{delegate}] and completed.\n\nResult:\n{result}"
    ...
```

### B6. `todo_write` / `todo_add` — support `delegate` field

```python
Action: todo_write(todos=[
  {"content": "Refactor serialize_messages", "status": "pending",
   "priority": "high", "delegate": "cursor-agent"},
  {"content": "Write tests", "status": "pending",
   "priority": "medium", "delegate": "api"}
])
```

### B7. `/todo delegate <index> <backend>` slash command

Allow changing delegation after task creation:
```
/todo delegate 1 cursor-agent
/todo delegate 2 gemini
/todo workflow-delegate cursor-agent   ← set workflow default
```

---

## Part A Implementation Steps

### A1. `src/main.py` — `_setup_session()`
```python
def _setup_session(session_name='default', workflow='default') -> Path:
    primary_dir  = Path.cwd() / '.session' / session_name / 'primary'
    workflow_dir = primary_dir / workflow
    primary_dir.mkdir(parents=True, exist_ok=True)
    workflow_dir.mkdir(parents=True, exist_ok=True)
    config.HISTORY_FILE    = str(primary_dir / 'conversation.json')
    config.TODO_FILE       = str(workflow_dir / 'todo.json')
    config.SESSION_DIR     = str(Path.cwd() / '.session' / session_name)
    config.ACTIVE_WORKFLOW = workflow
    _migrate_old_session(Path.cwd() / '.session' / session_name, primary_dir, workflow_dir)
```

### A2. `src/main.py` — workflow switch (`_on_workspace_switch`)
- Save current todos
- Update `config.TODO_FILE` → new workflow dir
- Load new workflow's todos

### A3. `core/history_manager.py`
- `_full_history_path()` → `full_conversation.json` (sibling of `conversation.json`)

### A4. `core/agent_runner.py` — sub-agent persistence
- Counter per session → `agent<N>` dir
- Save conversation + todos into `.session/<session>/sub/agent<N>/`

### A5. `workflow/loader.py` — global templates
- `TodoTemplateRegistry` loads `template/todo/` first, workflow overrides second

### A6. Migration — detect old flat structure, move files

---

## Files to Create / Modify

| File | Action |
|---|---|
| `core/delegate_runner.py` | **New** — backend routing |
| `lib/todo_tracker.py` | Add `delegate`, `delegate_result` fields to TodoItem |
| `core/tools.py` | `todo_update()` — check delegate on in_progress; `todo_write/add` — pass delegate field |
| `core/slash_commands.py` | `/todo delegate` command |
| `workflow/loader.py` | `default_delegate` in WorkspaceConfig; global template loading |
| `src/main.py` | `_setup_session()`, `_on_workspace_switch()` |
| `core/history_manager.py` | Path update for full_conversation.json |
| `core/agent_runner.py` | Sub-agent session persistence |
| `src/config.py` | `SESSION_DIR`, `ACTIVE_WORKFLOW` vars |
| `template/todo/` | **New dir** — global todo templates |

---

## Verification

1. **Structure**: `python src/main.py -s myproject -w rtl-gen`
   - `.session/myproject/primary/rtl-gen/todo.json` created ✓
   - `.session/myproject/primary/conversation.json` created ✓

2. **Workflow switch**: `/workflow mas-gen`
   - `.session/myproject/primary/mas-gen/todo.json` created ✓
   - rtl-gen todos preserved ✓

3. **Task delegation**:
   ```
   Action: todo_write(todos=[{"content":"refactor foo","status":"pending","priority":"high","delegate":"cursor-agent"}])
   Action: todo_update(index=1, status="in_progress")
   ```
   - cursor-agent executes the task ✓
   - Result injected as Observation ✓
   - Primary LLM reviews and approves ✓

4. **Workflow delegation**: set `"default_delegate": "cursor-agent"` in workspace.json
   - All tasks auto-delegate to cursor-agent ✓

5. **Sub-agent**: trigger explore/execute agent
   - `.session/myproject/sub/agent1/conversation.json` created ✓

6. **Migration**: existing `.session/default/conversation_history.json`
   - Auto-moved to `primary/conversation.json` ✓

7. **Global templates**: `template/todo/my_template.json`
   - `/todo template my_template` finds it from any workflow ✓
