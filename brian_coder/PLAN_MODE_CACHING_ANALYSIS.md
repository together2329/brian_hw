# Plan 모드 Prompt Caching 분석

## 현재 상태 분석

### ✅ Prompt Caching이 작동하는 부분

1. **Plan 실행 (각 step 내부)**
   ```python
   # _execute_approved_plan() → run_react_agent()
   messages = run_react_agent(messages, ...)

   # run_react_agent()에서 chat_completion_stream() 호출
   # → llm_client.py에서 cache breakpoints 적용
   ```

2. **일반 ReAct loop**
   - System message에 cache_control 적용
   - 메시지 히스토리의 긴 메시지에 breakpoints 설정

### ❌ Prompt Caching이 비효율적인 부분

1. **각 Step마다 새로운 System Message 추가**

```python
# main.py:1289
step_guidance = f"""⚠️ CRITICAL: FOCUS ONLY ON THIS STEP ⚠️
...
**Current Step**: {step_number} of {len(steps)}
**Task**: {step_text}
...
"""
messages.append({"role": "system", "content": step_guidance})
```

**문제점**:
- Step 1, Step 2, Step 3마다 **다른 system message**
- Cache miss 발생 (내용이 매번 다름)
- 비용 절감 효과 없음

2. **Explore Agent들의 독립적인 실행**

```python
# _spawn_parallel_explore_agents()
# 각 explore agent가 독립적으로 LLM 호출
for target in explore_targets:
    agent = ExploreAgent(...)
    result = agent.run(...)  # 각각 별도 LLM 호출
```

**문제점**:
- 3개의 explore agent = 3개의 독립적인 LLM 호출
- 서로 캐시를 공유하지 못함
- 같은 system message를 3번 전송

## 📊 현재 Caching 효율성

| 단계 | Cache Hit 가능성 | 이유 |
|------|------------------|------|
| Explore Agent 1 | ❌ 0% | 첫 호출, cache 생성 |
| Explore Agent 2 | ❌ 0% | 별도 프로세스, cache 공유 안 됨 |
| Explore Agent 3 | ❌ 0% | 별도 프로세스, cache 공유 안 됨 |
| Plan Agent | ❌ 0% | 독립 실행 |
| Plan Step 1 (iteration 1) | ✅ 0% | 첫 호출, cache 생성 |
| Plan Step 1 (iteration 2) | ✅ 90% | System message cache hit |
| Plan Step 1 (iteration 3) | ✅ 90% | System message + history cache hit |
| Plan Step 2 (iteration 1) | ❌ 0% | **새로운 system message** |
| Plan Step 2 (iteration 2) | ✅ 90% | System message cache hit |

**결과**:
- Step 내부: ✅ 효과적
- Step 간: ❌ 비효과적

## 💰 비용 분석

### 예시: 5-step plan 실행

**현재 (비효율적)**:
```
Step 1:
  - Iteration 1: 10,000 tokens (cache 생성)
  - Iteration 2-5: 각 1,000 tokens (cache hit 90%)

Step 2:
  - Iteration 1: 12,000 tokens (cache 생성 - 새 system msg)
  - Iteration 2-5: 각 1,200 tokens (cache hit 90%)

Step 3-5: 유사...

총 비용: 약 100,000 tokens (cache hit 부분적)
```

**개선 후 (효율적)**:
```
Step 1-5:
  - Step 1 Iteration 1: 10,000 tokens (cache 생성)
  - 이후 모든 iterations: cache hit 90%

총 비용: 약 40,000 tokens (60% 절감 가능)
```

## 🔧 개선 방안

### Option 1: Step Guidance를 User Message로 변경 ✅ (추천)

```python
# Before (비효율적)
messages.append({"role": "system", "content": step_guidance})

# After (효율적)
messages.append({"role": "user", "content": f"""
[SYSTEM INSTRUCTION FOR THIS STEP]

{step_guidance}
"""})
```

**장점**:
- System message 불변 → cache hit 극대화
- Step 간 cache 재사용 가능
- 구현 간단

**단점**:
- LLM이 user message를 덜 중요하게 볼 수 있음 (테스트 필요)

### Option 2: 공통 System Message + Step Context ✅ (추천)

```python
# 한 번만 추가 (plan 시작 시)
if not has_plan_system_message:
    messages.insert(0, {
        "role": "system",
        "content": """You are executing an approved plan.
Follow each step carefully and mark steps done when complete."""
    })

# 각 step마다 user message로 step 정보 전달
messages.append({
    "role": "user",
    "content": f"""Execute Step {step_number}/{len(steps)}: {step_text}

RULES:
- Work ONLY on this step
- Use tools to examine actual files
- Call mark_step_done({step_number}) when done
"""
})
```

**장점**:
- System message cache hit 100%
- Step 간 완전한 cache 재사용
- LLM이 지시를 잘 따름

### Option 3: Shared Context for Explore Agents 🔬 (실험적)

```python
# 모든 explore agent가 같은 base context 사용
base_messages = [
    {"role": "system", "content": "Standard explore agent instructions"}
]

# 각 agent는 추가 context만 전달
for target in explore_targets:
    agent_messages = base_messages.copy()
    agent_messages.append({"role": "user", "content": target})
    # LLM 호출 → base_messages는 cache됨
```

**장점**:
- Explore agent 간 cache 공유
- 비용 대폭 절감

**단점**:
- 병렬 실행 시 timing 문제 가능
- API provider의 cache 공유 정책에 의존

## 🎯 권장 사항

### 즉시 적용 (High Impact, Low Risk)

1. **Option 2 적용**: Step guidance를 user message로
   - 예상 비용 절감: 40-60%
   - 구현 난이도: 낮음
   - 리스크: 거의 없음

### 실험적 적용 (High Impact, Medium Risk)

2. **Explore Agent 최적화**
   - 공통 system message 사용
   - 예상 비용 절감: 20-30% (explore 단계)
   - 구현 난이도: 중간
   - 리스크: 병렬 실행 시 cache timing

## 📈 예상 개선 효과

**시나리오**: 5-step plan, 각 step 5 iterations

### Before (현재)
```
Explore (3 agents): 30,000 tokens (cache miss)
Plan: 10,000 tokens
Step 1: 10,000 (create) + 4,000 (90% cached) = 14,000
Step 2: 12,000 (create) + 4,800 (90% cached) = 16,800
Step 3: 12,000 (create) + 4,800 (90% cached) = 16,800
Step 4: 12,000 (create) + 4,800 (90% cached) = 16,800
Step 5: 12,000 (create) + 4,800 (90% cached) = 16,800

Total: ~121,200 tokens
```

### After (개선)
```
Explore (3 agents): 10,000 + 2,000 + 2,000 = 14,000 (shared cache)
Plan: 10,000 tokens
Step 1: 10,000 (create) + 4,000 (90% cached) = 14,000
Step 2: 1,000 (90% cached) + 4,000 (90% cached) = 5,000
Step 3: 1,000 (90% cached) + 4,000 (90% cached) = 5,000
Step 4: 1,000 (90% cached) + 4,000 (90% cached) = 5,000
Step 5: 1,000 (90% cached) + 4,000 (90% cached) = 5,000

Total: ~58,000 tokens (52% 절감!)
```

## 🔍 현재 설정 확인

```bash
# .config 파일
ENABLE_PROMPT_CACHING=true
CACHE_OPTIMIZATION_MODE=optimized

# 확인 방법
python3 -c "
import sys
sys.path.insert(0, 'src')
import config
print(f'Prompt Caching: {config.ENABLE_PROMPT_CACHING}')
print(f'Cache Mode: {config.CACHE_OPTIMIZATION_MODE}')
"
```

## 🚀 다음 단계

1. **Option 2 구현** (step guidance → user message)
2. **테스트 실행** (5-step plan)
3. **Cache hit rate 측정**
4. **비용 절감 확인**

---

**결론**: Plan 모드는 prompt caching을 사용하지만 **비효율적**입니다. Step guidance를 user message로 변경하면 **50%+ 비용 절감** 가능합니다.
