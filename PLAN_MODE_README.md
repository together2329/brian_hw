# Interactive Plan Mode - 사용 가이드

## 🎯 개요

Interactive Plan Mode는 복잡한 작업을 수행하기 전에 사용자와 대화하며 계획을 수립하고 개선하는 기능입니다.

### 주요 특징

- ✅ **대화형 Plan 개선**: 사용자 피드백으로 plan을 반복적으로 개선
- ✅ **자동 코드 탐색**: Plan Agent가 필요 시 spawn_explore 자동 호출
- ✅ **Plan 저장**: Plan을 파일로 저장하여 재사용 가능
- ✅ **Main Agent 통합**: 승인된 plan을 Main Agent가 자동 실행
- ✅ **TodoWrite 연동**: Steps를 자동으로 todo list로 tracking
- ✅ **강력한 Error Handling**: 실패 시 graceful degradation

---

## 🚀 빠른 시작

### 1. Plan Mode 진입

```bash
python3 brian_coder/src/main.py
```

```
You: /plan Create a simple 4-bit up counter with enable signal
```

### 2. Plan 검토 및 개선

Plan Agent가 초안을 생성합니다:

```
============================================================
[Plan Mode] Entering interactive planning mode
Commands: approve | cancel | show
============================================================

[Plan Mode] Draft plan created:

## Task Analysis
Create a simple 4-bit up counter module with enable signal...

## Implementation Steps
1. Create module skeleton with 4-bit counter register
2. Implement counter logic with enable control
3. Add testbench with enable/disable test cases
4. Compile with iverilog
5. Run simulation and verify waveforms

## Verification Strategy
- Test counting from 0 to 15
- Test enable=0 holds value
- Test rollover from 15 to 0

## Success Criteria
- Counter increments on clock when enable=1
- Counter holds when enable=0
- Clean rollover at max value

Plan feedback (or approve/cancel/show):
```

### 3-1. Plan 개선 (선택)

```
Plan feedback: Step 2를 더 구체적으로 설명해주세요
```

Plan Agent가 plan을 개선합니다:

```
[Plan Mode] Refining plan...

[Plan Mode] Updated plan:

## Implementation Steps
1. Create module skeleton with 4-bit counter register
2. Implement counter logic with enable control
   - Declare 4-bit counter register (reg [3:0] count)
   - On posedge clk: if enable=1, increment count
   - If enable=0, hold current value
   - Automatic rollover on overflow (4'hF -> 4'h0)
3. Add testbench with enable/disable test cases
...
```

### 3-2. Plan 승인

```
Plan feedback: approve
```

### 4. Main Agent 자동 실행

Plan이 저장되고 Main Agent가 자동으로 실행합니다:

```
[Plan Mode] Plan approved and saved: ~/.brian_coder/plans/create-a-simple-4-bit-20251221-205123.md

[Main Agent] Executing plan...

[Todos]
▶️  1. Create module skeleton with 4-bit counter register
⏸   2. Implement counter logic with enable control
⏸   3. Add testbench with enable/disable test cases
⏸   4. Compile with iverilog
⏸   5. Run simulation and verify waveforms

[Step 1/5] Creating module skeleton...
```

---

## 📝 사용 가능한 명령어

Plan Mode에서 사용할 수 있는 명령어:

| 명령어 | 설명 |
|--------|------|
| `approve` | Plan을 승인하고 Main Agent 실행 |
| `cancel` | Plan Mode 취소하고 Main chat로 복귀 |
| `show` | 현재 plan 다시 보기 |
| 피드백 입력 | Plan 개선 요청 (예: "Step 2를 더 구체적으로") |

---

## ⚙️ 고급 설정

### 환경변수 설정

`~/.brian_coder/.config` 또는 환경변수로 설정:

```bash
# Plan 저장 디렉토리
export PLAN_DIR="~/.brian_coder/plans"

# Debug 모드 (상세 로그 출력)
export PLAN_MODE_DEBUG=true

# Full debug (모든 prompt/response 출력)
export PLAN_MODE_DEBUG_FULL=true

# Stream 모드 (실시간 출력)
export PLAN_MODE_STREAM=true

# Context mode
export PLAN_MODE_CONTEXT_MODE="full"  # full, summary, recent
export PLAN_MODE_CONTEXT_RECENT_N=12   # recent mode 시 최근 N개 메시지

# Context 최대 길이
export PLAN_MODE_CONTEXT_MAX_CHARS=10000
```

### Context Mode 설명

- **full** (기본): 전체 대화 히스토리 전달
- **summary**: 대화 히스토리를 LLM으로 요약하여 전달
- **recent**: 최근 N개 메시지만 전달

---

## 💡 사용 예시

### 예시 1: Verilog 모듈 설계

```
You: /plan Design async FIFO with Gray code pointers

[Plan Agent가 초안 생성]

Plan feedback: Add CDC (Clock Domain Crossing) details to Step 3

[Plan Agent가 개선]

Plan feedback: Include formal verification steps

[Plan Agent가 추가 개선]

Plan feedback: approve

[Main Agent 실행]
```

### 예시 2: 기존 코드 참조

Plan Agent가 자동으로 기존 코드를 탐색합니다:

```
You: /plan Create SPI slave similar to existing I2C slave

[Plan Agent가 자동으로 spawn_explore("I2C slave") 호출]
[기존 코드를 참조하여 plan 생성]

Plan feedback: Use same register interface as I2C

[Plan 개선]

Plan feedback: approve
```

### 예시 3: 복잡한 시스템

```
You: /plan Create complete AXI4-Lite bridge with register file and interrupt controller

[Plan Agent가 상세한 plan 생성]

Plan feedback: Split into multiple phases with milestones

[Phase별로 구조화된 plan]

Plan feedback: Add unit test for each phase

[각 phase별 테스트 추가]

Plan feedback: approve
```

---

## 🔧 문제 해결

### 문제 1: Plan Mode가 작동하지 않음

**증상:**
```
You: /plan Create counter
Unknown command: /plan
```

**해결:**
- Brian Coder가 최신 버전인지 확인
- `brian_coder/core/slash_commands.py`에서 `/plan` 등록 확인

### 문제 2: Plan 생성이 너무 느림

**해결:**
```bash
# Context mode를 recent로 변경
export PLAN_MODE_CONTEXT_MODE="recent"
export PLAN_MODE_CONTEXT_RECENT_N=8

# 또는 summary 사용
export PLAN_MODE_CONTEXT_MODE="summary"
```

### 문제 3: Plan이 너무 간단함

**해결:**
- 더 구체적인 task 설명 제공
- Plan feedback으로 상세화 요청:
  ```
  Plan feedback: Please provide more detailed steps for each implementation phase
  ```

### 문제 4: spawn_explore가 작동하지 않음

**해결:**
- Debug mode 활성화하여 확인:
  ```bash
  export PLAN_MODE_DEBUG=true
  ```
- Plan Agent의 ALLOWED_TOOLS 확인

---

## 📊 Best Practices

### 1. Task 설명은 명확하게

❌ **나쁜 예:**
```
/plan counter
```

✅ **좋은 예:**
```
/plan Create a 16-bit up/down counter with enable, reset, and overflow flag
```

### 2. 단계적으로 개선

❌ **나쁜 예:**
```
Plan feedback: 전체 다시 작성해주세요
```

✅ **좋은 예:**
```
Plan feedback: Step 2의 Gray code 변환 로직을 더 구체적으로 설명해주세요
Plan feedback: Testbench에 corner case 추가해주세요
```

### 3. 필요한 경우에만 사용

**Plan Mode를 사용하면 좋은 경우:**
- 복잡한 multi-step 작업
- 여러 파일을 수정하는 작업
- 아키텍처 결정이 필요한 작업
- 기존 코드 패턴을 따라야 하는 작업

**Plan Mode가 필요 없는 경우:**
- 단순한 버그 수정
- 한 줄 코드 수정
- 명확한 단일 작업

### 4. Plan 파일 재사용

Plan 파일은 `~/.brian_coder/plans/`에 저장됩니다:

```bash
# 저장된 plan 확인
ls ~/.brian_coder/plans/

# Plan 재사용 (직접 파일 경로 전달)
# 현재는 수동으로 파일 내용을 복사하여 사용
```

---

## 📈 성능 최적화

### Context 크기 제한

대화 히스토리가 길면 느려질 수 있습니다:

```bash
# 최근 메시지만 사용
export PLAN_MODE_CONTEXT_MODE="recent"
export PLAN_MODE_CONTEXT_RECENT_N=10

# 또는 최대 문자 수 제한
export PLAN_MODE_CONTEXT_MAX_CHARS=5000
```

### Refinement 횟수 제한

plan_mode_loop()의 max_rounds 파라미터로 제한 가능 (기본: 10)

---

## 🎓 학습 자료

### 관련 문서

- **PLAN_MODE_E2E_TEST_GUIDE.md**: E2E 테스트 가이드 및 예제
- **PLAN_MODE_IMPROVEMENTS.md**: Error handling 개선 내역
- **test_plan_mode_e2e.py**: 자동 테스트 스크립트

### 실습 예제

1. **간단한 예제**: 4-bit counter
2. **중급 예제**: Async FIFO with Gray code
3. **고급 예제**: Complete AXI4-Lite bridge

---

## ❓ FAQ

**Q: Plan Mode와 일반 모드의 차이는?**

A: Plan Mode는 먼저 plan을 수립하고 사용자 승인 후 실행합니다. 일반 모드는 즉시 실행합니다.

**Q: Plan을 수정하려면?**

A: Plan feedback으로 개선 요청하거나, cancel 후 다시 시작하세요.

**Q: Plan 파일은 어디에 저장되나요?**

A: 기본적으로 `~/.brian_coder/plans/`에 저장됩니다. `PLAN_DIR` 환경변수로 변경 가능합니다.

**Q: spawn_explore는 자동으로 호출되나요?**

A: Plan Agent가 필요하다고 판단하면 자동으로 호출합니다. 사용자가 명시적으로 요청할 수도 있습니다.

**Q: Plan Mode 중에 에러가 발생하면?**

A: Error handling이 강화되어 있어 대부분의 에러는 graceful하게 처리됩니다. Debug mode에서 상세 정보를 확인할 수 있습니다.

---

## 🤝 기여 및 피드백

Plan Mode 사용 중 발견한 버그나 개선 아이디어는 이슈로 등록해주세요.

---

## 📄 라이선스

Brian Coder와 동일한 라이선스를 따릅니다.

---

**Happy Planning! 🚀**
