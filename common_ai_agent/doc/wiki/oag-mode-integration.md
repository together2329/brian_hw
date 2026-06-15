---
title: OAG_MODE — fuse a project's .codex OAG pack into the default agent
type: design
tags: [oag, codex, agents-md, default-agent, prompt-injection, tools, integration]
updated: 2026-06-15
related: [codex-rocev-agent-pack-20260611, cursor-agent-pack, platform-ontology, locked-truth-concept]
---

# OAG_MODE

Tightly fuse a project's `.codex` **OAG** (Ontology IP Agent) pack into the ATLAS
default agent. ATLAS is our own custom ReAct agent, so it does **not** need MCP to
use the OAG tools — it registers a native `oag` tool and calls the project's own
`.codex/scripts/oag_cli.py` gateway directly. The `.codex` MCP server
(`oag_mcp_server.py`) stays for external agents (Codex/Cursor); ATLAS bypasses it.

## What OAG_MODE=1 does

1. **Always reads the project's agent rules.** Every turn, the system prompt gets
   an `=== OAG / AGENTS.md ===` block built from `<root>/AGENTS.md`,
   `<root>/.codex/AGENTS.md`, and `<root>/.codex/rules/*.md`. This is **independent
   of the prompt-injection toggle** — OAG mode means "follow this project's rules".
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
| `OAG_MODE` | master switch (`1/true/on`) | off |
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
- Tests: `tests/test_oag_mode.py`.

## Proven

Live against `/Users/brian/Desktop/Project/ontology_ip_agent` (OAG_MODE=1):
`oag.inspect` on the `timer` IP returned a real `oag_tool_response.v1` (validation,
gaps, evidence), and the 22.8 KB AGENTS.md + rules block injected into the prompt.

## Next (deeper fusion, not yet wired)

- Run `.codex/hooks/*` (UserPromptSubmit context inject, Stop gate) inside the
  ATLAS turn lifecycle instead of only Codex's.
- Optionally point `oag_cli.py` at a real `common_ai_agent/scripts/oag.py` backend
  via `OAG_COMMON_AI_AGENT` (today the `.codex` self-contained gateway is used).
