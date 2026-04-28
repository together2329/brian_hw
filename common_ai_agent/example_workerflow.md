# Example Worker Flow — REST API Guide

How to start the agent HTTP server and drive it entirely via `curl` — no Python
imports needed. Covers the full lifecycle: submit, poll, stream logs, get results,
cancel, and chain workers together.

---

## 1. Start the server

```bash
cd common_ai_agent

# Minimal start
python3 core/agent_server.py --serve

# With explicit port and verbose terminal logging
python3 core/agent_server.py --serve --port 8001 --verbose

# Or via main.py
python3 main.py --serve --port 8001 --verbose
```

With `--verbose`, the server terminal prints every ReAct step in real-time:

```
  ⚙️ [run_a1b2] ReAct loop starting...
  📋 [run_a1b2] Write a hello.py that prints hello world
  💭 [run_a1b2] I need to create hello.py with a print statement.
  ▶️ [run_a1b2] Action: write_file(path="hello.py", content="print('hello world')")
  🔧 [run_a1b2] write_file(path="hello.py", ...)
  👁️ [run_a1b2] File written: hello.py
  ✅ [run_a1b2] Final Answer: Created hello.py
  🏁 [run_a1b2] Completed in 5.2s, 2 iterations, 1 files modified.
```

Without `--verbose` the server is silent — you only see the startup banner.

**Environment variables** (optional):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AGENT_SERVER_RUN_TTL` | `600` | Seconds before completed runs are garbage-collected |
| `AGENT_SERVER_CLEANUP_INTERVAL` | `60` | How often the cleanup thread wakes (seconds) |
| `AGENT_SERVER_MAX_ITERATIONS` | `30` | Max ReAct loop iterations per run |
| `AGENT_SERVER_VERBOSE` | `false` | Set `1`/`true`/`yes` to print ReAct log to terminal |

---

## 2. Endpoints at a glance

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/health` | Liveness check |
| `GET` | `/runs` | List all active runs |
| `POST` | `/run` | Submit a task |
| `GET` | `/status/{run_id}` | Poll progress |
| `GET` | `/result/{run_id}` | Get final output |
| `GET` | `/log/{run_id}` | ReAct transcript (full or delta) |
| `GET` | `/log/{run_id}/stream` | SSE real-time stream |
| `POST` | `/cancel/{run_id}` | Cancel a pending or running task |

---

## 3. Full lifecycle walkthrough

### 3.1 Health check

```bash
curl http://localhost:8000/health
```

```json
{"status":"ok","runs":0}
```

### 3.2 Submit a task — async (get a `run_id` back immediately)

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a hello.py that prints hello world"}'
```

```json
{"run_id":"run_e3f1a2b9","status":"pending"}
```

### 3.3 Poll until done

```bash
# Replace run_e3f1a2b9 with your run_id
curl -s http://localhost:8000/status/run_e3f1a2b9
```

```json
{
  "run_id": "run_e3f1a2b9",
  "status": "running",
  "task": "Write a hello.py that prints hello world",
  "log_entries": 8,
  "elapsed_s": 3.2,
  "error": null
}
```

Poll in a loop:

```bash
RUN_ID="run_e3f1a2b9"
while true; do
  STATUS=$(curl -s http://localhost:8000/status/$RUN_ID | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "Status: $STATUS"
  case "$STATUS" in
    completed|error|cancelled) break ;;
    *) sleep 1 ;;
  esac
done
echo "Done! Fetching result..."
curl -s http://localhost:8000/result/$RUN_ID | python3 -m json.tool
```

### 3.4 Stream ReAct log in real-time

```bash
RUN_ID="run_e3f1a2b9"
SINCE=0
while true; do
  RESP=$(curl -s "http://localhost:8000/log/$RUN_ID?since=$SINCE")
  ENTRIES=$(echo "$RESP" | python3 -c "import sys,json; print(len(json.load(sys.stdin)['entries']))")
  if [ "$ENTRIES" -gt 0 ]; then
    echo "$RESP" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data['entries']:
    t = e.get('type','?')
    c = e.get('content','')[:120]
    print(f'  [{t}] {c}')
"
    SINCE=$(echo "$RESP" | python3 -c "import sys,json; ents=json.load(sys.stdin)['entries']; print(ents[-1]['index']+1 if ents else 0)")
  fi
  STATUS=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  case "$STATUS" in completed|error|cancelled) break ;; esac
  sleep 1
done
```

Output looks like:

```
  [system] ReAct loop starting...
  [task] Write a hello.py that prints hello world
  [thought] I need to create hello.py with a print statement.
  [action] Action: write_file(path="hello.py", ...)
  [observation] File written: hello.py
  [completion] Final Answer: Created hello.py
  [done] Completed in 5.2s, 2 iterations, 1 files modified.
```

### 3.4b SSE stream (no polling)

```bash
# Stream a running task in real-time — no polling loop needed
curl -N http://localhost:8000/log/run_e3f1a2b9/stream
```

Output streams as events arrive:
```
data: {"index":0,"type":"system","content":"ReAct loop starting...","timestamp":1716500000.1}
data: {"index":1,"type":"task","content":"Write hello.py...","timestamp":1716500000.2}
data: {"index":2,"type":"thought","content":"I need to create...","timestamp":1716500000.5}
...
event: done
data: {"status": "completed"}
```

### 3.5 Get final result

```bash
curl -s http://localhost:8000/result/run_e3f1a2b9 | python3 -m json.tool
```

```json
{
  "run_id": "run_e3f1a2b9",
  "status": "completed",
  "result": "Final Answer: Created hello.py with print('hello world')",
  "files_modified": ["hello.py"],
  "files_examined": [],
  "iterations": 2,
  "todos_summary": []
}
```

### 3.6 Cancel a running task

```bash
curl -s -X POST http://localhost:8000/cancel/run_e3f1a2b9
```

```json
{"run_id":"run_e3f1a2b9","status":"cancelled"}
```

---

## 4. Sync mode — block until done

Add `"sync": true` and the POST blocks until the task completes:

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Write a hello.py that prints hello world",
    "sync": true
  }' | python3 -m json.tool
```

Returns the full result in one shot — no polling needed.

---

## 5. Submit with todos (structured task plan)

```bash
curl -s -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create a simple Python project",
    "todos": [
      {"content": "Write main.py with hello world", "status": "pending"},
      {"content": "Write README.md", "status": "pending"},
      {"content": "Verify both files exist", "status": "pending"}
    ],
    "sync": true
  }' | python3 -m json.tool
```

The response includes `todos_summary` showing which items were completed.

---

## 6. cmux integration

Start a worker dedicated to cmux operations:

```bash
python3 core/agent_server.py --serve --port 8001
```

### Capture the modifiable_ai_agent screen

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Call cmux_capture(lines=80). Describe what you see. Final Answer: <description>",
    "sync": true
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])"
```

### Send text to modifiable_ai_agent

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Call cmux_send(text=\"help\", capture_delay=2.0). Describe the response. Final Answer: <description>",
    "sync": true
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])"
```

### Restart modifiable_ai_agent

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Call cmux_restart_modifiable(). If it restarted, say RESTART OK. Final Answer: RESTART OK",
    "sync": true
  }'
```

### List all cmux panes

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Call cmux_tree(). List all panes. Final Answer: <tree>",
    "sync": true
  }'
```

### Split pane and run a command

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Call cmux_new_split(direction=\"right\", command=\"htop\"). Final Answer: SPLIT OK",
    "sync": true
  }'
```

---

## 7. Worker-to-worker chaining

Start two workers:

```bash
# Terminal 1 — Worker A
python3 core/agent_server.py --serve --port 8001

# Terminal 2 — Worker B
python3 core/agent_server.py --serve --port 8002
```

### Chain: Commander → Worker A → Worker B

```bash
curl -s -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Use worker_call to dispatch this task to http://localhost:8002: \"Write a test.py that prints ok\". Wait for completion. Final Answer: CHAIN <result from worker 2>",
    "sync": true
  }' | python3 -c "import sys,json; print(json.load(sys.stdin)['result'])"
```

### Multi-step chain: lint → fix → simulate

```bash
# Start 3 workers
python3 core/agent_server.py --serve --port 18797 &   # lint
python3 core/agent_server.py --serve --port 18798 &   # fix
python3 core/agent_server.py --serve --port 18799 &   # sim

# Dispatch coordinator task to lint worker
curl -s -X POST http://localhost:18797/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "You are a coordinator. Use worker_call to chain:\nStep 1: Send bad_syntax.v to lint_worker at http://localhost:18797 for linting.\nStep 2: If lint fails, send to fix_worker at http://localhost:18798.\nStep 3: Re-lint with lint_worker.\nStep 4: Simulate with sim_worker at http://localhost:18799.\nFinal Answer: CHAIN PASSED or CHAIN FAILED",
    "sync": true
  }'
```

---

## 8. Python (no imports) — using only urllib

If you want to script against the server without importing the project:

```python
import json, urllib.request

BASE = "http://localhost:8000"

def post(path, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BASE}{path}", data=body,
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

def get(path):
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as r:
        return json.loads(r.read())

# Health
print(get("/health"))  # {'status': 'ok', 'runs': 0}

# Submit sync
result = post("/run", {
    "task": "Write a hello.py that prints hello world",
    "sync": True,
})
print(result["status"])      # completed
print(result["result"])      # Final Answer: ...
print(result["files_modified"])  # ['hello.py']

# Async + poll
resp = post("/run", {"task": "Write goodbye.py"})
run_id = resp["run_id"]

import time
while True:
    s = get(f"/status/{run_id}")
    if s["status"] in ("completed", "error", "cancelled"):
        break
    time.sleep(1)

final = get(f"/result/{run_id}")
print(final["result"])
```

---

## 9. Full request/response reference

### `POST /run`

**Request:**

```json
{
  "task": "string (required)",
  "model": "string (optional)",
  "todos": [{"content": "...", "status": "pending"}],
  "context": "string (optional)",
  "sync": true
}
```

**Response (sync=true):**

```json
{
  "run_id": "run_abc123",
  "status": "completed",
  "result": "Final Answer: ...",
  "files_modified": ["hello.py"],
  "files_examined": ["counter.v"],
  "iterations": 5,
  "todos_summary": [
    {"index": 1, "content": "Write hello.py", "completed": true}
  ]
}
```

**Response (sync=false / async):**

```json
{"run_id": "run_abc123", "status": "pending"}
```

### `GET /status/{run_id}`

```json
{
  "run_id": "run_abc123",
  "status": "running",
  "task": "... (first 100 chars)",
  "log_entries": 14,
  "elapsed_s": 12.5,
  "error": null
}
```

### `GET /result/{run_id}`

Same shape as the sync response above.

### `GET /log/{run_id}?tail=20&since=5`

```json
{
  "run_id": "run_abc123",
  "status": "completed",
  "total_entries": 42,
  "entries": [
    {
      "index": 5,
      "type": "thought",
      "role": "assistant",
      "content": "I need to read the file first.",
      "timestamp": 1716500000.123
    },
    {
      "index": 6,
      "type": "action",
      "role": "assistant",
      "content": "Action: read_file(path=\"counter.v\")",
      "timestamp": 1716500000.456
    },
    {
      "index": 7,
      "type": "observation",
      "role": "tool",
      "content": "module counter(...",
      "timestamp": 1716500000.789
    }
  ]
}
```

### `POST /cancel/{run_id}`

```json
{"run_id": "run_abc123", "status": "cancelled"}
```

### `GET /health`

```json
{"status": "ok", "runs": 3}
```

### `GET /runs`

```json
{
  "total": 3,
  "runs": [
    {"run_id": "run_a1b2c3d4", "status": "running", "task": "Lint counter.v", "elapsed_s": 12.5, "error": null},
    {"run_id": "run_e5f6g7h8", "status": "completed", "task": "Write hello.py", "elapsed_s": 5.2, "error": null},
    {"run_id": "run_i9j0k1l2", "status": "pending", "task": "Simulate counter", "elapsed_s": 0.0, "error": null}
  ]
}
```

---

## 10. Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Connection refused` | Server not running. Start with `python3 core/agent_server.py --serve` |
| `404 run not found` | Run may have been garbage-collected (TTL expired). Submit a new task. |
| `409 already completed` | Cannot cancel a run that already finished. |
| `400 'task' is required` | POST body must include `"task"` key. |
| `LLM call failed` | Check `.env` has valid `OPENROUTER_API_KEY` or `ANTHROPIC_API_KEY`. |
| cmux tools return `(no output)` | cmux not installed or not in PATH. Run `which cmux`. |
| `fastapi not installed` | `pip install fastapi uvicorn` |
