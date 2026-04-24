# Todo System — Extended Workflow Engine

## 개요

기존 Todo List를 LangGraph/Prefect/Jenkins 수준의 워크플로우 엔진으로 확장.
LLM 판단 기반 실행 + Static 실행 + Sub-agent 위임 + 외부 CLI를 todo별로 지정 가능.

---

## 새 필드 설계

```json
{
  "content": "Implement RTL module",
  "activeForm": "Implementing RTL module",
  "status": "pending",
  "priority": "high",
  "detail": "...",
  "criteria": "...",

  "command": "make sim",
  "agent": "execute",
  "model": "kimi-k2.6",
  "context": "minimal",
  "context_group": "A",
  "on_reject": 3
}
```

---

## 필드 설명

### `command` — Static 실행 (LLM 없이)

```json
{"command": "make lint"}
{"command": "python3 scripts/gen.py"}
{"command": "vcs -sv tb/*.sv rtl/*.sv 2>&1"}
{"command": {"tool": "run_command", "args": {"command": "make sim", "timeout": 120}}}
{"command": {"tool": "write_file", "args": {"path": "out.md", "content": "..."}}}
{"command": {"tool": "grep_file", "args": {"pattern": "ERROR", "path": "sim.log"}}}
```

- string → shell 직접 실행 (subprocess)
- dict → `AVAILABLE_TOOLS[tool](**args)` 직접 호출
- 성공 → auto approved (review 스킵)
- 실패 → auto rejected, `on_reject` 있으면 해당 task로 점프
- EDA tool, Python, Make, Bash 스크립트 전부 가능

### `agent` — Task별 Agent 지정

```json
{"agent": "explore"}   → read-only 탐색, 빠른 조사
{"agent": "execute"}   → 파일 수정 / 실행 / 구현
{"agent": "review"}    → 결과 검증, criteria 체크
{"agent": "codex"}     → Codex CLI 외부 호출
{"agent": "gemini"}    → Gemini CLI 외부 호출
{"agent": "cursor"}    → Cursor-agent CLI 외부 호출
```

- 지정 없음 → primary agent가 직접 처리 (현재 방식)
- `command`가 있으면 `agent` 무관하게 static 실행 우선
- 외부 CLI는 `detail + criteria`를 prompt로 조합해 subprocess 실행, stdout 캡처

### `model` — Task별 모델 지정

```json
{"model": "gpt-4o-mini"}
{"model": "kimi-k2.6"}
{"model": "claude-sonnet-4-6"}
{"model": "gemini-2.5-pro"}
```

- 지정 없음 → 현재 설정 모델 사용
- 단순 탐색 → 작은/빠른 모델
- 복잡한 구현 → reasoning 모델
- 비용/성능 task별 최적화 가능

### `context` — 컨텍스트 크기

| 값 | 의미 |
|---|---|
| `full` | 전체 히스토리 (현재 방식) |
| `minimal` | 현재 task 관련 요약만 |
| `none` | system prompt만 (완전 clean start) |

- 지정 없음 → `full` (기존 동작 유지)

### `context_group` — 컨텍스트 공유 범위

```json
{"context_group": "rtl-impl"}
{"context_group": null}
```

- 같은 group → 이전 task 결과를 이어받아 실행 (LangGraph shared state)
- 다른 group → 독립적인 컨텍스트
- null → 컨텍스트 불필요 (command 직접 실행 등)
- primary 히스토리 전체 대신 그룹 내 결과만 공유 → 토큰 효율

### `on_reject` — Reject 시 점프

```json
{"on_reject": 3}
```

- 실패 시 지정된 task index(1-based)로 current_index 이동
- 지정 없음 → 현재처럼 rejected 상태 유지 (LLM이 수동 수정)
- 꼭 현재 task 앞뒤일 필요 없음 — 어느 index든 가능
- 순환 가능: Task 4 실패 → Task 2로 → Task 2 실패 → Task 1로

---

## 실행 흐름

```
task → in_progress
    ↓
command 있음?
    YES → static 실행 (LLM 없음)
            str  → subprocess
            dict → tool dispatcher
            ↓
            성공 → approved (review 스킵)
            실패 → on_reject 있음? → 해당 task로 점프 후 rejected
                   없음            → rejected 유지
    NO  →
    agent 있음?
        내부 (explore/execute/review)
            → background_task(agent, model, context_group 기반 컨텍스트)
            → execute 결과 → review agent → approved/rejected
        외부 (codex/gemini/cursor)
            → subprocess CLI 호출
            → stdout 캡처 → delegate_result 저장
            → primary or review agent가 approve/reject 판단
        없음
            → primary agent LLM 루프 (현재 방식)
```

---

## 예시 워크플로우

```json
[
  {
    "content": "Explored codebase structure",
    "activeForm": "Exploring codebase structure",
    "agent": "explore",
    "model": "gpt-4o-mini",
    "context": "none",
    "context_group": "rtl-impl"
  },
  {
    "content": "Implemented RTL module",
    "activeForm": "Implementing RTL module",
    "agent": "execute",
    "model": "kimi-k2.6",
    "context": "minimal",
    "context_group": "rtl-impl",
    "on_reject": 1
  },
  {
    "content": "Ran lint check",
    "activeForm": "Running lint check",
    "command": "verilator --lint-only rtl/*.sv 2>&1",
    "on_reject": 2
  },
  {
    "content": "Ran simulation",
    "activeForm": "Running simulation",
    "command": "make sim",
    "on_reject": 2
  },
  {
    "content": "Reviewed simulation results",
    "activeForm": "Reviewing simulation results",
    "agent": "review",
    "model": "claude-sonnet-4-6",
    "context_group": "rtl-impl"
  },
  {
    "content": "Generated testbench with Gemini",
    "activeForm": "Generating testbench with Gemini",
    "agent": "gemini",
    "context": "none",
    "criteria": "TB compiles\nDUT instantiated\nAt least 3 test cases"
  },
  {
    "content": "Wrote final report",
    "activeForm": "Writing final report",
    "command": {"tool": "write_file", "args": {"path": "report.md", "content": "# Report\n..."}}
  }
]
```

---

## 외부 CLI Agent 상세

### 지원 CLI

| agent | 실행 명령 | 설정 키 |
|---|---|---|
| `codex` | `codex "<prompt>"` | `CODEX_CLI_CMD` |
| `gemini` | `gemini -p "<prompt>"` | `GEMINI_CLI_CMD` |
| `cursor` | `cursor-agent "<prompt>"` | `CURSOR_CLI_CMD` |

### 동작 방식

```
task.detail + task.criteria → prompt 조합
    ↓
subprocess.run(f'{CLI_CMD} "{prompt}"')
    ↓
stdout → delegate_result 저장
    ↓
review agent or primary → 결과 보고 approve/reject
```

### `.config` 커스터마이즈

```
CODEX_CLI_CMD=codex
GEMINI_CLI_CMD=gemini -p
CURSOR_CLI_CMD=cursor-agent
EXTERNAL_AGENT_TIMEOUT=300
```

---

## 내부 vs 외부 Agent 비교

| | 내부 (explore/execute/review) | 외부 (codex/gemini/cursor) |
|---|---|---|
| 실행 방식 | background_task → ReAct 루프 | subprocess CLI 호출 |
| 컨텍스트 | context_group으로 공유 | prompt string으로 전달 |
| 도구 접근 | AVAILABLE_TOOLS 전체 | CLI 자체 기능 |
| 출력 형태 | 구조화된 AgentResult | stdout 텍스트 |
| 비용 | 현재 API 과금 | 각 CLI 과금 정책 |
| 적합한 경우 | 복잡한 구현/탐색 | 외부 AI 활용, 비교 실험 |

---

## LangGraph 대비

| LangGraph | 이 시스템 |
|---|---|
| Node | Todo task |
| Edge (순서) | Sequential 실행 |
| Conditional edge | `on_reject` 점프 |
| Node별 LLM | `agent` + `model` 지정 |
| Shared state | `context_group` |
| Static node | `command` 직접 실행 |
| 체크포인트 | todo.json 자동 저장 |
| 재시작 | in_progress task부터 재개 |
| 루프 | `loop` + `exit_condition` (기존) |
| 병렬 브랜치 | `background_task` 병렬 호출 |
| 시각화 | `/todo` 커맨드 |

---

## Prefect / Jenkins 대비

| | Prefect/Jenkins | 이 시스템 |
|---|---|---|
| Script 실행 | `@task` + shell | `command` 필드 |
| 순서 | `@flow` | Todo 순서 |
| 재시도 | retry policy | `on_reject` + rejection loop |
| 체크포인트 | DB | todo.json |
| 스케줄링 | cron 내장 | ❌ (cron + CLI로 외부 해결) |
| LLM 판단 | ❌ | ✅ (command 없으면 LLM) |
| 동적 플로우 설계 | ❌ | ✅ (plan mode) |
| 사람 개입 | 제한적 | ✅ human-in-the-loop |

---

## 현재 이미 구현된 것

| 기능 | |
|---|---|
| Sequential 실행 | ✅ |
| Loop + exit_condition | ✅ |
| Reject → retry | ✅ |
| 체크포인트 / 재시작 | ✅ |
| Human-in-the-loop | ✅ |
| Criteria 기반 approve/reject | ✅ |
| Work log (todo_note) | ✅ |
| Sub-agent (explore/execute/review) | ✅ |
| Validator (완료 전 shell 검증) | ✅ |

---

---

## 이상적인 실행 패턴

```
LLM (구현/창작)
    ↓
Static (lint/compile — 빠르고 확실)
    ↓ 실패 → LLM으로 되돌아감 (on_reject)
    ↓ 성공
Command (실행 — deterministic)
    ↓
LLM (결과 해석/검토)
```

LLM은 **만드는 것** 과 **판단하는 것** 만 담당.
중간 검증/실행은 static → 비용 최소화 + 신뢰성 향상.

```json
[
  {"content": "Implement RTL",     "agent": "execute", "context_group": "A"},
  {"content": "Syntax check",      "command": "verilator --lint-only rtl/*.sv", "on_reject": 1},
  {"content": "Run simulation",    "command": "make sim", "on_reject": 1},
  {"content": "Review results",    "agent": "review", "context_group": "A"}
]
```

---

## flow_builder — 워크플로우 자동 생성

사용자가 자연어로 요청하면 flow_builder가 최적화된 todo list를 자동 생성.

### 동작 방식

```
사용자: "/flow RTL 구현하고 lint, sim 돌려줘"
    ↓
flow_builder agent (explore)
  → Makefile, 스크립트, 프로젝트 구조 탐색
  → available commands 파악
    ↓
flow_builder (LLM 판단)
  → 각 단계가 LLM 필요한지 / static인지 결정
  → on_reject 관계 설계
  → 적합한 agent / model 선택
    ↓
todo_write() 호출 → todo list 생성
    ↓
사용자 확인 (plan mode) → 실행 시작
```

### 예시

```
사용자: "/flow RTL 구현 + 검증 파이프라인"

flow_builder 출력:
[
  {"content": "Explored project structure",
   "agent": "explore", "model": "gpt-4o-mini", "context": "none", "context_group": "rtl"},

  {"content": "Implemented RTL module",
   "agent": "execute", "model": "kimi-k2.6", "context_group": "rtl", "on_reject": 1},

  {"content": "Ran lint",
   "command": "verilator --lint-only rtl/*.sv 2>&1", "on_reject": 2},

  {"content": "Ran compilation",
   "command": "vcs -sv rtl/*.sv tb/*.sv 2>&1", "on_reject": 2},

  {"content": "Ran simulation",
   "command": "make sim", "on_reject": 2},

  {"content": "Reviewed results",
   "agent": "review", "model": "claude-sonnet-4-6", "context_group": "rtl"}
]
```

### flow_builder가 알아야 할 것

- 프로젝트 구조 (Makefile, 스크립트, 설정 파일)
- Available commands (`make lint`, `make sim`, EDA tool 명령어)
- LLM 필요 여부 판단 기준
- on_reject 의존 관계
- 각 단계에 적합한 agent / model

### 구현

- `/flow <description>` 슬래시 커맨드
- flow_builder = plan mode + explore agent 조합
- 프로젝트별 `.flow_config.json` 으로 커스터마이즈 가능:

```json
{
  "lint_cmd": "verilator --lint-only rtl/*.sv",
  "sim_cmd": "make sim",
  "compile_cmd": "vcs -sv rtl/*.sv tb/*.sv",
  "default_rtl_model": "kimi-k2.6",
  "default_review_model": "claude-sonnet-4-6"
}
```

---

## LangGraph와 비교

LangGraph로 동일한 파이프라인을 표현하면:

```python
@flow
def rtl_pipeline():
    rtl = implement_rtl()         # LLM node
    lint = run_lint(rtl)          # static node
    if lint.failed:
        return implement_rtl()    # back edge
    sim = run_sim(rtl)            # static node
    if sim.failed:
        return implement_rtl()    # back edge
    review(sim.result)            # LLM node
```

이 시스템으로 표현하면:

```json
[
  {"agent": "execute",         "on_reject": 1},
  {"command": "make lint",     "on_reject": 1},
  {"command": "make sim",      "on_reject": 1},
  {"agent": "review"}
]
```

**더 간결하고, 코드 없이 JSON만으로 표현 가능.**
그래프를 개발자가 코딩하는 대신 **LLM (flow_builder) 이 설계.**

---

---

## Edge — 노드 간 연결 (실행 흐름 제어)

LangGraph의 edge 개념을 todo 필드로 표현.
한 노드에서 조건에 따라 **여러 방향**으로 분기 가능.

### 현재 (implicit edge)

```
순서 edge:   Todo #1 → #2 → #3  (무조건 다음)
on_reject:   실패 시 1곳으로만 점프
```

### 확장 edge 필드

```json
{
  "content": "Run simulation",
  "command": "make sim",

  "on_success": 4,
  "on_reject": 2,
  "on_condition": [
    {"if": "coverage > 90", "goto": 5},
    {"if": "timeout",       "goto": 3},
    {"if": "error: syntax", "goto": 1}
  ]
}
```

| 필드 | 의미 |
|---|---|
| `on_success` | 성공 시 이동할 task index (기본: 다음 순서) |
| `on_reject` | 실패 시 이동할 task index |
| `on_condition` | stdout/stderr 패턴 매칭 → 조건별 분기 |

### on_condition 매칭 방식

```json
"on_condition": [
  {"if": "coverage > 90",  "goto": 5},
  {"if": "TIMEOUT",        "goto": 3},
  {"if": "syntax error",   "goto": 1}
]
```

- `if` → stdout/stderr에서 문자열 or 정규식 매칭
- 위에서부터 순서대로 체크, 첫 매칭에서 분기
- 매칭 없으면 → `on_reject` or `on_success` 기본값 사용

### 예시 — 복잡한 분기

```
              ┌──→ Task 5 (coverage 충분)
Task 4 (sim) ─┼──→ Task 2 (compile error → 재구현)
              └──→ Task 3 (timeout → sim 재실행)
```

```json
[
  {"content": "Implement RTL",   "agent": "execute"},
  {"content": "Compile",         "command": "make compile",  "on_reject": 1},
  {"content": "Run sim",         "command": "make sim",      "on_reject": 2,
   "on_condition": [
     {"if": "syntax error",  "goto": 1},
     {"if": "TIMEOUT",       "goto": 3}
   ]},
  {"content": "Check coverage",  "command": "make coverage",
   "on_condition": [
     {"if": "coverage: 9[0-9]", "goto": 5}
   ],
   "on_reject": 1},
  {"content": "Review",          "agent": "review"}
]
```

### LangGraph 대비

```python
# LangGraph
graph.add_conditional_edges("sim", lambda x:
    "implement" if "syntax error" in x.stderr else
    "sim"       if "TIMEOUT"      in x.stderr else
    "review"
)

# 이 시스템
{"command": "make sim",
 "on_condition": [
   {"if": "syntax error", "goto": 1},
   {"if": "TIMEOUT",      "goto": 3}
 ]}
```

---

---

## 외부 Orchestrator와 통신 (이 시스템을 Node로 사용)

이 시스템 자체를 외부 Orchestrator의 **노드**로 사용 가능.
LangGraph, 다른 AI 시스템, 스크립트가 이 시스템을 호출하고 결과를 받음.

### 현재 문제

```bash
python main.py  # 대화형 — 외부에서 호출 불가
```

### 필요한 인터페이스

**1. CLI headless 모드**
```bash
# 단발성 task 실행
python main.py --task "RTL 구현해" --output result.json

# stdin/stdout 파이프
echo "RTL 구현해" | python main.py --headless

# todo list 파일로 실행
python main.py --flow pipeline.json --output result.json
```

**2. HTTP API**
```
POST /run
{"task": "RTL 구현해", "context": "...", "model": "kimi-k2.6"}
→ {"status": "completed", "result": "...", "files_modified": [...]}

POST /flow
{"todos": [...]}
→ {"status": "completed", "results": [...]}

GET /status/{run_id}
→ {"status": "in_progress", "current_task": 3, "total": 5}
```

**3. Python SDK**
```python
from common_ai_agent import Agent

agent = Agent(model="kimi-k2.6")
result = agent.run("RTL 구현해")
print(result.output)

# flow 실행
result = agent.run_flow([
    {"content": "Implement", "agent": "execute"},
    {"content": "Lint",      "command": "make lint"},
])
```

### 외부 Orchestrator 연동 예시

**LangGraph에서 이 시스템을 Node로 사용:**
```python
from common_ai_agent import Agent

@node
def implement_rtl(state):
    agent = Agent(model="kimi-k2.6")
    result = agent.run(f"RTL 구현: {state.spec}")
    return {"rtl_code": result.output}

@node
def write_tb(state):
    agent = Agent(model="gemini")
    result = agent.run(f"TB 작성: {state.rtl_code}")
    return {"tb_code": result.output}

graph.add_node("implement", implement_rtl)
graph.add_node("write_tb",  write_tb)
```

**다른 AI 시스템에서 CLI로 호출:**
```bash
# Orchestrator가 shell로 호출
result=$(python main.py --task "RTL 구현해" --headless)
echo $result | jq '.status'
```

**Prefect flow에서 사용:**
```python
@task
def implement_rtl(spec):
    return subprocess.run(
        ["python", "main.py", "--task", spec, "--headless"],
        capture_output=True
    ).stdout

@flow
def rtl_pipeline(spec):
    rtl = implement_rtl(spec)
    lint_result = run_lint(rtl)
    ...
```

### Sub-agent 간 통신 (양방향)

현재는 단방향:
```
Primary → Sub-agent (결과만 받음)
```

Sub-agent가 Primary에게 질문이 필요한 경우:
```
Sub-agent Final Answer에 질문 포함
    ↓
Primary가 수신 → 판단 or 사용자에게 전달
    ↓
context_group에 답변 추가
    ↓
Sub-agent 재호출 (with answer)
```

HTTP API가 있으면 외부 Orchestrator도 동일하게 처리 가능:
```
GET /status/{run_id} → {"status": "waiting_input", "question": "AXI4 vs APB?"}
POST /input/{run_id} {"answer": "AXI4"}
→ 실행 재개
```

### output 포맷

```json
{
  "status": "completed",
  "run_id": "run_abc123",
  "result": "RTL 구현 완료. counter.sv 생성됨.",
  "files_modified": ["rtl/counter.sv"],
  "files_examined": ["rtl/", "tb/"],
  "iterations": 5,
  "elapsed_ms": 12400,
  "todos": [
    {"content": "Implement RTL", "status": "approved"},
    {"content": "Run lint",      "status": "approved"}
  ]
}
```

---

---

## Multi-Agent 시스템 — Common AI Agent를 Node로

### 기본 구조

Common AI Agent 하나가 todo graph 전체를 실행하고 결과를 반환.
Orchestrator는 내부 동작 몰라도 됨 — **블랙박스 node**.

```
Orchestrator Agent
    ↓
POST /run {"todos": [...전체 그래프...]}
    ↓
Common AI Agent (내부적으로 todo graph 실행)
  ├── Todo #1: explore   → node
  ├── Todo #2: execute   → node
  ├── Todo #3: make lint → node (static)
  ├── Todo #4: make sim  → node (static)
  └── Todo #5: review    → node
    ↓
{"status": "completed", "results": [...]}
    ↓
Orchestrator가 결과 수신 → 다음 단계로
```

### 병렬 Multi-Agent

여러 Common AI Agent가 독립적인 todo graph를 병렬 실행:

```
Orchestrator
    ├── Agent A: POST /run (RTL 구현 그래프)  ─┐
    ├── Agent B: POST /run (TB 작성 그래프)   ─┼→ 병렬 실행
    └── Agent C: POST /run (문서 작성 그래프) ─┘
            ↓ 모두 완료
        Agent D: POST /run (통합 검증 그래프)
```

### Orchestrator 예시

```python
# orchestrator.py
import requests
import concurrent.futures

BASE = "http://localhost:8000"

# 병렬 실행
with concurrent.futures.ThreadPoolExecutor() as ex:
    f_rtl  = ex.submit(requests.post, f"{BASE}/run",
                json={"todos": rtl_graph})
    f_tb   = ex.submit(requests.post, f"{BASE}/run",
                json={"todos": tb_graph})
    f_docs = ex.submit(requests.post, f"{BASE}/run",
                json={"todos": docs_graph})

rtl_result  = f_rtl.result().json()
tb_result   = f_tb.result().json()
docs_result = f_docs.result().json()

# 결과 취합 → 통합 검증
r = requests.post(f"{BASE}/run", json={
    "todos": verify_graph,
    "context": {
        "rtl":  rtl_result["result"],
        "tb":   tb_result["result"],
        "docs": docs_result["result"]
    }
})
print(r.json())
```

### PoC 구현 순서

```
1. FastAPI /run 엔드포인트 추가
        ↓
2. 단순 task 하나 실행 테스트
        ↓
3. todo graph (json) 전달 → 실행 → 결과 반환 테스트
        ↓
4. Orchestrator 스크립트 (2개 Agent 순서 호출)
        ↓
5. 병렬 실행 테스트
        ↓
6. 실제 RTL 파이프라인으로 검증
```

### output 포맷

```json
{
  "run_id": "run_abc123",
  "status": "completed",
  "result": "counter.sv 생성 완료, lint/sim 통과",
  "files_modified": ["rtl/counter.sv"],
  "files_examined": ["rtl/", "tb/"],
  "todos": [
    {"content": "Implement RTL", "status": "approved"},
    {"content": "Run lint",      "status": "approved"},
    {"content": "Run sim",       "status": "approved"}
  ],
  "elapsed_ms": 12400
}
```

---

---

## Tool / Skill / MCP / Agent 개념 정리

### 정의

```
Tool  — 내장 함수    (시스템에 기본 탑재)
Skill — custom 함수  (사용자가 만든 도메인 특화 도구)
MCP   — 외부 서비스  (GitHub, Slack, DB, 다른 AI 등)
Agent — 독립 LLM    (스스로 판단하며 Tool/Skill/MCP 사용)
```

### 이 시스템에서

```
Tool  → core/tools.py       read_file, run_command, write_file ...
Skill → workflow/skills/    사용자 정의 도메인 특화 도구
MCP   → .mcp.json           외부 서비스 연결
```

### Agent 입장에서는 전부 동일하게 호출

```
Action: read_file(path="a.sv")        ← Tool  (내장)
Action: analyze_verilog(path="a.sv")  ← Skill (custom)
Action: github_pr(repo="x", ...)      ← MCP   (외부)
```

호출 방법은 같고 출처만 다름.

### 계층 구조

```
Agent to Agent          ← 가장 높은 수준 (자율적, non-deterministic)
    ↓ 사용
Tool / Skill / MCP      ← Agent가 사용하는 수단 (함수 호출)
    ↓
command (static)        ← LLM 없이 직접 실행 (deterministic)
```

### Tool vs Agent 핵심 차이

```
Tool/Skill/MCP  → deterministic  (같은 입력 → 같은 출력)
Agent           → non-deterministic  (LLM이 판단, 매번 다를 수 있음)
```

---

---

## 실행 모드 로드맵

같은 Todo System 코드가 여러 모드로 동작.

### Mode 1: Interactive (현재)
```bash
python main.py
```
- TUI 대화형
- 사람이 직접 입력
- 현재 방식 그대로

### Mode 2: Headless
```bash
python main.py --headless --task "RTL 구현해줘"
python main.py --headless --flow pipeline.json
```
- TUI 없음
- 단발성 task 실행
- 결과를 stdout or JSON 파일로 출력
- 스크립트/CI에서 호출 가능

### Mode 3: Batch
```bash
python main.py --batch jobs.json
```
```json
// jobs.json
[
  {"task": "module A 구현", "model": "kimi-k2.6"},
  {"task": "module B 구현", "model": "kimi-k2.6"},
  {"task": "통합 검증",     "model": "claude-sonnet"}
]
```
- 여러 task를 순서대로 자동 실행
- 사람 개입 없음
- 결과 취합해서 report 생성
- Prefect/Jenkins 대체

### Mode 4: Server (HTTP API)
```bash
python main.py --server --port 8000
```
- FastAPI REST API
- 외부 프로그램이 HTTP로 호출
- 실행 중 상태 조회 가능
- Multi-Agent Orchestrator와 연동

```
POST /run    {"todos": [...]}  → run_id
GET  /status/{run_id}          → 진행 상태
POST /input/{run_id}           → 중간 입력 주입
GET  /result/{run_id}          → 최종 결과
```

### Mode 5: MCP Server
```bash
python main.py --mcp
```
- Anthropic MCP 표준 프로토콜
- Claude Code, Cursor 등에서 도구처럼 호출
- `.mcp.json`에 등록하면 자동 연결

```json
// 다른 Claude에서 이 시스템을 Tool로 사용
{
  "servers": {
    "common-ai-agent": {
      "command": "python main.py --mcp"
    }
  }
}
```

### Mode 6: A2A Server (Agent to Agent)
```bash
python main.py --a2a --port 9000
```
- Google A2A 표준 프로토콜
- 다른 AI Agent가 이 시스템을 Agent로 호출
- Agent Card 자동 공개 (`/.well-known/agent.json`)
- LangGraph 등 외부 Orchestrator와 표준 연동

---

### 모드별 비교

| 모드 | 호출자 | 프로토콜 | 용도 |
|---|---|---|---|
| Interactive | 사람 | TUI | 일반 사용 |
| Headless | 스크립트/CI | CLI | 자동화 |
| Batch | 스크립트 | CLI | 대량 실행 |
| Server | 어떤 프로그램 | REST HTTP | 범용 연동 |
| MCP | Claude/Cursor | MCP | AI Tool로 사용 |
| A2A | 다른 AI Agent | A2A | Multi-Agent |

### 구현 순서

```
1단계: Headless + Batch (CLI 확장 — 가장 단순)
2단계: Server (FastAPI — REST API)
3단계: MCP Server (표준 프로토콜)
4단계: A2A Server (Multi-Agent 표준)
```

---

## 구현 우선순위

1. `command` — static 실행 (shell + tool call)
2. `on_reject` — 실패 시 task 점프
3. `on_success` — 성공 시 task 점프
4. `on_condition` — 조건별 분기 (완전한 edge)
5. `agent` / `model` — todo별 지정
6. 외부 CLI agent (codex / gemini / cursor)
7. `context` / `context_group` — 컨텍스트 격리 및 공유
8. `flow_builder` — `/flow` 커맨드로 파이프라인 자동 생성
9. Headless CLI 모드 (`--task`, `--flow`, `--headless`)
10. HTTP API (`/run`, `/flow`, `/status`, `/input`)
11. Python SDK
12. Multi-Agent Orchestrator PoC
