# Desktop local tool execution — plan (2026-06-03)

**STATUS: PLAN / future direction.** Not shipped. Builds directly on
[[local-iproot-thin-llm-server-arch-20260529]] (Variant A / Variant B framing)
and adds what was *confirmed/discovered* in the 2026-06-03 session: the tool
dispatch seam (verified against code), EDA packaging reality, the git-access
security work, and the connection to the 100-concurrent-user ceiling. Related:
[[frontend-modernization-2026-05-29]] (Tauri) · [[tech-direction-recommendation-20260529]]
· [[atlas-context-root-model-20260603]] · [[common-ai-agent-map]].

## The idea (user, 2026-06-03)

> Process **all tool calls locally**, and do **only the LLM call on the server**.
> Each user ultimately works on their own local machine; the Desktop App pulls
> the IP (`.git` root) from the server and works locally.

This is **Variant A** from [[local-iproot-thin-llm-server-arch-20260529]] (local
agent loop + local tools; the remote shrinks to an **LLM gateway/license only**),
with git as the sync substrate between the local working copy and the server's
bare repos. Confirmed feasible this session. The user is leaning this way; the
open `고민` (below) is mainly the LLM-license model and Variant A vs B.

## Why this is the real answer to the 100-user ceiling

The 100-concurrent-user readiness review found the central server caps at **~30
active interactive workers** (`core/session_worker_policy.py`,
`ATLAS_SESSION_WORKER_MAX_ACTIVE=30`), plus single-SQLite / single-uvicorn-event-loop
/ shared-LLM-429 ceilings — all because 100 users were crammed onto ONE server
running one agent worker each.

**Variant A removes that ceiling by construction:** the agent loop runs on each
user's machine, so there is **no server-side `session_worker` per user** → the
30-worker cap simply does not apply to local-loop users. The server's remaining
job is a **stateless LLM gateway** (+ auth + git remote), which scales like any
API proxy well past 100. Heavy tool compute (RTL elaborate/sim/lint) and disk
move to each machine; tenant file isolation becomes natural (each user only has
their own working copy).

## Three configurations (pick the split)

| Config | Agent loop | Tool exec | LLM | Server role | 100-user ceiling | Local footprint |
|---|---|---|---|---|---|---|
| **A — local-first + LLM gateway** ⭐ user's lean | **local** | **local** | **server gateway** | LLM proxy + auth + git remote | **gone** (no server worker) | full local Python backend |
| **A′ — fully local** | local | local | local (own key) | git remote only | gone | full local Python backend + own LLM key |
| **B — remote brain / local hands** | **server** | **local** (tunneled) | server | runs the loop + LLM; tunnels tools out | **partial** (server still runs a loop per user) | thin (Rust executor, *zero local Python*) |

- **A** keeps LLM keys/metering central (no key distribution to 100 clients) and
  still removes the worker ceiling. Cost: a full local Python backend per machine
  (packaging — see below).
- **A′** is the simplest server-wise (server = git only) but distributes raw LLM
  keys to every client (key-management / cost-control problem).
- **B** is the only config that needs **no local Python** (the loop is remote; the
  Tauri Rust shell is the local tool-runner), but it is materially harder and does
  **not** fully remove the server ceiling (a remote loop still runs per active
  user, now blocked awaiting a tunneled tool result). See
  [[local-iproot-thin-llm-server-arch-20260529]] §"Two variants".

## The dispatch seam (verified 2026-06-03)

Confirmed in code: **`core/tool_dispatcher.py` `dispatch_tool()` is the single
chokepoint** where every tool executes (resolves the tool by name from an injected
`available_tools: Dict[str, Callable]`, calls it via `_call_with_timeout`, returns
the result synchronously). `core/react_loop.py` drives it; today the whole ReAct
task (LLM loop **and** tools) runs in-process inside one worker
(`src/atlas_worker_ipc.py` `_run_react_task`, JSON request/response files,
`ATLAS_WORKER_TRANSPORT="ipc"`) — there is **no per-tool IPC** yet.

Implication:
- **Variant A needs no seam change** — the loop is local, so tools already run
  in-process locally. Zero round-trip latency. This is the lightest path *logically*.
- **Variant B** would intercept exactly here: wrap `dispatch_tool` so file/EDA/git
  tools are sent over a transport to the local executor instead of called in-process.

## Tool split (which side runs what)

| Local (file/process-bound) | Server (state/UI/network-bound) |
|---|---|
| read/write/replace_in_file, list_dir, grep_file, run_command | ask_user (UI card), web/search |
| RTL elaborate / sim / lint (pyslang, iverilog, verilator, cocotb), vcd, coverage | ssot canonical writes, memory |
| git / scm (`core/scm.py`) | anything touching AtlasDB / sessions / chat |

Rule: **if it touches the IP working tree or spawns a process → local** (and the
files MUST be present locally — hence the git working copy + sync is a hard
prerequisite). State/UI/network → server.

## Transport (only needed for Variant B)

Reverse-tunnel over the **existing `/ws/agent` WebSocket**: the client connects
*out* to the server, so the server can push "run this tool" down that connection
and read the result back — **no inbound port/firewall on the client**. The worker
IPC JSON request/response envelope (`src/atlas_worker_ipc.py`) is the precedent for
the message shape (today task-grained; Variant B makes it tool-grained).
Caveat: ReAct loops are chatty (many read/grep/edit/run per turn) → each becomes a
round-trip. And a server telling the client to `run_command` is **remote code
execution on the user's box** → needs a tool whitelist + IP-dir confinement +
permission model (the problem Claude Code solves with permission prompts).

## Git as the sync substrate + access security

The Desktop App pulls the IP (`.git` root) from the server and works on a **local
working copy**; commits/pushes sync back to the server's bare repos
(`core/scm.py`). Because the **app** is the git client (not a human typing
`git clone`), it holds the session token → **HTTPS + token is the natural auth**;
no anonymous access needed.

This is wired to the 2026-06-03 **B1 git-access security work**:
- `/git/` smart-HTTP proxy is gated; `ATLAS_GIT_ANON_READ` controls anonymous
  fetch (set **`ATLAS_GIT_ANON_READ=0`** for this model — the app authenticates).
- The per-IP authorization gate (`core/atlas_fs_authz.py` + the `_fs_authz`
  adapter) enforces *who can pull which IP* at the server — exactly the access
  control this distributed model needs. (Default bind is `127.0.0.1`; a real
  multi-user deploy binds `0.0.0.0`/LAN, which is why the gate matters.)

## Database — keep the control plane CENTRAL (user wants this, 2026-06-03)

The DB is **not** all-or-nothing local. ATLAS already splits it
([[atlas-db-router-runtime-sharding-20260602]], branch `feat/runtime-db-100users`,
`core/atlas_db_router.py` + `core/runtime_rollup.py`), which maps cleanly:

| DB | Contents | Where | Why |
|---|---|---|---|
| **Control DB (`atlas.db`)** | users, auth, `ip_blocks` ACL, workspaces, licensing/metering, usage rollups, jobs index, admin dashboard, cross-user coordination | **CENTRAL (server) — managed** | single source of truth for identity/ACL/cost; backed up; admin visibility ([[admin-operational-dashboard-db-snapshot-20260603]]) |
| **Runtime DB (per-session, sharded)** | hot per-session prompt / worker / token / todo working state | **local (per machine)** | hot writes stay off the shared DB → removes the single-SQLite contention ceiling |

Flow: the local agent writes session working state to its **local runtime DB**;
low-frequency control-plane ops (login, ACL check, usage report) hit the **central
control DB** over a thin API; `core/runtime_rollup.py` (idempotent, no fanout)
**rolls usage/metadata up** into the central control DB for management + the admin
dashboard. So "DB를 관리하고 싶다" = keep the **control DB central**, push only the
hot per-session runtime writes local.

Why it still scales: the central control DB takes only **low-rate control-plane
writes** (logins, ACL, batched rollups) — NOT per-token hot writes — so one central
SQLite can serve 100 users (the 100-user review flagged Postgres as the eventual
control-DB step, but local-first removes most of that pressure; adopt Postgres only
if the control-plane write rate ever warrants it).

> If you instead want the WHOLE DB central (all session state on the server too):
> doable, but it reintroduces the single-writer SQLite contention the runtime-DB
> sharding was built to avoid — then Postgres for the control DB is the real fix,
> and per-message writes round-trip to the server (latency + central load).

**2026-06-03 follow-up — "SQLite + LLM call on the server, tools local":** the
agent loop is glued to the DB, so this forks on where the loop runs:

| Config | loop | DB | LLM | tools | 30-worker ceiling | trade |
|---|---|---|---|---|---|---|
| **Variant B** (= "all SQLite + LLM server, tools local") | **server** | server (all) | server | local | **stays** | clean DB/LLM, but server loop per user + tool-tunnel latency + RCE security |
| **Split (recommended)** | **local** | control=server / runtime=local | server | local | **gone** | "DB managed centrally" still holds via control DB + rollup |

So "SQLite 서버로" literally = **Variant B** (remote brain / local hands) — coherent
and gives central DB + LLM, but the server still runs a loop per active user (the
30-cap and single-event-loop pressure remain, and tools now round-trip). To ALSO
remove the ceiling, keep the **loop local** and put only the **control DB** central
(runtime DB local + `runtime_rollup` up) — you still "manage the DB centrally," just
not the hot per-message writes.

## Packaging — can the Python + EDA tools ship with the Desktop App?

**Yes (Tauri "Option B": PyInstaller freeze + Tauri `externalBin` sidecar)** —
already named as deferred in `src-tauri/src` / [[tauri-desktop-shell]].

Python code, FastAPI, and compiled wheels freeze fine. The hard part is the **EDA
native tools** (called via `run_command`, not Python):

| Tool | Form | Bundle difficulty | License | Note |
|---|---|---|---|---|
| **pyslang** | Python wheel (C++ ext) | ★ trivial | MIT | rides along in the PyInstaller freeze; **no separate binary** |
| **iverilog** | self-contained native (`iverilog`+`vvp`) | ★★ medium | GPLv2 | bundle binaries + relocatable libdir (`IVERILOG_*`); copyleft compliance |
| **verilator** | **code generator** (compiles generated C++ at runtime) | ★★★ hard | LGPL/Artistic | needs gcc/clang+make on target → **not self-contained** |

Recommendation: **pyslang (elaborate/lint) + iverilog (sim)** as the bundle-friendly
combo; treat **verilator as assume-preinstalled** (or only enable when a C++
toolchain is present). cocotb is a Python wheel but still needs an underlying
simulator → pair with iverilog.

> Packaging tension: Variant A/A′ run a full local Python backend → packaging +
> EDA-deps matter on every machine. Variant B's appeal was **zero local Python**
> (Rust executor) — but B is the harder refactor. This is part of the `고민`.

## The open `고민` (decisions deferred)

1. **LLM model**: gateway/license-server (A, central keys+metering) vs fully-local
   key (A′, simplest server but key distribution).
2. **A vs B**: A = no tool-layer refactor + zero latency, but full local Python +
   EDA packaging per machine. B = zero local Python + central updates, but tool-layer
   split + chatty-loop latency + RCE security model.
3. **Sync conflicts**: two users on one IP → git merge. Reuse the existing
   `ip_blocks` ACL / owner-slot as a single-writer lock, or per-user branches.

## Phased roadmap (PoC → end state)

1. **PoC (Variant A, headless)**: launch the local backend against a local `--root`
   (already works), reduce the remote to an LLM gateway in `src/llm_client.py`
   (`base_url` → server proxy). Prove "tools local, LLM remote" end-to-end with no
   server worker.
2. **Tauri Option B**: PyInstaller-freeze the backend + `externalBin` sidecar so the
   shell owns the local backend lifecycle (folder picker → `ATLAS_PROJECT_ROOT`).
3. **Git sync**: app authenticates (token) → clone/pull/push IP to/from server bare
   repos; `ATLAS_GIT_ANON_READ=0`; per-IP pull authorized by `_fs_authz`.
4. **Thin the server**: drop per-user workers; server = LLM gateway + auth/ACL + git
   remote (keep the web UI as a fallback for users who can't run local).
5. **(Optional) Variant B** later if "zero local Python" becomes the priority —
   wrap `dispatch_tool`, tunnel over `/ws/agent`, add the permission/sandbox model.

## One-line

ATLAS already supports a **local IP-root (`--root`)** and a **decoupled LLM layer**,
and the tool dispatch is a **single seam (`dispatch_tool`)** — so "tools local, LLM
on the server" (Variant A) is feasible, **removes the 30-worker ceiling**, and the
only real builds are LLM-gateway wiring, Tauri Option-B packaging (pyslang+iverilog
bundle, verilator preinstalled), and git sync secured by the B1 per-IP gate.
