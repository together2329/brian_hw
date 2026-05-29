# Local IP-root + thin LLM-license server (desktop-app architecture)

**STATUS: design concept / direction** — documents an architecture that ATLAS is
*already mostly built for*, plus the small gap to fully realize it. Not a record
of shipped behavior; the "already works" parts are verified against config/code
(file:line below), the "needed" parts are not yet implemented.

Idea (user, 2026-05-29): the remote **server provides only the LLM license/access**;
the actual IP work (`ROOT_IP`) runs against a **local filesystem path**. Natural fit
for the Desktop App direction. Related: [[frontend-modernization-2026-05-29]]
(Tauri) · [[tech-direction-recommendation-20260529]] · [[common-ai-agent-map]].

## Why it's already half-built: root separation

ATLAS separates "app code location" from "IP work location" as a first-class
config feature (`.config:44-58`, `src/config.py:158-165`):

| Var | Meaning |
|---|---|
| `ATLAS_SOURCE_ROOT` | the app code (this common_ai_agent checkout) |
| `ATLAS_WORKFLOW_ROOT` | workflow scripts/templates (`SOURCE_ROOT/workflow`) |
| `ATLAS_PROJECT_ROOT` | **parent dir holding IP dirs** (default = launch cwd) |
| `ATLAS_IP_ROOT` | optionally pin one active IP dir |

- `src/config.py:158-165` resolves `ATLAS_PROJECT_ROOT` / `ATLAS_IP_ROOT` via
  `_resolve_env_path(...)` → **accepts an arbitrary local path.**
- CLI flags already exist (`.config:51-52`):
  `python -m src.atlas_ui --workflow-root "$PWD/workflow" --root /path/to/IP_PARENT`
  and `--ip-root /path/to/IP_PARENT/<ip>`.
- `IP_ROOT` defaults to cwd — "where IPs live as direct subdirs" (`config.py:2621`).
- `ROOT_IP` is literally used as the example IP-parent path in code/comments
  (`config.py:2628`, `core/tools.py:686`), and is in active use today by a separate
  agent working under `~/Desktop/Project/ROOT_IP/`.

→ **Pointing the work at a local `ROOT_IP` path already works today via `--root`.**

## Why "server = LLM license only" is already separable

LLM access is its own config layer (`src/llm_client.py` + keys/provider in `.env`),
independent of the file/IP layer (`PROJECT_ROOT`). "Which LLM / which credentials"
is not coupled to "which files the agent edits." So the LLM-access concern can be
reduced to a thin remote without touching the file/work model.

## The Desktop App makes it clean

```
[Local machine — Desktop App]
  Tauri shell ──launches──> local FastAPI backend
              ATLAS_PROJECT_ROOT = user-picked local folder (e.g. ~/Desktop/Project/ROOT_IP)
              agent + workflow + atlas.db + files  →  all run locally against that path
        │
        └──(only outbound dependency)──> [Remote = LLM license / gateway ONLY]
```

- Local: agent loop, workflow stages, SQLite DB, file edits — all on the user's machine.
- Remote: just LLM license/access (metering, auth, or a proxy).
- SOURCE-side vs PROJECT-side split is already the design: `atlas.db` / `dist` /
  app code live under `SOURCE_ROOT`; IP work lives under `PROJECT_ROOT`.

## What already exists vs what's needed

| Already exists ✅ | Needs building |
|---|---|
| Root separation (`SOURCE` vs `PROJECT`/`IP`) + `--root` / `--ip-root` flags + cwd default | Tauri native **folder picker** → inject choice as `ATLAS_PROJECT_ROOT` |
| LLM access as a separate layer (`llm_client.py` + `.env`) | LLM-license model decision (below) |
| Tauri shell scaffolding in progress (Tauri loads the vite build output) | Tauri launches/owns the local FastAPI backend lifecycle |

**LLM-license model — pick one:**
- (a) **Fully local** — user's own API key in local `.env`; no remote at all.
- (b) **Thin remote license/proxy** — desktop app authenticates to a remote that
  meters/proxies LLM calls so users don't hold raw keys. (This is the
  "server = LLM license only" model the user described.)

## Two variants (which "thin server"?)

**Variant A — all-local + thin LLM server** (the model above). Python backend runs
LOCALLY; remote = LLM license/access only. Already half-built (`--root` + decoupled
LLM layer). **Tauri is NOT the enabler here** — this works today headless/CLI/browser
via `--root`; Tauri only adds packaging/UX (folder picker, bundled app, no terminal).

**Variant B — remote agent, local executor (remote brain / local hands)** — harder.
Run the **Python agent loop on a remote server**, but execute **tool calls + file I/O
locally** against `ROOT_IP`. This is the Claude Code / LSP / MCP pattern (remote
reasons, local acts). Materially harder than A, because today the tool layer
(`core/tools.py`) executes **in-process** with the loop (`core/react_loop.py`). To
split it:
- Decouple tool *invocation* (remote decides) from *execution* (local runs).
- Add a remote↔local **tool-call transport** (RPC over WebSocket — ATLAS already has
  `/ws/agent` to build on).
- Accept **latency**: ReAct loops are chatty (many read/grep/edit/run per turn) →
  each becomes a network round-trip.
- **Security gating**: a remote server telling the local box to run bash is remote
  code execution on the user's machine — needs permission/sandbox (the problem
  Claude Code solves with permission prompts).

In Variant B the **local client (Tauri shell, or a small daemon/CLI/MCP server)
becomes the local tool-runner** — a genuine, essential role (unlike Variant A where
Tauri is just packaging). Tauri's Rust shell has native FS + process access, so it
is a natural host for that local executor, driven over WS by the remote agent.

Difficulty: A = small gap (folder picker + launch). B = a real tool-layer refactor +
transport + latency/security design (medium–large).

## Strategic conclusion — why a desktop app at all

The defining capability of a desktop app vs a browser web UI is exactly one thing:
**local execution / local filesystem access** (browsers sandbox this away). A web UI
+ remote server can already do everything *except* touch the user's machine. So:

> **No local execution → the desktop app is just a heavier Chrome tab.**

Consequences:
- **Variant A is NOT architecturally new.** Today's ATLAS is already "local FastAPI
  server + browser web UI." Wrapping that in Tauri is the *same* architecture in a
  native window — Tauri adds only UX/distribution (folder picker, double-click app,
  no terminal). If you don't need more than that, the web UI is strictly simpler.
- **The worthwhile desktop play is Variant B** (remote brain / local hands) — it is
  the only configuration that delivers something a web UI fundamentally cannot:
  a cloud-managed agent acting on the user's *local* files.

Why B is worth its harder engineering — the real payoff is more than "local files":
- 🟢 **Zero local Python/deps** — the brain runs in a managed server env, so users
  never hit the local-interpreter hell (e.g. the markitdown / Python-3.9-vs-3.10
  mismatch). The local executor can be the Tauri Rust binary — **no local Python at
  all.**
- 🟢 **Central LLM license/metering** (the original "server = LLM license only" idea).
- 🟢 **Updates ship server-side**; the user keeps a thin client.
- 🟢 **Still acts on local files** — the thing the web UI can't do.

This is the **Claude Code / Cursor model**: heavy/managed brain remote, hands local.

**Decision rule:** if building a desktop app, build Variant B (local execution is the
only differentiator, and B maximizes it while removing the local-Python burden). If
Variant B's value isn't wanted, don't build a desktop app — keep the web UI, which
is simpler and architecturally equivalent to Variant A.

## Verification needed before committing
Confirm **no backend code assumes IP files live under `SOURCE_ROOT`** (vs the
separated `PROJECT_ROOT`). The design separates them, but audit edge cases — any
hardcoded co-location would break the local-path / desktop model. `atlas.db` and
`dist/` are correctly SOURCE-side; the audit is about whether any IP read/write or
path-join silently roots at SOURCE instead of PROJECT/IP.

## One-line
ATLAS already supports a **local IP-root via `--root`** and a **decoupled LLM layer**;
the Desktop App (Tauri) turns this into "local backend + folder-picker + remote
reduced to LLM-license-only." The only real gaps are the folder-picker wiring, the
Tauri→backend launch, and choosing the license model — plus a SOURCE-vs-PROJECT
co-location audit.
