# Sub-Agent Context 아키텍처

## 🎯 핵심 답변

**네, ExploreAgent도 별도 context를 사용합니다!**

모든 SubAgent (PlanAgent, ExploreAgent 등)는 **Main Agent와 완전히 격리된 독립적인 `_messages` context**를 가집니다.

---

## 📊 Context 격리 구조

### SubAgent Base 클래스 (`base.py:236-237`)

```python
class SubAgent(ABC):
    def __init__(self, ...):
        # 격리된 컨텍스트 (메인과 독립)
        self._messages: List[Dict[str, Any]] = []
        self._status = AgentStatus.PENDING
        self._action_plan: Optional[ActionPlan] = None
        self._tool_calls: List[Dict] = []
```

**핵심 포인트:**
- ✅ `self._messages` - SubAgent만의 독립 context
- ✅ Main Agent의 `messages`와 **완전히 분리**
- ✅ SubAgent 실행 시마다 초기화됨

---

## 🔄 Context 전달 방식

### 1. Main Agent → PlanAgent

**흐름:**
```
Main Agent
  ├─ messages: List[Dict] (전체 대화 히스토리)
  ↓
plan_mode_loop(task, context_messages=messages)
  ↓
_build_plan_context(context_messages)
  ├─ Mode: full, summary, recent
  └─ Output: context_text (string)
  ↓
PlanAgent.draft_plan(task, context=context_text)
  ↓
PlanAgent._messages (독립적인 context)
  ├─ [{"role": "system", "content": planning_prompt}]
  └─ [{"role": "user", "content": f"Task: {task}\n\nContext:\n{context_text}"}]
```

**코드 확인:**

**plan_mode.py:55-70**
```python
context_text = _build_plan_context(context_messages)

plan_agent = PlanAgent(
    name="plan_mode",
    llm_call_func=llm_call,
    execute_tool_func=_execute_plan_tool,
    max_iterations=20
)

result = plan_agent.draft_plan(task, context=context_text)
```

**plan_agent.py:224-234**
```python
def draft_plan(self, task: str, context: str = "") -> SubAgentResult:
    prompt = f"""Task:
{task}

Context:
{context if context else "None"}

Create a detailed plan using the required format.
"""
    return self._run_plan_prompt(prompt)
```

**핵심:**
- Main Agent의 messages → **string**으로 변환
- PlanAgent의 prompt에 **포함**됨
- PlanAgent._messages는 **독립적**

---

### 2. Main Agent → ExploreAgent

**흐름:**
```
Main Agent
  ├─ 도구 호출: spawn_explore(query="find FIFOs")
  ↓
tools.py:spawn_explore()
  ↓
ExploreAgent(...)
  ↓
agent.run(query, {"task": query})
  ↓
ExploreAgent._messages (독립적인 context)
  ├─ [{"role": "system", "content": exploration_prompt}]
  └─ [{"role": "user", "content": f"Task: {query}\n\nContext: ..."}]
```

**코드 확인:**

**tools.py:1624-1673**
```python
def spawn_explore(query):
    agent = ExploreAgent(
        name="explore",
        llm_call_func=call_llm_raw,
        execute_tool_func=execute_tool
    )

    result = agent.run(query, {"task": query})

    if result.status.value == "completed":
        return f"=== EXPLORATION RESULTS ===\n{result.output}"
    else:
        return f"Exploration failed: {result.errors}"
```

**base.py:268-289**
```python
def run(self, task: str, context: Dict[str, Any] = None) -> SubAgentResult:
    """
    에이전트 실행 메인 엔트리포인트
    """
    self._reset_state()  # _messages = [] 초기화
    self._initialize_context(task, context)  # context dict → string 변환
    # ...
```

**base.py:339-361**
```python
def _initialize_context(self, task: str, context: Dict[str, Any] = None):
    """독립적인 컨텍스트 초기화"""
    self._messages = []  # 독립적으로 초기화

    # context dict를 string으로 변환
    context_str = ""
    if context:
        context_parts = []
        for key, value in context.items():
            if key == "task":
                continue
            context_parts.append(f"- {key}: {value}")
        if context_parts:
            context_str = "\n[Context]\n" + "\n".join(context_parts)

    self._current_task = task
    self._context = context or {}
```

**핵심:**
- ExploreAgent도 **독립적인 _messages**
- context dict → **string**으로 변환
- Main Agent와 **격리됨**

---

## 📋 Context 격리의 이점

### 1. 독립성 (Isolation)

**Main Agent:**
```python
messages = [
    {"role": "system", "content": "You are a coding assistant..."},
    {"role": "user", "content": "Create FIFO"},
    {"role": "assistant", "content": "I'll explore first..."},
    {"role": "assistant", "content": "Action: spawn_explore(...)"},
    # ... 100+ messages ...
]
```

**ExploreAgent (독립적):**
```python
self._messages = [
    {"role": "system", "content": "You are an Exploration Agent..."},
    {"role": "user", "content": "Task: find FIFO implementations\n\nContext: None"},
    {"role": "assistant", "content": "Thought: I'll search for *.v files..."},
    # ... 단 몇 개의 messages ...
]
```

**이점:**
- ✅ SubAgent는 자신의 작업에만 집중
- ✅ Main Agent의 긴 히스토리에 영향받지 않음
- ✅ 토큰 사용량 최소화

### 2. 전문화 (Specialization)

**PlanAgent:**
```python
system_prompt = "You are a Planning Agent. DO NOT write code..."
```

**ExploreAgent:**
```python
system_prompt = "You are an Exploration Agent. ONLY use read-only tools..."
```

**이점:**
- ✅ 각 Agent의 역할이 명확
- ✅ Prompt 오염 방지
- ✅ 제약 사항 강제 (read-only 등)

### 3. 재사용성 (Reusability)

**Main Agent가 여러 번 호출:**
```python
# 첫 번째 호출
spawn_explore("find FIFO")  # 독립적인 context
# → ExploreAgent._messages는 초기화됨

# 두 번째 호출 (완전히 새로운 context)
spawn_explore("find UART")  # 독립적인 context
# → ExploreAgent._messages는 다시 초기화됨
```

**이점:**
- ✅ 이전 SubAgent 호출의 영향 없음
- ✅ 깨끗한 상태로 시작
- ✅ 병렬 실행 가능 (향후)

---

## 🔍 Context 전달 방식 비교

### Main Agent의 messages (List of Dicts)

```python
messages = [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "Create FIFO"},
    {"role": "assistant", "content": "I'll explore...", "_tokens": {...}},
    {"role": "user", "content": "Make it async"},
    # ... 계속 누적 ...
]
```

**특징:**
- ✅ 전체 대화 히스토리
- ✅ 토큰 메타데이터 포함
- ✅ 압축/요약 가능

### SubAgent에 전달되는 context (String)

```python
context_text = """
user: Create FIFO
assistant: I'll explore first...
user: Make it async
assistant: Let me check existing implementations...

[요약됨 또는 최근 N개만]
"""
```

**특징:**
- ✅ String으로 변환
- ✅ Prompt에 포함됨
- ✅ SubAgent는 참고만 하고 자신의 _messages는 독립적

---

## 🎨 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────┐
│ Main Agent                                              │
│                                                         │
│ messages: List[Dict]  ← 전체 대화 히스토리 누적         │
│ ├─ [0] system                                           │
│ ├─ [1] user: "Create FIFO"                              │
│ ├─ [2] assistant: "spawn_explore(...)"                  │
│ ├─ [3] user: "Make it async"                            │
│ └─ ... 계속 누적 ...                                    │
└─────────────────────────────────────────────────────────┘
           │
           │ spawn_explore(query="find FIFOs")
           │
           ↓
┌─────────────────────────────────────────────────────────┐
│ ExploreAgent (독립 실행)                                │
│                                                         │
│ _messages: List[Dict]  ← 독립적인 context (초기화됨)    │
│ ├─ [0] system: "You are Exploration Agent..."          │
│ ├─ [1] user: "Task: find FIFOs\nContext: None"         │
│ ├─ [2] assistant: "Thought: search *.v files..."       │
│ └─ [3] assistant: "Result: Found sync_fifo.v..."       │
│                                                         │
│ ALLOWED_TOOLS: {read_file, grep_file, ...}             │
│ (write_file, run_command 없음!)                        │
└─────────────────────────────────────────────────────────┘
           │
           │ return result
           │
           ↓
┌─────────────────────────────────────────────────────────┐
│ Main Agent (계속)                                       │
│                                                         │
│ messages: List[Dict]  ← 결과만 추가됨                   │
│ └─ [4] tool_result: "=== EXPLORATION RESULTS ===..."   │
│                                                         │
│ ExploreAgent의 _messages는 사라짐 (격리됨)              │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Plan Mode의 Context 전달

### 상세 흐름

```
User: /plan Create async FIFO
  ↓
Main Agent: messages (100+ entries)
  ↓
plan_mode_loop(task, context_messages=messages)
  ↓
_build_plan_context(messages)
  ├─ Mode: "full" → 전체 히스토리 string 변환
  ├─ Mode: "summary" → LLM으로 요약
  └─ Mode: "recent" → 최근 N개만 string 변환
  ↓
context_text = """
user: I need async FIFO
assistant: Let me check existing code...
user: Use Gray code pointers
...
"""
  ↓
PlanAgent.draft_plan(task, context=context_text)
  ↓
PlanAgent._messages = [
    {"role": "system", "content": "You are Planning Agent..."},
    {"role": "user", "content": f"""Task: Create async FIFO

Context:
{context_text}

Create a detailed plan..."""}
]
  ↓
[PlanAgent가 독립적으로 실행]
  ├─ spawn_explore("async FIFO") 자동 호출 가능
  └─ 결과 생성
  ↓
Return PlanModeResult(plan_path, plan_content)
```

**핵심:**
- Main Agent의 messages는 **참고용**으로만 사용
- PlanAgent._messages는 **완전히 독립적**
- PlanAgent는 자신만의 prompt와 system message 사용

---

## 📊 Context 사용량 비교

### Main Agent

```
messages: 150 entries
Total tokens: ~50,000 tokens
Context usage: 50,000 / 200,000 (25%)
```

### PlanAgent (격리된 context)

```
_messages: 5-10 entries
Total tokens: ~2,000 tokens
Context usage: 2,000 / 200,000 (1%)
```

**이점:**
- ✅ SubAgent는 훨씬 적은 토큰 사용
- ✅ Main Agent의 긴 히스토리 영향 없음
- ✅ 빠른 응답 시간

---

## ⚙️ Context Mode 설정 (Plan Mode)

Plan Mode에서는 Main Agent의 히스토리를 어떻게 전달할지 선택 가능:

### 1. Full Mode (기본)

```bash
export PLAN_MODE_CONTEXT_MODE="full"
```

**효과:**
- Main Agent의 전체 messages → string 변환
- PlanAgent가 모든 맥락 파악 가능
- 단, 토큰 사용량 증가

### 2. Summary Mode

```bash
export PLAN_MODE_CONTEXT_MODE="summary"
```

**효과:**
- Main Agent의 messages → LLM으로 요약
- 핵심만 전달
- 토큰 절약

### 3. Recent Mode

```bash
export PLAN_MODE_CONTEXT_MODE="recent"
export PLAN_MODE_CONTEXT_RECENT_N=10
```

**효과:**
- 최근 N개 messages만 string 변환
- 가장 관련 높은 정보만 전달
- 토큰 최소화

---

## 🎯 요약

### ✅ 모든 SubAgent는 독립 Context 사용

| Agent | Context 격리 | Main과 공유? |
|-------|-------------|-------------|
| Main Agent | `messages: List[Dict]` | N/A |
| PlanAgent | `_messages: List[Dict]` | ❌ 격리됨 |
| ExploreAgent | `_messages: List[Dict]` | ❌ 격리됨 |

### ✅ Context 전달 방식

```
Main messages (list) → string 변환 → SubAgent prompt에 포함 → SubAgent._messages (독립)
```

### ✅ 이점

1. **독립성**: SubAgent는 자신의 작업에만 집중
2. **전문화**: 각 Agent의 역할이 명확 (read-only 등)
3. **재사용성**: 이전 호출의 영향 없음
4. **효율성**: 토큰 사용량 최소화

### ✅ 검증

**테스트 실행:**
```bash
# ExploreAgent 테스트
python3 test_explore_agent.py
# ✅ 7/7 tests passed

# Plan Mode 테스트
python3 test_plan_mode_e2e.py
# ✅ 5/5 tests passed
```

---

## 📚 관련 파일

- **brian_coder/agents/sub_agents/base.py:236-237** - SubAgent 격리된 context
- **brian_coder/agents/sub_agents/base.py:339-361** - context 초기화
- **brian_coder/core/plan_mode.py:55-70** - PlanAgent context 전달
- **brian_coder/core/tools.py:1624-1673** - ExploreAgent context 전달

---

**결론: 네, ExploreAgent도 Main Agent와 완전히 격리된 별도 context를 사용합니다!** ✅
