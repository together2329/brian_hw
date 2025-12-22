# Plan Mode E2E Test Guide

## 자동 테스트 결과 ✅

모든 자동화된 테스트가 성공적으로 통과했습니다:

```
✅ PASS  Slash Command Registry
✅ PASS  Plan File Creation
✅ PASS  Step Extraction
✅ PASS  Error Handling
✅ PASS  PlanModeResult
```

**자동 테스트 실행 방법:**
```bash
python3 test_plan_mode_e2e.py
```

---

## 수동 E2E 테스트

### Test 1: Basic Plan Mode Flow (기본 플로우)

**목적**: 전체 plan mode 플로우가 정상적으로 작동하는지 확인

**단계:**

1. **Brian Coder 실행**
   ```bash
   cd brian_coder
   python3 src/main.py
   ```

2. **Plan Mode 진입**
   ```
   You: /plan Create a simple 4-bit up counter with enable signal
   ```

3. **Plan Agent 응답 확인**
   - Plan Mode 진입 메시지 표시 확인
   - "Entering interactive planning mode" 메시지
   - "Commands: approve | cancel | show" 안내

4. **초안 Plan 생성 확인**
   - Plan Agent가 자동으로 plan 생성
   - Plan이 다음 섹션들을 포함하는지 확인:
     - `## Task Analysis`
     - `## Implementation Steps`
     - `## Success Criteria`

5. **Plan 승인**
   ```
   Plan feedback: approve
   ```

6. **Plan 저장 확인**
   - "Plan approved and saved: ~/.brian_coder/plans/..." 메시지 확인
   - 파일이 실제로 생성되었는지 확인:
     ```bash
     ls -la ~/.brian_coder/plans/
     ```

7. **Main Agent 실행 확인**
   - Main Agent가 plan을 읽고 실행 시작
   - TodoWrite로 steps가 tracking되는지 확인
   - 각 step이 순차적으로 실행되는지 확인

**예상 출력:**
```
============================================================
[Plan Mode] Entering interactive planning mode
Commands: approve | cancel | show
============================================================

[Plan Mode] Draft plan created:

## Task Analysis
Create a simple 4-bit up counter with enable signal...

## Implementation Steps
1. Create module skeleton...
2. Implement counter logic...
3. Add testbench...
4. Compile and simulate...

## Success Criteria
- Counter increments correctly
- Enable signal controls counting

Plan feedback (or approve/cancel/show): approve

[Plan Mode] Plan approved and saved: ~/.brian_coder/plans/create-a-simple-4-bit-up-counter-20251221-205123.md

[Main Agent] Executing plan...
[Step 1/4] ▶️  Create module skeleton...
```

---

### Test 2: Plan Refinement Flow (개선 플로우)

**목적**: Plan을 반복적으로 개선하는 기능 확인

**단계:**

1. **Plan Mode 진입**
   ```
   You: /plan Design async FIFO with Gray code pointers
   ```

2. **초안 Plan 검토**
   - 생성된 plan 확인

3. **첫 번째 개선 요청**
   ```
   Plan feedback: Step 2를 더 구체적으로 설명해주세요
   ```

4. **개선된 Plan 확인**
   - "Refining plan..." 메시지
   - "Updated plan:" 출력
   - Step 2가 더 상세해졌는지 확인

5. **두 번째 개선 요청**
   ```
   Plan feedback: Testbench section을 추가해주세요
   ```

6. **최종 Plan 확인**
   - Testbench section이 추가되었는지 확인

7. **Plan 승인**
   ```
   Plan feedback: approve
   ```

**예상 출력:**
```
[Plan Mode] Refining plan...

[Plan Mode] Updated plan:

## Implementation Steps
1. Create module skeleton
2. Implement Gray code pointers
   - Declare wr_ptr_gray, rd_ptr_gray (10-bit)
   - Binary to Gray conversion: gray = (bin >> 1) ^ bin
   - Synchronize across clock domains with double-flop
3. Add full/empty flags...
```

---

### Test 3: Plan Cancellation (취소 테스트)

**목적**: Plan mode를 중간에 취소할 수 있는지 확인

**단계:**

1. **Plan Mode 진입**
   ```
   You: /plan Create SPI master controller
   ```

2. **초안 Plan 검토**
   - Plan 확인

3. **Plan 취소**
   ```
   Plan feedback: cancel
   ```

4. **취소 메시지 확인**
   - "Plan mode cancelled" 메시지
   - Main chat loop로 복귀

**예상 출력:**
```
Plan feedback (or approve/cancel/show): cancel

[Plan Mode] Cancelled.

⚠️  Plan mode cancelled.

You:
```

---

### Test 4: Show Command (Plan 재확인)

**목적**: 현재 plan을 다시 볼 수 있는지 확인

**단계:**

1. **Plan Mode 진입 및 plan 생성**
   ```
   You: /plan Create I2C master
   ```

2. **여러 번 개선**
   ```
   Plan feedback: Add clock stretching support
   Plan feedback: Add multi-master support
   ```

3. **현재 Plan 재확인**
   ```
   Plan feedback: show
   ```

4. **Plan이 다시 출력되는지 확인**

**예상 출력:**
```
Plan feedback (or approve/cancel/show): show

## Task Analysis
Create I2C master with clock stretching and multi-master support...
```

---

### Test 5: spawn_explore 자동 호출 (고급)

**목적**: Plan Agent가 자동으로 spawn_explore를 호출하는지 확인

**단계:**

1. **디버그 모드 활성화**
   ```bash
   export PLAN_MODE_DEBUG=true
   python3 src/main.py
   ```

2. **Plan Mode 진입 (기존 코드 참조 필요한 작업)**
   ```
   You: /plan Create async FIFO similar to existing sync FIFO
   ```

3. **Debug 출력 확인**
   - `[Plan Mode][Debug] Tool call: spawn_explore(query=...)` 메시지 확인
   - Plan Agent가 자동으로 기존 코드를 탐색하는지 확인

**예상 Debug 출력:**
```
[Plan Mode][Debug] Tool call: spawn_explore(query=sync FIFO implementation)
[Plan Mode][Debug] Tool result (3245 chars): Found sync_fifo.v, async_fifo.v...

[Plan Mode] Draft plan created:

## Task Analysis
Based on existing sync FIFO implementation (sync_fifo.v), create async FIFO...
```

---

### Test 6: Error Handling (에러 처리)

**목적**: 다양한 에러 상황을 올바르게 처리하는지 확인

**테스트 케이스:**

#### 6-1: 빈 task
```
You: /plan
```
**예상 출력:**
```
❌ Error: /plan requires a task description
Usage: /plan <task>
```

#### 6-2: LLM 호출 실패 시 Retry
- LLM이 일시적으로 실패할 때 retry 로직이 작동하는지 확인
- "Retrying with simplified prompt..." 메시지 확인

#### 6-3: Plan 파일 저장 실패
- 권한 문제 등으로 파일 저장 실패 시
- "Failed to save plan" 경고
- In-memory plan으로 계속 진행

#### 6-4: Refine 실패
- Plan 개선 중 에러 발생 시
- "Keeping previous plan" 메시지
- 이전 plan 유지

---

## 성공 기준

### ✅ 필수 기준

1. **Plan Mode 진입**: `/plan` 명령어로 정상 진입
2. **Plan 생성**: Plan Agent가 구조화된 plan 생성
3. **Interactive Refinement**: 사용자 피드백으로 plan 개선 가능
4. **Plan 저장**: Plan이 파일로 저장됨 (~/.brian_coder/plans/)
5. **Main Agent 실행**: Plan이 Main Agent에 전달되어 실행됨
6. **TodoWrite 통합**: Steps가 todo list로 tracking됨
7. **Error Handling**: 에러 발생 시 적절한 메시지와 복구

### ✅ 선택 기준 (고급)

1. **spawn_explore 자동 호출**: Plan Agent가 필요 시 자동으로 코드 탐색
2. **Context 전달**: Main chat history가 Plan Agent에 전달됨
3. **Debug 모드**: PLAN_MODE_DEBUG=true 시 상세 로그 출력
4. **Stream 모드**: PLAN_MODE_STREAM=true 시 실시간 출력

---

## 문제 해결

### 문제 1: Plan Mode가 진입되지 않음

**증상:**
```
You: /plan Create counter
Unknown command: /plan
```

**해결:**
- slash_commands.py에서 /plan command가 등록되었는지 확인
- `get_registry()` 호출 시 _cmd_plan이 있는지 확인

### 문제 2: Plan Agent가 응답하지 않음

**증상:**
- Plan Mode는 진입했지만 plan이 생성되지 않음

**해결:**
- LLM 연결 확인 (BASE_URL, API_KEY)
- `config.MODEL_NAME` 설정 확인
- PLAN_MODE_DEBUG=true로 상세 로그 확인

### 문제 3: spawn_explore가 작동하지 않음

**증상:**
- Plan Agent가 "Tool not allowed" 에러 반환

**해결:**
- PlanAgent의 `ALLOWED_TOOLS = {"spawn_explore"}` 확인
- _execute_plan_tool 함수가 올바르게 전달되는지 확인

### 문제 4: Plan 파일이 생성되지 않음

**증상:**
- Plan 승인했지만 파일이 없음

**해결:**
- ~/.brian_coder/plans/ 디렉토리 권한 확인
- `config.PLAN_DIR` 설정 확인
- 디버그 모드에서 파일 경로 확인

---

## 개선 내용 요약

### Error Handling 개선사항

1. **plan_mode.py**
   - ✅ Draft plan 생성 실패 시 retry with simplified prompt
   - ✅ Refine 실패 시 이전 plan 유지
   - ✅ Plan 저장 실패 시 in-memory plan으로 계속
   - ✅ spawn_explore 실패 시 적절한 에러 메시지
   - ✅ Exception 발생 시 debug mode에서 traceback 출력

2. **main.py**
   - ✅ Plan 파일 읽기 실패: FileNotFoundError, PermissionError 분리 처리
   - ✅ 빈 plan 파일 감지
   - ✅ TodoWrite 생성 실패 시 graceful fallback
   - ✅ Plan 실행 중 exception 처리
   - ✅ plan_mode_loop() 호출 exception 처리
   - ✅ Plan path가 없을 때 in-memory plan 사용

3. **slash_commands.py**
   - ✅ 빈 task 입력 검증

### E2E 테스트

**자동 테스트 (5/5 통과):**
- ✅ Slash Command Registry
- ✅ Plan File Creation
- ✅ Step Extraction
- ✅ Error Handling
- ✅ PlanModeResult Dataclass

**수동 테스트 체크리스트:**
- [ ] Test 1: Basic Plan Mode Flow
- [ ] Test 2: Plan Refinement Flow
- [ ] Test 3: Plan Cancellation
- [ ] Test 4: Show Command
- [ ] Test 5: spawn_explore Auto-call
- [ ] Test 6: Error Handling

---

## 다음 단계

1. **수동 테스트 실행**: 위의 6가지 수동 테스트 케이스 실행
2. **실제 프로젝트 적용**: 실제 Verilog 작업에서 plan mode 사용
3. **피드백 수집**: 사용 중 발견된 개선점 기록
4. **문서 업데이트**: 사용자 가이드 작성

---

## 결론

**현재 상태:**
- ✅ 모든 Phase 완료
- ✅ Error handling 강화 완료
- ✅ 자동 E2E 테스트 5/5 통과
- ⏳ 수동 테스트 대기

**준비 완료!** 🎉

Plan Mode는 production-ready 상태이며, 수동 테스트를 통해 최종 검증만 남았습니다.
