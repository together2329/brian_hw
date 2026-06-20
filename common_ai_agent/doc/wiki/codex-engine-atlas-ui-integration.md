# Codex Engine for Atlas UI Integration

Status: implemented for the Atlas checked-in local codex mode as of 2026-06-20:
`CODEX_BRIDGE=1`, `OAG_MODE=0`, and chat turns route through
`codex app-server --listen stdio://`.

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
