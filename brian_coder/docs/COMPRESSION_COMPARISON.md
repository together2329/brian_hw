# Compression 비교: Brian Coder vs Strix

## 📊 전체 비교표

| 항목 | **Brian Coder** | **Strix** |
|------|-----------------|-----------|
| **Token Counting** | ✅ API 호출 (실제 값) | ✅ litellm.token_counter() |
| **Threshold** | 80% (설정 가능) | 90% (고정) |
| **Max Tokens** | 65K (설정 가능) | 100K (고정) |
| **보존 메시지** | 최근 4개 | 최근 15개 |
| **압축 방식** | 전체 요약 (1번) | 청크 요약 (10개씩) |
| **이미지 처리** | ❌ 없음 | ✅ 최대 3개 보존 |
| **System 메시지** | 1개 보존 | 모두 보존 |
| **설정 가능성** | ✅ 높음 (.env) | ⚠️ 코드 수정 필요 |

---

## 🔍 상세 비교

### 1. Token Counting (토큰 계산)

#### Brian Coder
```python
def get_token_count_from_api(messages):
    """API에 max_tokens=1로 요청해서 실제 input token 받음"""
    data = {
        "model": config.MODEL_NAME,
        "messages": messages,
        "max_tokens": 1,
        "stream": False
    }
    # usage.prompt_tokens 또는 usage.input_tokens 받음
```

**장점:**
- ✅ **100% 정확**: LLM tokenizer가 직접 계산
- ✅ **모든 모델 지원**: OpenAI, Anthropic, OpenRouter 등
- ✅ **저렴한 비용**: output 1 token만 사용

**단점:**
- ❌ **API 호출 필요**: 네트워크 지연 발생

#### Strix
```python
def _count_tokens(text: str, model: str) -> int:
    try:
        count = litellm.token_counter(model=model, text=text)
        return int(count)
    except Exception:
        return len(text) // 4  # Fallback estimation
```

**장점:**
- ✅ **빠름**: 로컬 계산, API 호출 없음
- ✅ **라이브러리 사용**: litellm의 tokenizer

**단점:**
- ❌ **외부 의존성**: litellm 필요
- ⚠️ **모델별 차이**: 모델마다 tokenizer 다를 수 있음

**결론:** Brian은 정확성 우선, Strix는 속도 우선

---

### 2. Compression Strategy (압축 전략)

#### Brian Coder
```python
# Strategy: 전체를 한 번에 요약
system_msg = messages[0]
recent_msgs = messages[-4:]
to_summarize = messages[1:-4]

# LLM에게 전체 중간 부분 요약 요청 (1번)
summary = chat_completion_stream(summary_request)

new_history = [system_msg, summary_msg] + recent_msgs
```

**구조:**
```
[System] [Summary of messages 1-N] [Recent 4 messages]
```

**장점:**
- ✅ **간단함**: 1번 요약으로 끝
- ✅ **일관성**: 전체 흐름을 하나로 요약

**단점:**
- ❌ **큰 context**: 요약할 내용이 많으면 느림
- ❌ **한 번에 압축**: 점진적 압축 불가

#### Strix
```python
# Strategy: 10개씩 청크로 나눠서 요약
system_msgs = [모든 system 메시지]
recent_msgs = regular_msgs[-15:]
old_msgs = regular_msgs[:-15]

compressed = []
chunk_size = 10
for i in range(0, len(old_msgs), chunk_size):
    chunk = old_msgs[i:i + chunk_size]
    summary = _summarize_messages(chunk, model_name)
    compressed.append(summary)

return system_msgs + compressed + recent_msgs
```

**구조:**
```
[System 1] [System 2] ... [Summary 1-10] [Summary 11-20] ... [Recent 15]
```

**장점:**
- ✅ **점진적 압축**: 청크별로 나눠서 처리
- ✅ **병렬 가능**: 각 청크를 독립적으로 요약 가능 (구현은 안 됨)
- ✅ **많은 메시지 보존**: 최근 15개 유지

**단점:**
- ❌ **복잡함**: 여러 요약 메시지 생성
- ❌ **비용**: 여러 번 LLM 호출

**결론:** Brian은 단순하고 효율적, Strix는 복잡하지만 세밀함

---

### 3. Threshold & Limits (임계값과 한계)

#### Brian Coder
```python
MAX_CONTEXT_CHARS = 262144  # 65K tokens (설정 가능)
COMPRESSION_THRESHOLD = 0.8  # 80% (설정 가능)

threshold = 65536 * 0.8 = 52,428 tokens
```

**장점:**
- ✅ **설정 가능**: .env에서 자유롭게 조정
- ✅ **보수적 threshold**: 80%에서 미리 압축

**단점:**
- ⚠️ **기본값 작음**: 65K (Claude 200K 미사용)

#### Strix
```python
MAX_TOTAL_TOKENS = 100_000  # 고정
MIN_RECENT_MESSAGES = 15     # 고정

threshold = 100000 * 0.9 = 90,000 tokens
```

**장점:**
- ✅ **큰 context**: 100K까지 허용
- ✅ **많은 보존**: 최근 15개 메시지

**단점:**
- ❌ **고정값**: 코드 수정 필요
- ⚠️ **늦은 압축**: 90%까지 기다림

**결론:** Brian은 유연함, Strix는 큰 context 활용

---

### 4. Image Handling (이미지 처리)

#### Brian Coder
```python
# 이미지 처리 없음
```

**현재 상태:**
- ❌ 이미지 메시지 미처리
- ❌ 이미지도 text처럼 계산됨

#### Strix
```python
def _handle_images(messages, max_images=3):
    """최근 3개 이미지만 보존, 나머지는 텍스트로 교체"""
    image_count = 0
    for msg in reversed(messages):
        if image_url in msg:
            if image_count >= max_images:
                # 이미지를 텍스트로 교체
                item["type"] = "text"
                item["text"] = "[Previously attached image removed]"
            else:
                image_count += 1
```

**장점:**
- ✅ **이미지 관리**: 오래된 이미지 자동 제거
- ✅ **context 절약**: 이미지 token 큼

**결론:** Strix가 이미지 처리에서 우수

---

### 5. Summary Prompt (요약 프롬프트)

#### Brian Coder
```python
summary_prompt = """
Summarize the following conversation history concisely.
Focus on completed tasks, key decisions, and current state.
Ignore minor chatter.
"""
```

**특징:**
- ✅ **범용적**: 일반 대화용
- ✅ **간결함**: 작업 중심

#### Strix
```python
SUMMARY_PROMPT_TEMPLATE = """
You are an agent performing context condensation for a security agent.

CRITICAL ELEMENTS TO PRESERVE:
- Discovered vulnerabilities and potential attack vectors
- Scan results and tool outputs
- Access credentials, tokens, or authentication details found
- System architecture insights and potential weak points
- Progress made in the assessment
- Failed attempts and dead ends
- Any decisions made about the testing approach

COMPRESSION GUIDELINES:
- Preserve exact technical details (URLs, paths, parameters, payloads)
- Summarize verbose tool outputs while keeping critical findings
- Maintain version numbers, specific technologies identified
- Keep exact error messages that might indicate vulnerabilities
- Compress repetitive or similar findings into consolidated form
"""
```

**특징:**
- ✅ **특화됨**: Security assessment 전용
- ✅ **상세함**: 보존할 항목 명시
- ✅ **기술적**: 정확한 정보 보존 강조

**결론:** Strix는 security에 특화, Brian은 범용

---

### 6. System Messages (시스템 메시지)

#### Brian Coder
```python
system_msg = messages[0]  # 첫 번째만 보존
```

**특징:**
- ⚠️ **1개만**: 여러 system 메시지 중 첫 번째만

#### Strix
```python
system_msgs = []
for msg in messages:
    if msg.get("role") == "system":
        system_msgs.append(msg)

# 모든 system 메시지 보존
return system_msgs + compressed + recent_msgs
```

**특징:**
- ✅ **모두 보존**: 여러 system 메시지 처리
- ✅ **유연함**: 동적 system 메시지 지원

**결론:** Strix가 system 메시지 처리에서 우수

---

## 📈 성능 비교

### Token Counting 속도

| 방법 | Brian Coder | Strix |
|------|-------------|-------|
| 10K tokens | ~100-200ms (API) | ~5-10ms (local) |
| 50K tokens | ~200-400ms (API) | ~20-50ms (local) |

### Compression 속도

| 메시지 수 | Brian Coder | Strix |
|----------|-------------|-------|
| 50 messages | 1번 요약 (~2s) | 5번 요약 (~10s) |
| 100 messages | 1번 요약 (~3s) | 10번 요약 (~20s) |

### 비용 비교

**Brian Coder:**
```
Token count check: 7,061 input + 1 output = ~$0.0001
Summary: 8,000 input + 500 output = ~$0.005
Total per compression: ~$0.005
```

**Strix:**
```
Token count: Free (local)
Summary (10 chunks): 10 × (800 input + 200 output) = ~$0.015
Total per compression: ~$0.015
```

**결론:** Brian이 3배 저렴

---

## 🎯 장단점 요약

### Brian Coder 장점
1. ✅ **100% 정확한 token counting** (API 실제 값)
2. ✅ **저렴한 비용** (1번 요약)
3. ✅ **간단한 구조** (이해하기 쉬움)
4. ✅ **설정 가능** (.env 파일)
5. ✅ **Zero dependency** (stdlib만 사용)

### Brian Coder 단점
1. ❌ **이미지 미처리**
2. ❌ **System 메시지 1개만**
3. ❌ **API 호출 필요** (token counting)
4. ❌ **범용 프롬프트** (특화되지 않음)

### Strix 장점
1. ✅ **빠른 token counting** (로컬)
2. ✅ **이미지 처리**
3. ✅ **System 메시지 모두 보존**
4. ✅ **Security 특화 프롬프트**
5. ✅ **점진적 압축** (청크)
6. ✅ **많은 메시지 보존** (15개)

### Strix 단점
1. ❌ **외부 의존성** (litellm)
2. ❌ **비용 높음** (여러 번 요약)
3. ❌ **복잡한 구조**
4. ❌ **설정 불가** (코드 수정 필요)

---

## 🚀 개선 제안

### Brian Coder에 추가하면 좋을 기능

1. **이미지 처리 (from Strix)**
```python
def _handle_images(messages, max_images=3):
    # Strix 방식 그대로 적용
```

2. **System 메시지 모두 보존 (from Strix)**
```python
system_msgs = [msg for msg in messages if msg["role"] == "system"]
regular_msgs = [msg for msg in messages if msg["role"] != "system"]
```

3. **선택적 청크 압축**
```python
# .env에서 설정
COMPRESSION_MODE=single  # 또는 chunked
CHUNK_SIZE=10
```

4. **더 큰 기본 context**
```python
MAX_CONTEXT_CHARS=800000  # 200K tokens (Claude 최대 활용)
```

### Strix에서 배울 수 있는 점

1. ✅ **이미지 관리**: 매우 실용적
2. ✅ **도메인 특화 프롬프트**: Security agent에 최적화
3. ✅ **점진적 압축**: 대량 메시지 처리에 유리

---

## 🏆 결론

### 사용 시나리오별 추천

**Brian Coder가 더 좋은 경우:**
- ✅ 정확한 token counting 필요
- ✅ 비용 절감 중요
- ✅ 간단한 구조 선호
- ✅ 범용 코딩 assistant

**Strix가 더 좋은 경우:**
- ✅ Security assessment 작업
- ✅ 이미지 포함 대화
- ✅ 매우 긴 대화 (100K+ tokens)
- ✅ 빠른 token counting 필요

### 종합 평가

| 항목 | Winner |
|------|--------|
| Token Counting 정확도 | **Brian Coder** 🏆 |
| Token Counting 속도 | **Strix** 🏆 |
| 비용 효율성 | **Brian Coder** 🏆 |
| 이미지 처리 | **Strix** 🏆 |
| 설정 유연성 | **Brian Coder** 🏆 |
| 도메인 특화 | **Strix** 🏆 |
| 간결성 | **Brian Coder** 🏆 |
| 기능 완성도 | **Strix** 🏆 |

**결론:** 각자 장단점이 명확. Brian은 정확하고 저렴하고 간단. Strix는 기능이 풍부하고 특화됨.

---

## 💡 Best of Both Worlds

이상적인 compression은:

```python
class HybridCompressor:
    """Brian의 정확성 + Strix의 기능"""

    def compress_history(self, messages):
        # 1. Strix: 이미지 먼저 처리
        _handle_images(messages, max_images=3)

        # 2. Strix: System 메시지 모두 분리
        system_msgs = [m for m in messages if m["role"] == "system"]
        regular_msgs = [m for m in messages if m["role"] != "system"]

        # 3. Brian: API로 정확한 token count
        actual_tokens = get_token_count_from_api(messages)

        # 4. 임계값 체크
        if actual_tokens < threshold:
            return messages

        # 5. Brian: 단순 1번 요약 (비용 효율)
        recent = regular_msgs[-15:]  # Strix의 15개 보존
        to_summarize = regular_msgs[:-15]

        summary = summarize_with_llm(to_summarize)

        # 6. Strix 구조로 반환
        return system_msgs + [summary] + recent
```

이렇게 하면 **최고의 compression**! 🚀
