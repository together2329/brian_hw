# Claude Code → Common AI Agent: Architectural Analysis & Improvement Plan

> Based on analysis of leaked-claude-code (~1900 TypeScript files, ~513K LOC) and common_ai_agent (~50 Python files).

---

## Table of Contents

1. [Architecture Comparison](#1-architecture-comparison)
2. [Key Patterns in Claude Code](#2-key-patterns-in-claude-code)
3. [What common_ai_agent Already Does Well](#3-what-common_ai_agent-already-does-well)
4. [Improvement Plan](#4-improvement-plan)
5. [Implementation Priority Matrix](#5-implementation-priority-matrix)

---

## 1. Architecture Comparison

| Aspect | Claude Code | Common AI Agent |
|--------|-------------|-----------------|
| **Language** | TypeScript (Bun) | Python |
| **Agent Loop** | `coordinator/` + `QueryEngine.ts` (class-based, async generator) | `core/react_loop.py` (function-based, while-loop) |
| **Tool System** | `Tool.ts` interface with zod schemas, per-tool directory | `core/tools.py` flat functions, `tool_dispatcher.py` |
| **Task System** | `Task.ts` with typed states, multiple task types (shell, agent, remote) | `core/job.py` + `core/background.py` |
| **Sub-agents** | `AgentTool` with coordinator mode, workers, fork/share cache | `core/delegate_runner.py` (explore/execute/review) |
| **Context Mgmt** | `context/` + `services/compact/` with snip projection | `core/compressor.py` (LLM-based compression) |
| **Hook System** | `hooks/toolPermission/` + lifecycle hooks | `core/hooks.py` (7 hook points) |
| **Cost Tracking** | `cost-tracker.ts` (per-model, USD, cache tokens) | Basic token counting in react_loop |
| **Todo/Task** | `TodoWriteTool` with rich prompt engineering | `lib/todo_tracker.py` + todo_update tool |
| **Skills** | `skills/` with bundled skills, skill discovery | `core/skill_system/` + `skills/` |
| **Permissions** | Multi-layer: deny rules, sandbox, classifier | Basic safe mode, dangerous command blocking |
| **UI** | Custom Ink/React terminal renderer (Yoga layout) | Textual TUI + stdout fallback |

---

## 2. Key Patterns in Claude Code

### 2.1 Coordinator-Worker Architecture (HIGH VALUE)

Claude Code's most powerful pattern is the **coordinator mode** (`coordinator/coordinatorMode.ts`):

```
User → Coordinator (orchestrator)
         ├── Worker 1 (research, read-only)
         ├── Worker 2 (implementation, write)
         └── Worker 3 (verification, test)
```

**Key design principles:**
- Coordinator **never delegates understanding** — it synthesizes research findings into specific implementation specs
- Workers are **async** — results arrive as `<task-notification>` XML in user-role messages
- **Parallelism is the superpower** — independent tasks launch simultaneously
- Workers have **scoped tools** — researchers don't get write tools
- **Continue vs Spawn** decision: high context overlap → continue, low → spawn fresh
- Fork subagents share **prompt cache** with parent (cost optimization)

### 2.2 Tool Interface Design

Each tool in Claude Code implements a rich interface (`Tool.ts`):

```typescript
interface Tool {
  name: string
  aliases?: string[]                    // Backward compatibility
  searchHint?: string                   // For ToolSearch (3-10 words)
  call(args, context, canUseTool, ...)  // Execution
  description(input, options)           // Dynamic description
  inputSchema: z.ZodType               // Zod validation
  isEnabled(): boolean                 // Feature-gated
  isReadOnly(input): boolean           // For parallel safety
  isDestructive(input): boolean        // For permission prompts
  isConcurrencySafe(input): boolean    // For parallel execution
  interruptBehavior(): 'cancel'|'block' // How to handle user interrupt
  isOpenWorld?(input): boolean         // Network access needed?
  validateInput?(input, context)       // Pre-permission validation
  checkPermissions?(input, context)    // Permission logic
  maxResultSizeChars: number           // Output budget
  shouldDefer?: boolean                // Lazy-load via ToolSearch
  alwaysLoad?: boolean                 // Never defer
  backfillObservableInput?(input)      // Legacy field migration
}
```

**Key insights:**
- `isReadOnly()` / `isConcurrencySafe()` enable safe **parallel tool execution**
- `isDestructive()` gates permission prompts for dangerous operations
- `interruptBehavior()` distinguishes cancelable vs blocking tools
- `maxResultSizeChars` persists large outputs to disk (avoid context bloat)
- `shouldDefer` / `alwaysLoad` implement **lazy tool loading** (ToolSearch)

### 2.3 Rich Tool Prompts (HIGH VALUE)

Every tool has an extensive, carefully crafted **prompt** (`prompt.ts`):

- **BashTool**: 100+ lines covering tool preference, git safety, sandbox config, background execution, commit/PR workflows
- **AgentTool**: Detailed guidance on when to fork vs spawn, how to write worker prompts, coordinator examples
- **TodoWriteTool**: When to use/not use, state management rules, completion requirements, examples

**Pattern:** Each prompt includes:
1. When to use / when NOT to use
2. Detailed instructions with sub-items
3. Multiple `<example>` blocks with `<reasoning>` explanations
4. Edge cases and common mistakes

### 2.4 Permission System (Multi-Layer)

```
Tool Call Request
    │
    ▼
[1] validateInput() — check if input is valid in this context
    │
    ▼
[2] checkPermissions() — tool-specific permission logic
    │
    ▼
[3] Permission Rules (allow/deny/ask by source)
    │   - alwaysAllowRules
    │   - alwaysDenyRules
    │   - alwaysAskRules
    │
    ▼
[4] Sandbox (filesystem/network restrictions)
    │
    ▼
[5] canUseTool() — user-facing permission prompt (if needed)
```

### 2.5 Cost Tracking (Per-Model, Detailed)

```typescript
interface ModelUsage {
  inputTokens: number
  outputTokens: number
  cacheReadInputTokens: number
  cacheCreationInputTokens: number
  webSearchRequests: number
  costUSD: number
  contextWindow: number
  maxOutputTokens: number
}
```

- Tracks per-model costs with `calculateUSDCost(model, usage)`
- Persists to project config for session resume
- Includes cache token tracking (read vs creation)
- Lines changed tracking (added/removed)

### 2.6 Context Compaction

Claude Code has **multiple** compaction strategies:
1. **Snip compaction** — surgical removal of old tool outputs, preserving recent turns
2. **Compact service** — LLM-based summarization
3. **Tool result persistence** — large outputs saved to disk, replaced with file path
4. **Content replacement** — aggregate tool result budget per conversation thread

### 2.7 Task/Background System

```typescript
type TaskType = 'local_bash' | 'local_agent' | 'remote_agent' | 'in_process_teammate'
              | 'local_workflow' | 'monitor_mcp' | 'dream'
type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'killed'
```

- Each task type has its own `Task` implementation
- Tasks track: id, status, startTime, endTime, outputFile, outputOffset
- Task IDs are prefixed by type (`b` for bash, `a` for agent, etc.)
- Output is persisted to disk (`getTaskOutputPath(id)`)
- Tasks can be **polled**, **killed**, and **resumed**

---

## 3. What common_ai_agent Already Does Well

| Feature | Status | Quality |
|---------|--------|---------|
| **ReAct Loop** | ✅ Mature | Well-structured with dependency injection (`ReactLoopDeps`) |
| **Tool Dispatch** | ✅ Robust | Excellent error recovery: alias resolution, param remapping, positional→keyword fixing |
| **Hook System** | ✅ Good | 7 hook points, priority-based execution, built-in hooks (truncator, compactor, pruner) |
| **Context Compression** | ✅ Good | LLM-based single/chunked compression, turn protection, !important preservation |
| **Smart RAG** | ✅ Unique | Hybrid RAG with LLM judge for relevance decisions |
| **Graph Lite** | ✅ Unique | Knowledge graph for cross-session learning |
| **Procedural Memory** | ✅ Unique | Past experience injection for similar tasks |
| **Skill System** | ✅ Good | Dynamic skill loading and activation |
| **Todo Tracking** | ✅ Good | Rejection-livelock detection, continuation enforcement |
| **Plan Mode** | ✅ Good | Read-only enforcement, todo_write blocking in plan mode |
| **Web Tools** | ✅ Working | Firecrawl integration for search/fetch/extract |
| **Session Management** | ✅ Good | Snapshot/recovery, session persistence |

---

## 4. Improvement Plan

### Priority 1: Coordinator-Worker Mode (HIGH IMPACT)

**What:** Implement a coordinator mode where the agent orchestrates sub-agents for parallel task execution.

**Files to create/modify:**
- `core/coordinator.py` — New coordinator orchestrator
- `core/worker.py` — Worker agent with scoped tools
- `core/task_manager.py` — Task lifecycle management

**Design:**
```python
class Coordinator:
    """Orchestrates workers for parallel task execution."""
    
    def spawn_worker(self, task: str, tools: Set[str], mode: str = "worker") -> str:
        """Spawn a new worker. Returns task_id."""
        
    def send_message(self, task_id: str, message: str) -> None:
        """Continue an existing worker with follow-up instructions."""
        
    def stop_worker(self, task_id: str) -> None:
        """Stop a running worker."""
        
    def get_results(self) -> List[TaskNotification]:
        """Get completed worker results as notifications."""

class TaskNotification:
    task_id: str
    status: str  # completed | failed | killed
    summary: str
    result: str
    usage: dict  # tokens, tool_uses, duration_ms
```

**Key features from Claude Code:**
- Workers are async — results arrive as notifications
- Coordinator synthesizes findings before delegating implementation
- Read-only workers for research, write workers for implementation
- Verification workers get fresh context (no implementation assumptions)

---

### Priority 2: Enhanced Tool Interface (MEDIUM-HIGH IMPACT)

**What:** Make tools self-describing with metadata for permissions, parallelism, and output budgets.

**Files to modify:**
- `core/tool_schema.py` — Add tool metadata
- `core/tools.py` — Add metadata to each tool function
- `core/tool_dispatcher.py` — Use metadata for smarter dispatch

**Design:**
```python
@dataclass
class ToolMetadata:
    name: str
    aliases: List[str]
    is_readonly: Callable[..., bool]
    is_destructive: Callable[..., bool]
    is_concurrency_safe: Callable[..., bool]
    max_result_chars: int
    interrupt_behavior: str  # 'cancel' | 'block'
    search_hint: str
    should_defer: bool
    description_template: str  # Dynamic description
```

**Benefits:**
- Safe parallel tool execution (readonly tools can run concurrently)
- Better permission prompts (destructive vs non-destructive)
- Output budgeting (large results persisted to disk)
- Lazy tool loading for large tool registries

---

### Priority 3: Cost Tracking System (MEDIUM IMPACT)

**What:** Track per-model token usage and USD costs across the session.

**Files to create:**
- `core/cost_tracker.py` — New file

**Design (from Claude Code):**
```python
@dataclass
class ModelUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_tokens: int = 0
    cost_usd: float = 0.0
    context_window: int = 0

class CostTracker:
    """Tracks per-model token usage and costs."""
    
    def __init__(self):
        self._model_usage: Dict[str, ModelUsage] = {}
        self._total_cost: float = 0.0
        self._total_duration_ms: int = 0
        self._lines_added: int = 0
        self._lines_removed: int = 0
    
    def record(self, model: str, usage: dict, cost_usd: float):
        """Record usage from an API call."""
        
    def format_summary(self) -> str:
        """Format cost summary for display."""
        
    def save_to_project_config(self):
        """Persist costs for session resume."""
        
    def restore_from_project_config(self, session_id: str):
        """Restore costs from a previous session."""
```

---

### Priority 4: Tool Output Persistence (MEDIUM IMPACT)

**What:** When tool results exceed a threshold, persist to disk and return a file reference.

**Files to modify:**
- `core/tool_dispatcher.py` — Add output persistence
- `core/hooks.py` — Update truncator to persist

**Design (from Claude Code):**
```python
def _maybe_persist_result(tool_name: str, result: str, max_chars: int) -> str:
    """If result exceeds max_chars, persist to disk and return preview."""
    if len(result) <= max_chars:
        return result
    
    output_path = get_tool_output_path(tool_name)
    with open(output_path, 'w') as f:
        f.write(result)
    
    preview = result[:2000]
    return (
        f"{preview}\n\n"
        f"... [Full output ({len(result)} chars) saved to: {output_path}]\n"
        f"Use read_file('{output_path}') to view the complete result."
    )
```

---

### Priority 5: Enhanced Prompt Engineering (MEDIUM IMPACT)

**What:** Improve tool descriptions with rich prompt engineering from Claude Code patterns.

**Key improvements:**
1. **When to use / when NOT to use** — prevent model from using AgentTool for simple file reads
2. **Structured examples** with `<reasoning>` tags — teach the model WHY
3. **Git safety protocol** — never force-push, never amend after hook failure
4. **Background execution guidance** — when to use run_in_background vs foreground

**Files to modify:**
- `core/tool_descriptions/` — Rewrite each tool description
- `core/prompt_builder.py` — Add coordinator mode system prompt

---

### Priority 6: Permission Sandbox (MEDIUM IMPACT)

**What:** Multi-layer permission system with filesystem and network sandboxing.

**Files to create:**
- `core/permissions.py` — New file
- `core/sandbox.py` — New file

**Design:**
```python
class PermissionManager:
    """Multi-layer tool permission system."""
    
    def check(self, tool_name: str, tool_input: dict) -> PermissionResult:
        """
        1. Check deny rules (blanket deny)
        2. Check tool-specific permissions
        3. Check sandbox restrictions
        4. Return allow/deny/ask
        """
        
class SandboxConfig:
    """Filesystem and network sandbox configuration."""
    read_paths: List[str]
    write_paths: List[str]
    allowed_hosts: List[str]
    denied_hosts: List[str]
```

---

### Priority 7: Session Cost Persistence & Resume (LOW-MEDIUM IMPACT)

**What:** Save and restore session costs when resuming conversations.

**Files to modify:**
- `core/session_manager.py` — Add cost persistence
- `core/cost_tracker.py` — Add save/restore methods

---

### Priority 8: Tool Search / Lazy Loading (LOW IMPACT)

**What:** When tool count exceeds a threshold, defer tool schemas and add a ToolSearch tool.

**Design:**
```python
class ToolSearch:
    """Search available tools by keyword when deferred."""
    
    def search(self, query: str, tools: List[ToolMetadata]) -> List[ToolMetadata]:
        """Keyword match against tool names and search hints."""
```

---

## 5. Implementation Priority Matrix

| Priority | Feature | Impact | Effort | Files | Risk |
|----------|---------|--------|--------|-------|------|
| **P0** | Coordinator-Worker Mode | 🔴 Very High | 🔴 Large | 3 new | Medium |
| **P1** | Enhanced Tool Interface | 🟠 High | 🟡 Medium | 3 mod | Low |
| **P1** | Cost Tracking | 🟠 High | 🟢 Small | 1 new | Low |
| **P2** | Tool Output Persistence | 🟡 Medium | 🟢 Small | 2 mod | Low |
| **P2** | Rich Tool Prompts | 🟡 Medium | 🟡 Medium | Many | Low |
| **P3** | Permission Sandbox | 🟡 Medium | 🔴 Large | 2 new | Medium |
| **P3** | Session Cost Resume | 🟢 Low-Med | 🟢 Small | 2 mod | Low |
| **P4** | Tool Search/Lazy Load | 🟢 Low | 🟡 Medium | 1 new | Low |

---

## Key Takeaways

### What Claude Code does BETTER:
1. **Coordinator-Worker parallelism** — The biggest architectural advantage. Being able to launch parallel research, implementation, and verification workers transforms productivity.
2. **Rich tool metadata** — `isReadOnly`, `isDestructive`, `isConcurrencySafe` enable smarter automation.
3. **Tool output persistence** — Never waste context on large outputs. Persist to disk, reference by path.
4. **Detailed prompt engineering** — Every tool has extensive when-to-use guidance with examples.
5. **Per-model cost tracking** — Essential for managing multi-model API spend.

### What common_ai_agent does BETTER (or uniquely):
1. **Smart RAG** — Claude Code has no RAG. common_ai_agent's hybrid RAG with LLM judge is superior for domain knowledge.
2. **Graph Lite** — Knowledge graph for cross-session learning. No equivalent in Claude Code.
3. **Procedural Memory** — Past experience injection. Unique and valuable.
4. **Plan Mode** — While Claude Code has EnterPlanModeTool, common_ai_agent's plan_q mode with todo_write is more structured.
5. **Skill System** — More dynamic than Claude Code's bundled skills.
6. **Tool dispatch robustness** — common_ai_agent's alias resolution, param remapping, and error recovery in `tool_dispatcher.py` is more defensive than Claude Code's approach.

### Recommended Next Step:
**Start with P0 (Coordinator-Worker)** — it's the highest-impact change. Begin with the `coordinator.py` skeleton, implement `spawn_worker` and `get_results`, then wire it into the existing `delegate_runner.py` infrastructure.
