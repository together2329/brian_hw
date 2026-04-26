
# Compression Display Fix — 대화 기록

## 1. 문제 인식

**사용자:** "compression 동작이 오히려 고쳐서 이상해진 것 같은데?"

Compression Summary로 사용자에게 보여주는 내용과 실제 context에 들어가는 내용이 완전히 달랐음.

## 2. 원인 분석

`compressor.py`의 display 섹션(기존 lines 832-843)이 `compressed[0]`의 LLM 요약 텍스트만 보여주었지만,
실제 `new_history`에는 다음이 모두 합쳐져 들어갔음:

- System prompt (원본)
- LLM 생성 요약
- Todo Status
- Awaiting Input Note
- Important Messages (!important)
- Recent Messages (압축되지 않은 최근 메시지들)

## 3. 수정 내용

### 기존 코드 (lines 832-843)

```python
# Emit summary as markdown (TUI) or print to stdout (terminal)
if compressed:
    raw = compressed[0].get("content", "") if isinstance(compressed[0], dict) else ""
    import re as _re
    summary_text = _re.sub(r"^\[Previous Conversation Summary \(\d+ messages\)\]:\s*", "", raw)
    if summary_text.strip():
        md = f"## Compression Summary\n\n{summary_text.strip()}\n"
        if emit_fn:
            emit_fn(md)
        else:
            print(md)
return new_history
```

→ **문제:** LLM 요약만 보여줌. Todo, Awaiting, Important, Recent는 표시 안 함.

### 수정 후 코드 (lines 832-897)

```python
# Emit full context as markdown (TUI) or print to stdout (terminal)
import re as _re
md_parts = []

# 1. Compression Summary (LLM 생성 요약)
if compressed:
    for _ci, _comp_msg in enumerate(compressed):
        raw = _comp_msg.get("content", "")
        summary_text = _re.sub(r"^\[Previous Conversation Summary ...", "", raw)
        summary_text = _re.sub(r"^\[Summary chunk ...", "", summary_text)
        if summary_text.strip():
            md_parts.append("## Compression Summary\n\n" + summary_text.strip())

# 2. Todo Status
if todo_preservation:
    for _tp in todo_preservation:
        md_parts.append("## Todo Status\n\n" + _tpc.strip())

# 3. Awaiting Input Note
if awaiting_note:
    for _an in awaiting_note:
        md_parts.append("## Awaiting Input\n\n" + _anc.strip())

# 4. Important Messages
if important_msgs:
    md_parts.append("## Important Messages\n\n" + ...)

# 5. Recent Messages (brief preview, 200자)
if recent_msgs:
    md_parts.append("## Recent Messages\n\n" + ...)

# 6. Stats
md_parts.append("## Stats\n\n" + ...)

md = "\n\n---\n\n".join(md_parts) + "\n"
if emit_fn:
    emit_fn(md)
else:
    print(md)
return new_history
```

→ **개선:** 실제 context에 들어가는 모든 내용을 섹션별로 표시

---

## 4. 핵심 질문: "그 display 내용이 다음 context에 어떻게 들어가는거야?"

### 답변: display와 실제 context는 완전히 분리되어 있음

```
compress_history() 내부
│
├─ new_history 구성 (LLM이 다음 턴에 받는 실제 데이터)
│   system_msgs + important_msgs + compressed 
│   + awaiting_note + todo_preservation + recent_msgs
│   → system message consolidation (1개로 병합)
│   → new_history = [system(병합)] + [non-system messages...]
│
├─ emit_fn(md)  ←── 사용자 화면 표시용 (TUI)
│   "## Compression Summary\n## Todo Status\n..."
│
└─ return new_history  ←── 실제 다음 context
```

`emit_fn`은 `_textual_emit_content_fn` (TUI 화면 출력 함수)에 연결되어 있고,
`new_history`가 `react_loop.py`의 `messages = deps.compress_fn(...)` 로 돌아가서
실제 LLM 호출에 사용됨.

| | Display (emit_fn) | new_history (return) |
|---|---|---|
| **용도** | 사용자 화면 표시 | LLM 다음 호출 context |
| **형태** | Markdown 문자열 | `[{"role": "system", "content": "..."}, ...]` |
| **내용** | 요약, Todo, Recent 등 섹션별 표시 | system message 1개(모두 병합) + non-system msgs |
| **들어가는 곳** | TUI 화면 | `messages` 변수 → LLM API |

---

## 5. 핵심 질문: "compression에는 뭐가 들어가 그럼?"

### `compressed` 변수의 정체

`_compress_single()`이 반환하는 것:

```python
{
    "role": "system",
    "content": "[Previous Conversation Summary (42 messages)]: <LLM이 생성한 요약 텍스트>"
}
```

LLM에게 요청하는 구조:
- **system**: "You are a helpful assistant that summarizes..."
- **user**: `STRUCTURED_SUMMARY_PROMPT` (긴 지시어) + `conversation_text` (old_msgs의 role:content 들)

### raw_history 조립 (line 732-735)

```
raw_history = [
    system_msgs,          # 원래 system prompt (role: system)
    important_msgs,       # !important 메시지들 (role: user/assistant)
    compressed,           # LLM 요약 (role: system) 
    awaiting_note,        # [AWAITING USER INPUT...] (role: system)
    todo_preservation,    # [Todo Status]: ... (role: system)
    recent_msgs,          # 최근 메시지들 (role: user/assistant/tool)
]
```

### System message 병합 (lines 742-764) — 핵심

모든 `role: system`을 **하나로 합침**:

```
new_history = [
    {"role": "system", "content": """
        <원래 system prompt>
        
        [Previous Conversation Summary (42 messages)]: <LLM 요약>
        
        [AWAITING USER INPUT] Your previous turn asked...
        
        [Todo Status]:
          ✅ 1. [completed] ...
          ▶ 2. [in_progress] ...
          ⏸ 3. [pending] ...
        [Ongoing Task]: ...
    """},
    important_msgs...,   # role: user/assistant
    recent_msgs...,      # role: user/assistant/tool
]
```

### 최종: LLM이 다음 턴에 받는 구조

```
messages[0] = { role: "system", content: "원래프롬프트\n\n요약\n\nTodo\n\nAwaiting..." }
messages[1] = { role: "user", content: "..." }      # recent/important
messages[2] = { role: "assistant", content: "..." }  # recent/important
...
messages[N] = { role: "user", content: "새 사용자 입력" }
```

**`compressed` = LLM이 old_msgs를 요약한 텍스트**이고,
이것이 system message 안에 다른 시스템 정보(todo, awaiting 등)와 함께 `\n\n`으로 구분되어 병합됨.

---

## 6. Compression 전체 Flow

```
compress_history() 호출
  │
  ├─ 1. 임계값 체크 (preemptive / emergency threshold)
  ├─ 2. pre_compact hook 실행
  ├─ 3. 메시지 분리: system / !important / regular
  ├─ 4. Turn-based protection → old_msgs / recent_msgs 분리
  ├─ 5. Tool call pair 무결성 보장
  ├─ 6. Todo 보존 메시지 생성
  ├─ 7. _compress_single() 또는 _compress_chunked() 호출
  │     └─ LLM이 old_msgs 요약 → compressed 변수에 저장
  ├─ 8. Awaiting user input 감지
  ├─ 9. raw_history 조합:
  │     system_msgs + important_msgs + compressed
  │     + awaiting_note + todo_preservation + recent_msgs
  ├─ 10. System message consolidation (1개로 병합)
  │      모든 role:system → 하나의 system message에 \n\n로 join
  ├─ 11. Emergency pruning (여전히 초과 시 tail-truncate)
  ├─ 12. post_compact hook 실행
  ├─ 13. [NEW] 전체 context 내용을 markdown으로 emit (사용자 화면)
  └─ 14. return new_history → react_loop의 messages 변수에 할당
```

---

## 7. 호출 연결망

```
src/main.py
  └─ compress_history() wrapper (line 964)
       └─ _compress_history_impl() = core/compressor.compress_history()
            ├─ emit_fn = _textual_emit_content_fn (TUI 화면)
            └─ return new_history

src/main.py (line 984-986):
  emit_fn = lambda md: (_textual_emit_content_fn(md), _textual_emit_flush_fn())

react_loop.py (line 398):
  messages = deps.compress_fn(messages, todo_tracker=todo_tracker)
  
react_loop.py (line 562):
  messages = deps.compress_fn(messages, todo_tracker=todo_tracker, force=True)

src/main.py (line 996):
  compress_fn=compress_history  ← react_loop에 주입
```

---

## 8. 테스트 결과

- 기존 compressor 테스트 31개 통과 ✅
- `test_identity_at_beginning` — **pre-existing failure** (수정 전부터 실패)
  - `ACTIVE_WORKSPACE` → `[Workflow: ...]` 주입 기능이 미구현 상태
