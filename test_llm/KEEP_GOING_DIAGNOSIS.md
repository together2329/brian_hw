# Keep Going 기능 문제 진단 및 해결책

> `common_ai_agent`의 Keepalive / Keep Going 자동 진행 기능 분석

---

## 1. 현재 Keep Going 메커니즘 요약

Keep Going은 **2가지 경로**로 작동합니다:

### 경로 A — Keepalive (자동 주입)
```
src/main.py _keepalive_thread_fn()
```
- 사용자 입력 대기 중에만 동작 (`_keepalive_waiting[0] = True`)
- `KEEPALIVE_INTERVAL`초 동안 입력이 없으면 자동으로 `"keep going"` 메시지 주입
- Todo Tracker가 있으면 `get_continuation_prompt()` 결과를 덧붙임

### 경로 B — 수동 "keep going"
```
core/chat_loop.py
```
- 사용자가 직접 `"keep going"`, `"continue"`, `"계속"` 입력
- Todo Tracker의 현재 태스크 상태를 리마인더로 주입

---

## 2. 왜 잘 동작하지 않는가? — 문제점 6가지

### 🔴 문제 1 — Keepalive가 "입력 대기 상태"에서만 동작함

```python
# main.py 1315라인
if not _keepalive_waiting[0]:
    continue   # ← LLM이 작업 중이면 keepalive가 아예 실행 안 됨
```

**문제:** LLM이 긴 작업을 하고 있을 때(ReAct 루프 안에 있을 때)는  
`_keepalive_waiting = False`이므로 **Keepalive가 전혀 개입하지 못합니다.**

즉, Keepalive는 **"LLM이 멈췄는데 사용자가 타이핑 안 하는 상황"**에만 작동합니다.  
**"LLM이 중간에 멈추고 다음 태스크를 안 넘어가는 상황"**에는 무력합니다.

---

### 🔴 문제 2 — `app.exit()` 경쟁 상태 (Race Condition)

```python
# main.py 1337~1340라인 (prompt_toolkit 경로)
app = _multiline_prompt.app
if app is not None:
    app.exit(result=_full_msg)   # ← 강제로 prompt에 결과 주입
    continue
```

```python
# main.py 1344~1347라인 (fallback: stdin 경로)
_os.write(sys.stdin.fileno(), (_full_msg + "\n").encode())
```

**문제:**
- `app.exit()`는 prompt_toolkit이 **활성화된 상태**에서만 동작
- LLM 작업 중에는 prompt가 떠 있지 않으므로 `app.exit()`가 **실패하거나 무시됨**
- `stdin.write` fallback은 터미널 환경(TUI, IDE 터미널)에서 **대부분 동작하지 않음**
- 결과: Keepalive 메시지가 **조용히 사라짐** — 사용자는 아무 피드백도 못 받음

---

### 🔴 문제 3 — "keep going"이 너무 모호함

```python
KEEPALIVE_MESSAGE = os.getenv("KEEPALIVE_MESSAGE", "keep going")
```

**문제:** LLM 입장에서 `"keep going"`이라는 메시지만으로는:
- **무엇을** 계속해야 하는지
- **어디서** 이어서 해야 하는지
- **다음 태스크가 무엇인지**

알 수 없습니다. 특히 이전 작업이 완료된 상태라면 LLM은  
"뭘 더 해야 하지?"하고 혼란스러워하거나 엉뚱한 작업을 시작합니다.

`get_continuation_prompt()`가 덧붙여지긴 하지만, 이것도 **"현재 태스크 상태"**만 알려줄 뿐  
**"왜 멈췄고, 정확히 뭘 해야 하는지"**는 안 알려줍니다.

---

### 🔴 문제 4 — LLM이 ReAct 루프 안에서 "완료"하고 빠져나오면 Keepalive가 의미 없음

```
ReAct 루프: LLM 작업 → final answer → 루프 종료 → 사용자 입력 대기
                                                            ↑
                                                    여기서 Keepalive 대기
```

**문제:** LLM이 태스크를 하나 완료하고 `final_answer`를 내면 ReAct 루프가 **종료**됩니다.  
그 다음 사용자 입력을 기다리는데, 이때 Keepalive가 발동하면:

1. **이미 종료된 턴** — LLM이 "나 끝났어"라고 한 직후
2. **Keepalive가 "keep going" 주입** — LLM은 새 턴을 시작
3. **하지만 컨텍스트가 리셋됨** — 이전 턴의 도구 실행 결과, 파일 내용 등이 히스토리에만 남고,  
   LLM은 **새 턴에서 맥락을 다시 파악해야 함**
4. **효율 저하** — 연속 작업이어야 할 게 매 턴마다 "재시작"하는 느낌

---

### 🔴 문제 5 — `KEEPALIVE_INTERVAL` 기본값이 0 (비활성화)

```python
KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "0"))  # ← 기본 OFF
```

**문제:** 사용자가 명시적으로 환경변수를 설정하지 않으면 **Keepalive 자체가 꺼져 있습니다.**  
대부분의 사용자는 이 설정의 존재조차 모를 가능성이 높습니다.

---

### 🔴 문제 6 — LLM 빈 응답 후 Keepalive가 과도한 재시도 유발

빈 응답 → Recovery(재시도/압축/넛지) → 그래도 실패 → 사용자 입력 대기 →  
Keepalive 발동 → 또 "keep going" → 또 빈 응답 → **무한 루프 가능성**

현재 Keepalive가 **이전 턴이 빈 응답이었는지** 확인하지 않습니다.

---

## 3. 해결책

### 해결책 1 — ReAct 루프 내부 자동 Continue 도입

**핵심 아이디어:** Keepalive(외부 주입) 대신, **ReAct 루프 안에서 자동으로 다음 태스크로 넘어가는** 메커니즘을 추가.

```python
# core/react_loop.py — 새로운 auto-continue 로직

# ReAct 루프가 final_answer에 도달한 후:
if final_answer and todo_tracker and not todo_tracker.is_all_completed():
    next_task = todo_tracker.get_continuation_prompt()
    if next_task and auto_continue_enabled:
        # 새 턴을 시작하지 않고, 같은 루프 안에서 다음 태스크 주입
        messages.append({
            "role": "user", 
            "content": f"[Auto-continue] {next_task}"
        })
        collected_content = ""  # 리셋
        continue  # ← 루프 계속, 사용자 입력 불필요
```

**장점:**
- 컨텍스트가 리셋되지 않음 (같은 ReAct 루프 안에서 진행)
- 사용자 개입 없이 연속 작업 가능
- LLM이 이전 작업 맥락을 그대로 유지

---

### 해결책 2 — Keepalive 메시지 품질 개선

```python
# Before
_msg = "keep going"

# After — 구체적인 컨텍스트 포함
def _build_keepalive_message(todo_tracker, messages):
    parts = ["[Auto-continue]"]
    
    # 1. 마지막 assistant 응답 요약
    last_assistant = [m for m in messages if m["role"] == "assistant"]
    if last_assistant:
        parts.append(f"Previous work summary: {last_assistant[-1]['content'][:200]}")
    
    # 2. 다음 태스크 정보
    if todo_tracker and not todo_tracker.is_all_completed():
        current = todo_tracker.get_current_todo()
        idx = todo_tracker.current_index + 1
        total = len(todo_tracker.todos)
        parts.append(f"Next: Task {idx}/{total} — {current.content}")
        parts.append(f"Start with: todo_update(index={idx}, status='in_progress')")
    
    return "\n".join(parts)
```

---

### 해결책 3 — Keepalive 발동 조건 개선

```python
# Before: 무조건 keep going
if idle < _interval:
    continue

# After: 이전 턴 상태 확인
_last_was_empty = check_last_turn_empty(messages)
_last_was_error = check_last_turn_error(messages)

if _last_was_empty or _last_was_error:
    # 빈 응답/에러 직후에는 Keepalive 금지 — 무한 루프 방지
    _keepalive_last_activity[0] = time.time()  # 타이머 리셋
    continue
```

---

### 해결책 4 — `KEEPALIVE_INTERVAL` 기본값 변경 + 명시적 활성화

```python
# Before
KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "0"))

# After: Todo가 활성화되면 Keepalive도 자동 활성화
KEEPALIVE_INTERVAL = int(os.getenv("KEEPALIVE_INTERVAL", "120"))  # 2분

# 또는: Todo Tracker가 켜져 있으면 자동으로 Keepalive 활성화
if config.ENABLE_TODO_TRACKING and config.KEEPALIVE_INTERVAL == 0:
    config.KEEPALIVE_INTERVAL = 120  # 기본 2분
```

---

### 해결책 5 — Keepalive 상태 피드백 추가

현재 Keepalive가 실패해도 사용자가 모릅니다. 디버그 로그를 추가:

```python
# main.py _keepalive_thread_fn()
try:
    app.exit(result=_full_msg)
    print(f"[Keepalive] ✅ Injected via prompt_toolkit")
except Exception as e:
    print(f"[Keepalive] ⚠️ prompt_toolkit injection failed: {e}")

try:
    _os.write(sys.stdin.fileno(), ...)
    print(f"[Keepalive] ✅ Injected via stdin")
except Exception as e:
    print(f"[Keepalive] ⚠️ stdin injection failed: {e}")
    print(f"[Keepalive] ❌ All injection methods failed — keepalive dropped!")
```

---

## 4. 우선순위

| 우선순위 | 해결책 | 효과 | 난이도 |
|---------|--------|------|--------|
| **P0** | 해결책 1: ReAct 루프 내부 Auto-Continue | 근본 해결 | 중 |
| **P0** | 해결책 3: 빈 응답 후 Keepalive 금지 | 무한 루프 방지 | 낮음 |
| **P1** | 해결책 2: 메시지 품질 개선 | LLM 응답 품질 향상 | 낮음 |
| **P1** | 해결책 4: 기본값 활성화 | 사용자 경험 개선 | 매우 낮음 |
| **P2** | 해결책 5: 상태 피드백 | 디버깅 가능 | 매우 낮음 |

---

## 5. 한 줄 요약

> **현재 Keep Going은 "LLM이 멈춘 후 사용자가 입력 안 할 때"만 작동하는 반쪽짜리 기능입니다.**  
> 진짜 필요한 건 **"LLM이 ReAct 루프 안에서 자동으로 다음 태스크로 넘어가는"** 내부 Auto-Continue 메커니즘입니다.
