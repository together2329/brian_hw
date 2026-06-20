# Codex Engine for Atlas UI Integration

Status: the Codex app-server bridge is implemented and **opt-in** as of
2026-06-20. The default chat engine is `main` (the built-in Python ReAct
engine); set `CODEX_BRIDGE=1` (with `OAG_MODE=0`) to route chat turns through
`codex app-server --listen stdio://`. The gate honors truthiness, so the
checked-in `.config` default `CODEX_BRIDGE=0` keeps the built-in `main` engine.
When the bridge is enabled, codex native subagents (`/subagent`, multi-agent
mode) surface as dedicated lanes in the Atlas left workflow panel.

## Decision Shape

Codex can be used as the default-agent execution engine, but Atlas remains the
workflow authority.

```text
Atlas UI
  -> Atlas API / WebSocket / SSE
    -> Agent Engine Adapter
      -> legacy engine or Codex engine
        -> Atlas MCP/tools/workflow APIs
```

The browser should not call Codex directly. The UI talks only to Atlas. Atlas
chooses the engine, applies locked-truth policy, normalizes events, and records
evidence.

## Ownership Split

Codex owns execution mechanics:

```text
LLM turn loop
tool-call execution
streaming response
context/session handling
single active worker execution
prompt/skill instruction following
```

Atlas owns product authority:

```text
user / session / workspace / IP scope
requirement-level locked truth
ask_user Q&A and approval manifest
workflow dispatch guard
req -> obligation -> contract_ref -> evidence -> validator_result structure
deterministic pass/fail/blocked/waived judgment
signoff and artifact ownership
UI transcript and pipeline state
```

The important boundary:

```text
Codex is an execution engine.
Atlas is the lock, workflow, evidence, and UI control layer.
```

## UI Event Mapping

Atlas should convert Codex events into the existing Atlas transcript surface.

```text
Codex assistant text  -> AGENT row
Codex tool_call       -> ACTION row
Codex tool_result     -> OBS row
Codex ask_user tool   -> Q&A card
Codex final answer    -> AGENT final
Codex error/blocked   -> fail/blocked banner
```

This keeps the UI stable while allowing the backend engine to change.

## Role of Skill, MCP, Hook, and Subagent

Skill is behavior guidance:

```text
locked truth first
short tiktaka
ask_user for missing decisions
do not dump full drafts unless requested
do not treat legacy RTL/doc/SSOT as authority
```

Skill is useful, but not a hard guard.

MCP/tools expose Atlas actions to Codex:

```text
atlas.get_lock_status
atlas.ask_user
atlas.lock_requirement
atlas.dispatch_workflow
atlas.run_validator
atlas.read_pipeline_state
```

MCP/tools are the right bridge for engine integration, but dispatch still needs
server-side guard enforcement.

API guard is the real policy gate:

```text
if not every required requirement is locked or approved:
  reject dispatch_workflow
```

This prevents accidental tool calls from starting implementation before locked
truth is complete.

Hook is a safety net:

```text
detect locked-truth file mutation
restore protected files
audit invalid dispatch attempts
clean stale stop / interrupt / queue fences
surface server-side logs
```

Hooks should not be the primary policy mechanism because they run after, or
around, tool execution.

Subagents are a later owner-worker layer:

```text
ssot-owner
model-owner
rtl-owner
tb-owner
sim-owner
```

They are useful for orchestrator mode, but unnecessary for the MVP default
worker.

## MVP Recommendation

Keep the MVP small:

```text
1. Keep the existing Atlas UI.
2. Keep the default single active worker.
3. Add an engine switch: ATLAS_AGENT_ENGINE=legacy|codex.
4. Add a Codex runner adapter behind the existing API/WebSocket route.
5. Normalize Codex events into existing Atlas transcript events.
6. Route Codex ask_user to the existing Q&A card.
7. Keep workflow dispatch behind existing Atlas API guard.
8. Keep requirement lock and validator authority in Atlas.
```

Do not start with full orchestrator replacement, subagent owner routing, or
browser-to-Codex direct calls.

## Locked Truth Interaction

The default-agent front door should remain conversational.

Before all required requirements are locked:

```text
allowed:
  ask_user
  read existing docs/RTL/SSOT as candidate evidence
  summarize captured decisions
  identify the next missing requirement decision

blocked:
  dispatch_workflow
  generate RTL/TB/SIM
  mutate implementation artifacts
  mark legacy-derived requirements locked without user approval
```

After all required requirements are locked or approved:

```text
allowed:
  ssot-gen / fl-model-gen / rtl-gen / tb-gen / sim
  contract reflection
  evidence validation
  owner-routed repair loop
```

This is why the lock state should be requirement-level, with IP-level lock as
the derived condition:

```text
ip_locked = every required requirement is locked or approved
```

## Why This Is Better Than Prompt Only

Prompt-only control is weak. It can ask Codex to behave, but cannot guarantee
behavior.

The robust shape is layered:

```text
Skill/prompt:
  tells Codex what to do

MCP/tool surface:
  gives Codex only named Atlas operations

API guard:
  rejects illegal operations deterministically

Hook:
  audits and restores if something still slips through

Validator:
  decides pass/fail/blocked from artifacts, not prose
```

That keeps Codex useful without making it the authority for truth or signoff.

## Subagent Lanes (codex `/subagent` → Atlas left workflow panel)

When the codex bridge is enabled (`CODEX_BRIDGE=1`) and the conversation uses
codex multi-agent mode, the main codex agent can spawn **subagents** (the
`/subagent` flow / `spawn_agent` collab tool). Codex surfaces that activity to
the app-server client stream as dedicated `ThreadItem`s on the parent thread:

```text
collabToolCall   {id, tool, status, senderThreadId, receiverThreadId?,
                  newThreadId?, prompt?, agentStatus?}
                  tool ∈ spawn_agent | send_input | resume_agent | wait | close_agent
subAgentActivity {kind, agent_thread_id}
```

Child-thread `item/*` notifications also carry a `threadId` distinct from the
main thread id when the app-server forwards them.

The bridge normalizes all of this into ONE new Atlas envelope event so the UI
contract stays stable (same `session.emit(...)` channel the frontend already
consumes):

```text
session.emit("subagent",
  agent_id   = <child thread id | receiverThreadId>   # lane key (required)
  parent_id  = <parent/main thread id>
  label      = <agent nickname/role, else a derived label>
  status     = spawning | running | waiting | completed | failed | closed
  kind       = spawn | message | reasoning | tool | tool_result | status | result
  text       = <prompt on spawn · delta on message/reasoning · label on tool ·
                body on result>
)
```

Mapping (bridge `on_note`):

```text
collabToolCall spawn_agent  -> subagent(kind=spawn,   status=spawning/running, text=prompt)
collabToolCall wait/result  -> subagent(kind=result,  status=completed/failed, text=body)
collabToolCall send_input   -> subagent(kind=message, text=prompt)
subAgentActivity            -> subagent(kind=status,  status=<kind>)
item/* with foreign threadId-> subagent(kind=message|reasoning|tool, text=delta)  # best-effort live transcript
```

Frontend: `workspace-root-data-hook.tsx` subscribes to `subagent` and keeps a
`subagentLanes` map keyed by `agent_id`; `workspace-subagent-lanes.tsx` renders
each lane (label + status) in the left workflow panel
(`workspace-rootui-rail-tabs.tsx` `left-workflow-box`), expandable to show that
subagent's running transcript. The main chat feed is unchanged — subagent chat
lives in its own left-rail lanes, not inline.

Enablement: by default the bridge only **surfaces** whatever subagent activity
codex already emits (codex's own config/skills drive `/subagent` spawning), so
no process/turn flags change out of the box. Set
`CODEX_BRIDGE_MULTI_AGENT_MODE=explicitRequestOnly` (or `proactive`) to have the
bridge force-enable multi-agent mode (adds `-c features.multi_agent_mode=true`
to the app-server command and `multiAgentMode` to `turn/start`, with a
retry-without-param fallback for older builds). If codex never spawns a
subagent, no lanes appear (graceful).
