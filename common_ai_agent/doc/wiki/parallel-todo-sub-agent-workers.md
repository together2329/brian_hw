# Parallel TODO Sub-Agent Workers

Background worker fanout that lets the main agent hand a *batch* of
TODOs to `parallel_todo_dispatch(...)` and wait for aggregated
results, instead of walking the workflow TODO tracker one item at a
time.

Related: [[orchestrator-worker-handoff]] · [[workflow-feedback-and-scheduling]] ·
[[karpathy-llm-wiki-pattern]] · [[full-flow-pipeline]]

## Why

A workflow stage (e.g. `rtl-gen`) emits an `<ip>/rtl/rtl_todo_tracker.json`
with up to several hundred RTL-XXXX tasks. The main agent processes
those sequentially: pick one → `todo_update in_progress` → LLM step →
`todo_update completed` → `todo_update approved` → next. Each TODO
costs at least one LLM round-trip; 122 of them on a real RV32I run
take roughly an hour of clock time per LLM provider.

The agent's foreground ReAct loop is inherently serial — it can't
fan out work and wait. The codebase already had every primitive we
needed (background pool, sub-agent runner, model swap, cost lookup,
credential gate); the only missing piece was the dispatcher itself.

## Architecture decision

**Default: clean + prompt.** Each worker is a fresh sub-agent ReAct
loop launched with `(prompt, model, working_dir)` and *no* inherited
parent context. Profile state is snapshot/restored per worker so two
workers using different providers (e.g. `claude-cli` and
`gpt-5.3-codex`) do not trample each other's `os.environ`.

**Optional: fork (Phase 2, not yet implemented).** When the agent
already built up useful working memory (e.g. "I just read these ten
files"), a future call may carry that state into the worker via
`fork=True` + `fork_state=<dict>`. Until Phase 2 lands the dispatcher
raises `NotImplementedError` for `fork=True`. Phase 1 (clean) is
enough to drain the 122-TODO tracker quickly.

| Concern | fork + prompt | **clean + prompt** (default) |
|---|---|---|
| Sub-agent context | parent's tool history / TODO state | empty (fresh ReAct loop) |
| Mixed-model workers | fragile (shared profile env) | clean (thread-local snapshot+restore) |
| Worker cross-talk | possible (shared parent) | none (each worker reads its own `worker_<idx>/`) |
| Debug surface | tangled | per-worker `result.json` |
| Implementation cost | needs context-snapshot helper | one call to `DelegateRunner(backend="sub-agent")` |
| When to choose it | shared cognitive state, multi-turn follow-up, hypothesis splits | independent TODO batches, mixed-provider runs |

## Provider matrix (auto-pick)

When `models=None`, the dispatcher resolves the worker pool via
`_available_models()` — it walks a candidate list, asks
`headless_workflow.RealLLMProvider.available_reason(name)` whether
each one can actually run, and sorts the passing entries by
`lib.model_pricing.get_pricing` (cheapest first).

```
1. cursor-cli       (cursor-agent in PATH)
2. claude-cli       (claude in PATH)
3. gpt-5.3-codex    (opencode/Codex OAuth credential present)
4. glm-5.1          (ZAI_API_KEY or PROFILE_glm_API_KEY set)
5. deepseek-v4-pro  (PROFILE_deepseek_API_KEY or LLM_API_KEY set)
6. kimi-*           (PROFILE_kimi_API_KEY or KIMI_API_KEY set)
   + any other config profile that has an API key / base URL
```

Pass `models=["gpt-5.3-codex", "claude-cli", "glm-5.1"]` to skip the
discovery step and bind workers to those exact providers. CLI
backends report cost zero so the auto-sorter prefers them when
available.

## Reuse table (no new infrastructure)

| Component | Location | Role in the dispatcher |
|---|---|---|
| `BackgroundManager` | `core/background.py:43-112` | available, currently bypassed — dispatcher manages its own `ThreadPoolExecutor` per job so jobs can fan out beyond the global 3-task pool |
| `DelegateRunner(backend="sub-agent")` | `core/delegate_runner.py` | actual worker entry; wraps `run_agent_session` |
| `run_agent_session` | `core/agent_runner.py:146` | clean ReAct loop per worker |
| `config.set_active_profile` / `activate_cli_backend` | `src/config.py:554, 668` | live provider swap, scoped per worker |
| `config.scoped_model_runtime` | `src/config.py` | context-manager flavour of the swap used by the dispatcher |
| `RealLLMProvider.available_reason` | `src/headless_workflow.py:908` | credential / binary gate per model |
| `lib.model_pricing.get_pricing` | `lib/model_pricing.py` | cost-ascending order when `models=None` |

## Public surface

`core/tools.py` registers `parallel_todo_dispatch` in `AVAILABLE_TOOLS`.

```python
parallel_todo_dispatch(
    todos=[...],            # list / dict / JSON string / newline-or-comma text
    max_workers=3,          # cap when models is omitted
    models=None,            # explicit ["claude-cli", "gpt-5.3-codex", ...] or None
    timeout_s=1800,         # blocking wait ceiling
)
```

Returns a JSON string with `{job_id, status, worker_count,
completed_workers, failed_workers, todos_assigned, todos_done,
workers: [...]}`. `status` is one of `completed` / `partial` /
`partial_error` / `error` / `timeout` / `blocked`.

Worker artefacts land under `<project_root>/.workers/ptd_<id>/`:
- `manifest.json` — chosen models, chunk sizes, picked reason
- `<idx>/result.json` — per-worker status, todos_done, raw model output

## Verification recipe

1. **Unit (no network)** — monkeypatch `DelegateRunner.run` to return
   a fixed string instantly; call `dispatch(["t1", "t2", "t3"],
   max_workers=3, models=["fake-1", "fake-2", "fake-3"])`. Assert
   three `result.json` files written, `wait()` returns `completed`,
   `todos_assigned=3`.
2. **Profile guard** — `models=["claude-cli", "gpt-5.3-codex"]`,
   workers=2. Snapshot `os.environ[BASE_URL]` before/after dispatch.
   Main thread's value must be unchanged on return.
3. **Auto-pick** — set env so only two models pass
   `available_reason`. Call with `models=None, max_workers=3`. Expect
   two workers spawned, `status="partial"` with `worker_count=2`,
   one TODO left in the unassigned bucket.
4. **Integration** — real four-TODO batch, three workers, no model
   override. Confirm `manifest.json` records the auto-picked models,
   each `result.json` carries `todos_done`, and the main agent sees
   `models_resolved` in the aggregated reply.
5. **R2 cosmetic** — open ATLAS chat with the running agent calling
   `todo_update`. The chat row must render `step_update` while the
   right-side `Todo` panel keeps the workflow's RTL-XXXX IDs.

## Granting CLI tools per dispatch

`claude-cli` is invoked with `--tools ""` by default
(`src/claude_cli_backend.py:46`) so Claude Code's built-in
`WebSearch` / `WebFetch` / `Bash` / `Read` etc. are disabled —
common_ai_agent stays the single executor for `Action:` lines.

When a worker really needs Claude Code's own tools (typically web
search), the dispatcher exposes two pass-through arguments:

```python
parallel_todo_dispatch(
    todos=[...],
    models=["claude-cli"],
    claude_tools="WebSearch,WebFetch",
    # extra_overrides={"CLAUDE_CLI_PERMISSION_MODE": "default"},  # opt out of auto-bypass
)
```

- `claude_tools` becomes the worker's thread-local `CLAUDE_CLI_TOOLS`
  via `config.scoped_runtime_extra`. The dispatcher *also* sets
  `CLAUDE_CLI_PERMISSION_MODE="bypassPermissions"` so the headless
  worker doesn't stall on per-tool confirm prompts.
- `extra_overrides` is the escape hatch — any key in
  `src.config._THREAD_RUNTIME_KEYS` can be pushed onto the worker
  thread for that job only.

### Per-provider web access capability

| Provider | Built-in web | Path |
|---|---|---|
| `claude-cli` | ✅ via `claude_tools="WebSearch,WebFetch"` | dispatcher grants tool + flips permission mode |
| `cursor-cli` | ✅ always on (cursor-agent has no equivalent off-switch) | no flag needed |
| `gpt-5.3-codex` | ⚠ available via Responses API `web_search` tool but not currently auto-injected (`src/llm_client.py:_build_responses_request`) — parked work |
| `glm-5.1`, `kimi-*`, `deepseek-*` | ❌ no native web; route web prompts to claude-cli/cursor-cli |

## `web_search` / `web_fetch` (`core/tools_web.py`)

Top-level chat tools registered in `WEB_TOOLS`. Both accept an
`engine` argument that resolves through a try-list:

| `engine` | Try order |
|---|---|
| `"auto"` (default) | firecrawl → claude-cli (if installed) → cursor-cli (if installed) |
| `"firecrawl"` | firecrawl only |
| `"claude-cli"` | claude-cli only (uses `_search_via_claude_cli` / `_fetch_via_claude_cli`) |
| `"cursor-cli"` | cursor-cli only (uses `_search_via_cursor_cli` / `_fetch_via_cursor_cli`) |

The CLI helpers do not depend on the parallel dispatcher — they call
`src.claude_cli_backend.claude_cli_call` / `src.cursor_agent_backend.cursor_agent_call`
directly with a single message and `permission_mode="bypassPermissions"` /
`yolo=True`. Use this when the agent only needs one search, not a TODO
batch. The dispatcher's `claude_tools=` flag is the right hook when
you're already fanning work out across N workers.

## Lessons (after first real run)

_Drop entries here only if they satisfy the
[[wiki-curation-policy]] write-trigger: decision-not-in-code,
pattern-across-IPs, policy-not-fix, external-reference, IP-handover.
Coding fixes belong in workflow source + commit messages, not
here._
