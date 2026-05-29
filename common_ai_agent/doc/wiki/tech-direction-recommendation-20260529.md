# Tech Direction Recommendation — language / runtime / build (2026-05-29)

Strategic recommendation on which technologies `common_ai_agent` (ATLAS) should
move toward, evaluated against Go, Rust, Python, Node.js, Bun, jsx, tsx, ts.
Grounded in measured stack size and the latency bottlenecks already identified
this session — not generic language opinions.

Related: [[common-ai-agent-map]] · [[atlas-modular-refactor-status-20260528]] ·
[[workspace-jsx-decomposition-plan]] · [[atlas-refactoring-review-20260528]]

## Current state (measured 2026-05-29)

| Layer | Stack | Scale |
|---|---|---|
| Backend | **Python** (FastAPI + uvicorn + anthropic + httpx) | **361,895 LOC / 838 files** — the actual product |
| Frontend | **React** (jsx 44.7k + tsx 37.2k ≈ 82k LOC), buildless babel-in-browser, mid jsx→tsx migration | ~82k LOC |
| JS runtime | **Node** (`.nvmrc` present, no `bun.lockb`) | small |
| Go / Rust | **none** | — |
| Tauri (desktop) | referenced only in `vite.config.ts` comment; **no `tauri.conf.json` / `src-tauri`** | does not exist yet |

## Core principle: the agent is I/O-bound, not CPU-bound

A language switch (Go/Rust) only helps **CPU-bound + high-concurrency** work.
This project is not that:

- LLM API calls (anthropic/httpx) — network-bound waiting
- EDA tool subprocesses (`verilator`/`iverilog`/`yosys`/`cocotb`) — the heavy
  compute is **already in external C++ tools**; Python only orchestrates.

The three real slowness causes found this session are **all language-independent**:
1. DB wrapper re-init overhead per `with AtlasDB()` (already fixed: 7.85ms→0.012ms)
2. Worker model latency: glm-5.1 ~80s/call vs gpt-5.3-codex ~10s (~8×) — a model
   selection / `.env` default problem, not code
3. Frontend babel-in-browser load cost (see below)

Switching the backend language fixes none of these.

## Frontend buildless cost (why the UI feels heavy on first load)

The web UI has been React since its first commit (`80c847e6`, 2026-04-29) — there
was never a vanilla-JS phase. But it is served **buildless**: React/ReactDOM and
**Babel standalone** are loaded via `<script>` from `vendor/`, and `.jsx` files
are `<script type="text/babel" data-presets="react">` transpiled **in the browser
on every page load**.

Measured per-load cost:
- 34 jsx files transpiled in-browser = **43,907 lines / 1.9 MB**
- `workspace.jsx` alone = 13,286 lines
- `babel.min.js` = 3.0 MB to fetch + parse
- no service worker / precompiled cache → re-transpiled on every reload

`.tsx` is currently **not served at runtime** at all: html loads only `.jsx`,
babel has no typescript preset, and `vite.config.ts` says the build is wired at
the "Phase 4 cutover" when `app.tsx` becomes the entry. tsx is presently verified
only by vitest smoke tests.

## Per-technology verdict

### Python backend → keep. Do not rewrite.
362k LOC of domain logic (ReAct loop, IP workflow engine, tool system, FastAPI
server `atlas_ui.py` ~10k LOC). Rewrite = years lost, **zero ROI**. Python is the
AI-ecosystem home (anthropic SDK). Async I/O already covered by uvicorn/httpx.

### Rust / Go → no wholesale adoption. Surgical only.
The only justified entry: a pure-Python **CPU hotspot proven by profiling**
(e.g. Verilog parsing in `core/simple_linter.py`, `core/tools_verilog.py`) → wrap
*that function* in Rust via PyO3/maturin. Pinpoint, not rewrite. Go has
essentially no place here unless a separate high-throughput network service is
introduced. **Precondition: prove the hotspot first; never adopt on speculation.**

### jsx / tsx / ts → finish the TSX/TS migration, retire jsx.
Already at 89 tsx files / 37k LOC. Type safety across an 82k-LOC UI is a large
maintainability win. Rule: **components (with JSX) = `.tsx`**, **pure logic
(`lib/*.js`) = `.ts`** (not `.tsx`), **`styles.css` stays CSS**. Remaining work:
migrate the giant `workspace.jsx` (13k LOC) and wire `app.tsx` as the entry.
See [[workspace-jsx-decomposition-plan]].

### Vite build cutover → highest-leverage single move (★)
Turning on `vite build` simultaneously: ① removes `babel.min.js` (3 MB) + the
per-load 1.9 MB transpile → **kills the front-end load slowness**, ② enables
tsx-only, ③ enables npm libraries (e.g. React Flow), ④ enables full build-time
typecheck. Already scaffolded in `vite.config.ts` ("Phase 4 cutover"). This is
flipping on an already-laid path, not adopting new tech.

### Node vs Bun → stay on Node; Bun later, optional.
Vite/vitest are most stable on Node. Bun offers install/test speedups but
mid-migration runtime churn is risky. Revisit Bun as a drop-in test/build
accelerator after the build pipeline stabilizes. **Bun is not a backend option** —
the backend is Python.

### Tauri (desktop) → only if a desktop app is wanted, after the web UI is solid.
A thin Rust shell wrapping the web UI (the one legitimate place Rust enters),
not a rewrite. Defer until after the build cutover.

## Roadmap (priority order)

1. **[now] Finish jsx→tsx + Vite build cutover** — fixes front-end load slowness,
   type safety, and library access in one move. ~80% there already.
2. **[parallel] Fix glm→gpt worker model default** — the real cause of perceived
   slowness (~8×); a config/`.env` issue, not code. See [[atlas-refactoring-review-20260528]].
3. **[keep] Python backend** — leave it; only async/caching tuning if needed.
4. **[conditional] Rust PyO3 extension** — only if a Verilog parser/linter shows
   up as a profiled hotspot.
5. **[optional/later] Tauri desktop, Bun test acceleration** — after the above.

## One-line direction

> Don't switch languages — **consolidate**. Keep the Python backend (I/O-bound,
> rewrite ROI is zero); finish the front-end **TSX migration and turn on the Vite
> build** (which also resolves the load-time slowness); keep Node as the build
> runtime. Go/Rust/Bun/Tauri enter only for surgical purposes (a proven hotspot,
> or desktop packaging) — never as a rewrite.
