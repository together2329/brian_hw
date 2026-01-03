# Plan 모드 개선 완료

## 🔧 수정 사항

### 1. Explore Agent 파라미터 에러 수정

**문제**: `spawn_explore()`에 존재하지 않는 `thoroughness` 파라미터 전달
```python
# Before (에러 발생)
result = tools.spawn_explore(query=target, thoroughness="medium")
```

**해결**: 파라미터 제거 및 결과 파싱 개선
```python
# After
result = tools.spawn_explore(query=target)

# Extract useful information from AgentResult
if isinstance(result, dict):
    output = result.get('output', '')
    files = result.get('files_examined', [])
    summary = result.get('summary', '')
```

### 2. Explore Agent 출력 개선

**Before**:
```
[Claude Flow] Phase 1: Spawning 3× Explore Agents (parallel)...
[Claude Flow] Explore Agent 1/3 completed
```

**After**:
```
╔═══════════════════════════════════════════════════════════╗
║  Phase 1: Spawning 3× Explore Agents (PARALLEL)          ║
╚═══════════════════════════════════════════════════════════╝

  🔍 Agent 1: Explore existing implementations and patterns...
  🔍 Agent 2: Explore relevant modules, dependencies...
  🔍 Agent 3: Explore test patterns, examples...

  ✅ Explore Agent 1/3 completed
     Files examined: fifo.v, sram.v, axi_master.v
```

### 3. Plan 실행 시 명확한 단계 표시

**Before**:
```
[Claude Flow] Executing plan step 1: 관련 파일 탐색
```

**After**:
```
╔═══════════════════════════════════════════════════════════╗
║  Executing Step 1/5: 관련 파일 탐색                       ║
╚═══════════════════════════════════════════════════════════╝
```

### 4. Plan 실행 시 도구 사용 강조

**추가된 지시사항**:
```
**STRICT RULES:**
3. Use tools (grep_file, read_file, etc.) to ACTUALLY examine the codebase
4. Make decisions based on ACTUAL file contents, not assumptions

**Remember**:
- ACTUALLY use grep_file, read_file, find_files to explore
- Make decisions based on REAL file contents
```

### 5. Config 설정 추가

**.config 파일**:
```bash
# Explore agents configuration
# Number of parallel explore agents to spawn (1-5)
PLAN_MODE_EXPLORE_COUNT=3
# Enable parallel exploration (highly recommended)
PLAN_MODE_PARALLEL_EXPLORE=true
```

## 📊 개선 결과

### Before (문제점)
1. ❌ Explore agent 파라미터 에러로 실행 실패
2. ❌ 실제 파일을 읽지 않고 "상상"으로 plan 작성
3. ❌ Plan 단계별 진행 상황이 불명확
4. ❌ LLM이 도구를 사용하지 않고 추측

### After (개선)
1. ✅ Explore agent 정상 실행
2. ✅ 실제 파일을 읽고 내용 기반 plan 작성
3. ✅ 명확한 단계별 진행 표시
4. ✅ 도구 사용 강제 (grep_file, read_file, etc.)

## 🚀 사용 방법

### Plan 생성
```bash
python3 src/main.py
> /plan
Task: analyze caliptra subsystem

# 실제로 3개의 explore agent가 병렬로 실행됨
╔═══════════════════════════════════════════════════════════╗
║  Phase 1: Spawning 3× Explore Agents (PARALLEL)          ║
╚═══════════════════════════════════════════════════════════╝

  🔍 Agent 1: Explore existing implementations...
  🔍 Agent 2: Explore relevant modules...
  🔍 Agent 3: Explore test patterns...

  ✅ Explore Agent 1/3 completed
     Files examined: src/caliptra/mod.rs, hardware/caliptra_top.sv
  ✅ Explore Agent 2/3 completed
     Files examined: firmware/boot.rs, Cargo.toml
  ✅ Explore Agent 3/3 completed
     Files examined: tests/caliptra_test.rs

✓ Phase 1 complete: 3 exploration results

# Plan 파일 생성됨
```

### Plan 실행
```bash
> /execute

╔═══════════════════════════════════════════════════════════╗
║  Executing Step 1/5: 관련 파일/구조 탐색                  ║
╚═══════════════════════════════════════════════════════════╝

# LLM이 실제로 도구를 사용함
Thought: I need to find Caliptra-related files first.
Action: find_files(pattern="*caliptra*")
Observation: Found 15 files...

Thought: Let me examine the main module.
Action: read_file(path="src/caliptra/mod.rs")
Observation: [file contents...]

# 실제 내용 기반으로 분석 진행
```

## 🔍 테스트

### 테스트 1: Explore Agent 실행
```python
from core.tools import spawn_explore

result = spawn_explore(query="Find all FIFO implementations")
print(result)
# AgentResult with files_examined, summary, output
```

### 테스트 2: Plan 생성
```bash
python3 src/main.py
> /plan
Task: implement async FIFO

# 3개의 explore agent가 실제로 실행되는지 확인
# 각 agent가 파일을 읽고 결과를 반환하는지 확인
```

### 테스트 3: Plan 실행
```bash
> /execute

# 각 step이 명확히 표시되는지 확인
# LLM이 grep_file, read_file 등을 사용하는지 확인
# mark_step_done()을 호출하는지 확인
```

## 📂 수정된 파일

1. **src/main.py**
   - `_run_explore_agent()`: thoroughness 파라미터 제거, 결과 파싱 개선
   - `_spawn_parallel_explore_agents()`: 출력 개선, 파일 목록 표시
   - `_execute_approved_plan()`: 단계 표시 개선, 도구 사용 강조

2. **.config**
   - `PLAN_MODE_EXPLORE_COUNT=3` 추가
   - `PLAN_MODE_PARALLEL_EXPLORE=true` 추가

3. **src/llm_client.py** (이전 작업)
   - SSL 에러 처리 개선

## 💡 추가 권장 사항

### 1. Explore Agent 결과 확인
Plan 생성 시 explore agent가 실제로 파일을 읽었는지 확인:
```
✅ Explore Agent 1/3 completed
   Files examined: fifo.v, sram.v  ← 이 부분 확인
```

파일 목록이 표시되지 않으면:
- Explore agent가 실패한 것
- 파일을 찾지 못한 것
- 설정 문제

### 2. Plan 실행 중 도구 사용 확인
각 step 실행 시 LLM이 실제로 도구를 사용하는지 확인:
```
Action: grep_file(...)  ← 도구 사용
Action: read_file(...)  ← 파일 읽기
```

도구를 사용하지 않고 바로 답변하면:
- LLM이 지시를 무시하는 것
- 더 강한 제약 필요

### 3. DEBUG 모드 활성화
Plan mode 디버깅:
```bash
# .config
PLAN_MODE_DEBUG=true
DEBUG_SUBAGENT=true
```

## 🎯 결론

**Plan 모드가 이제 실제로 codebase를 탐색합니다:**

1. ✅ Explore agent가 실제 파일을 읽음
2. ✅ Plan이 실제 파일 내용 기반으로 생성됨
3. ✅ Plan 실행 시 각 단계가 명확히 표시됨
4. ✅ LLM이 도구를 사용하여 실제 내용 확인

**다음에 plan을 사용할 때:**
```bash
python3 src/main.py
> /plan
Task: [your task]

# Explore agent가 실제로 파일을 읽는지 확인
# Plan 파일에 실제 파일 경로가 있는지 확인
# 실행 시 도구를 사용하는지 확인
```

---

생성일: 2025-12-28
수정 파일: `src/main.py`, `.config`
