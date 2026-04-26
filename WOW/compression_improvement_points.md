
# Compression System — 개선 포인트 분석

## 🔴 Critical (기능 결함 / 데이터 손실 위험)

### 1. _compress_single의 과도한 truncation (lines 231-244)

```python
content = str(m.get("content") or "")[:1000]  # 메시지별 1000자
content = str(m.get("content", ""))[:500]      # tool 결과는 500자
```

**문제:** 
- tool 결과(코드, 파일 내용, 에러 메시지)가 500자로 잘림
- 중요한 코드 스니펫, 에러 메시지后半이 손실
- 10K+ chars 파일 내용이 500자로 축소되면 핵심 정보 사라짐

**개선안:**
```python
# 내용 기반 적응형 truncation
def _smart_truncate(content, max_chars=2000, priority_patterns=None):
    """코드/에러는 더 길게, 인사말은 더 짧게"""
    if priority_patterns:
        for pat in priority_patterns:
            if pat in content:
                return content[:max_chars * 2]  # 중요 내용은 2배
    return content[:max_chars]
```

### 2. Emergency pruning이 무식한 tail-cut (lines 770-780)

```python
pruned = prunable[-emergency_keep:]  # 그냥 뒤에서 N개 자르기
```

**문제:**
- 중요한 최근 메시지가 잘릴 수 있음
- 메시지 중요도 고려 없이 순서만으로 결정
- assistant 메시지가 user 메시지를 필요로 하는 경우 pair가 깨짐

**개선안:**
```python
# Role-pair 무결성 보장 + 중요도 기반 pruning
def _emergency_prune(messages, max_tokens, limit):
    # 1. assistant-tool 쌍 유지
    # 2. user 메시지는 반드시 보존
    # 3. 중요도 점수 기반 선택
    ...
```

### 3. 재압축 시 품질 열화 (Generation Loss)

```
원본 → 1차 압축 → 2차 압축 → ... → 내용 누적 손실
```

**문제:**
- 이미 압축된 summary가 다시 압축 대상이 됨
- 복사한 복사본을 또 복사하는 것과 같음
- 매 압축마다 정보 손실 누적

**개선안:**
```python
# 1차 압축 결과에 [FROZEN] 태그 → 재압축 대상에서 제외
# 또는: 압축 결과를 별도 보존 + 새 메시지만 추가 압축
if any("[Previous Conversation Summary" in str(m.get("content", "")) 
       for m in old_msgs):
    # 기존 summary는 보존하고 새 메시지만 추가 요약
    ...
```

### 4. _compress_chunked 에러 처리 (line 375)

```python
except Exception as e:
    print(f" Failed: {e}")
    if chunk:
        compressed.append(chunk[0])  # ← 첫 메시지만 저장, 나머지 전부 손실!
```

**문제:** chunk 내의 다른 모든 메시지가 조용히 사라짐

**개선안:**
```python
except Exception as e:
    print(f" Failed: {e}")
    # 전체 chunk를 하나의 system message로 보존
    combined = "\\n".join(f"{m.get('role')}: {str(m.get('content',''))[:300]}" for m in chunk)
    compressed.append({"role": "system", "content": f"[Chunk failed]: {combined}"})
```

---

## 🟡 Significant (성능 / 품질 저하)

### 5. 평탄화된 텍스트로 LLM에 전송 (lines 231-244)

```python
conversation_text += f"{role}: {content}\\n"
```

**문제:**
- 구조화된 메시지가 단순 텍스트로 변환
- `tool_calls`의 function name, arguments 등 메타데이터 손실
- `tool_call_id` 등 참조 정보 사라짐
- LLM이 도구 호출의 맥락을 잃음

**개선안:**
```python
# 구조 보존 포맷
if role == "assistant" and m.get("tool_calls"):
    for tc in m["tool_calls"]:
        fn = tc.get("function", {})
        conversation_text += f"assistant → called {fn.get('name')}({fn.get('arguments', '')[:200]})\\n"
elif role == "tool":
    conversation_text += f"tool({m.get('name', '?')}): {content}\\n"
```

### 6. System message consolidation이 구조 파괴 (lines 742-764)

```python
_merged = "\\n\\n".join(p for p in _sys_parts if p.strip())
new_history = [{"role": "system", "content": _merged}] + _non_sys
```

**문제:**
- 원래 system prompt, summary, todo, awaiting이 구분 없이 하나로 합쳐짐
- LLM이 어디가 원래 지시사항이고 어디가 요약인지 구분 불가
- 요약 내용이 원래 system prompt의 지시사항처럼 보일 수 있음

**개선안:**
```python
# 섹션 헤더로 구분
_merged_parts = []
if system_prompt_text:
    _merged_parts.append("=== SYSTEM INSTRUCTIONS ===\\n" + system_prompt_text)
if summary_text:
    _merged_parts.append("=== CONVERSATION SUMMARY ===\\n" + summary_text)
if todo_text:
    _merged_parts.append("=== TASK STATUS ===\\n" + todo_text)
_merged = "\\n\\n".join(_merged_parts)
```

### 7. Token 추정이 부정확 (`_default_estimate`, line 153)

```python
return len(text) // 4  # 항상 4문자 = 1토큰
```

**문제:**
- 코드: 2-3字符 = 1토큰 (과소평가)
- 한국어: 1-2字符 = 1토큰 (과소평가)
- 공백/반복: 6+字符 = 1토큰 (과대평가)
- 실제 토큰과 30-50% 오차 가능

**개선안:**
```python
def _estimate_tokens(text, lang="mixed"):
    # tiktoken 가용 시 사용
    try:
        import tiktoken
        enc = tiktoken.encoding_for_model("gpt-4")
        return len(enc.encode(text))
    except ImportError:
        # 내용 기반 추정
        code_ratio = sum(1 for c in text if c in '{}[]()=;<>') / max(len(text), 1)
        if code_ratio > 0.1:  # 코드가 많으면
            return int(len(text) / 3)  # 더 많은 토큰
        return len(text) // 4
```

### 8. Chunked compression의 파편화 (lines 307-375)

```python
for i in range(0, len(messages), chunk_size):
    chunk = messages[i : i + chunk_size]
    # 각 chunk 독립 요약 → chunk 간 연결성 손실
```

**문제:**
- 각 chunk가 독립적으로 요약됨
- chunk 경계에서 대화 맥락이 단절
- chunk 1의 결정이 chunk 2의 행동을 설명하는 경우 연결 끊김

**개선안:**
```python
# Overlap-based chunking
# 각 chunk의 마지막 2-3개 메시지를 다음 chunk의 앞에 포함
overlap = min(3, chunk_size // 3)
for i in range(0, len(messages), chunk_size - overlap):
    chunk = messages[max(0, i): i + chunk_size]
    ...
```

### 9. Pre-analysis가 추가 LLM 호출 (lines 390-433)

**문제:**
- 압축 전에 분석용 LLM 호출 1회 + 압축용 LLM 호출 1회 = 2배 비용
- 분석 결과가 summary prompt에 append → prompt 길이 증가
- 실제 효과 검증 안 됨

**개선안:**
```python
# 단일 호출에 분석 + 요약 통합
SINGLE_PASS_PROMPT = """
Step 1: Identify critical context (5-10 bullet points)
Step 2: Summarize the conversation preserving ALL critical items

## Critical Context
[your analysis here]

## Summary
[your summary here]
"""
# 응답 파싱으로 분리
```

---

## 🟢 Enhancement (개발자 경험 / 유지보수)

### 10. !important 감지가 문자열 기반 (lines 534-549)

```python
if "!important" in content.lower():
```

**문제:**
- 사용자가 `!important`를 정확히 쳐야 함
- 프로그래밍 방식으로 메시지 중요도 표시 불가
- CSS `!important`와 충돌 가능

**개선안:**
```python
# 메타데이터 기반 중요도
if msg.get("metadata", {}).get("pinned") or msg.get("pinned"):
    important_msgs.append(msg)
elif "!important" in content.lower():  # backward compat
    important_msgs.append(msg)
```

### 11. 압축 품질 메트릭 없음

**문제:**
- 압축 후 정보 보존율을 알 수 없음
- 어떤 정보가 손실되었는지 추적 불가
- 압축 prompt 개선의 피드백 루프 없음

**개선안:**
```python
# 압축 전후 키워드/엔티티 비교
def _measure_compression_quality(old_msgs, summary, original_messages):
    # 1. 파일 경로 추출
    old_paths = set(re.findall(r'[\w/]+\.\w+', all_old_text))
    new_paths = set(re.findall(r'[\w/]+\.\w+', summary))
    path_preservation = len(old_paths & new_paths) / max(len(old_paths), 1)
    
    # 2. 함수/클래스명 추출
    ...
    
    return {"path_preservation": path_preservation, ...}
```

### 12. Module-level 초기화 (line 99)

```python
STRUCTURED_SUMMARY_PROMPT = _load_default_compression_prompt()
```

**문제:**
- import 시점에 1회 로드 → workspace 변경 시 reload 필요
- `builtins._WORKSPACE_HOOK_MESSAGES`에 의존 (전역 상태 오염)
- 테스트에서 매번 reload 필요

**개선안:**
```python
# Lazy loading
def _get_compression_prompt():
    """매 호출 시 workspace context에서 로드"""
    msgs = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", {})
    if msgs.get("compression_system"):
        return msgs["compression_system"]
    return _STRUCTURED_SUMMARY_PROMPT_DEFAULT

# _compress_single에서 호출
summary_prompt = instruction or _get_compression_prompt()
```

### 13. _detect_awaiting_user 휴리스틱 (lines 178-207)

```python
_AWAIT_PATTERNS = (
    "please provide",
    "please specify",
    ...
)
```

**문제:**
- 영어 패턴만 인식
- 한국어, 중국어 등 다국어 질문 감지 불가
- "?" 포함 여부만으로 True → false positive 가능

**개선안:**
```python
_AWAIT_PATTERNS = (
    # English
    "please provide", "could you", "i need you to", ...
    # Korean
    "알려주세요", "확인해주세요", "제공해주세요", ...
    # Chinese
    "请提供", "请确认", ...
)
# 또는 LLM 기반 분류 (비용 증가하지만 정확)
```

### 14. compress_history 함수가 너무 김 (897 lines 중 480+ lines)

**문제:**
- 단일 함수가 480줄 — 이해/테스트/수정 어려움
- 책임이 너무 많음: 임계값 체크, 분리, 보호, 압축, 병합, 정리, hook, display

**개선안:**
```python
# 단계별 분리
class CompressionPipeline:
    def run(self, messages, **kwargs):
        messages = self.check_thresholds(messages)
        system, important, regular = self.separate(messages)
        old, recent = self.split(regular)
        compressed = self.compress(old)
        merged = self.consolidate(system, compressed, recent)
        return self.finalize(merged)
```

### 15. 압축 결과에 대한 사용자 피드백 없음

**문제:**
- 사용자가 "뭐가 날아갔는지" 알 수 없음
- 잘못된 압축에 대한 사용자 정정 불가

**개선안:**
```
[Compress] Summary generated. 
⚠️ The following may have been lost:
  - File: src/cache.py (mentioned in turns 3-5)
  - Decision: "Use Redis for caching" (turn 7)
Review? [y/N]
```

---

## 📊 우선순위 매트릭스

| # | 개선점 | 영향 | 난이도 | 우선순위 |
|---|--------|------|--------|----------|
| 1 | Truncation 개선 | 🔴 높음 | 낮음 | **P0** |
| 3 | 재압축 열화 방지 | 🔴 높음 | 중간 | **P0** |
| 4 | Chunked 에러 처리 | 🔴 높음 | 낮음 | **P0** |
| 2 | Emergency pruning 개선 | 🔴 높음 | 중간 | **P1** |
| 6 | System message 구조 보존 | 🟡 중간 | 낮음 | **P1** |
| 5 | 메시지 구조 보존 | 🟡 중간 | 낮음 | **P1** |
| 9 | Pre-analysis 통합 | 🟡 중간 | 낮음 | **P1** |
| 14 | 함수 분리 리팩토링 | 🟡 중간 | 높음 | **P2** |
| 7 | Token 추정 개선 | 🟡 중간 | 중간 | **P2** |
| 8 | Overlap chunking | 🟡 중간 | 중간 | **P2** |
| 11 | 품질 메트릭 | 🟢 낮음 | 중간 | **P3** |
| 10 | 중요도 메타데이터 | 🟢 낮음 | 낮음 | **P3** |
| 12 | Lazy loading | 🟢 낮음 | 낮음 | **P3** |
| 13 | 다국어 감지 | 🟢 낮음 | 낮음 | **P3** |
| 15 | 사용자 피드백 | 🟢 낮음 | 높음 | **P3** |
