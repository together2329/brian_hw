# LLM 빈 응답(Empty Response) 발생 원인과 대응 방안

> `common_ai_agent/core/react_loop.py` 기준 — 3단계 방어 체계 분석

---

## 1. 빈 응답이 발생하는 원인

| # | 원인 | 설명 |
|---|------|------|
| 1 | **Reasoning 토큰 초과** | DeepSeek R1, Claude(thinking) 등이 내부 추론에 출력 토큰을 전부 소진하여 실제 응답 본문이 비어 있음 |
| 2 | **컨텍스트 윈도우 포화** | 대화 히스토리가 너무 길어 모델이 출력을 생성할 공간이 부족 |
| 3 | **API 일시적 오류** | 타임아웃, Rate Limit, 네트워크 끊김 등 |
| 4 | **안전 필터 거부** | 모델이 응답을 거부하면서 빈 문자열을 반환 |

---

## 2. 전체 흐름도

```
                    LLM 응답 도착
                         │
               ┌─────────┴──────────┐
               │ 네이티브 툴콜 있음?  │
               └─────────┬──────────┘
                    YES ↓        NO ↓
                  ✅ 정상 처리      │
                                   ↓
                         ┌─────────────────┐
                         │  1단계: 재시도    │  최대 LLM_RETRY_COUNT회
                         └────────┬────────┘
                             실패 ↓
                         ┌─────────────────────────┐
                         │  2단계: 컨텍스트 압축      │  대화 히스토리 요약
                         │  + 재시도 카운터 초기화     │
                         └────────┬────────────────┘
                             실패 ↓
                         ┌─────────────────────────┐
                         │  3단계: 넛지(Nudge) 주입   │  "도구를 호출하거나 답해라"
                         │  + 재시도                 │
                         └────────┬────────────────┘
                             실패 ↓
                         ┌─────────────────────────┐
                         │  2단계 재실행: 압축        │  마지막 기회
                         └────────┬────────────────┘
                             실패 ↓
                       🔙 사용자 입력으로 복귀
```

---

## 3. 3단계 방어 체계 상세

### 3.1 1단계 — 단순 재시도 (Simple Retry)

> **위치:** `react_loop.py` 606~610라인

```python
if not collected_content.strip() and not _has_native:
    if _llm_retry < cfg.LLM_RETRY_COUNT:   # 기본값: 1회
        _llm_retry += 1
        continue   # LLM 다시 호출
```

| 항목 | 내용 |
|------|------|
| **동작** | LLM을 설정된 횟수만큼 재호출 |
| **기본 재시도 횟수** | 1회 (`LLM_RETRY_COUNT = 1`) |
| **예외 처리** | 네이티브 툴 콜이 있으면 빈 텍스트도 **정상 응답으로 간주** |

> ⚠️ **핵심 포인트:** 모델이 텍스트 없이 도구만 호출한 것은 정상 동작이므로,  
> `_has_native` 플래그로 이를 구분합니다.

---

### 3.2 2단계 — 컨텍스트 압축 복구 (Context Compression Recovery)

> **위치:** `react_loop.py` 611~621라인

```python
if not _reasoning_recovery_done and deps.compress_fn:
    _reasoning_recovery_done = True   # 1회만 실행
    _llm_retry = 0                    # 재시도 카운터 초기화
    messages = deps.compress_fn(messages, force=True, ...)
    continue
```

| 항목 | 내용 |
|------|------|
| **동작** | 오래된 대화 기록을 요약/압축하여 출력 토큰 확보 후 재시도 |
| **재시도 카운터** | **0으로 초기화** → 1단계 재시도 기회를 다시 얻음 |
| **실행 횟수** | 턴당 **1회만** 실행 (`_reasoning_recovery_done` 플래그로 제어) |

---

### 3.3 3단계 — 추론 전용 응답 감지 (Reasoning-Only Detection)

> **위치:** `react_loop.py` 632~673라인

`<think reasoning>` 태그 안에 **추론만** 적고 실제 응답을 안 한 경우를 감지합니다.

```python
# <think/> 태그 제거 후에도 내용이 비어있으면
if not collected_content.strip() and not _has_native:
    # 넛지(Nudge) 메시지 주입
    messages.append({
        "role": "user",
        "content": "[System] You produced only reasoning with no tool call or answer. "
                   "Please call the appropriate tool now, or provide your final answer directly."
    })
    continue
```

| 항목 | 내용 |
|------|------|
| **동작** | 모델이 추론만 하고 행동하지 않는 현상 방지 |
| **해결책** | "넛지(Nudge)" 메시지를 주입하여 도구 호출 또는 답변 유도 |
| **추가 복구** | 넛지 재시도도 실패하면 2단계(컨텍스트 압축) 재실행 |

---

### 3.4 최종 — 안전한 복귀 (Graceful Give Up)

> **위치:** `react_loop.py` 622~624, 671~673라인

```python
print(f"  LLM failed after retries. Returning to input.")
break   # 에러 없이 사용자 입력 프롬프트로 복귀
```

- 모든 단계가 실패하면 **크래시 없이** 사용자 입력 프롬프트로 안전하게 복귀합니다.

---

## 4. 관련 설정값

> **위치:** `src/config.py`

| 설정 | 기본값 | 환경변수 | 설명 |
|------|--------|----------|------|
| `LLM_RETRY_COUNT` | `1` | `LLM_RETRY_COUNT` | 빈 응답 시 최대 재시도 횟수 |
| `MAX_RECOVERY_ATTEMPTS` | `3` | `MAX_RECOVERY_ATTEMPTS` | 세션 롤백 복구 최대 횟수 |
| `ENABLE_NATIVE_TOOL_CALLS` | 설정에 따라 | — | 네이티브 툴 콜링 사용 여부 |
| `ENABLE_SESSION_RECOVERY` | 설정에 따라 | — | 반복 에러 시 세션 롤백 활성화 |

### 설정 변경 예시

```bash
# .env 파일
LLM_RETRY_COUNT=3
MAX_RECOVERY_ATTEMPTS=5
```

---

## 5. 핵심 요약

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   common_ai_agent가 빈 응답을 잘 처리하는 이유                     │
│                                                                  │
│   ① 단순 재시도만 하지 않고 원인을 진단함                           │
│      - 추론 토큰 초과?                                            │
│      - API 일시 오류?                                             │
│      - 컨텍스트 포화?                                              │
│                                                                  │
│   ② 원인별 맞춤 복구 전략 적용                                     │
│      - 재시도 → 컨텍스트 압축 → 넛지 주입 → 안전 복귀                │
│                                                                  │
│   ③ Reasoning 모델(R1, Claude thinking) 특화 처리                  │
│      - <think/> 태그 제거 후 감지                                  │
│      - "추론만 하고 응답 안 함" 문제를 넛지로 해결                    │
│                                                                  │
│   ④ 크래시 없이 안전한 복귀 보장                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```
