---
title: OAG_MODE — fuse a project's .codex OAG pack into the default agent
type: design
tags: [oag, codex, agents-md, default-agent, prompt-injection, tools, integration]
updated: 2026-06-16
related: [codex-rocev-agent-pack-20260611, cursor-agent-pack, platform-ontology, locked-truth-concept]
---

# OAG_MODE

Tightly fuse a project's `.codex` **OAG** (Ontology IP Agent) pack into the ATLAS
default agent. ATLAS is our own custom ReAct agent, so it does **not** need MCP to
use the OAG tools — it registers a native `oag` tool and calls the project's own
`.codex/scripts/oag_cli.py` gateway directly. The `.codex` MCP server
(`oag_mcp_server.py`) stays for external agents (Codex/Cursor); ATLAS bypasses it.

## What OAG_MODE=1 does

1. **Always reads the project's agent rules.** An `=== OAG / AGENTS.md ===` block
   built from `<root>/AGENTS.md`, `<root>/.codex/AGENTS.md`, and
   `<root>/.codex/rules/*.md` is appended to the **static system prompt** as a
   one-time rule block — it rides in the cached static layer (sent/cached once),
   not the per-turn dynamic context. This is **independent of the prompt-injection
   toggle** — OAG mode means "follow this project's rules".
2. **Exposes the native `oag` tool.** All 16 OAG tools
   (`oag.scaffold/inspect/context/compile/record/draft/ticket/check/decide/review/
   run.start/run.next/run.record/run.checkpoint/stop_check/graph`) are reachable
   via one tool that shells out to `.codex/scripts/oag_cli.py call --json`. It can
   also run a `.codex` script directly (`oag(script="oag_eval.py")`).

When OAG_MODE is off the `oag` tool is hidden (`filtered_available_tools`) and no
AGENTS.md is injected — the default agent is unchanged.

## Config

The `.codex` OAG pack is **vendored into common_ai_agent** (`common_ai_agent/.codex/`),
so OAG mode is **self-contained** — no external project needed. `.codex/AGENTS.md`
is the authoritative project agent doc (the ontology_ip_agent root AGENTS.md); the
original codex stub is kept as `.codex/AGENTS.codex.md`.

| env | meaning | default |
|---|---|---|
| `OAG_MODE` | master switch (`1/true/on`) | checked-in `.config`: on; code fallback with no env/config: off |
| `OAG_ROOT` | project holding `.codex/` | `OAG_ROOT` → `ATLAS_PROJECT_ROOT` → cwd → **platform root** (`common_ai_agent`, the vendored `.codex/`); first with `.codex/` or `AGENTS.md` |

## The `oag` tool

```
oag(tool="oag.run.next", ip="timer")
oag(tool="oag.inspect", ip="timer", stage="rtl-gen", intent="...")
oag(tool="oag.record", args_json='{"ip_dir":"timer","goal_id":"...", ...}')   # full args
oag(script="oag_eval.py")                                                      # raw .codex script
```
- `ip`/`stage`/`intent` are convenience shortcuts → `arguments.ip_dir/stage/intent`.
- `args_json` (a JSON object string) supplies the full argument set and wins over
  the shortcuts.

## Where it lives (ROCEV: REQ_PLAT_OAG_MODE_001)

- `src/config.py` — `OAG_MODE`, `OAG_ROOT` flags (`platform.config`).
- `core/prompt_builder.py` — `oag_mode_enabled()`, `oag_root()`,
  `_build_oag_agents_context()`, wired into `build_system_prompt`
  (`agent.prompt-builder`).
- `core/tools.py` — `oag()` tool + registry + `filtered_available_tools` gate;
  `core/tool_schema.py` — `oag` schema (`agent.tools`).
- `core/react_loop.py` — default worker native tool-call loop; if chat-mode
  iteration limits stop immediately after an OAG tool result, the tool tail is
  promoted to visible assistant text (`agent.react-loop`).
- `core/codex_appserver_bridge.py` — ATLAS web chat bridge for `CODEX_BRIDGE=1`;
  tool-only turns are promoted to visible assistant text if Codex emits tool
  output but no final `agentMessage` delta (`agent.codex-bridge`).
- Tests: `tests/test_oag_mode.py`.

## Checked-in default

As of 2026-06-16, the repository `.config` sets `OAG_MODE=1`. That makes local
ATLAS launches use the native OAG path by default without requiring a shell
export. The code fallback remains off when no env/config file provides
`OAG_MODE`, so hermetic tests and external embedders can still opt into the
feature explicitly.

## Web bridge visibility

Observed 2026-06-16: with either `OAG_MODE=1` alone (default worker native
tool-calls) or `OAG_MODE=1 CODEX_BRIDGE=1` (Codex app-server bridge), the model
can legally call `oag.inspect` and then end the turn without a natural-language
final message. The OAG result exists in the native tool response
(`oag_tool_response.v1`), but the ATLAS chat feed renders assistant text, so the
turn can look blank.

Both paths therefore treat "tool output but no assistant text" as visible
fallback. The default worker promotes the tail `role=tool` messages to a
bounded assistant message before returning the conversation; the Codex bridge
emits a bounded assistant token before `flush`/`done` and persists the same text
to the session conversation. Normal turns with real assistant text are unchanged.

## Context visibility

`/context -v` is the local audit surface for "why did the OAG worker behave that
way?" In OAG mode, AGENTS.md and `.codex/rules/*.md` are part of the ATLAS
worker's static system prompt, so the verbose context dump must show that local
system prompt text instead of replacing it with `System prompt hidden (...)`.
This exposes the ATLAS prompt that the app generated for its worker; it does not
expose any outer Codex/runtime private instructions.

## Proven

Live against `/Users/brian/Desktop/Project/ontology_ip_agent` (OAG_MODE=1):
`oag.inspect` on the `timer` IP returned a real `oag_tool_response.v1` (validation,
gaps, evidence), and the 22.8 KB AGENTS.md + rules block injected into the prompt.

## Next (deeper fusion, not yet wired)

- Run `.codex/hooks/*` (UserPromptSubmit context inject, Stop gate) inside the
  ATLAS turn lifecycle instead of only Codex's.
- Optionally point `oag_cli.py` at a real `common_ai_agent/scripts/oag.py` backend
  via `OAG_COMMON_AI_AGENT` (today the `.codex` self-contained gateway is used).
