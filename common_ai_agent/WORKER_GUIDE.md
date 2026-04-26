# Common AI Agent — Worker System Guide

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  Coordinator / Main Agent            │
│                                                     │
│  Tools: worker_call, worker_status, worker_result,  │
│         worker_call_all, background_task            │
└──────────┬──────────────┬──────────────┬────────────┘
           │              │              │
    ┌──────▼──────┐ ┌─────▼───────┐ ┌────▼──────┐
    │  Worker A   │ │  Worker B   │ │ Worker C  │
    │  :8001      │ │  :8002      │ │ :8003     │
    │  (lint)     │ │  (fix)      │ │ (simulate)│
    └─────────────┘ └─────────────┘ └───────────┘
```

Common AI Agent has **two worker systems**:

| System | File | Use Case |
|--------|------|----------|
| **Agent Server** | `core/agent_server.py` | Full HTTP API server — workers are independent processes |
| **Agent Client** | `core/agent_client.py` | HTTP client — coordinator calls workers |
| **Background Manager** | `core/background.py` | In-process thread pool — lightweight sub-agents |

---

## Method 1: Agent Server (Full HTTP Workers)

### Step 1: Start Worker Servers

Open separate terminals (or use `&`):

```bash
# Terminal 1: Start Worker A on port 8001
cd common_ai_agent
python main.py --serve --port 8001 --worker-name lint_worker

# Terminal 2: Start Worker B on port 8002
cd common_ai_agent
python main.py --serve --port 8002 --worker-name fix_worker

# Terminal 3: Start Worker C on port 8003
cd common_ai_agent
python main.py --serve --port 8003 --worker-name sim_worker
```

With auto-registration to a coordinator:
```bash
python main.py --serve --port 8001 \
  --worker-name lint_worker \
  --coordinator http://localhost:8000
```

### Step 2: Use from Main Agent (ReAct Loop)

From within your main agent session, use these tools:

#### Dispatch a task to a worker (sync — wait for result):
```
Action: worker_call
Action Input: worker="http://localhost:8001", task="Lint counter.v with iverilog -Wall", timeout=120
```

#### Dispatch async (returns immediately):
```
Action: worker_call
Action Input: worker="http://localhost:8001", task="Lint counter.v", timeout=120
```

#### Check status of running task:
```
Action: worker_status
Action Input: worker="http://localhost:8001", run_id="run_abc12345"
```

#### Get result of completed task:
```
Action: worker_result
Action Input: worker="http://localhost:8001", run_id="run_abc12345"
```

#### Cancel a running task:
```
Action: worker_cancel
Action Input: worker="http://localhost:8001", run_id="run_abc12345"
```

#### Dispatch same task to multiple workers in parallel:
```
Action: worker_call_all
Action Input: workers=[{"name":"lint","url":"http://localhost:8001"}, {"name":"sim","url":"http://localhost:8003"}], task="Verify counter.v compiles", timeout=120
```

### Step 3: Use from Python Code

```python
from core.agent_client import worker_call, worker_status, worker_result, worker_call_all

# Single worker — blocking call
result = worker_call(
    worker="http://localhost:8001",
    task="Run iverilog -Wall on counter.v and report errors",
    timeout=120,
    show_log=True,
)
print(result["status"])    # "completed" | "error" | "timeout"
print(result["result"])    # Final answer from worker agent

# Poll-based (async)
result = worker_call(
    worker="http://localhost:8001",
    task="Long running task...",
    timeout=600,
    poll_interval=5.0,
    show_log=True,
)

# Parallel dispatch to multiple workers
results = worker_call_all(
    workers=[
        {"name": "lint_worker", "url": "http://localhost:8001"},
        {"name": "sim_worker", "url": "http://localhost:8003"},
    ],
    task="Verify counter.v",
    timeout=120,
    max_workers=10,
)
# results = {
#   "total": 2,
#   "succeeded": 2,
#   "failed": 0,
#   "results": [{worker, status, result, elapsed_s}, ...]
# }
```

### Step 4: Use curl directly

```bash
# Health check
curl http://localhost:8001/health

# Start a task (sync — blocks until done)
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Read counter.v and summarize it", "sync": true}'

# Start a task (async — returns run_id immediately)
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{"task": "Lint counter.v", "sync": false}'
# → {"run_id": "run_abc12345", "status": "pending"}

# Poll status
curl http://localhost:8001/status/run_abc12345

# Get result
curl http://localhost:8001/result/run_abc12345

# Stream real-time log (SSE)
curl -N http://localhost:8001/log/run_abc12345/stream

# Cancel
curl -X POST http://localhost:8001/cancel/run_abc12345

# Register worker with coordinator
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{"name": "lint_worker", "url": "http://localhost:8001"}'

# List registered workers
curl http://localhost:8000/workers

# View metrics
curl http://localhost:8001/metrics
```

---

## Method 2: Background Manager (In-Process)

For lightweight sub-agents that run in the **same process** (no separate server needed):

```python
from core.background import get_background_manager

manager = get_background_manager(max_workers=3)

# Launch a background agent
task_id = manager.launch(
    agent="explore",          # Agent type: explore, plan, execute, review
    prompt="Find all Verilog modules in the project",
    parent_context="Working on counter.v verification",
)
# → "bg_a1b2c3d4"

# Check output (non-blocking)
output = manager.get_output(task_id)
# If running: "Task bg_a1b2c3d4 (explore) is still running. Elapsed: 12.3s"
# If done: "=== Background Task Result: bg_a1b2c3d4 (explore) ===\n..."

# List all tasks
manager.list_tasks()

# Cancel
manager.cancel(task_id)
```

From the ReAct loop:
```
Action: background_task
Action Input: agent="explore", prompt="Analyze the project structure"

# ... continue other work ...

Action: background_output
Action Input: task_id="bg_a1b2c3d4"
```

---

## API Reference

### Agent Server Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Liveness check |
| `GET` | `/metrics` | Run counts, success rate, uptime |
| `POST` | `/run` | Start a task (`sync=true` blocks) |
| `GET` | `/runs` | List all runs |
| `GET` | `/status/{run_id}` | Poll run progress |
| `GET` | `/result/{run_id}` | Get final result |
| `GET` | `/log/{run_id}` | Get ReAct transcript |
| `GET` | `/log/{run_id}/stream` | SSE real-time stream |
| `POST` | `/cancel/{run_id}` | Cancel a run |
| `POST` | `/register` | Register a worker |
| `GET` | `/workers` | List registered workers |

### POST /run Body

```json
{
  "task": "Lint counter.v with iverilog",
  "model": "",
  "todos": [{"content": "Step 1", "status": "pending"}],
  "context": "Working on Verilog verification",
  "sync": false
}
```

### Run Lifecycle

```
pending → running → completed
                  → error
                  → cancelled
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AGENT_SERVER_MAX_CONCURRENT` | 8 | Max concurrent runs |
| `AGENT_SERVER_MAX_ITERATIONS` | 30 | Max ReAct iterations per run |
| `AGENT_SERVER_RUN_TTL` | 600 | TTL for completed runs (seconds) |
| `AGENT_SERVER_PERSISTENCE` | true | Save runs to disk |
| `AGENT_SERVER_VERBOSE` | false | Print ReAct log to terminal |
| `AGENT_SERVER_API_KEY` | "" | Require X-API-Key header |
| `AGENT_SERVER_LOG_DIR` | "" | Directory for persistent logs |

---

## Quick Start: Worker Chaining Example

```bash
# 1. Start 3 workers
python main.py --serve --port 8001 --worker-name lint &
python main.py --serve --port 8002 --worker-name fix &
python main.py --serve --port 8003 --worker-name sim &
sleep 3

# 2. Verify all healthy
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# 3. Run chain: lint → fix → re-lint → simulate
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "You are a coordinator. Execute this chain:\n1. worker_call to http://localhost:8001: lint bad_syntax.v\n2. If FAILED, worker_call to http://localhost:8002: fix the syntax error\n3. worker_call to http://localhost:8001: re-lint the fixed file\n4. worker_call to http://localhost:8003: simulate counter.v + tb_counter.v\nReport CHAIN PASSED if all steps pass.",
    "sync": true
  }'
```

---

## When to Use Which System

| Scenario | Use | Why |
|----------|-----|-----|
| Heavy parallel work (lint + sim) | Agent Server | Separate processes, true parallelism |
| Need HTTP API access | Agent Server | REST endpoints for external tools |
| Multiple users sharing workers | Agent Server | Workers are network-accessible |
| Quick in-process sub-task | Background Manager | No startup overhead, shared memory |
| Sequential pipeline | Background Manager | Lower latency, no network |
| Coordinator-worker orchestration | Agent Server + Client | Full coordinator mode with registry |
