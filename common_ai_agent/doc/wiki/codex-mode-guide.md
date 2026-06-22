# Codex Mode Guide

ATLAS chat can run on two engines. As of 2026-06-22 the **default is Codex
mode**: chat turns route through `codex app-server` against a vendored OAG pack,
instead of the built-in Python ReAct engine.

```text
ATLAS Web UI ──WS──▶ atlas_ui gate ──▶ codex_appserver_bridge ──stdio JSON-RPC──▶ codex app-server
                       (CODEX_BRIDGE)        (run_codex_turn)                        └─ vendored .codex OAG pack
```

The browser never talks to codex directly. ATLAS chooses the engine, scopes the
session, normalizes codex events into the existing chat envelope, and records
evidence. Codex owns the turn loop, tool execution, hooks, skills, and subagents.

---

## 1. Engine switch (`.config`)

`common_ai_agent/.config`:

```bash
CODEX_BRIDGE=1                              # default: Codex engine. =0 → built-in `main` ReAct
CODEX_BRIDGE_HOME=ontology_ip_agent/.codex  # vendored OAG pack (resolved relative to common_ai_agent)
CODEX_BRIDGE_OAG_ROOT=ontology_ip_agent     # OAG project root visible to the app-server
CODEX_BRIDGE_ENABLE_HOOKS=1                 # codex native hooks (hooks.json: SessionStart/UserPromptSubmit/Stop)
CODEX_BRIDGE_RUN_OAG_HOOKS=1               # bridge also runs the OAG prompt hooks (context-inject)
CODEX_BRIDGE_STAGE_DOT_CODEX=1             # stage the pack into the turn's cwd so .codex-relative hooks resolve
CODEX_BRIDGE_TRUST_THREAD_CWD=1            # trust the thread cwd in CODEX_HOME config
CODEX_BRIDGE_BYPASS_HOOK_TRUST=1           # run staged hooks under app-server automation
OAG_MODE=0                                  # native ATLAS OAG injection OFF (codex reads the pack itself)
```

The engine gate is **truthiness-based** (`_truthy_env`): `1/true/yes/on` enable
it; `0/false/off/empty` fall back to the built-in `main` engine.

**Opt out** (use the built-in engine): set `CODEX_BRIDGE=0`.

### Optional env

| var | default | meaning |
|-----|---------|---------|
| `CODEX_BRIDGE_MULTI_AGENT_MODE` | (off) | `explicitRequestOnly` / `proactive` → force codex multi-agent so `/subagent` spawns. Off = surface whatever codex spawns on its own. |
| `CODEX_BRIDGE_SHOW_HOOKS` | `1` | show `🪝` hook / `📦` skill activity lines in chat. `0` hides them. |
| `CODEX_BRIDGE_BIN` | `codex` | codex binary on PATH. |
| `CODEX_BRIDGE_MODEL` | (codex default) | model override for the thread. |

---

## 2. Auth — IMPORTANT

Codex mode needs a logged-in codex CLI: **`~/.codex/auth.json`** (run `codex`
once and sign in). `CODEX_HOME` stays at `~/.codex` for auth — **do not** point
`CODEX_HOME` at the vendored pack (it has no `auth.json`); the bridge stages the
pack separately via `CODEX_BRIDGE_HOME`. Without auth, codex turns fail and the
UI shows an error banner.

---

## 3. The vendored OAG pack

`common_ai_agent/ontology_ip_agent/.codex/` is a checked-in copy of the OAG
pack (engine only — no IPs):

- `hooks/` + `hooks.json` — SessionStart / UserPromptSubmit / Stop hooks
  (context-inject, draft-pressure, mode-trigger, native-subagent-guard, …)
- `skills/` — `oag-ip-workflow` and friends (progressive-disclosure skills)
- `scripts/oag_cli.py` — the OAG gateway
- `rules/`, `agents/`, `schemas/`, `oag/`, `AGENTS.md`, `config.toml`

Runtime dirs (`.cache`, `runs`) are intentionally **not** vendored. IPs are
per-project (your session workspace / an external project), not part of the pack.

---

## 4. What you see in the UI

- **Subagent lanes (left WORKFLOW panel).** When codex spawns subagents
  (`/subagent`, multi-agent mode), `Main [default]` shows on top with the
  spawned agents indented below (nickname/role + thread id). Click a row → the
  **main chat pane** renders that agent's transcript; click `Main` to return to
  the original conversation (the main feed is preserved). A team of N agents = N
  lanes.
- **Hooks (`🪝`) + skill load (`📦`).** Each OAG hook firing shows as an
  activity line with its status message, e.g. `🪝 OAG: injecting IP context`,
  `📦 skill set loaded`. Hide with `CODEX_BRIDGE_SHOW_HOOKS=0`.
- **Reasoning / tool calls / file diffs / command output** stream into the chat
  as the usual reasoning/action/obs cards.

---

## 5. Run it

```bash
cd common_ai_agent
python3 scripts/run_atlas_codex.py            # vendored pack, :3041, hooks visible
#   --pack <dir>   project holding .codex (default: vendored ontology_ip_agent;
#                  use ~/Desktop/Project/ip_dev to run against that project's IPs)
#   --port <N>     server port (default 3041)
#   --no-build     skip the vite dist rebuild
```

The launcher temporarily writes the codex config into `.config` (restored on
exit — survives Ctrl-C), rebuilds the vite dist, frees the port, and serves on
`ATLAS_FRONTEND_MODE=vite`. Open `http://localhost:<port>` (admin/1151) and send
any prompt; OAG hooks (`🪝`) and skill load (`📦`) appear in the chat. Auth stays
on `~/.codex`.

Manual equivalent:

```bash
cd frontend/atlas && npm run build && cd ../..
ATLAS_FRONTEND_MODE=vite python3 src/atlas_ui.py --port 3041
```

---

## 6. Verify

| what | how |
|------|-----|
| config defaults | `pytest tests/test_oag_mode.py::test_repo_config_defaults_to_codex_mode` |
| gate truthiness | `pytest tests/test_oag_mode.py::test_codex_bridge_gate_honors_truthiness` |
| bridge ↔ real codex (hooks fire, ledger injected) | `python3 scripts/verify_oag_hook.py` / `verify_oag_turn.py` |
| subagent lanes in the browser | `node scripts/verify_subagent_ui_broad.mjs` (server running) |
| ontology | `python3 scripts/platform_ontology.py check` |

---

## 7. Troubleshooting

- **No response / error banner** → codex not authed. Run `codex` and sign in
  (`~/.codex/auth.json`).
- **No `🪝`/`📦` lines** → `CODEX_BRIDGE_ENABLE_HOOKS`/`CODEX_BRIDGE_RUN_OAG_HOOKS`
  off, or `CODEX_BRIDGE_SHOW_HOOKS=0`, or the pack didn't stage (check
  `CODEX_BRIDGE_HOME` resolves to an existing `.codex`).
- **Stale UI after a code change** → rebuild the vite dist (`npm run build`) and
  hard-refresh; the running server's `.config`/env wins over later edits until
  restart.
- **Want the old engine** → `CODEX_BRIDGE=0` (built-in `main` ReAct).

See also: [codex-engine-atlas-ui-integration.md](codex-engine-atlas-ui-integration.md).
