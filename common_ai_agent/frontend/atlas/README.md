# ATLAS · common_ai_agent frontend

A browser-based UI for `common_ai_agent`. Static HTML + React (in-browser
Babel) + a thin `window.backend` adapter that talks to a FastAPI / WebSocket
backend (`src/atlas_ui.py`).

```
brian_hw/common_ai_agent/
├── src/
│   ├── main.py                ← agent loop (unchanged)
│   ├── web_ui.py              ← legacy SSE UI (kept for compat)
│   └── atlas_ui.py            ← NEW: serves this frontend over WS
└── frontend/
    └── atlas/                 ← THIS FOLDER
        ├── index.html         ← entry point
        ├── styles.css         ← design tokens + components
        ├── backend.js         ← window.backend (mock | live ws)
        ├── data.jsx           ← mock data
        ├── shared.jsx         ← <Pill>, <Kbd>, ...
        ├── launcher.jsx       ← workspace launcher screen
        ├── pipeline.jsx       ← REQ→MAS→RTL→TB→SIM→LINT pipeline view
        ├── workspace.jsx      ← chat + sidebar (todo / ssot / diff)
        ├── qa.jsx             ← Q&A flow components
        └── app.jsx            ← top-level shell, theme, routing
```

## Running

### 1. Bring the backend up

```bat
:: from brian_hw\common_ai_agent\
python -m venv .venv
.venv\Scripts\activate
pip install fastapi "uvicorn[standard]" websockets

python src\atlas_ui.py --port 8765
```

Then open <http://127.0.0.1:8765>.

### 2. Frontend-only / static dev

You can open `index.html` directly in a browser — `backend.js` defaults to
`mock` mode and the UI runs against synthetic data. Useful for design
iterations without booting the agent.

To switch modes at runtime:

```js
localStorage.atlasBackend = 'live'   // or 'mock'
location.reload()
```

Or via URL: `?backend=live`.

## Architecture

```
┌────────────────────┐  WS  ┌──────────────────┐
│ Atlas UI (browser) │ ◀──▶ │ atlas_ui.py      │
│  React + JSX       │      │  FastAPI         │
│  window.backend    │      │  bridge          │
└────────────────────┘      └────────┬─────────┘
                                     │ _textual_* callbacks
                                     ▼
                            ┌──────────────────┐
                            │ main.py          │
                            │  ReAct loop      │
                            │  tools, agents   │
                            └──────────────────┘
```

`atlas_ui.py` reuses the same `_textual_*` callback hooks that `web_ui.py`
plugs into, so the agent code in `main.py` stays untouched. Tokens, todos,
context, and cost events flow out as JSON over `/ws/agent`; user prompts
flow back in.

## WebSocket protocol

### Server → client

| `type`         | payload                                          |
| -------------- | ------------------------------------------------ |
| `hello`        | `{frontend, running}`                            |
| `token`        | `{text, cls?}`              streamed agent reply |
| `reasoning`    | `{text}`                    `<thought>` block    |
| `todo_line`    | `{text}`                    todo update line     |
| `flush`        | `{}`                        end-of-block marker  |
| `context`      | `{used, max}`               token-context bar    |
| `cost`         | `{input, cached, output}`   per-turn token cost  |
| `stage`        | `{stage, state}`            pipeline stage event |
| `tool_event`   | `{tool, phase, result?}`    tool-call lifecycle  |
| `agent_state`  | `{running}`                                      |
| `error`        | `{message}`                                      |
| `done`         | `{}`                        turn complete        |

### Client → server

| `type`        | payload      |
| ------------- | ------------ |
| `prompt`      | `{text}`     |
| `interrupt`   | `{text?}`    |
| `run_stage`   | `{stage}`    *(reserved)*  |
| `tool_call`   | `{name, args}` *(reserved)* |

## Notes

- All `.jsx` files are transpiled in the browser via `@babel/standalone`.
  No bundler is needed — keep edits saved and refresh.
- Each `<script type="text/babel">` gets its own scope. Components shared
  across files are exposed on `window` (see end of `shared.jsx`).
- Letterbox scaling: the design canvas is 1920×1080 and is uniformly scaled
  to fit any viewport.
- Light/dark + Direction A/B toggles live in `app.jsx`.
