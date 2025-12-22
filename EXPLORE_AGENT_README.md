# ExploreAgent - 코드베이스 탐색 전용 에이전트

## 🎯 개요

ExploreAgent는 **읽기 전용** 도구만 사용하여 코드베이스를 탐색하고 정보를 수집하는 Sub-Agent입니다.

### 주요 특징

- ✅ **Read-Only**: 코드 작성/수정 없이 탐색만 수행
- ✅ **13가지 탐색 도구**: 파일 검색, 패턴 분석, 구조 파악
- ✅ **Plan Mode 통합**: PlanAgent가 자동으로 호출 가능
- ✅ **Main Agent 통합**: Main Agent도 spawn_explore로 호출 가능
- ✅ **구조화된 결과**: 발견된 파일, 패턴, 규칙을 요약

---

## 🛠️ 사용 가능한 도구 (13개)

### 파일 읽기
- `read_file` - 전체 파일 읽기
- `read_lines` - 특정 라인만 읽기

### 파일 검색
- `grep_file` - 패턴 검색 (정규식)
- `find_files` - 파일명 패턴으로 검색
- `list_dir` - 디렉토리 내용 나열

### Git 정보
- `git_status` - Git 상태 확인
- `git_diff` - Git diff 확인

### RAG 검색
- `rag_search` - 의미 기반 검색
- `rag_status` - RAG 데이터베이스 상태

### Verilog 전용
- `analyze_verilog_module` - Verilog 모듈 분석
- `find_signal_usage` - 신호 사용처 찾기
- `find_module_definition` - 모듈 정의 찾기
- `extract_module_hierarchy` - 모듈 계층 구조 추출

### ❌ 사용 불가 도구

ExploreAgent는 다음 도구를 **사용할 수 없습니다**:
- `write_file` - 파일 쓰기 금지
- `run_command` - 명령 실행 금지
- `replace_in_file` - 파일 수정 금지
- `replace_lines` - 라인 수정 금지

---

## 🚀 사용 방법

### 1. Main Agent에서 호출

Main Agent가 작업 중 코드베이스 정보가 필요할 때:

```
You: 기존 FIFO 구현을 참고해서 새로운 async FIFO를 만들어줘

Main Agent:
Thought: 먼저 기존 FIFO 구현을 찾아봐야겠다
Action: spawn_explore(query="find all FIFO implementations")
Observation:
=== EXPLORATION RESULTS ===
Files Found:
1. rtl/sync_fifo.v - Synchronous FIFO with simple pointer logic
2. rtl/async_fifo.v - Asynchronous FIFO with Gray code pointers
3. testbenches/fifo_tb.v - Common FIFO testbench

Patterns Identified:
- Use of dual-port SRAM
- Gray code for CDC (Clock Domain Crossing)
- Full/empty flag generation
- Parameterized depth and width

Conventions:
- Module naming: <type>_fifo.v
- Testbench naming: <module>_tb.v
===========================

Thought: 좋아, async_fifo.v를 참고해서 새로운 버전을 만들자
Action: read_file(path="rtl/async_fifo.v")
...
```

### 2. Plan Mode에서 자동 호출

**Plan Agent가 자동으로 spawn_explore를 호출합니다:**

```
You: /plan Create SPI master controller similar to existing I2C master

[Plan Mode 진입]

Plan Agent:
Thought: 기존 I2C 마스터 구현을 먼저 확인해야겠다
Action: spawn_explore(query="find I2C master implementations and understand interface")

[자동으로 코드베이스 탐색]

Plan Agent:
Based on exploration results, I found:
- i2c_master.v uses state machine with 5 states
- Register interface: CONTROL, STATUS, DATA, PRESCALE
- Interrupt on completion

## Implementation Plan
1. Create SPI master module with similar register interface
2. Implement 4-wire SPI protocol (MOSI, MISO, SCLK, CS)
3. Add baud rate generator (similar to I2C prescaler)
...
```

### 3. 직접 Python에서 호출

```python
from core.tools import spawn_explore

# 탐색 실행
result = spawn_explore("find all testbench files and identify testing patterns")

print(result)
# === EXPLORATION RESULTS ===
# Files Found:
# 1. testbenches/counter_tb.v
# 2. testbenches/fifo_tb.v
# ...
```

---

## 📋 ExploreAgent 동작 원리

### 1. 초기화

```python
from agents.sub_agents.explore_agent import ExploreAgent
from llm_client import call_llm_raw

agent = ExploreAgent(
    name="explore",
    llm_call_func=call_llm_raw,
    execute_tool_func=execute_tool
)
```

### 2. 탐색 실행

```python
result = agent.run(
    query="find all FIFO implementations",
    context={"task": "find all FIFO implementations"}
)
```

### 3. 결과 구조

```python
SubAgentResult(
    status=AgentStatus.COMPLETED,
    output="=== Files Found ===\n1. sync_fifo.v\n...",
    artifacts={
        "files_read": ["sync_fifo.v", "async_fifo.v"],
        "tool_calls_count": 5,
        "exploration_depth": 2
    },
    context_updates={
        "exploration_summary": "Found 2 FIFO implementations...",
        "files_examined": ["sync_fifo.v", "async_fifo.v"],
        "agent_type": "explore"
    },
    tool_calls=[
        {"tool": "find_files", "args": "*.v"},
        {"tool": "read_file", "args": "sync_fifo.v"},
        ...
    ],
    errors=[]
)
```

---

## 🔍 탐색 쿼리 예시

### 좋은 쿼리 (구체적)

✅ **파일 찾기:**
```python
spawn_explore("find all AXI protocol implementations")
spawn_explore("find testbench files for memory controllers")
```

✅ **패턴 이해:**
```python
spawn_explore("understand how clock domain crossing is handled")
spawn_explore("identify coding conventions for FSM implementation")
```

✅ **구조 파악:**
```python
spawn_explore("analyze the module hierarchy for PCIe subsystem")
spawn_explore("understand register interface patterns used in this project")
```

✅ **유사 코드 찾기:**
```python
spawn_explore("find UART implementations similar to I2C master")
spawn_explore("locate existing error handling patterns")
```

### 나쁜 쿼리 (모호함)

❌ **너무 광범위:**
```python
spawn_explore("everything")  # 너무 광범위
spawn_explore("all files")   # 의미 없음
```

❌ **실행 요청 포함:**
```python
spawn_explore("run simulation and show results")  # ExploreAgent는 실행 불가
spawn_explore("compile and fix errors")           # 수정 작업 불가
```

❌ **코드 생성 요청:**
```python
spawn_explore("create a new FIFO module")  # 생성 작업 불가
spawn_explore("write testbench")           # 작성 작업 불가
```

---

## 🔐 제약 사항

### 1. Read-Only 원칙

ExploreAgent는 **절대** 다음을 수행하지 않습니다:
- ❌ 파일 쓰기/수정
- ❌ 명령 실행
- ❌ 코드 생성
- ❌ 설계 작성

### 2. 정보 수집만

ExploreAgent는 **오직** 다음만 수행합니다:
- ✅ 파일 읽기
- ✅ 패턴 검색
- ✅ 구조 분석
- ✅ 정보 요약

### 3. Prompt 강제

ExploreAgent의 system prompt에는 다음이 포함됩니다:

```
⚠️ CRITICAL CONSTRAINTS:
- You can ONLY use read-only tools (no write, no run_command)
- DO NOT generate any code, modules, or implementations
- DO NOT draft solutions or write code snippets
- ONLY gather information, analyze structure, and summarize findings
```

---

## 🧪 테스트

### 자동 테스트 실행

```bash
python3 test_explore_agent.py
```

**테스트 결과:**
```
✅ PASS  ExploreAgent Class
✅ PASS  spawn_explore Function
✅ PASS  ExploreAgent Initialization
✅ PASS  ExploreAgent Prompts
✅ PASS  PlanAgent Integration
✅ PASS  spawn_explore Basic
✅ PASS  ExploreAgent Artifacts

Results: 7/7 tests passed
🎉 All ExploreAgent tests passed!
```

### 수동 테스트

```bash
cd brian_coder
python3 src/main.py
```

```
You: find all FIFO implementations using explore

Main Agent:
Action: spawn_explore(query="find all FIFO implementations")
...
```

---

## 📊 Plan Mode 통합

### PlanAgent + ExploreAgent 워크플로우

```
User: /plan Create async FIFO
  ↓
[Plan Mode]
  ↓
Plan Agent: "먼저 기존 코드를 탐색하겠습니다"
  ↓
Plan Agent: spawn_explore("async FIFO implementations")
  ↓
Explore Agent:
  ├─ find_files(pattern="*fifo*.v")
  ├─ read_file(path="async_fifo.v")
  ├─ analyze_verilog_module(path="async_fifo.v")
  └─ Return: "Found async_fifo.v with Gray code pointers..."
  ↓
Plan Agent: "탐색 결과를 바탕으로 plan 작성"
  ↓
Plan:
## Task Analysis
Based on existing async_fifo.v implementation...

## Implementation Steps
1. Create module skeleton (similar to async_fifo.v)
2. Implement Gray code conversion (pattern: gray = (bin >> 1) ^ bin)
...
```

### 통합 상태 확인

**PlanAgent의 ALLOWED_TOOLS:**
```python
ALLOWED_TOOLS: Set[str] = {"spawn_explore"}
```

**검증:**
```bash
python3 test_explore_agent.py
# Test 5: PlanAgent Integration
# ✅ PASS: PlanAgent can use spawn_explore
```

---

## 🎓 Best Practices

### 1. 구체적인 쿼리 작성

❌ **나쁜 예:**
```python
spawn_explore("files")
```

✅ **좋은 예:**
```python
spawn_explore("find all SPI controller implementations and identify common interface patterns")
```

### 2. 단계적 탐색

**복잡한 탐색은 여러 단계로 나눠서:**

```
Step 1: spawn_explore("find all memory controller modules")
Step 2: spawn_explore("understand AXI interface in found controllers")
Step 3: spawn_explore("identify testing patterns in controller testbenches")
```

### 3. Plan Mode에서 자동 활용

**Plan Mode를 사용하면 ExploreAgent가 자동으로 활용됩니다:**

```
/plan Create UART transmitter similar to existing I2C

[Plan Agent가 자동으로:]
1. spawn_explore("I2C implementations")
2. [결과 분석]
3. [Plan 작성 with 기존 패턴 참조]
```

---

## 🔧 문제 해결

### 문제 1: ExploreAgent가 코드를 생성함

**증상:** ExploreAgent가 탐색 대신 코드를 작성

**원인:** Prompt 오염 또는 ALLOWED_TOOLS 수정

**해결:**
- ExploreAgent.ALLOWED_TOOLS에 write_file이 없는지 확인
- Prompt가 "DO NOT generate code"를 포함하는지 확인

### 문제 2: spawn_explore 결과가 너무 짧음

**증상:** "No files found" 또는 매우 짧은 결과

**원인:** 쿼리가 너무 구체적이거나 코드베이스에 해당 파일 없음

**해결:**
- 더 광범위한 쿼리 사용
- 파일이 실제로 존재하는지 확인
- Debug mode 활성화하여 tool calls 확인

### 문제 3: PlanAgent가 spawn_explore를 호출하지 않음

**증상:** Plan Agent가 탐색 없이 plan 생성

**원인:** LLM이 탐색이 필요하다고 판단하지 않음

**해결:**
- Task 설명에 "기존 코드 참조" 명시
- 예: "/plan Create SPI master **similar to existing I2C master**"

---

## 📈 성능 최적화

### 1. 탐색 범위 제한

ExploreAgent의 max_iterations 조정:

```python
agent = ExploreAgent(
    name="explore",
    llm_call_func=call_llm_raw,
    execute_tool_func=execute_tool,
    max_iterations=5  # 기본값: 10
)
```

### 2. RAG 활용

대규모 코드베이스에서는 RAG 검색이 더 빠를 수 있습니다:

```python
spawn_explore("use rag_search to find FIFO implementations")
```

---

## 🆚 Main Agent vs ExploreAgent

| 특징 | Main Agent | ExploreAgent |
|------|-----------|--------------|
| 목적 | 작업 실행 | 정보 수집 |
| 도구 | 모든 도구 | 읽기 전용만 |
| 코드 작성 | ✅ 가능 | ❌ 불가 |
| 파일 수정 | ✅ 가능 | ❌ 불가 |
| 명령 실행 | ✅ 가능 | ❌ 불가 |
| 탐색 | ✅ 가능 | ✅ 전문 |
| 호출 방법 | 직접 대화 | spawn_explore |

---

## 🔗 관련 문서

- **PLAN_MODE_README.md**: Plan Mode 사용 가이드
- **test_explore_agent.py**: ExploreAgent 테스트
- **brian_coder/agents/sub_agents/explore_agent.py**: 소스 코드

---

## ❓ FAQ

**Q: ExploreAgent와 Main Agent의 차이는?**

A: ExploreAgent는 읽기 전용으로 탐색만 수행합니다. Main Agent는 모든 도구를 사용하여 작업을 실행합니다.

**Q: Plan Mode에서 spawn_explore가 자동으로 호출되나요?**

A: 네, Plan Agent가 필요하다고 판단하면 자동으로 호출합니다.

**Q: ExploreAgent로 테스트를 실행할 수 있나요?**

A: 아니요, ExploreAgent는 run_command를 사용할 수 없어 테스트 실행이 불가능합니다.

**Q: spawn_explore 결과를 파일로 저장하려면?**

A: spawn_explore 결과는 string으로 반환되므로 직접 파일에 저장할 수 있습니다:
```python
result = spawn_explore("find FIFOs")
with open("exploration_result.txt", "w") as f:
    f.write(result)
```

---

**Happy Exploring! 🔍**
