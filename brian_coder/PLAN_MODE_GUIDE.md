# 📋 Plan Mode Guide

Brian Coder의 Plan Mode는 복잡한 작업을 체계적으로 관리할 수 있는 기능입니다.

---

## 🎯 Plan Mode란?

복잡한 작업을 수행하기 전에:
1. **계획 수립** - 작업을 단계별로 나눔
2. **사용자 승인** (선택) - 사용자가 계획을 검토하고 수정
3. **순차 실행** - 각 단계를 순서대로 실행
4. **진행 추적** - 완료된 단계를 표시

---

## 🛠️ 사용 가능한 도구

### 기본 Plan 도구
```python
create_plan(task_description, steps)
get_plan()
mark_step_done(step_number)
```

### Interactive 도구 (권장)
```python
wait_for_plan_approval()  # 사용자 승인 대기
check_plan_status()       # 승인 상태 확인
```

---

## 📖 사용 방법

### **방법 1: 자동 실행 (AI 주도)**

LLM이 계획을 세우고 바로 실행합니다.

```
You: Design a counter with testbench and simulate it

Brian Coder:
→ create_plan(...)
→ [Step 1] write_file("counter.v", ...)
→ mark_step_done(1)
→ [Step 2] write_file("counter_tb.v", ...)
→ mark_step_done(2)
→ [Step 3] run_command("iverilog ...")
→ ...
```

**장점**: 빠름, 간단함
**단점**: 사용자 제어 없음

---

### **방법 2: Interactive Planning (사용자 승인, 권장 ⭐)**

사용자가 계획을 검토하고 수정한 후 실행합니다.

#### **Step-by-Step 워크플로우**

##### 1️⃣ 사용자가 작업 요청
```bash
You: Design a complete SPI master controller with testbench
```

##### 2️⃣ LLM이 초안 계획 생성
```
Brian Coder:
Thought: This is complex. I should create a plan and get user approval.
Action: create_plan(task_description="SPI Master Design",
                    steps="Create spi_master.v\nCreate testbench\nCompile\nSimulate")
Observation: Plan created.

Action: wait_for_plan_approval()
Observation: Plan saved to 'current_plan.md'. Waiting for approval...
```

##### 3️⃣ 사용자가 계획 검토 및 수정

**Terminal:**
```bash
$ cat current_plan.md
```

**파일 내용:**
```markdown
# USER INSTRUCTION:
# Review this plan and make any changes you want.
# When ready to proceed, add 'APPROVED' on the line below:
# STATUS:

---

# Task Plan
## Task: SPI Master Design

## Steps:
1. Create spi_master.v
2. Create testbench
3. Compile
4. Simulate
```

**사용자가 편집:** (vim, vscode, nano 등 사용)
```markdown
# STATUS: APPROVED

---

# Task Plan
## Task: SPI Master Design with Extra Features

## Steps:
1. Create spi_master.v with CPOL/CPHA support
2. Create comprehensive testbench with multiple test cases
3. Add assertions for protocol checking
4. Compile with iverilog
5. Run simulation with VCD output
6. Analyze waveforms and generate report
```

##### 4️⃣ 사용자가 승인 완료 알림
```
You: I've approved the plan. Please continue.
```

##### 5️⃣ LLM이 승인 확인 후 실행
```
Brian Coder:
Action: check_plan_status()
Observation: ✅ Plan is APPROVED!

Thought: Great! I'll execute step 1.
Action: write_file(path="spi_master.v", content="""...""")
Observation: Successfully wrote to 'spi_master.v'

Action: mark_step_done(step_number=1)
Observation: Step 1 marked as done.

[계속 진행...]
```

---

## 💡 실전 예시

### **예시 1: UART 설계**

```bash
You: Design a UART transmitter. I want to review the plan first.

Brian:
Action: create_plan(
    task_description="UART Transmitter Design",
    steps="""Create uart_tx.v module with configurable baud
Create uart_tx_tb.v testbench
Add start/stop bit logic
Compile with iverilog
Simulate transmission of 0x55
Analyze timing diagram"""
)

Action: wait_for_plan_approval()
```

**사용자가 수정:**
```markdown
# STATUS: APPROVED

## Steps:
1. Create uart_tx.v with 8-N-1 format (8 data bits, no parity, 1 stop bit)
2. Add parameterized baud rate generator (default 9600)
3. Create uart_tx_tb.v with test cases: 0x00, 0x55, 0xAA, 0xFF
4. Add VCD waveform generation
5. Compile with iverilog -Wall for warnings
6. Run simulation and capture output
7. Verify timing with baud rate calculator
8. Document the design in README.md
```

---

### **예시 2: 복잡한 프로젝트**

```bash
You: Create a complete AXI4-Lite slave interface with register file.
I need this to be production-ready with proper planning.

Brian:
[Creates initial plan]

You: [Edits plan to add:]
- Formal verification steps
- Compliance checking
- Performance analysis
- Documentation generation

Brian:
[Executes refined plan]
```

---

## 📁 Plan 파일 구조

### 승인 전 (Before Approval)
```markdown
# USER INSTRUCTION:
# STATUS:

---

# Task Plan
## Task: Counter Design

## Steps:
1. Create counter.v
2. Create testbench
```

### 승인 후 (After Approval)
```markdown
# STATUS: APPROVED

---

# Task Plan
## Task: Enhanced Counter Design

## Steps:
1. Create counter.v with enable signal ✅
2. Create testbench with edge cases
3. Compile
4. Simulate
```

---

## 🎓 Best Practices

### ✅ DO:
- 복잡한 작업에는 항상 Plan Mode 사용
- Interactive mode로 계획을 검토
- 단계를 구체적으로 작성
- 완료된 단계를 mark_step_done으로 표시
- 계획에 예상 출력/검증 포함

### ❌ DON'T:
- 간단한 작업에 Plan Mode 남용
- 너무 모호한 단계 작성
- 승인 없이 중요한 작업 실행
- 계획 없이 multi-step 작업 시작

---

## 🔧 Troubleshooting

### Q: Plan이 생성되지 않아요
```bash
# Check if plan file exists
ls -la current_plan.md

# If not, create manually
python3 -c "import tools; print(tools.create_plan('Test', 'Step1\nStep2'))"
```

### Q: 승인했는데 인식이 안 돼요
```bash
# Check approval status
grep "STATUS" current_plan.md

# Should show: # STATUS: APPROVED
```

### Q: 계획을 다시 시작하고 싶어요
```bash
rm current_plan.md
# Then create new plan
```

---

## 🚀 고급 사용법

### Plan 템플릿 사용

**Verilog 설계 템플릿:**
```
1. Research requirements and specifications
2. Create RTL module (.v)
3. Create comprehensive testbench (_tb.v)
4. Add assertions and coverage
5. Compile with warnings enabled
6. Run simulation with VCD output
7. Analyze waveforms
8. Document results
```

### 반복적 개선 워크플로우

```
Round 1: Create initial plan → Review → Approve → Execute
Round 2: Identify issues → Update plan → Approve → Fix
Round 3: Final verification → Approve → Complete
```

---

## 📊 Plan Mode vs No Plan

| 기능 | Plan Mode | No Plan |
|------|-----------|---------|
| 작업 구조화 | ✅ 명확한 단계 | ❌ 즉흥적 |
| 사용자 제어 | ✅ 승인 필요 | ❌ 자동 실행 |
| 진행 추적 | ✅ ✅ 표시 | ❌ 불명확 |
| 수정 가능 | ✅ 중간 수정 | ❌ 어려움 |
| 복잡한 작업 | ✅ 적합 | ❌ 혼란 |
| 간단한 작업 | ⚠️ 과도 | ✅ 적합 |

---

## 📚 더 많은 예시

### Example: 전체 프로젝트 워크플로우

```bash
You: Create a complete I2C master controller project

Brian:
[Creates plan]

You: [Reviews and adds:]
- Multi-master support
- Clock stretching
- Error recovery
- Formal verification

Brian:
[Executes step by step with your approval]
```

---

## 🎯 Summary

**Interactive Plan Mode를 사용하면:**
- ✅ 작업이 명확해집니다
- ✅ 사용자가 완전히 제어합니다
- ✅ 실수를 사전에 방지합니다
- ✅ 복잡한 프로젝트를 관리하기 쉽습니다

**언제 사용하나요?**
- 3단계 이상의 복잡한 작업
- 중요한 설계 작업
- 사용자 검토가 필요한 경우
- 학습/교육 목적

**시작하기:**
```bash
python3 main.py
You: Design [your project]. Create a plan for my review first.
```

Happy Planning! 🚀
